from rest_framework import serializers

from .models import ChatMessage, ChatSession


class ChatSessionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source="problem.title", read_only=True, default=None)
    message_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "problem", "problem_title", "message_count", "created_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]


class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=False, allow_null=True)
    problem_id = serializers.IntegerField(required=False, allow_null=True)
    message = serializers.CharField(min_length=1, max_length=4000)
