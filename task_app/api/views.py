from django.db.models import Count  # Importiert Aggregatfunktion fuer Kommentarzaehler.
from rest_framework import generics, permissions, status  # Importiert DRF-Generic-Views, Permission-Klassen und Statuscodes.
from rest_framework.exceptions import PermissionDenied  # Importiert Exception fuer verbotenen Zugriff.
from rest_framework.response import Response  # Importiert den DRF-Response-Wrapper.
from rest_framework.views import APIView  # Importiert die Basisklasse fuer benutzerdefinierte API-Endpunkte.

from board_app.models import Board  # Importiert das Board-Modell fuer Existenz- und Mitgliedschaftspruefungen.
from .permissions import (  # Importiert wiederverwendbare Permissions fuer Task- und Comment-Endpunkte.
	IsCommentAuthor,
	IsTaskBoardMember,
	IsTaskBoardMemberForCreate,
	IsTaskCreatorOrBoardOwnerCanDelete,
)
from .serializers import CommentListSerializer, CommentSerializer, TaskSerializer, TaskUpdateResponseSerializer  # Importiert Serializer fuer Task-/Comment-Endpunkte.
from ..models import Comment, Task  # Importiert Task- und Comment-Modelle fuer die Endpunkte.


def user_can_access_board(user, board):  # Hilfsfunktion zur Pruefung, ob ein Benutzer im Board-Kontext zugreifen darf.
	return board.owner_id == user.id or board.members.filter(id=user.id).exists()  # Gibt true zurueck bei Board-Owner oder Board-Member.


class TaskAssignedToMeListView(generics.ListAPIView):  # Endpunkt fuer Tasks, die dem aktuellen Benutzer zugewiesen sind.
	serializer_class = TaskSerializer  # Nutzt Task-Serializer fuer das Antwortformat.
	permission_classes = [permissions.IsAuthenticated]  # Erfordert authentifizierte Benutzer.

	def get_queryset(self):  # Baut das Queryset fuer den Assigned-to-me-Endpunkt.
		user = self.request.user  # Liest den aktuell authentifizierten Benutzer.
		return (  # Gibt optimiertes Queryset mit benoetigten Relationen zurueck.
			Task.objects.filter(assignies=user)  # Filtert Tasks, bei denen der aktuelle Benutzer zugewiesen ist.
			.select_related("board", "reviewer")  # Joint Board und Reviewer zur Reduzierung zusaetzlicher Queries.
			.prefetch_related("assignies")  # Prefetched die Assignee-Relation fuer die Serialisierung.
			.annotate(comments_count=Count("comments", distinct=True))  # Annotiert jeden Task mit Kommentaranzahl.
			.distinct()  # Entfernt Duplikate durch Joins.
		)


class TaskReviewingListView(generics.ListAPIView):  # Endpunkt fuer Tasks, die vom aktuellen Benutzer reviewed werden.
	serializer_class = TaskSerializer  # Nutzt Task-Serializer fuer das Antwortformat.
	permission_classes = [permissions.IsAuthenticated]  # Erfordert authentifizierte Benutzer.

	def get_queryset(self):  # Baut das Queryset fuer den Reviewing-Endpunkt.
		user = self.request.user  # Liest den aktuell authentifizierten Benutzer.
		return (  # Gibt optimiertes Queryset mit benoetigten Relationen zurueck.
			Task.objects.filter(reviewer=user)  # Filtert Tasks, bei denen der aktuelle Benutzer Reviewer ist.
			.select_related("board", "reviewer")  # Joint Board und Reviewer zur Reduzierung zusaetzlicher Queries.
			.prefetch_related("assignies")  # Prefetched die Assignee-Relation fuer die Serialisierung.
			.annotate(comments_count=Count("comments", distinct=True))  # Annotiert jeden Task mit Kommentaranzahl.
			.distinct()  # Entfernt Duplikate durch Joins.
		)


