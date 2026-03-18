from django.urls import path
from .views import BoardViewSet, EmailCheckView

urlpatterns = [
    path("boards/", BoardViewSet.as_view({"get": "list", "post": "create"}), name="board-list-create",),
    path("boards/<int:board_id>/", BoardViewSet.as_view({"get": "retrieve", "patch": "partial_update", "put": "update", "delete": "destroy"}), name="board-detail",),
    path("boards/email-check/", EmailCheckView.as_view(), name="board-email-check"),
]
