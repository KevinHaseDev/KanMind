from django.contrib.auth import get_user_model  # Importiert Hilfsfunktion fuer den Zugriff auf das aktive User-Modell.
from rest_framework import serializers  # Importiert DRF-Serializerklassen und Validierungswerkzeuge.

from ..models import Comment, Task  # Importiert Task- und Comment-Modelle fuer diese Serializer.


User = get_user_model()  # Ermittelt das aktuell konfigurierte Custom-User-Modell.


class UserSummarySerializer(serializers.ModelSerializer):  # Serialisiert eine kompakte Benutzerdarstellung.
    class Meta:  # Definiert Model-Bindung und ausgegebene Felder.
        model = User  # Verwendet das aktive User-Modell.
        fields = ["id", "email", "fullname"]  # Gibt nur grundlegende Identitaetsfelder aus.


class TaskSerializer(serializers.ModelSerializer):  # Haupt-Serializer fuer Erstellen, Listen und Bearbeiten von Tasks.
    ALLOWED_STATUSES = {"to-do", "in-progress", "review", "done"}  # Definiert erlaubte Statuswerte.
    ALLOWED_PRIORITIES = {"low", "medium", "high"}  # Definiert erlaubte Prioritaetswerte.

    assignee = serializers.SerializerMethodField(read_only=True)  # Gibt das Assignee-Objekt in der Antwort aus.
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)  # Akzeptiert die Assignee-User-ID in Request-Daten.
    reviewer = UserSummarySerializer(read_only=True)  # Gibt verschachtelte Reviewer-Daten in Antworten aus.
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)  # Akzeptiert die Reviewer-User-ID in Request-Daten.
    due_date = serializers.DateTimeField(format="%Y-%m-%d", input_formats=["%Y-%m-%d", "iso-8601"])  # Formatiert due_date als Datum und akzeptiert Datum/ISO-Eingabe.
    comments_count = serializers.SerializerMethodField(read_only=True)  # Gibt die Anzahl der Kommentare fuer diesen Task aus.

    class Meta:  # Definiert Model-Zuordnung und erlaubte API-Felder.
        model = Task  # Verknuepft den Serializer mit dem Task-Modell.
        fields = [  # Listet alle Request-/Response-Felder fuer Tasks.
            "id",  # Gibt die Task-ID aus.
            "board",  # Gibt die Board-ID fuer Create/List aus.
            "title",  # Gibt den Task-Titel aus.
            "description",  # Gibt die Task-Beschreibung aus.
            "status",  # Gibt den Task-Status aus.
            "priority",  # Gibt die Task-Prioritaet aus.
            "assignee",  # Gibt verschachtelte Assignee-Daten aus.
            "assignee_id",  # Akzeptiert Assignee-ID in Schreibanfragen.
            "reviewer",  # Gibt verschachtelte Reviewer-Daten aus.
            "reviewer_id",  # Akzeptiert Reviewer-ID in Schreibanfragen.
            "due_date",  # Gibt das formatierte Faelligkeitsdatum aus.
            "comments_count",  # Gibt die Anzahl verknuepfter Kommentare aus.
        ]
        read_only_fields = ["id", "comments_count"]

    def get_assignee(self, obj):  # Berechnet das Assignee-Objekt fuer API-Antworten.
        request = self.context.get("request")  # Liest das Request-Objekt aus dem Serializer-Kontext, falls vorhanden.
        if request and request.user and request.user.is_authenticated:  # Prueft, ob ein authentifizierter aktueller Benutzer vorhanden ist.
            user = obj.assignees.filter(id=request.user.id).first()  # Bevorzugt den aktuellen Benutzer bei nutzerbezogenen Endpunkten.
            if user:  # Behandelt den Fall, dass der aktuelle Benutzer zugewiesen ist.
                return UserSummarySerializer(user).data  # Gibt die serialisierte User-Zusammenfassung zurueck.

        user = obj.assignees.order_by("id").first()  # Faellt fuer allgemeine Endpunkte auf den ersten zugewiesenen Benutzer zurueck.
        if not user:  # Behandelt Tasks ohne Assignees.
            return None  # Gibt null zurueck, wenn kein Assignee existiert.
        return UserSummarySerializer(user).data  # Gibt die serialisierten Assignee-Daten zurueck.

    def get_comments_count(self, obj):  # Berechnet die Gesamtanzahl der Kommentare fuer Task-Antworten.
        if hasattr(obj, "comments_count"):  # Nutzt den annotierten Wert wieder, wenn er bereits vorhanden ist.
            return obj.comments_count  # Gibt die vorab berechnete Kommentaranzahl zurueck.
        return obj.comments.count()  # Fragt sonst die Anzahl ueber die Datenbankbeziehung ab.

    def validate_status(self, value):  # Validiert erlaubte Statuswerte.
        if value not in self.ALLOWED_STATUSES:  # Lehnt nicht unterstuetzte Status ab.
            raise serializers.ValidationError("Status must be one of: to-do, in-progress, review, done.")  # Gibt einen lesbaren Validierungsfehler zurueck.
        return value  # Akzeptiert gueltigen Status.

    def validate_priority(self, value):  # Validiert erlaubte Prioritaetswerte.
        if value not in self.ALLOWED_PRIORITIES:  # Lehnt nicht unterstuetzte Prioritaeten ab.
            raise serializers.ValidationError("Priority must be one of: low, medium, high.")  # Gibt einen lesbaren Validierungsfehler zurueck.
        return value  # Akzeptiert gueltige Prioritaet.

    def validate_assignee_id(self, value):  # Validiert, dass die Assignee-User-ID existiert.
        if value is None:  # Erlaubt explizites null zum Entfernen des Assignees.
            return value  # Gibt null unveraendert zurueck.
        if not User.objects.filter(id=value).exists():  # Prueft die Existenz des Benutzers per ID.
            raise serializers.ValidationError("Invalid assignee user id.")  # Gibt Validierungsfehler bei fehlendem Benutzer aus.
        return value  # Akzeptiert existierende User-ID.

    def validate_reviewer_id(self, value):  # Validiert, dass die Reviewer-User-ID existiert.
        if value is None:  # Erlaubt explizites null zum Entfernen des Reviewers.
            return value  # Gibt null unveraendert zurueck.
        if not User.objects.filter(id=value).exists():  # Prueft die Existenz des Benutzers per ID.
            raise serializers.ValidationError("Invalid reviewer user id.")  # Gibt Validierungsfehler bei fehlendem Benutzer aus.
        return value  # Akzeptiert existierende User-ID.

    def validate(self, attrs):  # Fuehrt felduebergreifende Validierung nach Einzelpruefungen durch.
        board = attrs.get("board") or getattr(self.instance, "board", None)  # Ermittelt Board aus Payload oder bestehendem Task.
        assignee_id = attrs.get("assignee_id", serializers.empty)  # Liest optionale Assignee-ID aus der Payload.
        reviewer_id = attrs.get("reviewer_id", serializers.empty)  # Liest optionale Reviewer-ID aus der Payload.

        if board is not None and assignee_id not in (serializers.empty, None):  # Validiert nur, wenn Board existiert und Assignee angegeben ist.
            if not board.members.filter(id=assignee_id).exists():  # Stellt sicher, dass der Assignee Mitglied desselben Boards ist.
                raise serializers.ValidationError({"assignee_id": "Assignee must be a member of the board."})  # Gibt Fehler zur Board-Mitgliedschaft aus.

        if board is not None and reviewer_id not in (serializers.empty, None):  # Validiert nur, wenn Board existiert und Reviewer angegeben ist.
            if not board.members.filter(id=reviewer_id).exists():  # Stellt sicher, dass der Reviewer Mitglied desselben Boards ist.
                raise serializers.ValidationError({"reviewer_id": "Reviewer must be a member of the board."})  # Gibt Fehler zur Board-Mitgliedschaft aus.

        return attrs  # Gibt validierte Attribute zurueck, wenn alle Pruefungen bestanden sind.

    def create(self, validated_data):  # Erstellt einen neuen Task und setzt Assignee-/Reviewer-Relationen.
        assignee_id = validated_data.pop("assignee_id", None)  # Entfernt Assignee-ID aus den normalen Modellfeldern.
        reviewer_id = validated_data.pop("reviewer_id", None)  # Entfernt Reviewer-ID aus den normalen Modellfeldern.

        if reviewer_id is not None:  # Setzt Reviewer nur, wenn er angegeben ist.
            validated_data["reviewer_id"] = reviewer_id  # Fuegt Reviewer ueber FK-ID wieder hinzu.

        task = Task.objects.create(**validated_data)  # Erstellt die Task-Zeile in der Datenbank.

        if assignee_id is not None:  # Setzt Assignee-Relation nur, wenn sie angegeben ist.
            task.assignees.set([assignee_id])  # Ersetzt die Assignee-Menge durch genau eine User-ID.

        return task  # Gibt die erstellte Task-Instanz zurueck.

    def update(self, instance, validated_data):  # Aktualisiert einen bestehenden Task mit partieller/vollstaendiger Payload.
        assignee_id = validated_data.pop("assignee_id", serializers.empty)  # Liest optionale Assignee-Update-Eingabe.
        reviewer_id = validated_data.pop("reviewer_id", serializers.empty)  # Liest optionale Reviewer-Update-Eingabe.

        if reviewer_id is not serializers.empty:  # Aktualisiert Reviewer nur, wenn das Feld vorhanden ist.
            instance.reviewer_id = reviewer_id  # Setzt neue Reviewer-ID (oder null).

        for attr, value in validated_data.items():  # Iteriert ueber verbleibende Modellfelder.
            setattr(instance, attr, value)  # Wendet jedes Feld-Update auf die Modellinstanz an.

        instance.save()  # Speichert aktualisierte skalare Felder in der Datenbank.

        if assignee_id is not serializers.empty:  # Aktualisiert Assignee nur, wenn das Feld vorhanden ist.
            if assignee_id is None:  # Behandelt explizites Entfernen des Assignees.
                instance.assignees.clear()  # Entfernt alle zugewiesenen Benutzer.
            else:  # Behandelt das Ersetzen des Assignees.
                instance.assignees.set([assignee_id])  # Setzt genau eine Assignee-Relation.

        return instance  # Gibt die aktualisierte Task-Instanz zurueck.


