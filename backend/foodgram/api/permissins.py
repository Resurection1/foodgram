from rest_framework import permissions


class IsUserorAdmin(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (obj.id == request.user
                or request.user.is_superuser)

class IsAdminAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    message = "Доступ запрещен!"

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
            or obj.author == request.user
        )
