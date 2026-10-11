from django.db import models


class Verdict(models.TextChoices):
    """提交状态机：pending → judging → 终态"""

    PENDING = "pending", "等待判题"
    JUDGING = "judging", "判题中"
    ACCEPTED = "accepted", "通过"
    WRONG_ANSWER = "wrong_answer", "答案错误"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded", "超时"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded", "内存超限"
    RUNTIME_ERROR = "runtime_error", "运行时错误"
    COMPILE_ERROR = "compile_error", "编译错误"
    SYSTEM_ERROR = "system_error", "系统错误"


NON_TERMINAL_STATUSES = {Verdict.PENDING, Verdict.JUDGING}
TERMINAL_STATUSES = {v for v in Verdict.values if v not in NON_TERMINAL_STATUSES}
