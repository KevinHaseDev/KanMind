from django.db.models import Count
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from board.models import Board
from .models import Comment, Task
from .serializers import CommentListSerializer, CommentSerializer, TaskSerializer, TaskUpdateResponseSerializer


def user_can_access_board(user, board):
	return board.owner_id == user.id or board.members.filter(id=user.id).exists()


class TaskAssignedToMeListView(generics.ListAPIView):
	serializer_class = TaskSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		return (
			Task.objects.filter(assignies=user)
			.select_related("board", "reviewer")
			.prefetch_related("assignies")
			.annotate(comments_count=Count("comments", distinct=True))
			.distinct()
		)


class TaskReviewingListView(generics.ListAPIView):
	serializer_class = TaskSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		return (
			Task.objects.filter(reviewer=user)
			.select_related("board", "reviewer")
			.prefetch_related("assignies")
			.annotate(comments_count=Count("comments", distinct=True))
			.distinct()
		)


class TaskCreateView(generics.CreateAPIView):
	serializer_class = TaskSerializer
	permission_classes = [permissions.IsAuthenticated]

	def create(self, request, *args, **kwargs):
		board_id = request.data.get("board")
		if board_id is not None and not Board.objects.filter(id=board_id).exists():
			return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)

		return super().create(request, *args, **kwargs)

	def perform_create(self, serializer):
		board = serializer.validated_data.get("board")
		if board and not user_can_access_board(self.request.user, board):
			raise PermissionDenied("You must be a board owner or member to create tasks for this board.")
		serializer.save(created_by=self.request.user)


class TaskDetailView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get_object(self, task_id):
		return Task.objects.select_related("board", "reviewer").prefetch_related("assignies").filter(id=task_id).annotate(
			comments_count=Count("comments", distinct=True)
		).first()

	def _check_board_access(self, user, task):
		board = task.board
		if board and not user_can_access_board(user, board):
			raise PermissionDenied("You must be a board owner or member to access this task.")

	def patch(self, request, task_id):
		task = self.get_object(task_id)
		if task is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

		if "board" in request.data:
			return Response({"board": ["Changing the board of a task is not allowed."]}, status=status.HTTP_400_BAD_REQUEST)

		self._check_board_access(request.user, task)
		serializer = TaskSerializer(task, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		updated_task = serializer.save()
		updated_task = (
			Task.objects.select_related("board", "reviewer")
			.prefetch_related("assignies")
			.annotate(comments_count=Count("comments", distinct=True))
			.get(id=updated_task.id)
		)
		return Response(TaskUpdateResponseSerializer(updated_task).data, status=status.HTTP_200_OK)

	def delete(self, request, task_id):
		task = self.get_object(task_id)
		if task is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

		board_owner_id = task.board.owner_id if task.board else None
		if request.user.id not in {task.created_by_id, board_owner_id}:
			raise PermissionDenied("Only the task creator or board owner can delete this task.")

		task.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class TaskCommentsListCreateView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get_task(self, task_id):
		return Task.objects.select_related("board").filter(id=task_id).first()

	def _check_board_access(self, user, task):
		board = task.board
		if board and not user_can_access_board(user, board):
			raise PermissionDenied("You must be a board owner or member to access comments of this task.")

	def get(self, request, task_id):
		task = self.get_task(task_id)
		if task is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

		self._check_board_access(request.user, task)
		comments = Comment.objects.filter(task=task).select_related("author").order_by("created_at")
		return Response(CommentListSerializer(comments, many=True).data, status=status.HTTP_200_OK)

	def post(self, request, task_id):
		task = self.get_task(task_id)
		if task is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

		self._check_board_access(request.user, task)
		serializer = CommentSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		comment = serializer.save(task=task, author=request.user)
		return Response(CommentListSerializer(comment).data, status=status.HTTP_201_CREATED)


class TaskCommentDeleteView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def delete(self, request, task_id, comment_id):
		comment = Comment.objects.select_related("task", "task__board", "author").filter(id=comment_id, task_id=task_id).first()
		if comment is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

		if comment.author_id != request.user.id:
			raise PermissionDenied("Only the comment author can delete this comment.")

		comment.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
