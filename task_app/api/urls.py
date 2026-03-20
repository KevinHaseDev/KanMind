from django.urls import path

from .views import (
    CommentListCreateView,
    TaskCommentsListCreateView,
    TaskAssignedToMeListView,
    TaskDetailView,
    TaskListCreateView,
    TaskReviewingListView,
    TaskCommentDeleteView,
)

urlpatterns = [
    path('', TaskListCreateView.as_view(), name="tasks-list-create"),
    path('assigned-to-me/', TaskAssignedToMeListView.as_view(), name="tasks-assigned-to-me"),
    path('reviewing/', TaskReviewingListView.as_view(), name="tasks-reviewing"),
    path('<int:task_id>/', TaskDetailView.as_view(), name="tasks-detail"),
    path('<int:task_id>/comments/', TaskCommentsListCreateView.as_view(), name="tasks-comments"),
    path('<int:task_id>/comments/<int:comment_id>/', TaskCommentDeleteView.as_view(), name="tasks-comment-delete"),
]
