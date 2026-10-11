from django.contrib import admin

from .models import Problem, Tag, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 0


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "difficulty", "is_public", "created_by", "updated_at")
    list_filter = ("difficulty", "is_public")
    inlines = [TestCaseInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
