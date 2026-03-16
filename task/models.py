from django.conf import settings
from django.db import models

# Create your models here.

class Task(models.Model):
    board = models.ForeignKey('board.Board', related_name='tasks', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_tasks', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=50)
    due_date = models.DateTimeField()
    assignies = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='tasks')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviewed_tasks', on_delete=models.CASCADE, null=True, blank=True)


class Comment(models.Model):
    task = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='task_comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)