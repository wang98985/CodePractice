from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminDashboardView,
    AdminUserViewSet,
    AdminViewSet,
    LoginView,
    MeView,
    RegisterView,
    ResetPasswordView,
    SendEmailCodeView,
    UserProfileView,
)

router = DefaultRouter()
router.register("admin/users", AdminUserViewSet, basename="admin-user")
router.register("admin/admins", AdminViewSet, basename="admin-admin")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/send-email-code/", SendEmailCodeView.as_view(), name="auth-send-email-code"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="auth-reset-password"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("users/<int:pk>/profile/", UserProfileView.as_view(), name="user-profile"),
    path("", include(router.urls)),
]
