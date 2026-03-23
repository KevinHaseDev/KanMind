from django.contrib import admin

from .models import Comment, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"title",
		"board",
		"status",
		"priority",
		"reviewer",
		"created_by",
		"due_date",
	)
	list_filter = ("status", "priority", "board")
	search_fields = ("title", "description")
	filter_horizontal = ("assignees",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ("id", "task", "author", "created_at")
	list_filter = ("created_at",)
	search_fields = ("content", "author__email", "author__fullname")
