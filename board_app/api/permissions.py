from rest_framework import permissions                            # Importiert die Basisklassen und Konstanten fuer Permissions.


class IsBoardOwnerOrReadOnly(permissions.BasePermission):        # Objektbezogene Permission fuer Board-Zugriffsbeschraenkungen.
	"""Allow read/patch for board owner or member; allow delete only for owner."""   # Beschreibt das Verhalten dieser Permission.

	message = "Only the board owner can modify this board."    # Fehlermeldung bei Verweigerung.

	def has_object_permission(self, request, view, obj):        # Prüft Berechtigungen für ein konkretes Board-Objekt.
		if request.user.is_superuser:                             # Superuser darf unabhaengig von Owner/Mitgliedschaft zugreifen.
			return True
		if request.method in permissions.SAFE_METHODS or request.method == "PATCH":  # Erlaubt Lesen (SAFE_METHODS) und PATCH für Owner oder Mitglieder des Boards.
			return obj.owner_id == request.user.id or obj.members.filter(id=request.user.id).exists()    # True wenn Owner oder Mitglied.
		return obj.owner_id == request.user.id                    # True nur wenn Request-User Owner ist. Für alle anderen Methoden (z.B. DELETE) nur Owner erlaubt.

