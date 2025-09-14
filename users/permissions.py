from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Проверяет, является ли пользователь суперпользователем.

    Методы
    -------
    has_permission(request, view) -> bool
        Возвращает ``True``, если пользователь — суперпользователь (``is_superuser``).
        В противном случае — ``False``.
    """
    def has_permission(self, request, view):
        return request.user.is_superuser


class IsManagerOrAdmin(BasePermission):
    """
    Проверяет, является ли пользователь менеджером или суперпользователем.

    Методы
    -------
    has_permission(request, view) -> bool
        Возвращает ``True``, если пользователь — суперпользователь
        или его роль равна ``"manager"``.
        В противном случае — ``False``.
    """
    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.role == "manager"
