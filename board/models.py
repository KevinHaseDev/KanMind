from django.db import models
from django.conf import settings

# Create your models here.

class Board(models.Model):
    title = models.CharField(max_length=255)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='boards')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_boards', on_delete=models.CASCADE)

# auth.User ist nur ein lückenfüller für meinen richtigen User.