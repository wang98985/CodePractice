from rest_framework import serializers

from apps.judge.languages import get_language
from apps.problems.models import Problem

from .models import MAX_CODE_LENGTH, Submission


class SubmissionCreateSerializer(serializers.ModelSerializer):
    problem = serializers.PrimaryKeyRelatedField(queryset=Problem.objects.all())

    class Meta:
        model = Submission
        fields = ["id", "problem", "language", "code", "status"]
        read_only_fields = ["id", "status"]

    def validate_problem(self, value):
        user = self.context["request"].user
        if not value.is_public and not user.is_admin_role:
            raise serializers.ValidationError("题目不存在或未公开")
        return value

    def validate(self, attrs):
        problem = attrs["problem"]
        language = attrs["language"]
        code = attrs.get("code", "")

        if not code.strip():
            raise serializers.ValidationError({"code": "代码不能为空"})
        if len(code.encode("utf-8")) > MAX_CODE_LENGTH:
            raise serializers.ValidationError({"code": "代码超过 64KB 上限"})
        if get_language(language) is None:
            raise serializers.ValidationError({"language": "不支持的语言"})
        if language not in (problem.allowed_languages or []):
            raise serializers.ValidationError({"language": "该题目不允许此语言"})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return Submission.objects.create(
            user=request.user,
            problem=validated_data["problem"],
            language=validated_data["language"],
            code=validated_data["code"],
            total_cases=validated_data["problem"].test_cases.count(),
        )


class SubmissionListSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source="problem.title", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id", "problem", "problem_title", "username", "language",
            "status", "time_used_ms", "memory_used_kb",
            "passed_cases", "total_cases", "created_at",
        ]


class SubmissionDetailSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source="problem.title", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id", "problem", "problem_title", "username", "language", "code",
            "status", "time_used_ms", "memory_used_kb",
            "passed_cases", "total_cases", "error_message",
            "created_at", "finished_at",
        ]


class SubmissionStatusSerializer(serializers.ModelSerializer):
    """轻量轮询序列化器"""

    class Meta:
        model = Submission
        fields = [
            "id", "status", "time_used_ms", "memory_used_kb",
            "passed_cases", "total_cases",
        ]
