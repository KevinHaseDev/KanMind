from django.urls import path

from .views import (
    TaskViewSet,
    TaskCommentsListCreateView,
    TaskCommentDeleteView,
)

urlpatterns = [
    path(
        "tasks/",
        TaskViewSet.as_view({"get": "list", "post": "create"}),
        name="tasks-list-create",
    ),
    path(
        "tasks/assigned-to-me/",
        TaskViewSet.as_view({"get": "assigned_to_me"}),
        name="tasks-assigned-to-me",
    ),
    path(
        "tasks/reviewing/",
        TaskViewSet.as_view({"get": "reviewing"}),
        name="tasks-reviewing",
    ),
    path(
        "tasks/<int:task_id>/",
        TaskViewSet.as_view({"get": "retrieve", "patch": "partial_update", "put": "update", "delete": "destroy"}),
        name="tasks-detail",
    ),
    path("tasks/<int:task_id>/comments/", TaskCommentsListCreateView.as_view({"get": "list", "post": "create"}), name="task-comments"),
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        TaskCommentDeleteView.as_view({"delete": "destroy"}),
        name="task-comment-delete",
    ),
]
