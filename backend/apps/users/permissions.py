"""Custom permissions for role-based access control."""

from rest_framework.permissions import BasePermission
from .models import UserRole


class IsGlobalAdmin(BasePermission):
    """Only GLOBAL_ADMIN users can access."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.GLOBAL_ADMIN
        )


class IsRH(BasePermission):
    """RH and GLOBAL_ADMIN can access."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.RH, UserRole.GLOBAL_ADMIN)
        )


class IsRHOrLeader(BasePermission):
    """Any authenticated user can access (all roles)."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.RH, UserRole.LEADER, UserRole.GLOBAL_ADMIN)
        )


class IsAccountOwnerOrRH(BasePermission):
    """User can access their own data; RH/GLOBAL_ADMIN can access any."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.role in (UserRole.RH, UserRole.GLOBAL_ADMIN):
            return True
        return obj == request.user
