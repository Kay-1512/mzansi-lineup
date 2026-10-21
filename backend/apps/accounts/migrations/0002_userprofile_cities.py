from django.db import migrations, models

# Mirrors the choices the old `city` CharField used to have — hardcoded
# here (rather than imported) since migrations must not depend on the
# current state of models.py.
SLUG_TO_DISPLAY = {
    "johannesburg": "Johannesburg",
    "pretoria": "Pretoria",
    "cape_town": "Cape Town",
    "durban": "Durban",
}
DISPLAY_TO_SLUG = {v: k for k, v in SLUG_TO_DISPLAY.items()}


def migrate_city_to_cities(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    for profile in UserProfile.objects.exclude(city__isnull=True).exclude(city=""):
        display = SLUG_TO_DISPLAY.get(profile.city)
        profile.cities = [display] if display else []
        profile.save(update_fields=["cities"])


def reverse_cities_to_city(apps, schema_editor):
    UserProfile = apps.get_model("accounts", "UserProfile")
    for profile in UserProfile.objects.exclude(cities=[]):
        first = profile.cities[0] if profile.cities else None
        profile.city = DISPLAY_TO_SLUG.get(first)
        profile.save(update_fields=["city"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="cities",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(migrate_city_to_cities, reverse_cities_to_city),
        migrations.RemoveField(model_name="userprofile", name="city"),
    ]
