from django.contrib.auth.models import AbstractUser         # Importiert Djangos erweiterbare Basis fuer Benutzer.
from django.db import models                                # Importiert Djangos Basis-Klassen fuer Modelle.

from .managers import CustomUserManager                     # Importiert den Custom-Manager fuer E-Mail-basierte User-Erstellung.


class CustomUser(AbstractUser):                             # Definiert das projektspezifische User-Modell.
    username = None                                         # Entfernt das Username-Feld, damit E-Mail als eindeutiger Login genutzt wird.
    fullname = models.CharField(max_length=255, blank=True) # Speichert den vollstaendigen Namen des Benutzers.
    email = models.EmailField("email address", unique=True) # Speichert die eindeutige E-Mail fuer die Authentifizierung.

    USERNAME_FIELD = 'email'                                # Konfiguriert E-Mail als primaeren Authentifizierungs-Identifikator.
    REQUIRED_FIELDS = []                                    # Entfernt zusaetzliche Pflichtfelder fuer createsuperuser neben E-Mail/Passwort.

    objects = CustomUserManager()                           # Verwendet den Custom-Manager fuer E-Mail-zentrierte User-Erstellung.

    def __str__(self):                                      # Definiert eine lesbare String-Darstellung des Benutzers.
        return self.email                                   # Gibt die Benutzer-E-Mail in Admin/Logs aus.

    class Meta:                                             # Definiert Metadaten fuer dieses Modell.
        verbose_name = "custom user"                        # Setzt die einzelne Anzeigenbezeichnung im Admin.
        verbose_name_plural = "custom users"                # Setzt die pluralisierte Anzeigenbezeichnung im Admin.
        ordering = ["email"]                                # Standard-Ordering nach E-Mail.