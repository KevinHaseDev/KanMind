from django.http import Http404
from django.db.models import Count, Q

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from board_app.models import Board
from ..models import Comment, Task
from .permissions import (
    IsCommentAuthor,
    IsTaskBoardMember,
    IsTaskBoardMemberForCreate,
    IsTaskCreatorOrBoardOwnerCanDelete,
)
from .serializers import (
    CommentListSerializer,
    CommentSerializer,
    TaskSerializer,
    TaskUpdateResponseSerializer,
)


def user_can_access_board(user, board):
    if user.is_superuser:
        return True
    return board.owner_id == user.id or board.members.filter(id=user.id).exists()


class TaskViewSet(viewsets.ModelViewSet):
    """ModelViewSet fuer Task CRUD. Zusätzliche Listen als Actions: assigned_to_me, reviewing."""
    queryset = Task.objects.select_related("board", "reviewer").prefetch_related("assignees").annotate(comments_count=Count("comments", distinct=True))
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        user = self.request.user
        qs = (
            Task.objects.filter(
                Q(board__owner=user) | Q(board__members=user) | Q(created_by=user) | Q(assignees=user) | Q(reviewer=user)
            )
            .select_related("board", "reviewer")
            .prefetch_related("assignees")
            .annotate(comments_count=Count("comments", distinct=True))
            .distinct()
        )
        return qs

    def get_permissions(self):
        # Always require authentication
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsTaskBoardMemberForCreate()]
        if self.action in ["partial_update", "destroy", "update"]:
            return [permissions.IsAuthenticated(), IsTaskBoardMember(), IsTaskCreatorOrBoardOwnerCanDelete()]
        if self.action == "retrieve":
            return [permissions.IsAuthenticated(), IsTaskBoardMember()]
        # list and non-object custom list-like actions are protected by authentication and queryset filtering
        if self.action in ["list", "assigned_to_me", "reviewing"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        board = serializer.validated_data.get("board")
        initial_board = serializer.initial_data.get("board") if hasattr(serializer, "initial_data") else None
        if initial_board is not None and board is None:
            raise NotFound("Board not found.")

        if board and not user_can_access_board(self.request.user, board):
            raise PermissionDenied("You must be a board owner or member to create tasks for this board.")

        serializer.save(created_by=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        if "board" in request.data:
            return Response({"board": ["Changing the board of a task is not allowed."]}, status=status.HTTP_400_BAD_REQUEST)

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        updated_task = self.get_queryset().get(id=instance.id)
        return Response(TaskUpdateResponseSerializer(updated_task).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="assigned-to-me")
    def assigned_to_me(self, request):
        user = request.user
        qs = (
            Task.objects.filter(assignees=user)
            .select_related("board", "reviewer")
            .prefetch_related("assignees")
            .annotate(comments_count=Count("comments", distinct=True))
            .distinct()
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TaskSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="reviewing")
    def reviewing(self, request):
        user = request.user
        qs = (
            Task.objects.filter(reviewer=user)
            .select_related("board", "reviewer")
            .prefetch_related("assignees")
            .annotate(comments_count=Count("comments", distinct=True))
            .distinct()
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TaskSerializer(qs, many=True)
        return Response(serializer.data)


class TaskCommentsListCreateView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember]

    def get_task(self, request, task_id):
        task = Task.objects.select_related("board").filter(id=task_id).first()
        if task is None:
            raise Http404
        self.check_object_permissions(request, task)
        return task

    def list(self, request, task_id=None):
        task = self.get_task(request, task_id)
        qs = Comment.objects.filter(task=task).select_related("author").order_by("created_at")
        serializer = CommentListSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, task_id=None):
        task = self.get_task(request, task_id)
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, author=request.user)
        return Response(CommentListSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)


class TaskCommentDeleteView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthor]

    def destroy(self, request, task_id=None, comment_id=None):
        qs = Comment.objects.select_related("task", "task__board", "author").filter(task_id=task_id, id=comment_id)
        comment = qs.first()
        if comment is None:
            raise Http404
        self.check_object_permissions(request, comment)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
