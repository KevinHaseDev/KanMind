from board_app.models import Board								# Importiert das Board-Modell zur Pruefung von Mitgliedschaften.
from rest_framework.permissions import BasePermission			# Importiert die Basisklasse zum Erstellen eigener Permissions.


def is_board_owner_or_member(user, board):						# Hilfsfunktion, die prueft, ob ein User Owner oder Member eines Boards ist.
	if user.is_superuser:										# Superuser darf immer auf Boards zugreifen.
		return True
	return board.owner_id == user.id or board.members.filter(id=user.id).exists()	# True fuer Owner oder vorhandenes Mitglied.


class IsTaskBoardMemberForCreate(BasePermission):				# Permission fuer das Erstellen von Tasks in einem Board.
	"""Ensure task creation is allowed only for board owner/member when board is provided."""	# Dokumentiert das Verhalten.

	message = "You must be a board owner or member to create tasks for this board."  # Fehlermeldung bei Verweigerung.

	def has_permission(self, request, view):					# Ueberprueft allgemeine (nicht objektbezogene) Berechtigung.
		if request.method != "POST":							# Nur POST-Anfragen interessieren diese Permission.
			return True											# Andere Methoden bleiben unberuecksichtigt.
		board_id = request.data.get("board")					# Liest optional die Board-ID aus dem Request-Body.
		if not board_id:										# Wenn keine Board-ID angegeben ist, erlauben wir die Aktion (keine Board-Restriktion).
			return True
		board = Board.objects.filter(id=board_id).first()		# Versucht, das Board-Objekt zu laden.
		if board is None:										# Existiert das Board nicht, wird die Existenz an anderer Stelle geprueft; hier erlauben wir weiter.
			return True
		return is_board_owner_or_member(request.user, board)	# True nur wenn User Owner oder Member ist.


class IsTaskBoardMember(BasePermission):						# Objektbezogene Permission fuer Task- und zugehoerige Ressourcen.
	"""Allow access to task-scoped resources only for board owner/member."""	# Dokumentiert das Verhalten.

	message = "You must be a board owner or member to access this task."  # Fehlermeldung bei Verweigerung.

	def has_object_permission(self, request, view, obj):		# Prueft Berechtigungen gegen ein konkretes Task/Comment-Objekt.
		task = getattr(obj, "task", obj)						# Falls obj ein Comment ist, hole das zugehoerige Task, sonst nutze obj direkt.
		board = getattr(task, "board", None)					# Bestimme das zugehoerige Board (kann None sein).
		if board is None:										# Falls kein Board gesetzt ist, verweigere Zugriff (kontextspezifisch).
			return False
		return is_board_owner_or_member(request.user, board)	# True nur wenn User Owner oder Member ist.


class IsTaskCreatorOrBoardOwnerCanDelete(BasePermission):		# Permission, die loeschen einschränkt.
	"""Allow deleting a task only for task creator or board owner."""	# Dokumentiert das Verhalten.

	message = "Only the task creator or board owner can delete this task."  # Fehlermeldung bei Verweigerung.

	def has_object_permission(self, request, view, obj):		# Prueft objektbezogene Delete-Rechte.
		if request.user.is_superuser:							# Superuser darf Tasks immer loeschen.
			return True
		if request.method != "DELETE":							# Nur fuer DELETE-Anfragen relevant.
			return True											# Andere Methoden nicht betroffen.
		board_owner_id = obj.board.owner_id if obj.board else None	# Bestimme Board-Owner-ID falls vorhanden.
		return request.user.id in {obj.created_by_id, board_owner_id}	# True nur fuer Task-Ersteller oder Board-Owner.


class IsCommentAuthor(BasePermission):							# Permission, die das Loeschen von Kommentaren auf den Autor beschraenkt.
	"""Allow deleting comments only for their author."""		# Dokumentiert das Verhalten.

	message = "Only the comment author can delete this comment."  # Fehlermeldung bei Verweigerung.

	def has_object_permission(self, request, view, obj):		# Prueft objektbezogene Rechte fuer Kommentare.
		if request.user.is_superuser:							# Superuser darf Kommentare immer loeschen.
			return True
		if request.method != "DELETE":							# Nur fuer DELETE-Anfragen relevant.
			return True											# Andere Methoden sind nicht betroffen.
		return obj.author_id == request.user.id					# True nur, wenn der Request-User der Autor des Kommentars ist.

