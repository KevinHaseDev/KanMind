from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from rest_framework import generics, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from ..models import Board
from .permissions import IsBoardOwnerOrReadOnly
from .serializers import (
	BoardDetailSerializer,
	BoardListSerializer,
	BoardSerializer,
	BoardUpdateResponseSerializer,
	EmailCheckQuerySerializer,
	UserSummarySerializer,
)


User = get_user_model()  # Ermittelt das konfigurierte Custom-User-Modell.


class BoardListCreateView(generics.ListCreateAPIView):  # Endpunkt fuer Board-Liste und Board-Erstellung.
	serializer_class = BoardSerializer  # Verwendet standardmaessig den Basis-Serializer.
	permission_classes = [permissions.IsAuthenticated]  # Erfordert authentifizierte Benutzer.

	def get_serializer_class(self):  # Waehlt den Serializer anhand der HTTP-Methode.
		if self.request.method == "GET":  # Nutzt den Summary-Serializer fuer Listenantworten.
			return BoardListSerializer  # Gibt den Board-Listen-Serializer zurueck.
		return BoardSerializer  # Nutzt den Basis-Serializer fuer Create-Payload-Validierung.

	def get_queryset(self):  # Baut das Queryset fuer den Board-Listenendpunkt.
		user = self.request.user  # Liest den authentifizierten Benutzer.
		return (  # Gibt ein annotiertes Queryset mit Board-Statistiken zurueck.
			Board.objects.filter(Q(owner=user) | Q(members=user))
			.distinct()
			.annotate(
				member_count=Count("members", distinct=True),
				ticket_count=Count("tasks", distinct=True),
				tasks_to_do_count=Count("tasks", filter=Q(tasks__status__iexact="to-do"), distinct=True),
				tasks_high_prio_count=Count("tasks", filter=Q(tasks__priority__iexact="high"), distinct=True),
			)
		)

	def perform_create(self, serializer):
		board = serializer.save(owner=self.request.user)
		board.members.add(self.request.user)

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


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):  # Endpunkt fuer Board-GET/PATCH/DELETE per ID.
	queryset = Board.objects.select_related("owner").prefetch_related("members", "tasks", "tasks__assignees", "tasks__reviewer")  # Optimiert relationale Ladevorgaenge fuer Detailantworten.
	serializer_class = BoardSerializer  # Verwendet standardmaessig den Basis-Serializer.
	permission_classes = [permissions.IsAuthenticated, IsBoardOwnerOrReadOnly]  # Erzwingt Authentifizierung und objektbezogene Board-Permissions.
	lookup_url_kwarg = "board_id"  # Liest die Board-ID aus dem URL-Parameter board_id.
	http_method_names = ["get", "patch", "delete", "head", "options"]

	def get_serializer_class(self):  # Waehlt den Serializer anhand der Methode.
		if self.request.method == "GET":  # Nutzt den Detail-Serializer fuer Retrieve.
			return BoardDetailSerializer
		return BoardSerializer

	def partial_update(self, request, *args, **kwargs):
		instance = self.get_object()
		serializer = BoardSerializer(instance, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		board = serializer.save()

		if "members" in serializer.validated_data:
			board.members.set(serializer.validated_data["members"])
			board.members.add(board.owner)

		response_serializer = BoardUpdateResponseSerializer(board)
		return Response(response_serializer.data, status=status.HTTP_200_OK)


class EmailCheckView(generics.RetrieveAPIView):  # Endpunkt zum Pruefen, ob eine E-Mail zu einem bestehenden Benutzer gehoert.
	permission_classes = [permissions.IsAuthenticated]  # Erfordert einen authentifizierten Benutzer.
	authentication_classes = [TokenAuthentication]  # Verwendet Token-Authentifizierung fuer diesen Endpunkt.
	serializer_class = UserSummarySerializer

	def get_object(self):
		query_serializer = EmailCheckQuerySerializer(data=self.request.query_params)  # Validiert die Query-Parameter.
		if not query_serializer.is_valid():
			raise ValidationError(query_serializer.errors)

		email = query_serializer.validated_data["email"]  # Liest den validierten E-Mail-Wert.
		user = User.objects.filter(email=email).first()  # Sucht nach passendem Benutzer ueber E-Mail.
		if user is None:
			raise NotFound("Email not found.")

		return user
