from django.conf import settings                            # Importiert die User-Model-Setting des Projekts fuer sichere User-Relationen.
from django.db import models                                # Importiert Djangos Basis-Feldklassen fuer Modelle.


class Task(models.Model):                                   # Definiert das Datenbankmodell fuer einen Task.
    board = models.ForeignKey('board.Board', related_name='tasks', on_delete=models.CASCADE, null=True, blank=True)  # Verknuepft jeden Task mit einem Board und loescht Tasks beim Loeschen des Boards.
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_tasks', on_delete=models.SET_NULL, null=True, blank=True)  # Speichert den Ersteller und behaelt Task-Daten auch bei geloeschtem User.
    title = models.CharField(max_length=255)                # Speichert den kurzen Titel des Tasks.
    description = models.TextField()                        # Speichert die ausfuehrliche Task-Beschreibung.
    status = models.CharField(max_length=50)                # Speichert den Workflow-Status (z. B. to-do oder done).
    priority = models.CharField(max_length=50)              # Speichert die Prioritaetsstufe des Tasks.
    due_date = models.DateTimeField()                       # Speichert Datum und Uhrzeit der Faelligkeit.
    assignies = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='tasks')  # Speichert die dem Task zugewiesenen Benutzer.
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviewed_tasks', on_delete=models.CASCADE, null=True, blank=True)  # Speichert den optionalen Reviewer fuer diesen Task.


class Comment(models.Model):                                # Definiert das Datenbankmodell fuer einen Task-Kommentar.
    task = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)  # Verknuepft jeden Kommentar mit einem Task und loescht Kommentare mit dem Task.
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='task_comments', on_delete=models.CASCADE)  # Speichert, welcher Benutzer den Kommentar geschrieben hat.
    content = models.TextField()                            # Speichert den Inhalt des Kommentars.
    created_at = models.DateTimeField(auto_now_add=True)    # Speichert den Zeitstempel der Kommentarerstellung.