from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework.authentication import TokenAuthentication
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Board
from .serializers import (
	BoardDetailSerializer,
	BoardListSerializer,
	BoardSerializer,
	BoardUpdateResponseSerializer,
	EmailCheckQuerySerializer,
	UserSummarySerializer,
)


User = get_user_model()


class IsBoardOwnerOrReadOnly(permissions.BasePermission):
	def has_object_permission(self, request, view, obj):
		if request.method in permissions.SAFE_METHODS or request.method == "PATCH":
			return obj.owner_id == request.user.id or obj.members.filter(id=request.user.id).exists()
		return obj.owner_id == request.user.id


class BoardListCreateView(generics.ListCreateAPIView):
	serializer_class = BoardSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_serializer_class(self):
		if self.request.method == "GET":
			return BoardListSerializer
		return BoardSerializer

	def get_queryset(self):
		user = self.request.user
		return (
			Board.objects.filter(Q(owner=user) | Q(members=user))
			.distinct()
			.annotate(
				member_count=Count("members", distinct=True),
				ticket_count=Count("tasks", distinct=True),
				tasks_to_do_count=Count("tasks", filter=Q(tasks__status__iexact="to-do"), distinct=True),
				tasks_high_prio_count=Count("tasks", filter=Q(tasks__priority__iexact="high"), distinct=True),
			)
		)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		board = serializer.save(owner=request.user)
		board.members.add(request.user)

		summary_board = (
			Board.objects.filter(pk=board.pk)
			.annotate(
				member_count=Count("members", distinct=True),
				ticket_count=Count("tasks", distinct=True),
				tasks_to_do_count=Count("tasks", filter=Q(tasks__status__iexact="to-do"), distinct=True),
				tasks_high_prio_count=Count("tasks", filter=Q(tasks__priority__iexact="high"), distinct=True),
			)
			.first()
		)

		response_serializer = BoardListSerializer(summary_board)
		headers = self.get_success_headers(response_serializer.data)
		return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
	queryset = Board.objects.select_related("owner").prefetch_related("members", "tasks", "tasks__assignies", "tasks__reviewer")
	serializer_class = BoardSerializer
	permission_classes = [permissions.IsAuthenticated, IsBoardOwnerOrReadOnly]
	lookup_url_kwarg = "board_id"

	def get_serializer_class(self):
		if self.request.method == "GET":
			return BoardDetailSerializer
		return BoardSerializer

	def patch(self, request, *args, **kwargs):
		instance = self.get_object()
		serializer = BoardSerializer(instance, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		board = serializer.save()

		if "members" in serializer.validated_data:
			board.members.set(serializer.validated_data["members"])
			board.members.add(board.owner)

		response_serializer = BoardUpdateResponseSerializer(board)
		return Response(response_serializer.data, status=status.HTTP_200_OK)


class EmailCheckView(APIView):
	permission_classes = [permissions.IsAuthenticated]
	authentication_classes = [TokenAuthentication]

	def get(self, request):
		query_serializer = EmailCheckQuerySerializer(data=request.query_params)
		if not query_serializer.is_valid():
			return Response(query_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		email = query_serializer.validated_data["email"]
		user = User.objects.filter(email=email).first()
		if user is None:
			return Response({"detail": "Email not found."}, status=status.HTTP_404_NOT_FOUND)

		return Response(UserSummarySerializer(user).data, status=status.HTTP_200_OK)
