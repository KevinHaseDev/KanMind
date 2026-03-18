# ORM-based migration to rename M2M field 'assignies' -> 'assignees'
from django.conf import settings
from django.db import migrations, models


def _copy_assignies_to_assignees(apps, schema_editor):
    Task = apps.get_model('task_app', 'Task')
    # Resolve user model from settings.AUTH_USER_MODEL (e.g. 'auth_app.CustomUser')
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(user_app_label, user_model_name)

    # Iterate tasks and copy relations from old manager to new manager
    for task in Task.objects.all():
        try:
            old_qs = getattr(task, 'assignies').all()
        except Exception:
            # Old relation may not exist in some historical states; skip safely
            continue
        if old_qs.exists():
            new_mgr = getattr(task, 'assignees')
            new_mgr.set(list(old_qs))


def _copy_assignees_to_assignies(apps, schema_editor):
    Task = apps.get_model('task_app', 'Task')
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(user_app_label, user_model_name)

    for task in Task.objects.all():
        try:
            new_qs = getattr(task, 'assignees').all()
        except Exception:
            continue
        if new_qs.exists():
            old_mgr = getattr(task, 'assignies')
            old_mgr.set(list(new_qs))


class Migration(migrations.Migration):

    dependencies = [
        ('task_app', '0004_task_created_by'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1) Add the new field (creates the new M2M table)
        migrations.AddField(
            model_name='task',
            name='assignees',
            field=models.ManyToManyField(related_name='tasks', to=settings.AUTH_USER_MODEL),
        ),

        # 2) Copy existing relations from old M2M field to new one using ORM
        migrations.RunPython(_copy_assignies_to_assignees, reverse_code=_copy_assignees_to_assignies),

        # 3) Remove old field (drops the old M2M table)
        migrations.RemoveField(
            model_name='task',
            name='assignies',
        ),
    ]
