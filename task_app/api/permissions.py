from rest_framework.permissions import BasePermission
from board_app.models import Board


def is_board_owner_or_member(user, board):
    if user.is_superuser:
        return True
    return board.owner_id == user.id or board.members.filter(id=user.id).exists()


class IsTaskBoardMemberForCreate(BasePermission):
    message = "You must be a board owner or member to create tasks for this board."

    def has_permission(self, request, view):
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
    message = "You must be a board owner or member to access this task."

    def has_object_permission(self, request, view, obj):
        task = getattr(obj, "task", obj)
        board = getattr(task, "board", None)
        if board is None:
            return False
        return is_board_owner_or_member(request.user, board)


class IsTaskCreatorOrBoardOwnerCanDelete(BasePermission):
    message = "Only the task creator or board owner can delete this task."

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.method != "DELETE":
            return True
        board_owner_id = obj.board.owner_id if obj.board else None
        return request.user.id in {obj.created_by_id, board_owner_id}


class IsCommentAuthor(BasePermission):
    message = "Only the comment author can delete this comment."

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.method != "DELETE":
            return True
        return obj.author_id == request.user.id
