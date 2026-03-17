from django.urls import path  # Importiert URL-Pfad-Helfer fuer Routendefinitionen.

from .views import LoginView, RegistrationView  # Importiert Auth-API-Views fuer die Routen.


urlpatterns = [  # Definiert URL-Patterns der Auth-App.
    path("registration/", RegistrationView.as_view(), name="registration"),  # Ordnet den Registrierungsendpunkt zu.
    path("login/", LoginView.as_view(), name="login"),  # Ordnet den Login-Endpunkt zu.
]
