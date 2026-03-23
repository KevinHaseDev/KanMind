"""Permission classes for board API endpoints."""

from rest_framework import permissions


class IsBoardOwnerOrReadOnly(permissions.BasePermission):
    """Allow read/member patch access and owner-only destructive changes."""

    message = "Only the board owner can modify this board."

    def has_permission(self, request, view):
        """Require an authenticated user for all board endpoint actions."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Check board-level access by method and role."""
        if request.user.is_superuser:
            return True
        if request.method in (
            permissions.SAFE_METHODS or request.method == "PATCH"
            ):
            return obj.owner_id == request.user.id or obj.members.filter(
                id=request.user.id
            ).exists()
        return obj.owner_id == request.user.id

