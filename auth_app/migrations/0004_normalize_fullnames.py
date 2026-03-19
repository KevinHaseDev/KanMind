from django.db import migrations


def normalize_fullnames(apps, schema_editor):
    CustomUser = apps.get_model("auth_app", "CustomUser")

    for user in CustomUser.objects.all():
        fullname = " ".join((user.fullname or "").strip().split())
        if not fullname:
            local_part = (user.email or "User").split("@")[0] or "User"
            user.fullname = f"{local_part} User"
            user.save(update_fields=["fullname"])
            continue

        if len(fullname.split(" ")) < 2:
            user.fullname = f"{fullname} User"
            user.save(update_fields=["fullname"])


class Migration(migrations.Migration):

    dependencies = [
        ("auth_app", "0003_create_guest_user"),
    ]

    operations = [
        migrations.RunPython(normalize_fullnames, migrations.RunPython.noop),
    ]
