"""Permission classes for task and comment API endpoints."""

from rest_framework.permissions import BasePermission

from board_app.models import Board


def is_board_owner_or_member(user, board):
    """Return whether user is superuser, board owner, or board member."""
    if user.is_superuser:
        return True
    return board.owner_id==user.id or board.members.filter(id=user.id).exists()


def is_authenticated_user(user):
    """Return whether the provided user is authenticated."""
    return bool(user and user.is_authenticated)


class IsTaskBoardMemberForCreate(BasePermission):
    """Allow task creation only for users who can access the target board."""

    message = "You must be a owner or member to create tasks for this board."

    def has_permission(self, request, view):
        """Check authentication and board membership requirements for POST."""
        if not is_authenticated_user(request.user):
            return False
        if request.method != "POST":
            return True
        board_id = request.data.get("board")
        if not board_id:
            return True
        board = Board.objects.filter(id=board_id).first()
        if board is None:
            return True
        return is_board_owner_or_member(request.user, board)


class IsTaskBoardMember(BasePermission):
    """Allow task access only for board owners, members, or superusers."""

    message = "You must be a board owner or member to access this task."

    def has_permission(self, request, view):
        """Require authenticated users for all task operations."""
        return is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        """Check board visibility for task or comment-linked task object."""
        task = getattr(obj, "task", obj)
        board = getattr(task, "board", None)
        if board is None:
            return False
        return is_board_owner_or_member(request.user, board)


class IsTaskCreatorOrBoardOwnerCanDelete(BasePermission):
    """Limit task deletion to task creator, board owner, or superuser."""

    message = "Only the task creator or board owner can delete this task."

    def has_permission(self, request, view):
        """Require authenticated users before object-level delete checks."""
        return is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        """Authorize DELETE only for creator, board owner, or superuser."""
        if request.user.is_superuser:
            return True
        if request.method != "DELETE":
            return True
        board_owner_id = obj.board.owner_id if obj.board else None
        return request.user.id in {obj.created_by_id, board_owner_id}


class IsCommentAuthor(BasePermission):
    """Limit comment deletion to the comment author or superuser."""

    message = "Only the comment author can delete this comment."

    def has_permission(self, request, view):
        """Require authenticated users for comment operations."""
        return is_authenticated_user(request.user)

    def has_object_permission(self, request, view, obj):
        """Authorize DELETE only for the comment author or superuser."""
        if request.user.is_superuser:
            return True
        if request.method != "DELETE":
            return True
        return obj.author_id == request.user.id
