from django.conf import settings
from django.db import models


class Notification(models.Model):
    """站内通知

    统一由 Notification.notify() 写入，前端通过通知中心查看。
    """

    class Kind(models.TextChoices):
        DISCUSSION_REPLY = "discussion_reply", "讨论回复"
        SYSTEM = "system", "系统通知"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications", verbose_name="接收用户",
    )
    kind = models.CharField(
        "类型", max_length=32, choices=Kind.choices, default=Kind.SYSTEM, db_index=True
    )
    title = models.CharField("标题", max_length=120)
    content = models.TextField("内容", blank=True)
    link = models.CharField("跳转链接", max_length=255, blank=True)
    is_read = models.BooleanField("是否已读", default=False, db_index=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = "通知"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.title}"

    @classmethod
    def notify(cls, user, title, content="", link="", kind=Kind.SYSTEM):
        """给指定用户写一条通知；自己触发自己的动作时不打扰。"""
        if user is None:
            return None
        return cls.objects.create(
            user=user, kind=kind, title=title, content=content, link=link
        )
