import os

from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.judge.tasks import _judge, run_submission

from .models import Submission
from .serializers import (
    SubmissionCreateSerializer,
    SubmissionDetailSerializer,
    SubmissionListSerializer,
    SubmissionStatusSerializer,
)

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
