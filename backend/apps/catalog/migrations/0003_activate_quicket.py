from django.db import migrations


def activate(apps, schema_editor):
    Source = apps.get_model("catalog", "Source")
    Source.objects.filter(slug="quicket").update(is_active=True)


def deactivate(apps, schema_editor):
    Source = apps.get_model("catalog", "Source")
    Source.objects.filter(slug="quicket").update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_seed_sources_and_genres")]

    operations = [migrations.RunPython(activate, deactivate)]
