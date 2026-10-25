from django.conf import settings
from django.db import models


class UserAchievement(models.Model):
    """用户已解锁的成就（解锁时落库，保证首次解锁时间可追溯）"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="achievements", verbose_name="用户",
    )
    code = models.CharField("成就编码", max_length=50)
    unlocked_at = models.DateTimeField("解锁时间", auto_now_add=True)

    class Meta:
        verbose_name = "用户成就"
        verbose_name_plural = "用户成就"
        ordering = ["-unlocked_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "code"], name="uniq_user_achievement"),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.code}"


# 成就定义：metric 对应 views 里计算的指标，target 为达成阈值
ACHIEVEMENTS = [
    {
        "code": "first_ac",
        "name": "初露锋芒",
        "description": "首次通过一道题目",
        "category": "入门",
        "metric": "ac_problems",
        "target": 1,
    },
    {
        "code": "ac_10",
        "name": "小有所成",
        "description": "累计通过 10 道不同题目",
        "category": "里程碑",
        "metric": "ac_problems",
        "target": 10,
    },
    {
        "code": "ac_50",
        "name": "渐入佳境",
        "description": "累计通过 50 道不同题目",
        "category": "里程碑",
        "metric": "ac_problems",
        "target": 50,
    },
    {
        "code": "ac_100",
        "name": "百题斩",
        "description": "累计通过 100 道不同题目",
        "category": "里程碑",
        "metric": "ac_problems",
        "target": 100,
    },
    {
        "code": "submit_100",
        "name": "百炼成钢",
        "description": "累计提交 100 次",
        "category": "坚持",
        "metric": "total_submissions",
        "target": 100,
    },
    {
        "code": "easy_ac",
        "name": "稳扎稳打",
        "description": "通过一道简单题",
        "category": "难度",
        "metric": "easy_ac",
        "target": 1,
    },
    {
        "code": "medium_ac",
        "name": "渐入深处",
        "description": "通过一道中等题",
        "category": "难度",
        "metric": "medium_ac",
        "target": 1,
    },
    {
        "code": "hard_ac",
        "name": "登峰造极",
        "description": "通过一道困难题",
        "category": "难度",
        "metric": "hard_ac",
        "target": 1,
    },
]

ACHIEVEMENT_BY_CODE = {item["code"]: item for item in ACHIEVEMENTS}
