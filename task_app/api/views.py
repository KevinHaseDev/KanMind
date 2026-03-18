from django.db.models import Count   									# Importiert Aggregatfunktion fuer Kommentarzaehler.
from django.http import Http404										# Importiert 404-Exception fuer explizite Not-Found-Faelle.
from rest_framework import generics, permissions, status  					# Importiert DRF-Generic-Views, Permission-Klassen und Statuscodes.
from rest_framework.exceptions import PermissionDenied  					# Importiert Exception fuer verbotenen Zugriff.
from rest_framework.exceptions import NotFound   						# Importiert Exception fuer nicht gefunden.
from rest_framework.response import Response  							# Importiert den DRF-Response-Wrapper.

from board_app.models import Board  									# Importiert das Board-Modell fuer Existenz- und Mitgliedschaftspruefungen.
from .permissions import (  											# Importiert wiederverwendbare Permissions fuer Task- und Comment-Endpunkte.
	IsCommentAuthor,
	IsTaskBoardMember,
	IsTaskBoardMemberForCreate,
	IsTaskCreatorOrBoardOwnerCanDelete,
)
from .serializers import CommentListSerializer, CommentSerializer, TaskSerializer, TaskUpdateResponseSerializer  # Importiert Serializer fuer Task-/Comment-Endpunkte.
from ..models import Comment, Task  									# Importiert Task- und Comment-Modelle fuer die Endpunkte.


def user_can_access_board(user, board):  								# Hilfsfunktion zur Pruefung, ob ein Benutzer im Board-Kontext zugreifen darf.
	if user.is_superuser:  												# Superuser darf immer auf Board-bezogene Task-Aktionen zugreifen.
		return True
	return board.owner_id == user.id or board.members.filter(id=user.id).exists()  # Gibt true zurueck bei Board-Owner oder Board-Member.


class TaskAssignedToMeListView(generics.ListAPIView):  					# Endpunkt fuer Tasks, die dem aktuellen Benutzer zugewiesen sind.
	serializer_class = TaskSerializer  										# Nutzt Task-Serializer fuer das Antwortformat.
	permission_classes = [permissions.IsAuthenticated]  					# Erfordert authentifizierte Benutzer.

	def get_queryset(self):  											# Baut das Queryset fuer den Assigned-to-me-Endpunkt.
		user = self.request.user  										# Liest den aktuell authentifizierten Benutzer.
		return (  															# Gibt optimiertes Queryset mit benoetigten Relationen zurueck.
			Task.objects.filter(assignies=user)  							# Filtert Tasks, bei denen der aktuelle Benutzer zugewiesen ist.
			.select_related("board", "reviewer")  						# Joint Board und Reviewer zur Reduzierung zusaetzlicher Queries.
			.prefetch_related("assignies")  							# Prefetched die Assignee-Relation fuer die Serialisierung.
			.annotate(comments_count=Count("comments", distinct=True))  	# Annotiert jeden Task mit Kommentaranzahl.
			.distinct()  											# Entfernt Duplikate durch Joins.
		)


class TaskReviewingListView(generics.ListAPIView):  						# Endpunkt fuer Tasks, die vom aktuellen Benutzer reviewed werden.
	serializer_class = TaskSerializer  										# Nutzt Task-Serializer fuer das Antwortformat.
	permission_classes = [permissions.IsAuthenticated]  					# Erfordert authentifizierte Benutzer.

	def get_queryset(self):  											# Baut das Queryset fuer den Reviewing-Endpunkt.
		user = self.request.user  										# Liest den aktuell authentifizierten Benutzer.
		return (  															# Gibt optimiertes Queryset mit benoetigten Relationen zurueck.
			Task.objects.filter(reviewer=user)  							# Filtert Tasks, bei denen der aktuelle Benutzer Reviewer ist.
			.select_related("board", "reviewer")  						# Joint Board und Reviewer zur Reduzierung zusaetzlicher Queries.
			.prefetch_related("assignies")  							# Prefetched die Assignee-Relation fuer die Serialisierung.
			.annotate(comments_count=Count("comments", distinct=True))  	# Annotiert jeden Task mit Kommentaranzahl.
			.distinct()  											# Entfernt Duplikate durch Joins.
		)


