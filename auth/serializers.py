from django.contrib.auth import get_user_model  # Importiert Hilfsfunktion, um das aktive User-Modell aufzulösen.
from django.contrib.auth import authenticate  # Importiert Djangos Authentifizierungsfunktion.
from rest_framework import serializers  # Importiert die Basis-Serializerklassen von DRF.


User = get_user_model()  # Ermittelt das konfigurierte Custom-User-Modell.


class RegistrationSerializer(serializers.ModelSerializer):  # Serializer für Registrierungsdaten und Validierung.
    repeated_password = serializers.CharField(write_only=True, min_length=8)  # Fügt ein zweites Passwortfeld zur Bestätigung hinzu.

    class Meta:  # Definiert Model-Bindung und Feldkonfiguration.
        model = User  # Verknüpft den Serializer mit dem User-Modell.
        fields = ["fullname", "email", "password", "repeated_password"]  # Stellt die Registrierungsfelder bereit.
        extra_kwargs = {  # Konfiguriert das Verhalten für sensible Felder.
            "password": {"write_only": True, "min_length": 8},  # Versteckt das Passwort in Antworten und erzwingt Mindestlaenge.
        }

    def validate_email(self, value):  # Prüft, ob die E-Mail noch verfügbar ist.
        if User.objects.filter(email=value).exists():  # Sucht nach einem bereits existierenden Account.
            raise serializers.ValidationError("Email is already registered.")  # Gibt einen Validierungsfehler bei Duplikaten zurück.
        return value  # Akzeptiert eine eindeutige E-Mail.

    def validate(self, attrs):  # Feldübergreifende Validierung für die Passwortbestätigung.
        if attrs["password"] != attrs["repeated_password"]:  # Vergleicht beide eingegebenen Passwörter.
            raise serializers.ValidationError({"repeated_password": "Passwords do not match."})  # Gibt Fehler bei Nicht-Übereinstimmung aus.
        return attrs  # Gibt validierte Eingabedaten zurück.

    def create(self, validated_data):  # Erstellt einen User mit sicher gehashtem Passwort.
        validated_data.pop("repeated_password")  # Entfernt das Hilfsfeld, das nicht im Modell gespeichert wird.
        user = User.objects.create_user(  # Ruft create_user des Managers auf, um Passwort zu hashen und User zu speichern.
            email=validated_data["email"],  # Setzt die Login-E-Mail des Users.
            password=validated_data["password"],  # Übergibt das Rohpasswort (wird im Manager gehasht).
            fullname=validated_data["fullname"],  # Setzt das Vollnamen-Feld.
        )
        return user  # Gibt die erstellte User-Instanz zurück.


class LoginSerializer(serializers.ModelSerializer):  # Serializer für Login-Payload und Credential-Validierung.
    email = serializers.EmailField()  # Nimmt eine E-Mail entgegen und validiert das Format.

    class Meta:  # Definiert Model-Bindung und Feldkonfiguration.
        model = User  # Verknüpft den Serializer mit dem User-Modell.
        fields = ["email", "password"]  # Stellt die Login-Felder bereit.
        extra_kwargs = {  # Konfiguriert den Umgang mit dem Passwortfeld.
            "password": {"write_only": True},  # Versteckt das Passwort in API-Antworten.
        }

    def validate(self, attrs):  # Authentifiziert die übergebenen Zugangsdaten.
        email = attrs.get("email")  # Liest die E-Mail aus der Anfrage.
        password = attrs.get("password")  # Liest das Passwort aus der Anfrage.

        user = authenticate(  # Versucht die Django-Authentifizierung mit den gelieferten Daten.
            request=self.context.get("request"),  # Gibt das Request-Objekt für Backend/Context weiter.
            email=email,  # Nutzt E-Mail als Login-Identifikator.
            password=password,  # Nutzt das Klartextpasswort zur Backend-Prüfung.
        )

        if user is None:  # Behandelt ungültige Login-Daten.
            raise serializers.ValidationError({"detail": "Invalid credentials."})  # Gibt einen Login-Fehler zurück.

        attrs["user"] = user  # Speichert den authentifizierten User fuer die View-Schicht.
        return attrs  # Gibt validierte Daten inklusive User zurück.
