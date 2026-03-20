from django.urls import path
from .views import BoardDetailView, BoardListCreateView, EmailCheckView

urlpatterns = [
    path('', BoardListCreateView.as_view(), name="boards_list_create"),
    path('<int:board_id>/', BoardDetailView.as_view(), name="boards_detail"),
    path('email-check/', EmailCheckView.as_view(), name="boards_email_check"),
]
