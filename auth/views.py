from rest_framework import status  # Importiert standardisierte HTTP-Statuskonstanten.
from rest_framework.response import Response  # Importiert das Response-Objekt von DRF.
from rest_framework.views import APIView  # Importiert die Basisklasse fuer API-Endpunkte.
from rest_framework.authtoken.models import Token  # Importiert das Token-Modell fuer Auth-Tokens.

from .serializers import LoginSerializer, RegistrationSerializer  # Importiert Serializer fuer Login und Registrierung.


class RegistrationView(APIView):  # Behandelt den Endpunkt fuer Benutzerregistrierung.
	permission_classes = []  # Erlaubt oeffentlichen Zugriff ohne Authentifizierung.
	authentication_classes = []  # Deaktiviert Authentifizierungspflicht fuer diesen Endpunkt.

	def post(self, request):  # Behandelt POST-Anfragen fuer die Registrierung.
		serializer = RegistrationSerializer(data=request.data)  # Validiert die eingehenden Registrierungsdaten.
		if not serializer.is_valid():  # Prueft, ob die Validierung fehlgeschlagen ist.
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Gibt Validierungsfehler mit Status 400 zurueck.

		user = serializer.save()  # Erstellt den Benutzer in der Datenbank.
		token, _ = Token.objects.get_or_create(user=user)  # Erstellt oder holt ein Token fuer den neuen Benutzer.

		response_data = {  # Baut die vom Frontend erwartete Antwortstruktur auf.
			"token": token.key,  # Enthaelt den Authentifizierungs-Token.
			"fullname": user.fullname,  # Enthaelt den vollstaendigen Namen des Benutzers.
			"email": user.email,  # Enthaelt die E-Mail des Benutzers.
			"user_id": user.id,  # Enthaelt die numerische Benutzer-ID.
		}
		return Response(response_data, status=status.HTTP_201_CREATED)  # Gibt eine erfolgreiche Erstellungsantwort zurueck.


class LoginView(APIView):  # Behandelt den Login-Endpunkt.
	permission_classes = []  # Erlaubt oeffentlichen Zugriff ohne Authentifizierung.
	authentication_classes = []  # Deaktiviert Authentifizierungspflicht fuer diesen Endpunkt.

	def post(self, request):  # Behandelt POST-Anfragen fuer den Login.
		serializer = LoginSerializer(data=request.data, context={"request": request})  # Validiert Login-Daten mit dem Serializer.
		if not serializer.is_valid():  # Prueft, ob die Zugangsdaten gueltig sind.
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Gibt Login-Fehler mit Status 400 zurueck.

		user = serializer.validated_data["user"]  # Liest den authentifizierten Benutzer aus den Serializer-Daten.

		token, _ = Token.objects.get_or_create(user=user)  # Erstellt oder holt ein Token fuer den authentifizierten Benutzer.
		response_data = {  # Baut die vom Frontend erwartete Antwortstruktur auf.
			"token": token.key,  # Enthaelt den Authentifizierungs-Token.
			"fullname": user.fullname,  # Enthaelt den vollstaendigen Namen des Benutzers.
			"email": user.email,  # Enthaelt die E-Mail des Benutzers.
			"user_id": user.id,  # Enthaelt die numerische Benutzer-ID.
		}
		return Response(response_data, status=status.HTTP_200_OK)  # Gibt eine erfolgreiche Login-Antwort zurueck.
