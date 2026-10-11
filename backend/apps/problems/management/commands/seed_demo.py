"""导入示例题目与测试用例（幂等，可重复执行）"""
from django.core.management.base import BaseCommand

from apps.problems.models import Problem, Tag, TestCase

PROBLEMS = [
    {
        "title": "A+B 问题",
        "difficulty": "easy",
        "tags": ["入门", "模拟"],
        "time_limit_ms": 2000,
        "memory_limit_kb": 65536,
        "description": """## 题目描述

输入两个整数 $a$ 和 $b$，输出它们的和。

## 输入格式

一行，两个整数 $a, b$（$0 \\le a, b \\le 10^9$），以空格分隔。

## 输出格式

一行，一个整数，表示 $a + b$ 的结果。

## 提示

注意使用 64 位整数。""",
        "reference_answer": """a, b = map(int, input().split())
print(a + b)""",
        "cases": [
            {"input_data": "1 2\n", "expected_output": "3\n", "is_sample": True, "is_hidden": False, "order": 0},
            {"input_data": "1000000000 1000000000\n", "expected_output": "2000000000\n", "is_sample": False, "is_hidden": True, "order": 1},
            {"input_data": "0 0\n", "expected_output": "0\n", "is_sample": False, "is_hidden": True, "order": 2},
        ],
    },
    {
        "title": "判断质数",
        "difficulty": "easy",
        "tags": ["数学", "数论"],
        "time_limit_ms": 2000,
        "memory_limit_kb": 65536,
        "description": """## 题目描述

给定一个正整数 $n$，判断它是否为质数。

## 输入格式

一行，一个正整数 $n$（$1 \\le n \\le 10^{12}$）。

## 输出格式

如果是质数输出 `Yes`，否则输出 `No`。

## 提示

$10^{12}$ 规模需要 $O(\\sqrt{n})$ 试除法，暴力枚举会超时（TLE）。""",
        "reference_answer": """import math

n = int(input())
if n < 2:
    print("No")
else:
    is_prime = True
    for i in range(2, int(math.isqrt(n)) + 1):
        if n % i == 0:
            is_prime = False
            break
    print("Yes" if is_prime else "No")""",
        "cases": [
            {"input_data": "2\n", "expected_output": "Yes\n", "is_sample": True, "is_hidden": False, "order": 0},
            {"input_data": "999999999989\n", "expected_output": "Yes\n", "is_sample": False, "is_hidden": True, "order": 1},
            {"input_data": "999999999999\n", "expected_output": "No\n", "is_sample": False, "is_hidden": True, "order": 2},
            {"input_data": "1\n", "expected_output": "No\n", "is_sample": False, "is_hidden": True, "order": 3},
        ],
    },
    {
        "title": "字符串反转",
        "difficulty": "medium",
        "tags": ["字符串"],
        "time_limit_ms": 2000,
        "memory_limit_kb": 65536,
        "description": """## 题目描述

给定一行字符串，将其中的每个单词反转后按原顺序输出。

- 单词由空格分隔
- 标点符号视为单词的一部分

## 输入格式

一行，一个字符串 $s$（$1 \\le |s| \\le 10^5$）。

## 输出格式

一行，处理后的字符串。

## 示例解释

输入 `hello world`，输出 `olleh dlrow`。""",
        "reference_answer": """s = input()
print(' '.join(word[::-1] for word in s.split(' ')))""",
        "cases": [
            {"input_data": "hello world\n", "expected_output": "olleh dlrow\n", "is_sample": True, "is_hidden": False, "order": 0},
            {"input_data": "CodePractice online judge\n", "expected_output": "ecitcarPedoC enilno egduj\n", "is_sample": True, "is_hidden": False, "order": 1},
            {"input_data": "a\n", "expected_output": "a\n", "is_sample": False, "is_hidden": True, "order": 2},
        ],
    },
    {
        "title": "区间求和（卡暴力）",
        "difficulty": "hard",
        "tags": ["前缀和", "数据结构"],
        "time_limit_ms": 2000,
        "memory_limit_kb": 65536,
        "description": """## 题目描述

给定一个长度为 $n$ 的整数数组，回答 $q$ 次询问：每次询问给定区间 $[l, r]$，求区间元素和。

## 输入格式

第一行两个整数 $n, q$（$1 \\le n \\le 10^6$，$1 \\le q \\le 10^5$）。

第二行 $n$ 个整数 $a_i$（$|a_i| \\le 10^9$）。

接下来 $q$ 行，每行两个整数 $l, r$（$1 \\le l \\le r \\le n$）。

## 输出格式

对每次询问输出一行区间和。

## 提示

使用前缀和预处理。每次询问都遍历区间的 $O(nq)$ 暴力写法会超时（TLE）。

读入数据量较大，Python 建议使用 `sys.stdin`。""",
        "reference_answer": """import sys

def main():
    data = sys.stdin.buffer.read().split()
    idx = 0
    n = int(data[idx]); idx += 1
    q = int(data[idx]); idx += 1
    prefix = [0] * (n + 1)
    for i in range(1, n + 1):
        prefix[i] = prefix[i - 1] + int(data[idx]); idx += 1
    out = []
    for _ in range(q):
        l = int(data[idx]); idx += 1
        r = int(data[idx]); idx += 1
        out.append(str(prefix[r] - prefix[l - 1]))
    sys.stdout.write("\\n".join(out) + "\\n")

main()""",
        "cases": [
            {
                "input_data": "5 2\n1 2 3 4 5\n1 3\n2 5\n",
                "expected_output": "6\n14\n",
                "is_sample": True, "is_hidden": False, "order": 0,
            },
            {
                "input_data": "3 1\n-1000000000 1000000000 -1\n1 3\n",
                "expected_output": "-1\n",
                "is_sample": False, "is_hidden": True, "order": 1,
            },
            {
                "input_data": "100000 1\n" + " ".join(["1"] * 100000) + "\n1 100000\n",
                "expected_output": "100000\n",
                "is_sample": False, "is_hidden": True, "order": 2,
            },
        ],
    },
]


class Command(BaseCommand):
    help = "导入示例题目、标签与测试用例"

    def handle(self, *args, **options):
        created_count = 0
        for item in PROBLEMS:
            problem, created = Problem.objects.get_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "difficulty": item["difficulty"],
                    "time_limit_ms": item["time_limit_ms"],
                    "memory_limit_kb": item["memory_limit_kb"],
                    "allowed_languages": ["python"],
                    "reference_answer": item["reference_answer"],
                    "is_public": True,
                },
            )
            if created:
                created_count += 1
                for tag_name in item["tags"]:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    problem.tags.add(tag)
                for case in item["cases"]:
                    TestCase.objects.create(problem=problem, **case)
                self.stdout.write(self.style.SUCCESS(f"已创建题目：{problem.title}"))
            else:
                self.stdout.write(f"已存在，跳过：{problem.title}")

        self.stdout.write(
            self.style.SUCCESS(f"完成。新增 {created_count} 道题目，共 {Problem.objects.count()} 道")
        )
