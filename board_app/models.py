from django.conf import settings
from django.db import models

# Create your models here.

class Board(models.Model):
    title = models.CharField(max_length=255)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='boards')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='owned_boards', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "board"
        verbose_name_plural = "boards"
        ordering = ["title"]