class CommentSerializer(serializers.ModelSerializer):  # Serializer fuer Kommentar-Erstellung und interne Kommentar-Payloads.
    author = UserSummarySerializer(read_only=True)  # Gibt verschachtelte Author-Daten in diesem Serializer aus.

    class Meta:  # Definiert Model-Bindung und Felder fuer den Create-Serializer.
        model = Comment  # Verknuepft den Serializer mit dem Comment-Modell.
        fields = ["id", "content", "author", "created_at"]  # Gibt ID, Inhalt, Author und Zeitstempel aus.
        read_only_fields = ["id", "author", "created_at"]  # Verhindert clientseitige Aenderungen an generierten Feldern.


class CommentListSerializer(serializers.ModelSerializer):  # Serializer fuer Kommentarlisten und Post-Antworten.
    author = serializers.SerializerMethodField()  # Gibt den Author als Vollnamen-String aus.

    class Meta:  # Definiert die Ausgabestruktur des Listen-Serializers.
        model = Comment  # Verknuepft den Serializer mit dem Comment-Modell.
        fields = ["id", "created_at", "author", "content"]  # Gibt exakt die benoetigten Listenfelder zurueck.

    def get_author(self, obj):  # Wandelt das Author-Objekt in einen Anzeigestring um.
        return obj.author.fullname  # Gibt den vollstaendigen Author-Namen zurueck.