class TaskCreateView(generics.CreateAPIView):  							# Endpunkt zum Erstellen eines Tasks.
	serializer_class = TaskSerializer  										# Nutzt Task-Serializer fuer Ein- und Ausgabe.
	permission_classes = [permissions.IsAuthenticated, IsTaskBoardMemberForCreate]  # Erfordert Authentifizierung und Board-Zugehoerigkeit fuer Task-Erstellung.
	# Board-Existenz und Permissions werden in perform_create behandelt; keine explizite create()-Override notwendig.

	def perform_create(self, serializer):
		board = serializer.validated_data.get("board")
		# Falls der Client eine Board-ID gesendet hat, aber das Board nicht validiert wurde -> 404
		initial_board = serializer.initial_data.get("board") if hasattr(serializer, "initial_data") else None
		if initial_board is not None and board is None:
			raise NotFound("Board not found.")

		if board and not user_can_access_board(self.request.user, board):
			raise PermissionDenied("You must be a board owner or member to create tasks for this board.")

		serializer.save(created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):  		# Endpunkt fuer Patchen und Loeschen eines einzelnen Tasks.
	queryset = Task.objects.select_related("board", "reviewer").prefetch_related("assignies").annotate(comments_count=Count("comments", distinct=True))  # Liefert optimiertes Queryset inkl. Kommentaranzahl.
	serializer_class = TaskSerializer  									# Nutzt TaskSerializer fuer eingehende Patch-Validierung.
	permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember, IsTaskCreatorOrBoardOwnerCanDelete]  # Erzwingt objektbezogene Zugriffs- und Delete-Regeln.
	lookup_url_kwarg = "task_id"  										# Liest die Task-ID aus dem URL-Parameter task_id.
	http_method_names = ["patch", "delete"]  						# Erlaubt nur PATCH und DELETE fuer diesen Endpunkt.

	def partial_update(self, request, *args, **kwargs):  					# Behandelt partielle Updates mit benutzerdefinierter Antwortstruktur.
		if "board" in request.data:  									# Blockiert Board-Neuzuweisung ueber den Patch-Endpunkt.
			return Response({"board": ["Changing the board of a task is not allowed."]}, status=status.HTTP_400_BAD_REQUEST)  # Gibt 400 fuer unerlaubtes Board-Feld zurueck.

		instance = self.get_object()  									# Laedt Task inkl. automatischer Objekt-Permission-Pruefung.
		serializer = self.get_serializer(instance, data=request.data, partial=True)  # Baut Serializer fuer partielle Update-Validierung.
		serializer.is_valid(raise_exception=True)  						# Validiert die Request-Payload.
		self.perform_update(serializer)  								# Speichert die aktualisierte Task-Instanz.

		updated_task = self.get_queryset().get(id=instance.id)  				# Laedt aktualisierten Task mit annotierten Feldern neu.
		return Response(TaskUpdateResponseSerializer(updated_task).data, status=status.HTTP_200_OK)  # Gibt die geforderte Update-Antwortstruktur zurueck.


class TaskCommentsListCreateView(generics.ListCreateAPIView):  			# Endpunkt zum Listen und Erstellen von Kommentaren unter einem Task.
	permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember]  	# Erfordert Authentifizierung und Board-Zugehoerigkeit.

	def get_serializer_class(self):  									# Waehlt den Serializer anhand der HTTP-Methode.
		if self.request.method == "GET":  								# Nutzt den Listen-Serializer fuer GET-Antworten.
			return CommentListSerializer
		return CommentSerializer  										# Nutzt den Create-Serializer fuer POST-Validierung.

	def get_task(self):  											# Laedt den Task fuer den URL-Parameter task_id.
		task = Task.objects.select_related("board").filter(id=self.kwargs["task_id"]).first()  # Holt Task inkl. Board-Relation.
		if task is None:  											# Behandelt unbekannte Task-ID.
			raise Http404
		self.check_object_permissions(self.request, task)  					# Prueft objektbezogene Board-Mitglieds-Permissions.
		return task

	def get_queryset(self):  										# Baut das Queryset fuer Kommentarlisten.
		task = self.get_task()  										# Laedt und prueft den Parent-Task.
		return Comment.objects.filter(task=task).select_related("author").order_by("created_at")  # Gibt Kommentare chronologisch sortiert zurueck.

	def perform_create(self, serializer):
		# Setzt Parent-Task und Author beim Erstellen (wird von Generic create() aufgerufen).
		task = self.get_task()
		serializer.save(task=task, author=self.request.user)

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		comment = serializer.instance
		return Response(CommentListSerializer(comment).data, status=status.HTTP_201_CREATED)


class TaskCommentDeleteView(generics.DestroyAPIView):  					# Endpunkt zum Loeschen eines bestimmten Kommentars.
	permission_classes = [permissions.IsAuthenticated, IsCommentAuthor]  	# Erfordert Authentifizierung und Author-Rechte.
	lookup_url_kwarg = "comment_id"  									# Liest die Kommentar-ID aus dem URL-Parameter comment_id.

	def get_queryset(self):  										# Schränkt loeschbare Kommentare auf den uebergebenen Task ein.
		return Comment.objects.select_related("task", "task__board", "author").filter(task_id=self.kwargs["task_id"])  # Laedt Kommentare nur im Kontext des angefragten Tasks.
