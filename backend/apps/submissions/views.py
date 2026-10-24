import os

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, pagination, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.judge.tasks import _judge, run_submission
from apps.judge.verdicts import Verdict

from .models import Submission
from .serializers import (
    SubmissionCreateSerializer,
    SubmissionDetailSerializer,
    SubmissionListSerializer,
    SubmissionStatusSerializer,
)

User = get_user_model()

# Vercel 等无常驻进程的平台：设 SYNC_JUDGE=true 改为同步判题
SYNC_JUDGE = os.getenv("SYNC_JUDGE", "false").lower() == "true"


class SubmissionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """提交：创建（入 MQ 队列）/ 列表 / 详情 / 轮询"""

    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["problem", "status"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Submission.objects.select_related("user", "problem")
        # admin 可通过 ?user_id= 查看他人提交
        user_id = self.request.query_params.get("user_id")
        if user_id and user.is_admin_role:
            return qs.filter(user_id=user_id)
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return SubmissionCreateSerializer
        if self.action == "retrieve":
            return SubmissionDetailSerializer
        return SubmissionListSerializer

    def get_object(self):
        obj = get_object_or_404(
            Submission.objects.select_related("user", "problem"), pk=self.kwargs["pk"]
        )
        if obj.user_id != self.request.user.id and not self.request.user.is_admin_role:
            raise PermissionDenied("无权查看他人提交")
        return obj

    def perform_create(self, serializer):
        submission = serializer.save()
        if SYNC_JUDGE:
            # 同步判题（Vercel 等无常驻 Celery worker 的环境）
            try:
                _judge(submission.pk)
            except Exception as exc:  # noqa: BLE001
                from apps.judge.verdicts import Verdict
                submission.status = Verdict.SYSTEM_ERROR
                submission.error_message = f"judge crashed: {exc}"[:2000]
                submission.save(update_fields=["status", "error_message"])
        else:
            # 入 MQ 队列，由 Celery worker 异步判题
            run_submission.delay(str(submission.pk))
        self.instance = submission

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        submission = self.instance
        return Response(
            {"id": submission.id, "status": submission.status},
            status=201,
        )

    @action(detail=True, methods=["get"], url_path="status")
    def status_poll(self, request, pk=None):
        """轻量轮询端点"""
        submission = self.get_object()
        return Response(SubmissionStatusSerializer(submission).data)


class LeaderboardPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LeaderboardView(APIView):
    """练习排行榜：按通过题目数(去重)、通过提交数排序。

    只统计有过提交记录的账号，未参与练习的用户不占榜单位次。
    排名规则：通过题目数 → 通过提交数 → 用户 ID（先注册者优先），
    保证分页结果稳定、不出现同位次跳变。
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = (
            User.objects.filter(is_active=True)
            .annotate(
                solved_count=Count(
                    "submissions__problem",
                    filter=Q(submissions__status=Verdict.ACCEPTED),
                    distinct=True,
                ),
                accepted_count=Count(
                    "submissions", filter=Q(submissions__status=Verdict.ACCEPTED)
                ),
                total_submissions=Count("submissions"),
            )
            .filter(total_submissions__gt=0)
            .order_by("-solved_count", "-accepted_count", "id")
        )

        paginator = LeaderboardPagination()
        page_rows = paginator.paginate_queryset(queryset, request, view=self)
        # page_size 参数只在 get_page_size 内部生效，这里从分页器取实际值
        page_size = paginator.page.paginator.per_page
        offset = (paginator.page.number - 1) * page_size

        results = []
        for idx, user in enumerate(page_rows, start=1):
            results.append(
                {
                    "rank": offset + idx,
                    "user_id": user.id,
                    "nickname": user.nickname or f"用户{user.id}",
                    "solved_count": user.solved_count,
                    "accepted_count": user.accepted_count,
                    "total_submissions": user.total_submissions,
                    "accuracy": (
                        round(user.accepted_count / user.total_submissions * 100, 1)
                        if user.total_submissions
                        else 0.0
                    ),
                }
            )

        return Response(
            {
                "count": paginator.page.paginator.count,
                "page": paginator.page.number,
                "page_size": page_size,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": results,
                "me": self._my_rank(queryset, request.user),
            }
        )

    @staticmethod
    def _my_rank(queryset, user):
        """当前用户在总榜中的名次（无提交记录时为 None）。"""
        mine = Submission.objects.filter(user=user).aggregate(
            solved_count=Count(
                "problem", filter=Q(status=Verdict.ACCEPTED), distinct=True
            ),
            accepted_count=Count("id", filter=Q(status=Verdict.ACCEPTED)),
            total_submissions=Count("id"),
        )
        if not mine["total_submissions"]:
            return None
        better = queryset.filter(
            Q(solved_count__gt=mine["solved_count"])
            | Q(solved_count=mine["solved_count"], accepted_count__gt=mine["accepted_count"])
            | Q(
                solved_count=mine["solved_count"],
                accepted_count=mine["accepted_count"],
                id__lt=user.id,
            )
        ).count()
        return {
            "rank": better + 1,
            "user_id": user.id,
            "nickname": user.nickname or f"用户{user.id}",
            "solved_count": mine["solved_count"],
            "accepted_count": mine["accepted_count"],
            "total_submissions": mine["total_submissions"],
            "accuracy": round(
                mine["accepted_count"] / mine["total_submissions"] * 100, 1
            ),
        }
