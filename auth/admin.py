from django.contrib import admin  # Importiert die Django-Admin-Site-API.
from django.contrib.auth.admin import UserAdmin  # Importiert die Standard-Basisklasse fuer User-Admin.

from .models import CustomUser  # Importiert das Custom-User-Modell zur Registrierung im Admin.


@admin.register(CustomUser)  # Registriert das Custom-User-Modell mit dieser Admin-Klasse.
class CustomUserAdmin(UserAdmin):  # Passt die Admin-Oberflaeche fuer das Custom-User-Modell an.
	model = CustomUser  # Verknuepft die Admin-Klasse mit dem CustomUser-Modell.
	ordering = ("email",)  # Sortiert die Benutzerliste nach E-Mail.
	list_display = ("email", "fullname", "is_staff", "is_superuser")  # Definiert die Spalten in der Admin-Benutzerliste.
	search_fields = ("email", "fullname")  # Aktiviert die Suche nach E-Mail und Vollname.

	fieldsets = (  # Definiert die Felder im Benutzer-Bearbeitungsformular.
		(None, {"fields": ("email", "password")}),  # Zeigt die zentralen Login-Felder.
		("Personal info", {"fields": ("fullname", "first_name", "last_name")}),  # Zeigt persoenliche Profildaten.
		(  # Startet den Berechtigungsbereich.
			"Permissions",  # Beschriftet den Berechtigungsbereich.
			{"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},  # Zeigt Autorisierungsfelder.
		),
		("Important dates", {"fields": ("last_login", "date_joined")}),  # Zeigt Zeitstempel-Felder des Accounts.
	)
	add_fieldsets = (  # Definiert die Felder im Benutzer-Erstellungsformular im Admin.
		(  # Startet den Abschnitt fuer das Erstellungsformular.
			None,  # Nutzt den Standard-Abschnittstitel.
			{  # Startet das Dictionary mit Feldoptionen.
				"classes": ("wide",),  # Nutzt ein breites Layout im Admin-Erstellungsformular.
				"fields": ("email", "fullname", "password1", "password2", "is_staff", "is_superuser"),  # Zeigt die noetigen Felder zum Erstellen eines Benutzers.
			},
		),
	)
