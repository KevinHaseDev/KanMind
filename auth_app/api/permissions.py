from rest_framework.permissions import AllowAny					# Importiert die erlaubnis-Klasse, die allen Zugriff zulaesst.


class PublicAuthPermission(AllowAny):							# Definiert eine explizite Permission-Klasse fuer oeffentliche Auth-Endpunkte.
	"""Explicit permission marker for public auth endpoints."""	# Dokumentiert den Zweck dieser Permission-Klasse.

