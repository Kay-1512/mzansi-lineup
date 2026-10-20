from django.db import migrations

# A starting set of well-known metro suburbs — expand via the admin as real
# fetched venue data reveals more mismatches. Each is uncontroversially part
# of its canonical city's metro area (not a nearby-but-separate town).
STARTER_ALIASES = {
    "Sandton": "Johannesburg",
    "Rosebank": "Johannesburg",
    "Midrand": "Johannesburg",
    "Soweto": "Johannesburg",
    "Centurion": "Pretoria",
    "Umhlanga": "Durban",
    "Durban North": "Durban",
    "Camps Bay": "Cape Town",
    "Sea Point": "Cape Town",
    "Claremont": "Cape Town",
}


def seed(apps, schema_editor):
    CityAlias = apps.get_model("catalog", "CityAlias")
    for alias, canonical_city in STARTER_ALIASES.items():
        CityAlias.objects.update_or_create(
            alias=alias, defaults={"canonical_city": canonical_city}
        )


def unseed(apps, schema_editor):
    CityAlias = apps.get_model("catalog", "CityAlias")
    CityAlias.objects.filter(alias__in=STARTER_ALIASES.keys()).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_cityalias")]

    operations = [migrations.RunPython(seed, unseed)]
