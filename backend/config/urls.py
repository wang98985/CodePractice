from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.problems.urls")),
    path("api/", include("apps.submissions.urls")),
    path("api/", include("apps.assistant.urls")),
]
