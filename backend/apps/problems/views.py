import json
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole, IsSuperAdminRole
from apps.judge.verdicts import Verdict
from apps.submissions.models import Submission

from .bulk_import import decode_uploaded, import_problems
from .cache_utils import (
    PROBLEM_LIST_CACHE_TTL,
    invalidate_problem_list_cache,
    problem_list_cache_key,
)
from .filters import ProblemFilterSet
from .models import DailyProblem, Favorite, Problem, Tag, TestCase
from .pagination import ManagePagination
from .serializers import (
    DailyProblemSerializer,
    FavoriteSerializer,
    ProblemDetailSerializer,
    ProblemListSerializer,
    ProblemManageListSerializer,
    ProblemManageSerializer,
    TagSerializer,
    TestCaseManageSerializer,
)


class TagListView(ListAPIView):
    """标签列表（公开）"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class ProblemViewSet(viewsets.ModelViewSet):
    """
    题目公开接口：
    - list/retrieve 公开（仅 is_public）
    - create/update/destroy 需管理员
    """

    queryset = Problem.objects.filter(is_public=True).prefetch_related("tags")
    filterset_class = ProblemFilterSet
    search_fields = ["title", "description"]
    ordering_fields = ["id", "difficulty", "created_at"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminRole()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProblemListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ProblemManageSerializer
        return ProblemDetailSerializer

    def list(self, request, *args, **kwargs):
        """公开题目列表：命中缓存直接返回，避免重复查库。"""
        key = problem_list_cache_key(request.META.get("QUERY_STRING", ""))
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, PROBLEM_LIST_CACHE_TTL)
        return response

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        invalidate_problem_list_cache()

    def perform_update(self, serializer):
        serializer.save()
        invalidate_problem_list_cache()

    def destroy(self, request, *args, **kwargs):
        problem = self.get_object()
        problem.delete()
        invalidate_problem_list_cache()
        return Response(status=204)


class ProblemManageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """管理端题目列表（含未公开与统计）"""

    permission_classes = [IsAdminRole]
    serializer_class = ProblemManageListSerializer
    filterset_class = ProblemFilterSet
    search_fields = ["title"]
    pagination_class = ManagePagination

    def get_queryset(self):
        return (
            Problem.objects.all()
            .prefetch_related("tags")
            .annotate(test_case_count=Count("test_cases"))
            .order_by("-updated_at")
        )


class ProblemBulkImportView(APIView):
    """超管批量导入题目：CSV 文件 / 粘贴文本 / JSON 数组

    - multipart 字段 file（.csv/.txt/.json）优先；
    - 否则取 JSON/表单字段 content（粘贴的 CSV 或 JSON 数组文本）。
    返回 {created, failed, created_count, failed_count}，单行失败不影响其他行。
    """

    permission_classes = [IsSuperAdminRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is not None:
            text = decode_uploaded(upload.read())
        elif isinstance(request.data, list):
            # 请求体本身就是 JSON 题目数组，直接导入
            text = json.dumps(request.data, ensure_ascii=False)
        else:
            content = (request.data or {}).get("content")
            if not content or not str(content).strip():
                return Response(
                    {"detail": "请上传 .csv/.txt/.json 文件，或在 content 中粘贴 CSV/JSON 内容"},
                    status=400,
                )
            text = str(content)
        created, failed = import_problems(text, request.user)
        if created:
            invalidate_problem_list_cache()
        return Response(
            {
                "created": created,
                "failed": failed,
                "created_count": len(created),
                "failed_count": len(failed),
            }
        )


class TestCaseManageViewSet(viewsets.ModelViewSet):
    """管理端测试用例 CRUD（嵌套在题目下）"""

    permission_classes = [IsAdminRole]
    serializer_class = TestCaseManageSerializer

    def get_queryset(self):
        return TestCase.objects.filter(problem_id=self.kwargs["problem_pk"])

    def perform_create(self, serializer):
        problem = get_object_or_404(Problem, pk=self.kwargs["problem_pk"])
        serializer.save(problem=problem)


class FavoriteViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """我的收藏：列表 / 取消收藏 / 收藏切换

    - GET    /api/favorites/            收藏列表（内联题目摘要，按收藏时间倒序）
    - DELETE /api/favorites/{id}/       取消收藏
    - POST   /api/favorites/toggle/     body {problem_id} → {favorited: bool}
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related("problem")
            .prefetch_related("problem__tags")
        )

    @action(detail=False, methods=["post"], url_path="toggle")
    def toggle(self, request):
        problem_id = request.data.get("problem_id")
        if not problem_id:
            return Response({"detail": "缺少 problem_id"}, status=400)
        problem = Problem.objects.filter(pk=problem_id, is_public=True).first()
        if problem is None:
            return Response({"detail": "题目不存在"}, status=404)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, problem=problem
        )
        if not created:
            favorite.delete()
        return Response({"favorited": created})


def _pick_daily_problem(date):
    """按日期确定性选取公开题目，保证同一天所有用户看到同一道题。"""
    ids = list(
        Problem.objects.filter(is_public=True).order_by("id").values_list("id", flat=True)
    )
    if not ids:
        return None
    return Problem.objects.get(pk=ids[date.toordinal() % len(ids)])


def _get_daily(date):
    record = DailyProblem.objects.filter(date=date).select_related("problem").first()
    if record is not None:
        return record
    problem = _pick_daily_problem(date)
    if problem is None:
        return None
    # 并发首次访问时唯一约束兜底：抢输的一方复用已有记录
    record, _ = DailyProblem.objects.get_or_create(date=date, defaults={"problem": problem})
    return record


class DailyProblemView(APIView):
    """每日一题

    GET /api/daily/ →
    {
      "today": {date, problem, submitted, accepted} | null,
      "recent": [{date, problem, accepted}]   # 最近 6 天（不含今天）
    }
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        today_record = _get_daily(today)

        if today_record is None:
            return Response({"today": None, "recent": []})

        problem = today_record.problem
        # 不按 created_at 日期过滤：MySQL 时区转换不可靠，改用「是否做过这道题」
        stats = Submission.objects.filter(
            user=request.user, problem=problem
        ).aggregate(
            submitted=Count("id"),
            accepted=Count("id", filter=Q(status=Verdict.ACCEPTED)),
        )

        today_data = DailyProblemSerializer(today_record).data
        today_data["submitted"] = stats["submitted"] > 0
        today_data["accepted"] = stats["accepted"] > 0

        records = [
            record
            for record in (_get_daily(today - timedelta(days=offset)) for offset in range(1, 7))
            if record is not None
        ]
        accepted_ids = set(
            Submission.objects.filter(
                user=request.user,
                problem_id__in=[record.problem_id for record in records],
                status=Verdict.ACCEPTED,
            ).values_list("problem_id", flat=True)
        )
        recent = []
        for record in records:
            row = DailyProblemSerializer(record).data
            row["accepted"] = record.problem_id in accepted_ids
            recent.append(row)

        return Response({"today": today_data, "recent": recent})
