from collections import Counter
from datetime import timedelta
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Count
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.problems.models import Problem
from apps.submissions.models import Submission

from .models import EmailCode, User
from .permissions import IsAdminRole, IsSuperAdminRole
from .serializers import (
    AdminCreateSerializer,
    RegisterSerializer,
    RoleTokenObtainPairSerializer,
    UserManageSerializer,
    UserSerializer,
    is_qq_email,
)

User = get_user_model()

EMAIL_CODE_TTL_MINUTES = 10
EMAIL_CODE_RESEND_SECONDS = 60


class SendEmailCodeView(APIView):
    """发送注册邮箱验证码（公开，仅 QQ 邮箱，60 秒重发限制）"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email") or "").strip().lower()
        if not is_qq_email(email):
            return Response({"email": ["目前仅支持 QQ 邮箱注册（@qq.com）"]}, status=400)
        if User.objects.filter(email__iexact=email).exists():
            return Response({"email": ["该邮箱已被注册"]}, status=400)

        latest = (
            EmailCode.objects.filter(email__iexact=email).order_by("-created_at").first()
        )
        if latest and (timezone.now() - latest.created_at).total_seconds() < EMAIL_CODE_RESEND_SECONDS:
            wait = EMAIL_CODE_RESEND_SECONDS - int(
                (timezone.now() - latest.created_at).total_seconds()
            )
            return Response({"detail": f"发送过于频繁，请 {wait} 秒后再试"}, status=429)

        code = f"{random.SystemRandom().randint(0, 999999):06d}"
        EmailCode.objects.create(
            email=email,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=EMAIL_CODE_TTL_MINUTES),
        )

        try:
            send_mail(
                subject="【CodePractice】注册验证码",
                message=(
                    f"您的注册验证码为：{code}\n"
                    f"{EMAIL_CODE_TTL_MINUTES} 分钟内有效，请勿泄露给他人。"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as exc:  # noqa: BLE001 SMTP 配置错误时明确提示
            latest_code = EmailCode.objects.filter(email__iexact=email, is_used=False).latest("created_at")
            latest_code.delete()
            return Response(
                {"detail": f"邮件发送失败，请检查后端邮箱配置（{exc.__class__.__name__}）"},
                status=500,
            )
        return Response({"detail": "验证码已发送，10 分钟内有效"})


class RegisterView(generics.CreateAPIView):
    """注册（公开），默认角色为普通用户"""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data, status=status.HTTP_201_CREATED
        )


class LoginView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """当前登录用户信息查看/修改"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """管理端-普通用户管理（admin+）：列表/详情/禁用/重置密码"""

    permission_classes = [IsAdminRole]
    serializer_class = UserManageSerializer
    filter_backends = [SearchFilter]
    search_fields = ["username", "email"]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.USER).order_by("-date_joined")

    @action(detail=True, methods=["patch"], permission_classes=[IsSuperAdminRole], url_path="set-role")
    def set_role(self, request, pk=None):
        """超管修改任意用户角色"""
        user = self.get_object()
        role = request.data.get("role")
        if role not in User.Role.values:
            return Response({"detail": "无效角色"}, status=status.HTTP_400_BAD_REQUEST)
        if user == request.user and role != User.Role.SUPER_ADMIN:
            return Response(
                {"detail": "不能降级自己的超级管理员账号"}, status=status.HTTP_400_BAD_REQUEST
            )
        user.role = role
        user.save(update_fields=["role"])
        return Response(UserManageSerializer(user).data)


class AdminViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """管理端-管理员管理（仅超管）：列表/创建"""

    permission_classes = [IsSuperAdminRole]

    def get_queryset(self):
        return User.objects.filter(
            role__in=[User.Role.ADMIN, User.Role.SUPER_ADMIN]
        ).order_by("-date_joined")

    def get_serializer_class(self):
        return UserManageSerializer if self.action == "list" else AdminCreateSerializer


class AdminDashboardView(APIView):
    """管理端-仪表盘统计（仅超管）"""

    permission_classes = [IsSuperAdminRole]

    def get(self, request):
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        status_distribution = {
            item["status"]: item["count"]
            for item in Submission.objects.values("status").annotate(count=Count("id"))
        }
        # MySQL 未加载时区表时 CONVERT_TZ 返回 NULL，因此按本地日期在 Python 侧聚合
        local_tz = timezone.get_current_timezone()
        recent_dates = Counter(
            ts.astimezone(local_tz).date()
            for ts in Submission.objects.filter(created_at__gte=week_ago).values_list(
                "created_at", flat=True
            )
        )
        trend = [
            {
                "date": (now.date() - timedelta(days=offset)).isoformat(),
                "count": recent_dates.get(now.date() - timedelta(days=offset), 0),
            }
            for offset in range(6, -1, -1)
        ]

        return Response(
            {
                "user_total": User.objects.count(),
                "admin_total": User.objects.filter(
                    role__in=[User.Role.ADMIN, User.Role.SUPER_ADMIN]
                ).count(),
                "problem_total": Problem.objects.count(),
                "submission_total": Submission.objects.count(),
                "status_distribution": status_distribution,
                "submission_trend_7d": trend,
            }
        )
