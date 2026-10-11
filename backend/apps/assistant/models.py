from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="chat_sessions", verbose_name="用户",
    )
    problem = models.ForeignKey(
        "problems.Problem", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="chat_sessions", verbose_name="关联题目",
    )
    title = models.CharField("会话标题", max_length=60, blank=True, default="新的对话")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "AI 会话"
        verbose_name_plural = "AI 会话"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ChatSession#{self.pk} {self.user} {self.title}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "用户"
        ASSISTANT = "assistant", "助理"
        SYSTEM = "system", "系统"

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages", verbose_name="会话"
    )
    role = models.CharField("角色", max_length=10, choices=Role.choices)
    content = models.TextField("内容")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "AI 消息"
        verbose_name_plural = "AI 消息"
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"
