from rest_framework.permissions import BasePermission

from apps.authentication.choices import UserRoleChoices


class RolePermission(BasePermission):
    allowed_roles: tuple = ()

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.role in self.allowed_roles
        )


class IsAdminRole(RolePermission):
    allowed_roles = (UserRoleChoices.ADMIN,)


class IsAdminOrEditorRole(RolePermission):
    allowed_roles = (UserRoleChoices.ADMIN, UserRoleChoices.EDITOR)


class IsAnyRole(RolePermission):
    allowed_roles = (
        UserRoleChoices.ADMIN,
        UserRoleChoices.EDITOR,
        UserRoleChoices.VIEWER,
    )
