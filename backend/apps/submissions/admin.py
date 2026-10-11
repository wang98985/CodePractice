from django.contrib import admin

from .models import Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "problem", "language", "status",
        "time_used_ms", "memory_used_kb", "passed_cases", "created_at",
    )
    list_filter = ("status", "language")
    search_fields = ("user__username", "problem__title")
    readonly_fields = [f.name for f in Submission._meta.fields]
