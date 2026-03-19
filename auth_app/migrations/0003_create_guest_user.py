from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_guest_user(apps, schema_editor):
    CustomUser = apps.get_model("auth_app", "CustomUser")

    guest_email = "kevin@kovacsi.de"
    guest_password = "asdasdasd"
    guest_fullname = "Guest User"

    if CustomUser.objects.filter(email=guest_email).exists():
        return

    guest_user = CustomUser(
        email=guest_email,
        fullname=guest_fullname,
        password=make_password(guest_password),
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    guest_user.save()


class Migration(migrations.Migration):

    dependencies = [
        ("auth_app", "0002_alter_customuser_options_alter_customuser_managers_and_more"),
    ]

    operations = [
        migrations.RunPython(create_guest_user, migrations.RunPython.noop),
    ]
