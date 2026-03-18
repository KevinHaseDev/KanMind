from django.contrib.auth import get_user_model  # Importiert Hilfsfunktion zum Ermitteln des aktiven User-Modells.
from django.db.models import Count, Q  # Importiert Aggregation und OR-Query-Helferobjekte.
from rest_framework.authentication import TokenAuthentication  # Importiert Token-Authentifizierung fuer geschuetzte Endpunkte.
from rest_framework import generics, permissions, status  # Importiert DRF-Generic-Views, Permissions und Statuscodes.
from rest_framework.response import Response  # Importiert den DRF-Response-Wrapper.
from rest_framework.views import APIView  # Importiert die Basisklasse fuer benutzerdefinierte API-Endpunkte.

from .permissions import IsBoardOwnerOrReadOnly  # Importiert objektbezogene Board-Detail-Permission.
from .serializers import (  # Importiert Serializer, die in Board-API-Endpunkten verwendet werden.
	BoardDetailSerializer,  # Importiert Serializer fuer Board-Detailantworten.
	BoardListSerializer,  # Importiert Serializer fuer Listen-/Create-Zusammenfassungen.
	BoardSerializer,  # Importiert Basis-Board-Serializer fuer Eingaben.
	BoardUpdateResponseSerializer,  # Importiert Serializer fuer Board-Patch-Antworten.
	EmailCheckQuerySerializer,  # Importiert Serializer fuer email-check-Query-Validierung.
	UserSummarySerializer,  # Importiert verschachtelten User-Serializer fuer email-check-Erfolg.
)
from ..models import Board  # Importiert das Board-Modell fuer Board-Endpunkte.


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
			Board.objects.filter(Q(owner=user) | Q(members=user))  # Beinhaltet Boards, die der User besitzt oder denen er angehoert.
			.distinct()  # Entfernt Duplikate durch Many-to-many-Joins.
			.annotate(  # Fuegt berechnete Zaehler fuer die Listenantwort hinzu.
				member_count=Count("members", distinct=True),  # Zaehlt eindeutige Board-Mitglieder.
				ticket_count=Count("tasks", distinct=True),  # Zaehlt eindeutige Tasks am Board.
				tasks_to_do_count=Count("tasks", filter=Q(tasks__status__iexact="to-do"), distinct=True),  # Zaehlt Tasks mit Status to-do.
				tasks_high_prio_count=Count("tasks", filter=Q(tasks__priority__iexact="high"), distinct=True),  # Zaehlt Tasks mit hoher Prioritaet.
			)
		)

	def create(self, request, *args, **kwargs):  # Behandelt Board-Erstellung mit benutzerdefinierter Summary-Antwort.
		serializer = self.get_serializer(data=request.data)  # Validiert die eingehende Board-Payload.
		serializer.is_valid(raise_exception=True)  # Gibt bei ungueltiger Payload Status 400 aus.
		board = serializer.save(owner=request.user)  # Erstellt das Board mit aktuellem Benutzer als Owner.
		board.members.add(request.user)  # Stellt sicher, dass der Owner auch Board-Member ist.

		summary_board = (  # Laedt das Board mit annotierten Zaehlern fuer die Antwort neu.
			Board.objects.filter(pk=board.pk)  # Filtert auf das neu erstellte Board.
			.annotate(  # Fuegt die laut API-Vertrag erwarteten Summary-Zaehler hinzu.
				member_count=Count("members", distinct=True),  # Zaehlt Mitglieder.
				ticket_count=Count("tasks", distinct=True),  # Zaehlt Tasks.
				tasks_to_do_count=Count("tasks", filter=Q(tasks__status__iexact="to-do"), distinct=True),  # Zaehlt to-do-Tasks.
				tasks_high_prio_count=Count("tasks", filter=Q(tasks__priority__iexact="high"), distinct=True),  # Zaehlt High-Priority-Tasks.
			)
			.first()  # Gibt die annotierte Board-Instanz zurueck.
		)

		response_serializer = BoardListSerializer(summary_board)  # Serialisiert die Board-Summary-Payload.
		headers = self.get_success_headers(response_serializer.data)  # Baut Erfolgs-Header wie Location, falls verfuegbar.
		return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)  # Gibt die Summary-Antwort zur Erstellung zurueck.


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):  # Endpunkt fuer Board-GET/PATCH/DELETE per ID.
	queryset = Board.objects.select_related("owner").prefetch_related("members", "tasks", "tasks__assignies", "tasks__reviewer")  # Optimiert relationale Ladevorgaenge fuer Detailantworten.
	serializer_class = BoardSerializer  # Verwendet standardmaessig den Basis-Serializer.
	permission_classes = [permissions.IsAuthenticated, IsBoardOwnerOrReadOnly]  # Erzwingt Authentifizierung und objektbezogene Board-Permissions.
	lookup_url_kwarg = "board_id"  # Liest die Board-ID aus dem URL-Parameter board_id.

	def get_serializer_class(self):  # Waehlt den Serializer anhand der Methode.
		if self.request.method == "GET":  # Nutzt den Detail-Serializer fuer Retrieve.
			return BoardDetailSerializer  # Gibt den Board-Detail-Serializer zurueck.
		return BoardSerializer  # Nutzt den Basis-Serializer fuer Updates.

	def patch(self, request, *args, **kwargs):  # Behandelt partielle Board-Updates fuer Titel/Mitglieder.
		instance = self.get_object()  # Laedt das Board-Objekt inklusive Permission-Pruefungen.
		serializer = BoardSerializer(instance, data=request.data, partial=True)  # Validiert die partielle Update-Payload.
		serializer.is_valid(raise_exception=True)  # Gibt bei ungueltiger Payload Status 400 aus.
		board = serializer.save()  # Speichert aktualisierte Board-Felder.

		if "members" in serializer.validated_data:  # Wendet Member-Update nur an, wenn das Feld uebergeben wurde.
			board.members.set(serializer.validated_data["members"])  # Ersetzt die Member-Liste mit den uebergebenen IDs.
			board.members.add(board.owner)  # Fuegt den Owner erneut hinzu, damit er sicher Member bleibt.

		response_serializer = BoardUpdateResponseSerializer(board)  # Serialisiert das benutzerdefinierte Patch-Antwortformat.
		return Response(response_serializer.data, status=status.HTTP_200_OK)  # Gibt eine erfolgreiche Patch-Antwort zurueck.


