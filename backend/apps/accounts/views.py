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
from apps.judge.verdicts import Verdict
from apps.notifications.models import Notification

from .models import EmailCode, User
from .permissions import IsAdminRole, IsSuperAdminRole
from .serializers import (
    AdminCreateSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    RoleTokenObtainPairSerializer,
    UserManageSerializer,
    UserProfileSerializer,
    UserSerializer,
    is_qq_email,
)

User = get_user_model()

EMAIL_CODE_TTL_MINUTES = 10
EMAIL_CODE_RESEND_SECONDS = 60


class SendEmailCodeView(APIView):
    """发送邮箱验证码（公开，仅 QQ 邮箱，60 秒重发限制）。

    purpose=register（默认）：注册用，要求邮箱未注册；
    purpose=reset：找回密码用，要求邮箱已注册。
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email") or "").strip().lower()
        purpose = str(request.data.get("purpose") or "register").strip().lower()
        if purpose not in {"register", "reset"}:
            purpose = "register"
        if not is_qq_email(email):
            return Response({"email": ["目前仅支持 QQ 邮箱（@qq.com）"]}, status=400)

        registered = User.objects.filter(email__iexact=email).exists()
        if purpose == "register" and registered:
            return Response({"email": ["该邮箱已被注册"]}, status=400)
        if purpose == "reset" and not registered:
            return Response({"email": ["该邮箱尚未注册"]}, status=400)

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

        action = "找回密码" if purpose == "reset" else "注册"
        try:
            send_mail(
                subject=f"【CodePractice】{action}验证码",
                message=(
                    f"您的{action}验证码为：{code}\n"
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


class ResetPasswordView(APIView):
    """忘记密码：校验 QQ 邮箱验证码后重置密码（公开）"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "密码已重置，请使用新密码登录"})


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
    search_fields = ["nickname", "email"]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.USER).order_by("-date_joined")

    def update(self, request, *args, **kwargs):
        """普通用户信息变更：改密码 / 禁用启用时给该用户发系统通知"""
        user = self.get_object()
        old_active = user.is_active
        password_changed = bool(request.data.get("password"))
        response = super().update(request, *args, **kwargs)
        user.refresh_from_db()
        if password_changed:
            Notification.notify(
                user,
                title="密码已被管理员重置",
                content="你的登录密码已被管理员重置，请尽快使用新密码登录并妥善保管。",
            )
        if old_active and not user.is_active:
            Notification.notify(
                user,
                title="账号已被禁用",
                content="你的账号已被管理员禁用，如有疑问请联系平台管理员。",
            )
        return response

    @action(detail=True, methods=["patch"], permission_classes=[IsSuperAdminRole], url_path="set-role")
    def set_role(self, request, pk=None):
        """超管修改用户角色（含把管理员降为普通用户）。

        不能沿用 self.get_object()：本 viewset 的 queryset 只含普通用户，
        管理员不在其中会导致改角色时直接 404，这里按 pk 直接取、绕过角色过滤。
        """
        user = User.objects.filter(pk=pk).first()
        if user is None:
            return Response({"detail": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)
        role = request.data.get("role")
        if role not in (User.Role.USER, User.Role.ADMIN):
            return Response({"detail": "无效角色"}, status=status.HTTP_400_BAD_REQUEST)
        if user.role == User.Role.SUPER_ADMIN:
            return Response(
                {"detail": "不能修改超级管理员的角色"}, status=status.HTTP_400_BAD_REQUEST
            )
        user.role = role
        update_fields = ["role"]
        # 降为普通用户时一并回收 Django admin 后台访问权限
        if role == User.Role.USER and user.is_staff:
            user.is_staff = False
            update_fields.append("is_staff")
        user.save(update_fields=update_fields)
        Notification.notify(
            user,
            title="你的账号角色已变更",
            content=f"当前角色：{'管理员' if role == User.Role.ADMIN else '普通用户'}。",
        )
        return Response(UserManageSerializer(user).data)


class AdminViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """管理端-管理员管理（仅超管）：列表/创建/重置密码"""

    permission_classes = [IsSuperAdminRole]

    def get_queryset(self):
        return User.objects.filter(
            role__in=[User.Role.ADMIN, User.Role.SUPER_ADMIN]
        ).order_by("-date_joined")

    def get_serializer_class(self):
        return UserManageSerializer if self.action == "list" else AdminCreateSerializer

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        """超管重置管理员密码（管理员不在普通用户列表中，这是唯一的补救入口）"""
        user = self.get_object()
        password = str(request.data.get("password") or "")
        if len(password) < 6:
            return Response({"detail": "密码至少 6 位"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.save(update_fields=["password"])
        Notification.notify(
            user,
            title="密码已被超级管理员重置",
            content="你的登录密码已被超级管理员重置，请尽快使用新密码登录并妥善保管。",
        )
        return Response({"detail": "密码已重置"})


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


class UserProfileView(generics.RetrieveAPIView):
    """用户主页：资料 + 练习统计 + 最近提交（需登录）"""

    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        qs = Submission.objects.filter(user=user)

        submission_total = qs.count()
        accepted_total = qs.filter(status=Verdict.ACCEPTED).count()
        solved_ids = set(
            qs.filter(status=Verdict.ACCEPTED).values_list("problem_id", flat=True)
        )
        attempted_ids = set(qs.values_list("problem_id", flat=True))

        # 难度分布（已通过题目按 difficulty 计数）
        difficulty_solved = {"easy": 0, "medium": 0, "hard": 0}
        if solved_ids:
            for item in (
                Problem.objects.filter(id__in=solved_ids)
                .values("difficulty")
                .annotate(count=Count("id"))
            ):
                if item["difficulty"] in difficulty_solved:
                    difficulty_solved[item["difficulty"]] = item["count"]

        language_distribution = [
            {"language": item["language"], "count": item["count"]}
            for item in qs.values("language").annotate(count=Count("id")).order_by("-count")
        ]
        status_distribution = [
            {"status": item["status"], "count": item["count"]}
            for item in qs.values("status").annotate(count=Count("id")).order_by("-count")
        ]

        recent_submissions = [
            {
                "id": s.id,
                "problem": {
                    "id": s.problem_id,
                    "title": s.problem.title,
                    "difficulty": s.problem.difficulty,
                },
                "language": s.language,
                "status": s.status,
                "time_used_ms": s.time_used_ms,
                "memory_used_kb": s.memory_used_kb,
                "created_at": s.created_at,
            }
            for s in qs.select_related("problem").order_by("-created_at")[:10]
        ]

        data = {
            "user": UserProfileSerializer(user).data,
            "stats": {
                "submission_total": submission_total,
                "accepted_total": accepted_total,
                "solved_count": len(solved_ids),
                "attempted_count": len(attempted_ids),
                "acceptance_rate": (
                    round(accepted_total / submission_total * 100, 1)
                    if submission_total
                    else 0.0
                ),
                "difficulty_solved": difficulty_solved,
                "language_distribution": language_distribution,
                "status_distribution": status_distribution,
            },
            "recent_submissions": recent_submissions,
        }
        if request.user.id == user.id:
            data["solved_problem_ids"] = sorted(solved_ids)
        return Response(data)

