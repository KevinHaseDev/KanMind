from django.urls import path        # Importiert URL-Pfad-Helfer fuer Routendefinitionen.

from .views import (                # Importiert Task- und Comment-API-Views fuer die Routen.
    TaskAssignedToMeListView,       # Importiert die assigned-to-me-Listen-View.
    TaskCommentsListCreateView,     # Importiert die comments list/create View.
    TaskCommentDeleteView,          # Importiert die comment delete View.
    TaskCreateView,                 # Importiert die task create View.
    TaskDetailView,                 # Importiert die task detail patch/delete View.
    TaskReviewingListView,          # Importiert die reviewing Listen-View.
)


urlpatterns = [                     # Definiert URL-Patterns der Task-App.
    path("tasks/assigned-to-me/", TaskAssignedToMeListView.as_view(), name="tasks-assigned-to-me"),     # Ordnet den assigned-to-me-Endpunkt zu.
    path("tasks/reviewing/", TaskReviewingListView.as_view(), name="tasks-reviewing"),                  # Ordnet den reviewing-Endpunkt zu.
    path("tasks/", TaskCreateView.as_view(), name="tasks-create"),                                      # Ordnet den Task-Create-Endpunkt zu.
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="tasks-detail"),                        # Ordnet den Task-Patch/Delete-Endpunkt zu.
    path("tasks/<int:task_id>/comments/", TaskCommentsListCreateView.as_view(), name="task-comments"),  # Ordnet den Comment-List/Create-Endpunkt zu.
    path("tasks/<int:task_id>/comments/<int:comment_id>/", TaskCommentDeleteView.as_view(), name="task-comment-delete"),  # Ordnet den Comment-Delete-Endpunkt zu.
]
