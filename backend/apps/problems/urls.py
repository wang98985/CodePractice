from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DailyProblemView,
    FavoriteViewSet,
    ProblemBulkImportView,
    ProblemManageViewSet,
    ProblemViewSet,
    TagListView,
    TestCaseManageViewSet,
)

router = DefaultRouter()
router.register("problems", ProblemViewSet, basename="problem")
router.register("admin/problems", ProblemManageViewSet, basename="admin-problem")
router.register("favorites", FavoriteViewSet, basename="favorite")

problem_tc_list = TestCaseManageViewSet.as_view({"get": "list", "post": "create"})
problem_tc_detail = TestCaseManageViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("daily/", DailyProblemView.as_view(), name="daily-problem"),
    # 必须在 router 之前注册，避免被 problems/<pk>/ 详情路由吞掉
    path("problems/admin/bulk-upload/", ProblemBulkImportView.as_view(), name="problem-bulk-import"),
    path(
        "problems/<int:problem_pk>/test-cases/",
        problem_tc_list,
        name="problem-testcases",
    ),
    path(
        "problems/<int:problem_pk>/test-cases/<int:pk>/",
        problem_tc_detail,
        name="problem-testcase-detail",
    ),
    path("", include(router.urls)),
]