class TaskCreateView(generics.CreateAPIView):  # Endpunkt zum Erstellen eines Tasks.
	serializer_class = TaskSerializer  # Nutzt Task-Serializer fuer Ein- und Ausgabe.
	permission_classes = [permissions.IsAuthenticated, IsTaskBoardMemberForCreate]  # Erfordert Authentifizierung und Board-Zugehoerigkeit fuer Task-Erstellung.

	def create(self, request, *args, **kwargs):  # Ueberschreibt create fuer einen benutzerdefinierten board-not-found-Status.
		board_id = request.data.get("board")  # Liest die Board-ID aus dem Request-Body.
		if board_id is not None and not Board.objects.filter(id=board_id).exists():  # Prueft, ob das angegebene Board existiert.
			return Response({"detail": "Board not found."}, status=status.HTTP_404_NOT_FOUND)  # Gibt 404 zurueck, wenn das Board nicht existiert.

		return super().create(request, *args, **kwargs)  # Faellt auf den normalen DRF-Create-Ablauf zurueck.

	def perform_create(self, serializer):  # Fuegt Permission-Pruefungen vor dem Speichern hinzu.
		board = serializer.validated_data.get("board")  # Liest das validierte Board-Objekt.
		if board and not user_can_access_board(self.request.user, board):  # Blockiert Benutzer ausserhalb des Board-Kontexts.
			raise PermissionDenied("You must be a board owner or member to create tasks for this board.")  # Gibt 403 zurueck, wenn Board-Zugriff fehlt.
		serializer.save(created_by=self.request.user)  # Speichert den Task und setzt den Ersteller automatisch.


class TaskDetailView(APIView):  # Endpunkt fuer Patchen und Loeschen eines einzelnen Tasks.
	permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember, IsTaskCreatorOrBoardOwnerCanDelete]  # Erzwingt objektbezogene Zugriffs- und Delete-Regeln.

	def get_object(self, task_id):  # Hilfsfunktion, um einen Task mit optimierten Relationen zu laden.
		return Task.objects.select_related("board", "reviewer").prefetch_related("assignies").filter(id=task_id).annotate(  # Baut optimiertes Queryset fuer einen Task.
			comments_count=Count("comments", distinct=True)  # Annotiert den Task mit Kommentaranzahl.
		).first()  # Gibt den ersten Treffer oder None zurueck.

	def patch(self, request, task_id):  # Behandelt partielle Updates eines Tasks.
		task = self.get_object(task_id)  # Laedt den Task per ID.
		if task is None:  # Behandelt unbekannte Task-ID.
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)  # Gibt 404 fuer fehlenden Task zurueck.

		if "board" in request.data:  # Blockiert Board-Neuzuweisung ueber den Patch-Endpunkt.
			return Response({"board": ["Changing the board of a task is not allowed."]}, status=status.HTTP_400_BAD_REQUEST)  # Gibt 400 fuer unerlaubtes Board-Feld zurueck.

		self.check_object_permissions(request, task)  # Prueft objektbezogene Task-Permissions.
		serializer = TaskSerializer(task, data=request.data, partial=True)  # Erstellt Serializer fuer partielle Update-Validierung.
		serializer.is_valid(raise_exception=True)  # Validiert die Request-Payload.
		updated_task = serializer.save()  # Speichert die aktualisierte Task-Instanz.
		updated_task = (  # Laedt den Task mit annotierten Feldern fuer die Antwort neu.
			Task.objects.select_related("board", "reviewer")  # Joint Board- und Reviewer-Relation.
			.prefetch_related("assignies")  # Prefetched die Assignee-Relation.
			.annotate(comments_count=Count("comments", distinct=True))  # Berechnet die Kommentaranzahl erneut per Annotation.
			.get(id=updated_task.id)  # Holt die aktualisierte Zeile per ID.
		)
		return Response(TaskUpdateResponseSerializer(updated_task).data, status=status.HTTP_200_OK)  # Gibt die Update-Antwort mit geforderter Feldstruktur zurueck.

	def delete(self, request, task_id):  # Behandelt das Loeschen eines Tasks.
		task = self.get_object(task_id)  # Laedt den Task per ID.
		if task is None:  # Behandelt unbekannte Task-ID.
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)  # Gibt 404 fuer fehlenden Task zurueck.
		self.check_object_permissions(request, task)  # Prueft objektbezogene Task-Permissions.

		task.delete()  # Loescht die Task-Zeile dauerhaft aus der Datenbank.
		return Response(status=status.HTTP_204_NO_CONTENT)  # Gibt eine leere Erfolgsantwort zurueck.


