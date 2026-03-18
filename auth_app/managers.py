from django.contrib.auth.base_user import BaseUserManager  # Importiert den Basis-Manager fuer Custom-User-Erstellung.


class CustomUserManager(BaseUserManager):  # Definiert einen Custom-Manager fuer E-Mail-basierte Benutzer.
    use_in_migrations = True  # Macht den Manager waehrend Migration-Serialisierung verfuegbar.

    def _create_user(self, email, password, **extra_fields):  # Interne Hilfsmethode fuer create_user und create_superuser.
        if not email:  # Prueft, ob die erforderliche E-Mail uebergeben wurde.
            raise ValueError("The Email field must be set")  # Bricht die Erstellung ohne E-Mail ab.

        email = self.normalize_email(email)  # Normalisiert das E-Mail-Format fuer konsistente Speicherung.
        user = self.model(email=email, **extra_fields)  # Erstellt eine noch nicht gespeicherte User-Instanz.
        user.set_password(password)  # Hasht das Rohpasswort sicher.
        user.save(using=self._db)  # Speichert den Benutzer in der konfigurierten Datenbank.
        return user  # Gibt die gespeicherte User-Instanz zurueck.

    def create_user(self, email, password=None, **extra_fields):  # Oeffentliche Methode fuer normale Benutzer.
        extra_fields.setdefault("is_staff", False)  # Stellt sicher, dass normale Benutzer standardmaessig kein Staff sind.
        extra_fields.setdefault("is_superuser", False)  # Stellt sicher, dass normale Benutzer keine Superuser sind.
        return self._create_user(email, password, **extra_fields)  # Delegiert die eigentliche Erstellung an die Hilfsmethode.

    def create_superuser(self, email, password=None, **extra_fields):  # Oeffentliche Methode fuer Admin-Benutzer.
        extra_fields.setdefault("is_staff", True)  # Erzwingt das Staff-Flag fuer Superuser.
        extra_fields.setdefault("is_superuser", True)  # Erzwingt das Superuser-Flag fuer Superuser.

        if extra_fields.get("is_staff") is not True:  # Validiert die Korrektheit des Staff-Flags.
            raise ValueError("Superuser must have is_staff=True.")  # Wirft Fehler, wenn das Staff-Flag falsch ist.
        if extra_fields.get("is_superuser") is not True:  # Validiert die Korrektheit des Superuser-Flags.
            raise ValueError("Superuser must have is_superuser=True.")  # Wirft Fehler, wenn das Superuser-Flag falsch ist.

        return self._create_user(email, password, **extra_fields)  # Delegiert die eigentliche Erstellung an die Hilfsmethode.
