from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.role == "manager"


class IsExecutor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.executor == request.user