class EmailCheckView(APIView):  # Endpunkt zum Pruefen, ob eine E-Mail zu einem bestehenden Benutzer gehoert.
	permission_classes = [permissions.IsAuthenticated]  # Erfordert einen authentifizierten Benutzer.
	authentication_classes = [TokenAuthentication]  # Verwendet Token-Authentifizierung fuer diesen Endpunkt.

	def get(self, request):  # Behandelt GET-Anfragen fuer email-check.
		query_serializer = EmailCheckQuerySerializer(data=request.query_params)  # Validiert die Query-Parameter.
		if not query_serializer.is_valid():  # Behandelt ungueltige oder fehlende E-Mail-Parameter.
			return Response(query_serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Gibt Validierungsfehler zurueck.

		email = query_serializer.validated_data["email"]  # Liest den validierten E-Mail-Wert.
		user = User.objects.filter(email=email).first()  # Sucht nach passendem Benutzer ueber E-Mail.
		if user is None:  # Behandelt den Fall ohne Treffer.
			return Response({"detail": "Email not found."}, status=status.HTTP_404_NOT_FOUND)  # Gibt 404 zurueck, wenn E-Mail unbekannt ist.

		return Response(UserSummarySerializer(user).data, status=status.HTTP_200_OK)  # Gibt die passende User-Zusammenfassung zurueck.
