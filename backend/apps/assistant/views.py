"""AI 助理视图：会话管理 + SSE 流式聊天"""
import json

from django.db import close_old_connections
from django.db.models import Count
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.views import APIView

from apps.problems.models import Problem

from .models import ChatMessage, ChatSession
from .serializers import (
    ChatMessageSerializer,
    ChatRequestSerializer,
    ChatSessionSerializer,
)
from .services import build_context, local_reply, stream_remote_reply


def _sse(data):
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


class ChatSessionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """AI 会话列表/创建/删除"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return (
            ChatSession.objects.filter(user=self.request.user)
            .select_related("problem")
            .annotate(message_count=Count("messages"))
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SessionMessagesView(generics.ListAPIView):
    """会话历史消息（仅 owner）"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer
    pagination_class = None

    def get_queryset(self):
        session = get_object_or_404(
            ChatSession, pk=self.kwargs["session_id"], user=self.request.user
        )
        return session.messages.all()


class ChatStreamView(APIView):
    """
    POST /api/assistant/chat/  —— SSE 流式回复
    body: {session_id?, problem_id?, message}
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        message = data["message"].strip()

        # 定位或创建会话
        session = None
        if data.get("session_id"):
            session = get_object_or_404(
                ChatSession, pk=data["session_id"], user=request.user
            )
        if session is None:
            problem = None
            if data.get("problem_id"):
                problem = get_object_or_404(Problem, pk=data["problem_id"])
            session = ChatSession.objects.create(
                user=request.user, problem=problem, title=message[:30]
            )
        elif data.get("problem_id") and session.problem_id != data["problem_id"]:
            session.problem_id = data["problem_id"]
            session.save(update_fields=["problem"])

        problem = session.problem

        # 先落库用户消息，再开始流式响应
        ChatMessage.objects.create(session=session, role=ChatMessage.Role.USER, content=message)

        response = StreamingHttpResponse(
            self._event_stream(session, problem, message),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    def _event_stream(self, session, problem, message):
        close_old_connections()
        collected = []

        try:
            if self._ai_enabled():
                history = list(
                    session.messages.filter(role__in=[ChatMessage.Role.USER, ChatMessage.Role.ASSISTANT])
                    .order_by("-created_at", "-id")[:10]
                )[::-1]
                context = build_context(problem, history, message)
                try:
                    for delta in stream_remote_reply(context):
                        collected.append(delta)
                        yield _sse({"delta": delta})
                except Exception as exc:  # noqa: BLE001  上游失败 → 降级
                    if not collected:
                        yield _sse({"event": "notice", "message": f"AI 服务暂不可用，已切换本地助手模式 ({exc})"})
                        for piece in self._chunk(local_reply(problem, message)):
                            collected.append(piece)
                            yield _sse({"delta": piece})
            else:
                for piece in self._chunk(local_reply(problem, message)):
                    collected.append(piece)
                    yield _sse({"delta": piece})
        except GeneratorExit:
            content = "".join(collected)
            if content:
                self._persist(session, content)
            raise
        except Exception as exc:  # noqa: BLE001
            yield _sse({"event": "error", "message": str(exc)})

        content = "".join(collected)
        if content:
            self._persist(session, content)
        yield _sse({"event": "done"})

    @staticmethod
    def _ai_enabled():
        from django.conf import settings

        return bool(settings.AI_API_KEY and settings.AI_API_BASE_URL)

    @staticmethod
    def _chunk(text, size=16):
        for i in range(0, len(text), size):
            yield text[i : i + size]

    @staticmethod
    def _persist(session, content):
        close_old_connections()
        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.ASSISTANT, content=content
        )
