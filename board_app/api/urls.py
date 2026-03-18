from django.urls import path  # Importiert URL-Pfad-Helfer fuer Routendefinitionen.

from .views import BoardDetailView, BoardListCreateView, EmailCheckView  # Importiert Board-API-Views fuer die Routen.


urlpatterns = [  # Definiert URL-Patterns der Board-App.
    path("boards/", BoardListCreateView.as_view(), name="board-list-create"),  # Ordnet den Endpunkt fuer Board-Liste/Erstellung zu.
    path("boards/<int:board_id>/", BoardDetailView.as_view(), name="board-detail"),  # Ordnet den Board-Detailendpunkt zu.
    path("email-check/", EmailCheckView.as_view(), name="email-check"),  # Ordnet den email-check-Endpunkt zu.
]
