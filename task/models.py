from django.conf import settings
from django.db import models

# Create your models here.

class Task(models.Model):
    board = models.ForeignKey('board.Board', related_name='tasks', on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=50)
    due_date = models.DateTimeField()
    assignies = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='tasks')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviewed_tasks', on_delete=models.CASCADE)