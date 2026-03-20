from rest_framework import permissions


class IsBoardOwnerOrReadOnly(permissions.BasePermission):
    message = "Only the board owner can modify this board."

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.method in permissions.SAFE_METHODS or request.method == "PATCH":
            return obj.owner_id == request.user.id or obj.members.filter(id=request.user.id).exists()
        return obj.owner_id == request.user.id

