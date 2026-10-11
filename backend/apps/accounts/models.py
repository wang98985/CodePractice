from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # createsuperuser 创建的账号强制为超级管理员
        extra_fields.setdefault("role", self.model.Role.SUPER_ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """三级角色用户：普通用户 / 管理员 / 超级管理员"""

    class Role(models.TextChoices):
        USER = "user", "普通用户"
        ADMIN = "admin", "管理员"
        SUPER_ADMIN = "super_admin", "超级管理员"

    objects = UserManager()

    role = models.CharField(
        "角色", max_length=20, choices=Role.choices, default=Role.USER, db_index=True
    )
    email = models.EmailField("邮箱", unique=True)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return f"{self.username}({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role in {self.Role.ADMIN, self.Role.SUPER_ADMIN}

    @property
    def is_super_admin_role(self):
        return self.is_superuser or self.role == self.Role.SUPER_ADMIN


class EmailCode(models.Model):
    """注册邮箱验证码（6 位数字，10 分钟有效，验证后作废）"""

    email = models.EmailField("邮箱", db_index=True)
    code = models.CharField("验证码", max_length=6)
    expires_at = models.DateTimeField("过期时间")
    is_used = models.BooleanField("是否已使用", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "邮箱验证码"
        verbose_name_plural = "邮箱验证码"
        ordering = ["-created_at"]
