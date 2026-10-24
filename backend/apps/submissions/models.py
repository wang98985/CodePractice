from django.conf import settings
from django.db import models

from apps.judge.verdicts import Verdict

MAX_CODE_LENGTH = 64 * 1024  # 代码长度上限 64KB


class Submission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="submissions", verbose_name="提交人",
    )
    problem = models.ForeignKey(
        "problems.Problem", on_delete=models.CASCADE,
        related_name="submissions", verbose_name="题目",
    )
    language = models.CharField("语言", max_length=20)
    code = models.TextField("代码", max_length=MAX_CODE_LENGTH)
    status = models.CharField(
        "状态", max_length=30, choices=Verdict.choices,
        default=Verdict.PENDING, db_index=True,
    )
    time_used_ms = models.IntegerField("耗时(ms)", null=True, blank=True)
    memory_used_kb = models.IntegerField("内存(KB)", null=True, blank=True)
    passed_cases = models.PositiveIntegerField("通过用例数", default=0)
    total_cases = models.PositiveIntegerField("用例总数", default=0)
    error_message = models.TextField("错误信息", blank=True, default="")
    created_at = models.DateTimeField("提交时间", auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField("判题完成时间", null=True, blank=True)

    class Meta:
        verbose_name = "提交记录"
        verbose_name_plural = "提交记录"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["problem", "-created_at"]),
            # 排行榜按用户聚合，覆盖 (user, status) 过滤与计数
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"Submission#{self.pk} {self.user} @{self.problem} [{self.status}]"
