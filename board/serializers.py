from django.contrib.auth import get_user_model  # Importiert Hilfsfunktion zum Ermitteln des aktiven User-Modells.
from rest_framework import serializers  # Importiert Serializer-Klassen von DRF.

from .models import Board  # Importiert das Board-Modell fuer Board-Serializer.
from task.models import Task  # Importiert das Task-Modell fuer Board-Detailantworten.


User = get_user_model()  # Ermittelt das konfigurierte Custom-User-Modell.


class BoardSerializer(serializers.ModelSerializer):  # Basis-Serializer fuer Board-Erstellung und -Update.
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)  # Akzeptiert Member-IDs in Requests.

    class Meta:  # Definiert Model-Zuordnung und Feldkonfiguration.
        model = Board  # Verknuepft den Serializer mit dem Board-Modell.
        fields = ["id", "title", "owner", "members"]  # Stellt Felder id, title, owner und members bereit.
        read_only_fields = ["id", "owner"]  # Verhindert manuelle Bearbeitung von id und owner.


class BoardListSerializer(serializers.ModelSerializer):  # Serializer fuer die Zusammenfassung im Board-Listenendpunkt.
    owner_id = serializers.IntegerField(read_only=True)  # Gibt die Owner-ID des Boards aus.
    member_count = serializers.IntegerField(read_only=True)  # Gibt die Anzahl aller Board-Mitglieder aus.
    ticket_count = serializers.IntegerField(read_only=True)  # Gibt die Anzahl aller Tasks auf dem Board aus.
    tasks_to_do_count = serializers.IntegerField(read_only=True)  # Gibt die Anzahl der Tasks im Status to-do aus.
    tasks_high_prio_count = serializers.IntegerField(read_only=True)  # Gibt die Anzahl der Tasks mit hoher Prioritaet aus.

    class Meta:  # Definiert Model-Zuordnung und Antwortfelder.
        model = Board  # Verknuepft den Serializer mit dem Board-Modell.
        fields = [  # Listet die Felder fuer Listen-/Create-Zusammenfassungsantworten.
            "id",  # Enthae lt die Board-ID.
            "title",  # Enthae lt den Board-Titel.
            "member_count",  # Enthae lt die Anzahl der Mitglieder.
            "ticket_count",  # Enthae lt die Anzahl der Tasks.
            "tasks_to_do_count",  # Enthae lt die Anzahl der to-do-Tasks.
            "tasks_high_prio_count",  # Enthae lt die Anzahl der High-Priority-Tasks.
            "owner_id",  # Enthae lt die Owner-ID.
        ]


class UserSummarySerializer(serializers.ModelSerializer):  # Wiederverwendbarer kompakter Serializer fuer verschachtelte User-Ausgabe.
    class Meta:  # Definiert Model-Bindung und Ausgabefelder.
        model = User  # Verknuepft den Serializer mit dem User-Modell.
        fields = ["id", "email", "fullname"]  # Stellt grundlegende Identitaetsfelder bereit.


class BoardTaskSerializer(serializers.ModelSerializer):  # Serializer fuer die verschachtelte Task-Liste im Board-Detail.
    assignee = serializers.SerializerMethodField()  # Berechnet ein verschachteltes Assignee-Objekt.
    reviewer = UserSummarySerializer(read_only=True)  # Gibt ein verschachteltes Reviewer-Objekt aus.
    due_date = serializers.SerializerMethodField()  # Formatiert due_date als Datumsstring.
    comments_count = serializers.SerializerMethodField()  # Gibt die Anzahl der Kommentare pro Task aus.

    class Meta:  # Definiert Model-Bindung und Ausgabefelder.
        model = Task  # Verknuepft den Serializer mit dem Task-Modell.
        fields = [  # Listet die verschachtelten Task-Felder fuer den Board-Detailendpunkt.
            "id",  # Enthae lt die Task-ID.
            "title",  # Enthae lt den Task-Titel.
            "description",  # Enthae lt die Task-Beschreibung.
            "status",  # Enthae lt den Task-Status.
            "priority",  # Enthae lt die Task-Prioritaet.
            "assignee",  # Enthae lt die verschachtelte Assignee-Zusammenfassung.
            "reviewer",  # Enthae lt die verschachtelte Reviewer-Zusammenfassung.
            "due_date",  # Enthae lt das Faelligkeitsdatum ohne Zeitanteil.
            "comments_count",  # Enthae lt die Kommentaranzahl.
        ]

    def get_assignee(self, obj):  # Berechnet die erste Assignee-Zusammenfassung fuer die Task-Ausgabe.
        user = obj.assignies.order_by("id").first()  # Liest den ersten zugewiesenen User nach ID-Sortierung.
        if not user:  # Behandelt den Fall ohne Assignee.
            return None  # Gibt null fuer Assignee zurueck.
        return UserSummarySerializer(user).data  # Gibt die serialisierte Assignee-Zusammenfassung zurueck.

    def get_due_date(self, obj):  # Formatiert due_date als YYYY-MM-DD.
        if obj.due_date is None:  # Behandelt fehlende due_date-Werte.
            return None  # Gibt null fuer due_date zurueck.
        return obj.due_date.date().isoformat()  # Gibt ISO-Datumsstring ohne Zeit zurueck.

    def get_comments_count(self, obj):  # Berechnet die Anzahl der Kommentare fuer den Task.
        return obj.comments.count()  # Gibt die Kommentaranzahl ueber den Related-Manager zurueck.


class BoardDetailSerializer(serializers.ModelSerializer):  # Serializer fuer den Board-Detailendpunkt.
    owner_id = serializers.IntegerField(read_only=True)  # Gibt die Owner-ID direkt aus.
    members = UserSummarySerializer(many=True, read_only=True)  # Gibt verschachtelte Member-Zusammenfassungen aus.
    tasks = BoardTaskSerializer(many=True, read_only=True)  # Gibt die verschachtelte Task-Liste aus.

    class Meta:  # Definiert Model-Bindung und Ausgabefelder.
        model = Board  # Verknuepft den Serializer mit dem Board-Modell.
        fields = ["id", "title", "owner_id", "members", "tasks"]  # Gibt die vollstaendige Board-Detailstruktur zurueck.


class BoardUpdateResponseSerializer(serializers.ModelSerializer):  # Serializer fuer die Antwortstruktur bei Board-PATCH.
    owner_data = UserSummarySerializer(source="owner", read_only=True)  # Gibt die Owner-Zusammenfassung unter owner_data aus.
    members_data = UserSummarySerializer(source="members", many=True, read_only=True)  # Gibt Member-Zusammenfassungen unter members_data aus.

    class Meta:  # Definiert Model-Bindung und Ausgabefelder.
        model = Board  # Verknuepft den Serializer mit dem Board-Modell.
        fields = ["id", "title", "owner_data", "members_data"]  # Gibt die Antwortstruktur fuer Board-Updates zurueck.


class EmailCheckQuerySerializer(serializers.Serializer):  # Serializer zur Validierung der Query-Parameter fuer email-check.
    email = serializers.EmailField(required=True)  # Erfordert einen gueltigen E-Mail-Query-Parameter.
