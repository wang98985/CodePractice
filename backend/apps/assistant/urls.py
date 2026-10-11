from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChatSessionViewSet, ChatStreamView, SessionMessagesView

router = DefaultRouter()
router.register("assistant/sessions", ChatSessionViewSet, basename="assistant-session")

urlpatterns = [
    path(
        "assistant/sessions/<int:session_id>/messages/",
        SessionMessagesView.as_view(),
        name="assistant-session-messages",
    ),
    path("assistant/chat/", ChatStreamView.as_view(), name="assistant-chat"),
    path("", include(router.urls)),
]