class TaskUpdateResponseSerializer(serializers.ModelSerializer):  # Serializer fuer erfolgreiche PATCH-Antworten.
    assignee = serializers.SerializerMethodField(read_only=True)  # Gibt die Assignee-Zusammenfassung in der Update-Antwort aus.
    reviewer = UserSummarySerializer(read_only=True)  # Gibt die Reviewer-Zusammenfassung in der Update-Antwort aus.
    due_date = serializers.DateTimeField(format="%Y-%m-%d")  # Formatiert due_date als einfachen Datumsstring.

    class Meta:  # Definiert die Struktur der Update-Antwort.
        model = Task  # Verknuepft den Serializer mit dem Task-Modell.
        fields = [  # Gibt exakt die fuer die Update-Antwort geforderten Felder zurueck.
            "id",  # Enthaelt die Task-ID.
            "title",  # Enthaelt den aktualisierten Titel.
            "description",  # Enthaelt die aktualisierte Beschreibung.
            "status",  # Enthaelt den aktualisierten Status.
            "priority",  # Enthaelt die aktualisierte Prioritaet.
            "assignee",  # Enthaelt die verschachtelte Assignee-Zusammenfassung.
            "reviewer",  # Enthaelt die verschachtelte Reviewer-Zusammenfassung.
            "due_date",  # Enthaelt das formatierte Faelligkeitsdatum.
        ]

    def get_assignee(self, obj):  # Berechnet das Assignee-Objekt fuer die Update-Antwort.
        user = obj.assignees.order_by("id").first()  # Liest den ersten zugewiesenen Benutzer fuer die Ausgabe.
        if not user:  # Behandelt den Fall ohne Assignee.
            return None  # Gibt null fuer Assignee zurueck.
        return UserSummarySerializer(user).data  # Gibt die serialisierte User-Zusammenfassung zurueck.
