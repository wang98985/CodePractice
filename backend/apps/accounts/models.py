from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """以邮箱作为登录名（USERNAME_FIELD=email）。

    AbstractUser 仍带有 username 列，这里统一把 username 自动设为邮箱，
    界面上不再对外暴露 username，用户展示名使用 nickname。
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("必须提供邮箱")
        email = self.normalize_email(email).lower()
        extra_fields.setdefault("username", email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # createsuperuser 创建的账号强制为超级管理员
        extra_fields.setdefault("role", self.model.Role.SUPER_ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """三级角色用户：普通用户 / 管理员 / 超级管理员"""

    class Role(models.TextChoices):
        USER = "user", "普通用户"
        ADMIN = "admin", "管理员"
        SUPER_ADMIN = "super_admin", "超级管理员"

    # 登录凭证改为邮箱；nickname 作为统一展示名
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    role = models.CharField(
        "角色", max_length=20, choices=Role.choices, default=Role.USER, db_index=True
    )
    email = models.EmailField("邮箱", unique=True)
    nickname = models.CharField("昵称", max_length=32, blank=True, default="")
    bio = models.CharField("个人简介", max_length=200, blank=True, default="")

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
