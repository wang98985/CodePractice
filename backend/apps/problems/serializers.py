from rest_framework import serializers

from .models import DailyProblem, Favorite, Problem, Tag, TestCase


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class TestCasePublicSerializer(serializers.ModelSerializer):
    """示例用例（题目详情页展示）"""

    class Meta:
        model = TestCase
        fields = ["id", "input_data", "expected_output", "order"]


class TestCaseManageSerializer(serializers.ModelSerializer):
    """管理端用例 CRUD"""

    class Meta:
        model = TestCase
        fields = ["id", "problem", "input_data", "expected_output", "is_sample", "is_hidden", "order", "created_at"]
        read_only_fields = ["id", "problem", "created_at"]


class ProblemListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Problem
        fields = [
            "id", "title", "difficulty", "tags",
            "time_limit_ms", "memory_limit_kb", "is_public", "created_at",
        ]


class ProblemDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    sample_cases = serializers.SerializerMethodField()
    reference_answer = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = [
            "id", "title", "description", "difficulty", "tags",
            "time_limit_ms", "memory_limit_kb", "allowed_languages",
            "reference_answer", "is_public", "is_favorited",
            "sample_cases", "created_at", "updated_at",
        ]

    def get_sample_cases(self, obj):
        cases = obj.test_cases.filter(is_sample=True)
        return TestCasePublicSerializer(cases, many=True).data

    def get_reference_answer(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False) and user.is_admin_role:
            return obj.reference_answer
        return None

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return False
        return obj.favorites.filter(user_id=user.id).exists()


class ProblemManageSerializer(serializers.ModelSerializer):
    """管理端题目 CRUD（含未公开题目）"""

    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)

    class Meta:
        model = Problem
        fields = [
            "id", "title", "description", "difficulty",
            "time_limit_ms", "memory_limit_kb", "allowed_languages",
            "reference_answer", "is_public", "tags",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate_allowed_languages(self, value):
        from apps.judge.languages import get_language

        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("allowed_languages 必须为非空数组")
        for lang in value:
            if get_language(lang) is None:
                raise serializers.ValidationError(f"不支持的语言: {lang}")
        return value

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        problem = Problem.objects.create(**validated_data)
        problem.tags.set(tags)
        return problem

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        return instance


class ProblemManageListSerializer(serializers.ModelSerializer):
    """管理端题目列表（含用例数统计）"""

    tags = TagSerializer(many=True, read_only=True)
    test_case_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Problem
        fields = [
            "id", "title", "difficulty", "tags", "is_public",
            "time_limit_ms", "memory_limit_kb", "test_case_count", "updated_at",
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    """收藏列表：内联题目摘要，便于前端直接渲染"""

    problem = ProblemListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "problem", "created_at"]
        read_only_fields = ["id", "problem", "created_at"]


class DailyProblemSerializer(serializers.ModelSerializer):
    """每日一题：只暴露题目摘要，题面走详情接口"""

    problem = ProblemListSerializer(read_only=True)

    class Meta:
        model = DailyProblem
        fields = ["date", "problem"]
