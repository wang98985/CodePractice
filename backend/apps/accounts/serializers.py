from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import EmailCode

User = get_user_model()


def is_qq_email(email: str) -> bool:
    return email.lower().endswith("@qq.com")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)
    nickname = serializers.CharField(min_length=2, max_length=32)
    code = serializers.CharField(write_only=True, min_length=6, max_length=6)

    class Meta:
        model = User
        fields = ["id", "email", "nickname", "password", "code"]

    def validate_email(self, value):
        value = value.strip().lower()
        if not is_qq_email(value):
            raise serializers.ValidationError("目前仅支持 QQ 邮箱注册（@qq.com）")
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("该邮箱已被注册")
        return value

    def validate_nickname(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("请填写昵称")
        return value

    def validate(self, attrs):
        email = attrs["email"]
        code = attrs.pop("code")
        record = (
            EmailCode.objects.filter(email__iexact=email, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if record is None:
            raise serializers.ValidationError({"code": "请先获取邮箱验证码"})
        if record.expires_at < timezone.now():
            raise serializers.ValidationError({"code": "验证码已过期，请重新获取"})
        if record.code != code:
            raise serializers.ValidationError({"code": "验证码不正确"})
        record.is_used = True
        record.save(update_fields=["is_used"])
        return attrs

    def create(self, validated_data):
        # 注册用户默认 role=user，username 由 UserManager 自动设为邮箱
        return User.objects.create_user(**validated_data)


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """登录（邮箱 + 密码）签发的 JWT 携带 role/昵称，响应体附带用户信息"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        token["nickname"] = user.nickname
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "nickname": self.user.nickname,
            "role": self.user.role,
        }
        return data


class ResetPasswordSerializer(serializers.Serializer):
    """忘记密码：校验 QQ 邮箱验证码后重置密码"""

    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(
        write_only=True, min_length=6, max_length=128
    )

    def validate_email(self, value):
        value = value.strip().lower()
        if not is_qq_email(value):
            raise serializers.ValidationError("目前仅支持 QQ 邮箱（@qq.com）")
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("该邮箱尚未注册")
        return value

    def validate(self, attrs):
        record = (
            EmailCode.objects.filter(email__iexact=attrs["email"], is_used=False)
            .order_by("-created_at")
            .first()
        )
        if record is None:
            raise serializers.ValidationError({"code": "请先获取邮箱验证码"})
        if record.expires_at < timezone.now():
            raise serializers.ValidationError({"code": "验证码已过期，请重新获取"})
        if record.code != attrs["code"]:
            raise serializers.ValidationError({"code": "验证码不正确"})
        attrs["record"] = record
        return attrs

    def create(self, validated_data):
        user = User.objects.get(email__iexact=validated_data["email"])
        user.set_password(validated_data["new_password"])
        user.save(update_fields=["password"])
        record = validated_data["record"]
        record.is_used = True
        record.save(update_fields=["is_used"])
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "email", "nickname", "bio",
            "role", "is_active", "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "date_joined"]


class UserProfileSerializer(serializers.ModelSerializer):
    """用户主页资料序列化器（含角色显示名）"""

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "nickname", "bio",
            "role", "role_display", "date_joined",
        ]
        read_only_fields = fields


class UserManageSerializer(serializers.ModelSerializer):
    """管理端用户管理序列化器"""

    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = ["id", "nickname", "email", "role", "is_active", "password", "date_joined"]
        read_only_fields = ["id", "date_joined"]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user


class AdminCreateSerializer(serializers.ModelSerializer):
    """超级管理员创建管理员账号"""

    password = serializers.CharField(write_only=True, min_length=6)
    nickname = serializers.CharField(max_length=32, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "email", "nickname", "password"]

    def create(self, validated_data):
        validated_data.setdefault("nickname", "")
        return User.objects.create_user(role=User.Role.ADMIN, **validated_data)
