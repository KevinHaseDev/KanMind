from django.urls import path

from .views import (
    TaskAssignedToMeListView,
    TaskDetailView,
    TaskCommentsListCreateView,
    TaskCommentDeleteView,
    TaskListCreateView,
    TaskReviewingListView,
)

urlpatterns = [
    path(
        'tasks/',
        TaskListCreateView.as_view(),
        name="tasks-list-create",
    ),
    path(
        'tasks/assigned-to-me/',
        TaskAssignedToMeListView.as_view(),
        name="tasks-assigned-to-me",
    ),
    path(
        'tasks/reviewing/',
        TaskReviewingListView.as_view(),
        name="tasks-reviewing",
    ),
    path(
        'tasks/<int:task_id>/',
        TaskDetailView.as_view(),
        name="tasks-detail",
    ),
    path('tasks/<int:task_id>/comments/', TaskCommentsListCreateView.as_view(), name="task-comments"),
    path(
        'tasks/<int:task_id>/comments/<int:comment_id>/',
        TaskCommentDeleteView.as_view(),
        name="task-comment-delete",
    ),
]
