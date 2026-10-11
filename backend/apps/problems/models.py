from django.conf import settings
from django.db import models


def default_allowed_languages():
    return ["python"]


class Tag(models.Model):
    name = models.CharField("标签名", max_length=50, unique=True)

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Problem(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "简单"
        MEDIUM = "medium", "中等"
        HARD = "hard", "困难"

    title = models.CharField("标题", max_length=200)
    description = models.TextField("题面(Markdown)")
    difficulty = models.CharField(
        "难度", max_length=10, choices=Difficulty.choices,
        default=Difficulty.EASY, db_index=True,
    )
    time_limit_ms = models.IntegerField("时限(ms)", default=2000)
    memory_limit_kb = models.IntegerField("内存限制(KB)", default=65536)
    allowed_languages = models.JSONField(
        "允许语言", default=default_allowed_languages, blank=True
    )
    reference_answer = models.TextField("参考答案", blank=True, default="")
    is_public = models.BooleanField("是否公开", default=False, db_index=True)
    tags = models.ManyToManyField(
        Tag, blank=True, related_name="problems", verbose_name="标签"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_problems", verbose_name="创建人",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "题目"
        verbose_name_plural = "题目"
        ordering = ["id"]

    def __str__(self):
        return f"{self.pk}. {self.title}"


class TestCase(models.Model):
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE, related_name="test_cases", verbose_name="题目"
    )
    input_data = models.TextField("输入数据")
    expected_output = models.TextField("期望输出")
    is_sample = models.BooleanField("示例用例(题面展示)", default=False)
    is_hidden = models.BooleanField("隐藏判题用例", default=True)
    order = models.PositiveIntegerField("顺序", default=0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "测试用例"
        verbose_name_plural = "测试用例"
        ordering = ["order", "id"]

    def __str__(self):
        return f"TestCase#{self.pk} of Problem#{self.problem_id}"
