"""超管批量导入题目：CSV（含表头）/ JSON 数组 文本解析与入库。

CSV 表头（列顺序无关，缺省列取默认值）：
    标题,题面,难度,时限ms,内存MB,标签,参考答案,示例输入,示例输出,隐藏输入,隐藏输出,公开

- 难度：easy/medium/hard 或 简单/中等/困难
- 标签分隔符：; 或 ； 或 、
- 多组示例/隐藏用例：字段内用 ||| 分隔，输入与输出按顺序一一对应
- 公开：true/1/yes/是 视为公开，默认 false
- CSV 引号字段内允许换行；换行符统一为 \n
"""

import csv
import io
import json

from django.db import transaction

from .models import Problem, Tag, TestCase

COLUMNS = [
    "标题", "题面", "难度", "时限ms", "内存MB", "标签", "参考答案",
    "示例输入", "示例输出", "隐藏输入", "隐藏输出", "公开",
]

DIFFICULTY_MAP = {
    "easy": Problem.Difficulty.EASY,
    "medium": Problem.Difficulty.MEDIUM,
    "hard": Problem.Difficulty.HARD,
    "简单": Problem.Difficulty.EASY,
    "中等": Problem.Difficulty.MEDIUM,
    "困难": Problem.Difficulty.HARD,
}

# JSON 字段别名（英文字段名 → CSV 列名）
JSON_ALIASES = {
    "title": "标题", "description": "题面", "difficulty": "难度",
    "time_limit_ms": "时限ms", "memory_limit_mb": "内存MB",
    "tags": "标签", "reference_answer": "参考答案",
    "sample_input": "示例输入", "sample_output": "示例输出",
    "hidden_input": "隐藏输入", "hidden_output": "隐藏输出",
    "is_public": "公开",
}

CASE_SEP = "|||"


def decode_uploaded(raw: bytes) -> str:
    """文件字节流解码：utf-8(-sig) → gbk → 兜底替换错误字符"""
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _normalize_text(value: str) -> str:
    """统一换行符并去掉首尾空行/空白"""
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def _split_cases(value) -> list:
    """按 ||| 切分多组用例输入/输出"""
    if value is None:
        return []
    text = _normalize_text(str(value))
    if not text:
        return []
    return [p for p in (_normalize_text(part) for part in text.split(CASE_SEP)) if p]


def parse_rows(text: str):
    """解析为 (行号, 行字典) 列表；行字典键为 CSV 列名"""
    text = text.lstrip("\ufeff").strip()
    rows = []
    if text.startswith("["):
        data = json.loads(text)
        for idx, item in enumerate(data, start=1):
            row = {}
            for key, value in item.items():
                row[JSON_ALIASES.get(str(key), str(key))] = value
            rows.append((idx, row))
        return rows

    reader = csv.DictReader(io.StringIO(text))
    for idx, raw in enumerate(reader, start=2):  # 第 1 行为表头
        row = {}
        for key, value in (raw or {}).items():
            if key is None or value is None:
                continue
            canonical = key.strip().lstrip("\ufeff")
            if canonical in COLUMNS:
                row[canonical] = value
        rows.append((idx, row))
    return rows


def _to_int(row, name, default, minimum):
    raw = str(row.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(float(raw))
    except ValueError:
        raise ValueError(f"{name} 必须是数字，收到: {raw!r}")
    if value < minimum:
        raise ValueError(f"{name} 不能小于 {minimum}")
    return value


def _parse_bool(row):
    raw = str(row.get("公开") or "").strip().lower()
    return raw in ("true", "1", "yes", "y", "是")


def build_problem(row, user) -> Problem:
    """校验单行并创建题目（含标签与测试用例），失败抛 ValueError"""
    title = str(row.get("标题") or "").strip()
    if not title:
        raise ValueError("标题不能为空")
    description = str(row.get("题面") or "").strip()
    if not description:
        raise ValueError("题面不能为空")

    difficulty_raw = str(row.get("难度") or "easy").strip().lower()
    difficulty = DIFFICULTY_MAP.get(difficulty_raw)
    if difficulty is None:
        raise ValueError(f"难度必须是 easy/medium/hard 或 简单/中等/困难，收到: {difficulty_raw!r}")

    time_limit_ms = _to_int(row, "时限ms", 2000, 100)
    memory_mb = _to_int(row, "内存MB", 64, 1)

    sample_inputs = _split_cases(row.get("示例输入"))
    sample_outputs = _split_cases(row.get("示例输出"))
    hidden_inputs = _split_cases(row.get("隐藏输入"))
    hidden_outputs = _split_cases(row.get("隐藏输出"))
    if len(sample_inputs) != len(sample_outputs):
        raise ValueError(
            f"示例输入({len(sample_inputs)}组)与示例输出({len(sample_outputs)}组)数量不一致，"
            f"多组请用 {CASE_SEP} 分隔"
        )
    if len(hidden_inputs) != len(hidden_outputs):
        raise ValueError(
            f"隐藏输入({len(hidden_inputs)}组)与隐藏输出({len(hidden_outputs)}组)数量不一致，"
            f"多组请用 {CASE_SEP} 分隔"
        )
    if not sample_inputs and not hidden_inputs:
        raise ValueError("至少需要一组示例或隐藏测试用例")

    tag_names = [
        t for t in (
            x.strip() for x in str(row.get("标签") or "").replace("；", ";").replace("、", ";").split(";")
        ) if t
    ]

    with transaction.atomic():
        problem = Problem.objects.create(
            title=title,
            description=description,
            difficulty=difficulty,
            time_limit_ms=time_limit_ms,
            memory_limit_kb=memory_mb * 1024,
            reference_answer=_normalize_text(row.get("参考答案") or ""),
            is_public=_parse_bool(row),
            created_by=user,
        )
        if tag_names:
            problem.tags.set([Tag.objects.get_or_create(name=name)[0] for name in tag_names])
        order = 0
        for case_input, case_output in zip(sample_inputs, sample_outputs):
            TestCase.objects.create(
                problem=problem, input_data=case_input, expected_output=case_output,
                is_sample=True, is_hidden=False, order=order,
            )
            order += 1
        for case_input, case_output in zip(hidden_inputs, hidden_outputs):
            TestCase.objects.create(
                problem=problem, input_data=case_input, expected_output=case_output,
                is_sample=False, is_hidden=True, order=order,
            )
            order += 1
    return problem


def import_problems(text: str, user):
    """批量导入，返回 (created, failed)；单行失败不影响其他行"""
    try:
        rows = parse_rows(text)
    except (json.JSONDecodeError, csv.Error) as exc:
        return [], [{"row": 0, "title": "", "error": f"解析失败: {exc}"}]
    if not rows:
        return [], [{"row": 0, "title": "", "error": "没有解析到任何题目行"}]

    created, failed = [], []
    for row_num, row in rows:
        title = str(row.get("标题") or "").strip()
        if not any(str(v or "").strip() for v in row.values()):
            continue  # 跳过空行
        try:
            problem = build_problem(row, user)
            created.append({"id": problem.id, "title": problem.title})
        except ValueError as exc:
            failed.append({"row": row_num, "title": title, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001 单行异常不阻断整批
            failed.append({"row": row_num, "title": title, "error": f"创建失败: {exc}"})
    return created, failed
