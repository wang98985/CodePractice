from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LeaderboardView, SubmissionViewSet

router = DefaultRouter()
router.register("submissions", SubmissionViewSet, basename="submission")

urlpatterns = [
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    *router.urls,
]
