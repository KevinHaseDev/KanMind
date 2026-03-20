from django.http import Http404
from django.db.models import Count, Q

from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
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


class TaskBaseQuerysetMixin:
    def _base_task_queryset(self):
        return (
            Task.objects.select_related("board", "reviewer")
            .prefetch_related("assignees")
            .annotate(comments_count=Count("comments", distinct=True))
        )


class TaskListCreateView(TaskBaseQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            self._base_task_queryset()
            .filter(
                Q(board__owner=user) | Q(board__members=user) | Q(created_by=user) | Q(assignees=user) | Q(reviewer=user)
            )
            .distinct()
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsTaskBoardMemberForCreate()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        board = serializer.validated_data.get("board")
        initial_board = serializer.initial_data.get("board") if hasattr(serializer, "initial_data") else None
        if initial_board is not None and board is None:
            raise NotFound("Board not found.")

        if board and not user_can_access_board(self.request.user, board):
            raise PermissionDenied("You must be a board owner or member to create tasks for this board.")

        serializer.save(created_by=self.request.user)


class TaskAssignedToMeListView(TaskBaseQuerysetMixin, generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self._base_task_queryset().filter(assignees=self.request.user).distinct()


class TaskReviewingListView(TaskBaseQuerysetMixin, generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self._base_task_queryset().filter(reviewer=self.request.user).distinct()


class TaskDetailView(TaskBaseQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember]
    lookup_url_kwarg = "task_id"
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        return (
            self._base_task_queryset()
            .filter(
                Q(board__owner=user) | Q(board__members=user) | Q(created_by=user) | Q(assignees=user) | Q(reviewer=user)
            )
            .distinct()
        )

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [permissions.IsAuthenticated(), IsTaskBoardMember(), IsTaskCreatorOrBoardOwnerCanDelete()]
        if self.request.method == "GET":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def partial_update(self, request, *args, **kwargs):
        if "board" in request.data:
            return Response({"board": ["Changing the board of a task is not allowed."]}, status=status.HTTP_400_BAD_REQUEST)

        instance = self.get_object()

        if set(request.data.keys()) == {"status"}:
            raw_status = str(request.data.get("status", "")).strip().lower()
            status_aliases = {
                "todo": "to-do",
                "to do": "to-do",
                "in progress": "in-progress",
            }
            normalized_status = status_aliases.get(raw_status, raw_status)
            allowed_statuses = {"to-do", "in-progress", "review", "done"}
            if normalized_status not in allowed_statuses:
                raise ValidationError({"status": ["Status must be one of: to-do, in-progress, review, done."]})

            instance.status = normalized_status
            instance.save(update_fields=["status"])
            updated_task = self.get_queryset().get(id=instance.id)
            return Response(TaskUpdateResponseSerializer(updated_task).data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        updated_task = self.get_queryset().get(id=instance.id)
        return Response(TaskUpdateResponseSerializer(updated_task).data, status=status.HTTP_200_OK)

    def options(self, request, *args, **kwargs):
        response = super().options(request, *args, **kwargs)
        response["Allow"] = "GET, PATCH, DELETE, HEAD, OPTIONS"
        response["Access-Control-Allow-Methods"] = "GET, PATCH, DELETE, OPTIONS"
        return response


class TaskCommentsListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember]
    serializer_class = CommentListSerializer

    def _get_task(self):
        task_id = self.kwargs.get("task_id")
        task = Task.objects.select_related("board").filter(id=task_id).first()
        if task is None:
            raise Http404
        self.check_object_permissions(self.request, task)
        return task

    def get_queryset(self):
        task = self._get_task()
        return Comment.objects.filter(task=task).select_related("author").order_by("created_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentSerializer
        return CommentListSerializer

    def create(self, request, *args, **kwargs):
        task = self._get_task()
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, author=request.user)
        return Response(CommentListSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)


class TaskCommentDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsCommentAuthor]
    serializer_class = CommentListSerializer
    lookup_url_kwarg = "comment_id"

    def get_object(self):
        task_id = self.kwargs.get("task_id")
        comment_id = self.kwargs.get("comment_id")
        qs = Comment.objects.select_related("task", "task__board", "author").filter(task_id=task_id, id=comment_id)
        comment = qs.first()
        if comment is None:
            raise Http404
        self.check_object_permissions(self.request, comment)
        return comment