from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """允许管理员与超级管理员"""

    message = "需要管理员权限"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin_role)


class IsSuperAdminRole(BasePermission):
    """仅允许超级管理员"""

    message = "需要超级管理员权限"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_super_admin_role)
