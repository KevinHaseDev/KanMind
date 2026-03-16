from django.urls import path

from .views import (
    TaskAssignedToMeListView,
    TaskCommentsListCreateView,
    TaskCommentDeleteView,
    TaskCreateView,
    TaskDetailView,
    TaskReviewingListView,
)


urlpatterns = [
    path("tasks/assigned-to-me/", TaskAssignedToMeListView.as_view(), name="tasks-assigned-to-me"),
    path("tasks/reviewing/", TaskReviewingListView.as_view(), name="tasks-reviewing"),
    path("tasks/", TaskCreateView.as_view(), name="tasks-create"),
    path("tasks/<int:task_id>/", TaskDetailView.as_view(), name="tasks-detail"),
    path("tasks/<int:task_id>/comments/", TaskCommentsListCreateView.as_view(), name="task-comments"),
    path("tasks/<int:task_id>/comments/<int:comment_id>/", TaskCommentDeleteView.as_view(), name="task-comment-delete"),
]
