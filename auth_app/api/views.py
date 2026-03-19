from rest_framework import generics, status  					# Importiert DRF-Generic-Views und standardisierte HTTP-Statuskonstanten.
from rest_framework.response import Response  				# Importiert das Response-Objekt von DRF.
from rest_framework.authtoken.models import Token  			# Importiert das Token-Modell fuer Auth-Tokens.

from .permissions import PublicAuthPermission  				# Importiert oeffentliche Permission fuer Auth-Endpunkte.
from .serializers import LoginSerializer, RegistrationSerializer  # Importiert Serializer fuer Login und Registrierung.


def get_safe_fullname(user):
	fullname = " ".join((user.fullname or "").strip().split())
	if not fullname:
		local_part = (user.email or "User").split("@")[0] or "User"
		return f"{local_part} User"
	if len(fullname.split(" ")) < 2:
		return f"{fullname} User"
	return fullname


class RegistrationView(generics.CreateAPIView):
	permission_classes = [PublicAuthPermission]  # Erlaubt oeffentlichen Zugriff ohne Authentifizierung.
	authentication_classes = []  # Deaktiviert Authentifizierungspflicht fuer diesen Endpunkt.
	serializer_class = RegistrationSerializer  # Definiert den Serializer fuer CreateAPIView.

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		token, _ = Token.objects.get_or_create(user=user)

		response_data = {
			"token": token.key,
			"fullname": get_safe_fullname(user),
			"email": user.email,
			"user_id": user.id,
		}
		headers = self.get_success_headers(serializer.data)
		return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(generics.CreateAPIView):  						# Behandelt den Login-Endpunkt.
	permission_classes = [PublicAuthPermission]  			# Erlaubt oeffentlichen Zugriff ohne Authentifizierung.
	authentication_classes = []  							# Deaktiviert Authentifizierungspflicht fuer diesen Endpunkt.
	serializer_class = LoginSerializer                          # Definiert den Serializer fuer den Create-View.

	def create(self, request, *args, **kwargs):  							# Behandelt POST-Anfragen fuer den Login.
		serializer = self.get_serializer(data=request.data, context={"request": request})  # Validiert Login-Daten mit dem Serializer.
		if not serializer.is_valid():  						# Prueft, ob die Zugangsdaten gueltig sind.
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Gibt Login-Fehler mit Status 400 zurueck.

		user = serializer.validated_data["user"]  			# Liest den authentifizierten Benutzer aus den Serializer-Daten.

		token, _ = Token.objects.get_or_create(user=user)  	# Erstellt oder holt ein Token fuer den authentifizierten Benutzer.
		response_data = {  									# Baut die vom Frontend erwartete Antwortstruktur auf.
			"token": token.key,  							# Enthaelt den Authentifizierungs-Token.
			"fullname": get_safe_fullname(user),  					# Enthaelt den vollstaendigen Namen des Benutzers.
			"email": user.email,  							# Enthaelt die E-Mail des Benutzers.
			"user_id": user.id,  							# Enthaelt die numerische Benutzer-ID.
		}
		return Response(response_data, status=status.HTTP_200_OK)  # Gibt eine erfolgreiche Login-Antwort zurueck.