class TaskCommentsListCreateView(APIView):  # Endpunkt zum Listen und Erstellen von Kommentaren unter einem Task.
	permission_classes = [permissions.IsAuthenticated, IsTaskBoardMember]  # Erfordert Authentifizierung und Board-Zugehoerigkeit.

	def get_task(self, task_id):  # Hilfsfunktion zum Laden eines Tasks mit Board-Relation.
		return Task.objects.select_related("board").filter(id=task_id).first()  # Gibt Task per ID oder None zurueck.

	def get(self, request, task_id):  # Behandelt Anfragen fuer Kommentarlisten.
		task = self.get_task(task_id)  # Laedt den Task per ID.
		if task is None:  # Behandelt unbekannte Task-ID.
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)  # Gibt 404 fuer fehlenden Task zurueck.
		self.check_object_permissions(request, task)  # Prueft objektbezogene Comment-Listen-Permissions.
		comments = Comment.objects.filter(task=task).select_related("author").order_by("created_at")  # Laedt Kommentare chronologisch sortiert mit Author-Relation.
		return Response(CommentListSerializer(comments, many=True).data, status=status.HTTP_200_OK)  # Gibt die serialisierte Kommentarliste zurueck.

	def post(self, request, task_id):  # Behandelt das Erstellen eines neuen Kommentars.
		task = self.get_task(task_id)  # Laedt den Task per ID.
		if task is None:  # Behandelt unbekannte Task-ID.
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)  # Gibt 404 fuer fehlenden Task zurueck.
		self.check_object_permissions(request, task)  # Prueft objektbezogene Comment-Create-Permissions.
		serializer = CommentSerializer(data=request.data)  # Baut den Serializer fuer Eingabevalidierung auf.
		serializer.is_valid(raise_exception=True)  # Validiert die Kommentar-Payload.
		comment = serializer.save(task=task, author=request.user)  # Speichert den Kommentar mit Task und authentifiziertem Author.
		return Response(CommentListSerializer(comment).data, status=status.HTTP_201_CREATED)  # Gibt den erstellten Kommentar im Listenformat zurueck.


class TaskCommentDeleteView(APIView):  # Endpunkt zum Loeschen eines bestimmten Kommentars.
	permission_classes = [permissions.IsAuthenticated, IsCommentAuthor]  # Erfordert Authentifizierung und Author-Rechte.

	def delete(self, request, task_id, comment_id):  # Behandelt Anfragen zum Loeschen von Kommentaren.
		comment = Comment.objects.select_related("task", "task__board", "author").filter(id=comment_id, task_id=task_id).first()  # Laedt Kommentar im Kontext des Tasks.
		if comment is None:  # Behandelt unbekannten Kommentar oder falsche Task-Kommentar-Kombination.
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)  # Gibt 404 fuer fehlende Kommentar/Task-Kombination zurueck.
		self.check_object_permissions(request, comment)  # Prueft objektbezogene Comment-Delete-Permissions.

		comment.delete()  # Loescht die Kommentarzeile dauerhaft.
		return Response(status=status.HTTP_204_NO_CONTENT)  # Gibt eine leere Erfolgsantwort zurueck.
