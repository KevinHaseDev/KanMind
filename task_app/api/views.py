"""Task API views for listing, modifying, and commenting on tasks."""

from django.http import Http404
from django.db.models import Count, Q

from rest_framework import generics, status
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
    """Return whether a user can access the given board."""
    if user.is_superuser:
        return True
    return board.owner_id == user.id or board.members.filter(id=user.id).exists()


class TaskBaseQuerysetMixin:
    """Provide a shared optimized base queryset for task API views."""

    def _base_task_queryset(self):
        """Return task queryset with joins and comment count annotation."""
        return (
            Task.objects.select_related("board", "reviewer")
            .prefetch_related("assignees")
            .annotate(comments_count=Count("comments", distinct=True))
        )


class TaskListCreateView(TaskBaseQuerysetMixin, generics.ListCreateAPIView):
    """List accessible tasks and create a task on an accessible board."""

    serializer_class = TaskSerializer
    permission_classes = [IsTaskBoardMemberForCreate]

    def get_queryset(self):
        """Return tasks visible to the current user."""
        user = self.request.user
        return (
            self._base_task_queryset()
            .filter(
                Q(board__owner=user)
                | Q(board__members=user)
                | Q(created_by=user)
                | Q(assignees=user)
                | Q(reviewer=user)
            )
            .distinct()
        )

    def get_permissions(self):
        """Apply create permission only for POST requests."""
        if self.request.method == "POST":
            return [IsTaskBoardMemberForCreate()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create task after validating board access constraints."""
        board = self._get_requested_board(serializer)
        self._ensure_board_access(board)
        serializer.save(created_by=self.request.user)

    def _get_requested_board(self, serializer):
        """Return validated board and detect non-existing board ids."""
        board = serializer.validated_data.get("board")
        initial_board = getattr(serializer, "initial_data", {}).get("board")
        if initial_board is not None and board is None:
            raise NotFound("Board not found.")
        return board

    def _ensure_board_access(self, board):
        """Ensure current user can create tasks for the board."""
        if board and not user_can_access_board(self.request.user, board):
            raise PermissionDenied(
                "You must be a board owner or member to create tasks for this board."
            )


class TaskAssignedToMeListView(TaskBaseQuerysetMixin, generics.ListAPIView):
    """List tasks assigned to the current user."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        """Return distinct tasks assigned to the current user."""
        return self._base_task_queryset().filter(assignees=self.request.user).distinct()


class TaskReviewingListView(TaskBaseQuerysetMixin, generics.ListAPIView):
    """List tasks where the current user is reviewer."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        """Return distinct tasks reviewed by the current user."""
        return self._base_task_queryset().filter(reviewer=self.request.user).distinct()


class TaskDetailView(TaskBaseQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, and delete a single accessible task."""

    serializer_class = TaskSerializer
    permission_classes = [IsTaskBoardMember]
    lookup_url_kwarg = "task_id"
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Return tasks visible to the current user."""
        user = self.request.user
        return (
            self._base_task_queryset()
            .filter(
                Q(board__owner=user)
                | Q(board__members=user)
                | Q(created_by=user)
                | Q(assignees=user)
                | Q(reviewer=user)
            )
            .distinct()
        )

    def get_permissions(self):
        """Apply extra permission checks for write and delete operations."""
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsTaskBoardMember(), IsTaskCreatorOrBoardOwnerCanDelete()]
        return super().get_permissions()

    def _board_change_response(self):
        """Return a 400 response when board changes are requested."""
        return Response(
            {"board": ["Changing the board of a task is not allowed."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _normalize_status(self, status_value):
        """Normalize status aliases to canonical status values."""
        status_aliases = {
            "todo": "to-do",
            "to do": "to-do",
            "in progress": "in-progress",
        }
        raw_status = str(status_value or "").strip().lower()
        return status_aliases.get(raw_status, raw_status)

    def _validate_status(self, status_value):
        """Validate normalized status and return it."""
        normalized_status = self._normalize_status(status_value)
        allowed_statuses = {"to-do", "in-progress", "review", "done"}
        if normalized_status not in allowed_statuses:
            raise ValidationError(
                {
                    "status": [
                        "Status must be one of: to-do, in-progress, review, done."
                    ]
                }
            )
        return normalized_status

    def _build_update_response(self, instance):
        """Build the standard task update response payload."""
        updated_task = self.get_queryset().get(id=instance.id)
        serializer = TaskUpdateResponseSerializer(updated_task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _update_status_only(self, instance, status_value):
        """Apply a status-only patch and return API response."""
        instance.status = self._validate_status(status_value)
        instance.save(update_fields=["status"])
        return self._build_update_response(instance)

    def _update_partial_fields(self, instance, request_data):
        """Apply a generic partial update and return API response."""
        serializer = self.get_serializer(instance, data=request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return self._build_update_response(instance)

    def partial_update(self, request, *args, **kwargs):
        """Patch task fields while enforcing board and status constraints."""
        if "board" in request.data:
            return self._board_change_response()

        instance = self.get_object()
        if set(request.data.keys()) == {"status"}:
            return self._update_status_only(instance, request.data.get("status"))
        return self._update_partial_fields(instance, request.data)

    def options(self, request, *args, **kwargs):
        """Expose explicit CORS allow-methods for this endpoint."""
        response = super().options(request, *args, **kwargs)
        response["Allow"] = "GET, PATCH, DELETE, HEAD, OPTIONS"
        response["Access-Control-Allow-Methods"] = "GET, PATCH, DELETE, OPTIONS"
        return response


class TaskCommentsListCreateView(generics.ListCreateAPIView):
    """List comments for a task and create comments on that task."""

    permission_classes = [IsTaskBoardMember]
    serializer_class = CommentListSerializer

    def _get_task(self):
        """Fetch task by URL parameter and enforce object permissions."""
        task_id = self.kwargs.get("task_id")
        task = Task.objects.select_related("board").filter(id=task_id).first()
        if task is None:
            raise Http404
        self.check_object_permissions(self.request, task)
        return task

    def get_queryset(self):
        """Return comments ordered by creation timestamp."""
        task = self._get_task()
        return (
            Comment.objects.filter(task=task)
            .select_related("author")
            .order_by("created_at")
        )

    def get_serializer_class(self):
        """Use write serializer for POST and list serializer otherwise."""
        if self.request.method == "POST":
            return CommentSerializer
        return CommentListSerializer

    def create(self, request, *args, **kwargs):
        """Create a comment for the resolved task."""
        task = self._get_task()
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(task=task, author=request.user)
        return Response(CommentListSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)


class TaskCommentDeleteView(generics.DestroyAPIView):
    """Delete a task comment if permission checks pass."""

    permission_classes = [IsCommentAuthor]
    serializer_class = CommentListSerializer
    lookup_url_kwarg = "comment_id"

    def get_object(self):
        """Return comment identified by task and comment ids."""
        task_id = self.kwargs.get("task_id")
        comment_id = self.kwargs.get("comment_id")
        qs = Comment.objects.select_related("task", "task__board", "author")
        qs = qs.filter(task_id=task_id, id=comment_id)
        comment = qs.first()
        if comment is None:
            raise Http404
        self.check_object_permissions(self.request, comment)
        return comment