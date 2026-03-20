"""Definiert die zentrale URL-Konfiguration des Projekts und bindet alle App-Routen ein."""  # Beschreibt den Zweck dieses URL-Moduls.
from django.contrib import admin  # Importiert die Admin-Site von Django.
from django.urls import include, path  # Importiert Funktionen fuer URL-Pfade und das Einbinden weiterer URL-Dateien.

urlpatterns = [  # Definiert alle zentralen URL-Eintraege des Projekts.
    path('admin/', admin.site.urls),  # Bindet den Django-Admin unter /admin/ ein.
    path('api/', include('auth_app.api.urls')),  # Bindet alle Auth-API-Endpunkte unter /api/ ein.
    path('api/', include('board_app.api.urls')),  # Bindet alle Board-API-Endpunkte unter /api/ ein.
    path('api/', include('task_app.api.urls')),  # Bindet alle Task-API-Endpunkte unter /api/ ein.
]  # Beendet die URL-Liste.
