"""AI 助理服务层：OpenAI 兼容流式客户端 + 本地规则降级"""
import json

import httpx
from django.conf import settings

SYSTEM_PROMPT = (
    "你是 CodePractice 在线代码练习评测平台的 AI 助理，"
    "擅长算法与编程教学。回答要求：思路清晰、步骤化、给出关键代码片段（Python 优先）、"
    "控制篇幅，先讲思路再给实现，避免直接给出完整题解除非用户明确要求。"
    "请始终使用中文回答。"
)

HISTORY_WINDOW = 10  # 携带最近 10 条历史消息作为上下文


def build_context(problem, history_messages, user_message):
    """构造 OpenAI 兼容的 messages 数组"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if problem is not None:
        description_brief = problem.description[:1500]
        messages.append(
            {
                "role": "system",
                "content": (
                    f"用户当前正在练习以下题目，请结合题目回答：\n"
                    f"标题：{problem.title}\n"
                    f"难度：{problem.get_difficulty_display()}\n"
                    f"时限：{problem.time_limit_ms}ms / 内存限制：{problem.memory_limit_kb}KB\n"
                    f"题面：\n{description_brief}"
                ),
            }
        )
    for m in history_messages:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": user_message})
    return messages


def stream_remote_reply(messages):
    """调用 OpenAI 兼容 API 的流式回复，逐块 yield delta 字符串；失败抛异常"""
    url = f"{settings.AI_API_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.AI_MODEL,
        "messages": messages,
        "stream": True,
    }
    with httpx.stream(
        "POST", url, headers=headers, json=payload, timeout=settings.AI_TIMEOUT_SECONDS
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = (choices[0].get("delta") or {}).get("content") or ""
            if delta:
                yield delta


def local_reply(problem, user_message):
    """无 API key 或上游失败时的本地规则化回复"""
    parts = [f"已收到你的问题：「{user_message[:80]}」"]

    if problem is not None:
        parts.append(
            f"关于题目《{problem.title}》（{problem.get_difficulty_display()}，"
            f"时限 {problem.time_limit_ms}ms / 内存 {problem.memory_limit_kb}KB）："
        )
        parts.append(
            "1. 先通读题面与示例输入输出，确认数据范围与边界条件；\n"
            "2. 想清楚暴力解法，估算复杂度是否在时限内；\n"
            "3. 再考虑优化方向（排序、哈希、双指针、动态规划等）；\n"
            "4. 提交代码后根据判题反馈（WA/TLE/MLE/RE）逐项排查。"
        )
    else:
        parts.append(
            "你可以先选择一道题目，再带着题目上下文向我提问，我能给出更有针对性的建议。"
        )

    parts.append("（提示：在 backend/.env 中配置 AI_API_KEY 即可启用真实大模型流式助理）")
    return "\n\n".join(parts)
