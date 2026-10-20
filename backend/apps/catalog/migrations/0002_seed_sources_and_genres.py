from django.db import migrations

# Keywords are intentionally broad and lowercase — matching is a simple
# case-insensitive substring check against title+description+artists
# (see apps/events/scoring/steps.py). Tune these in the admin as real
# listings reveal false positives/negatives.
GENRES = {
    "Amapiano": ["amapiano", "piano", "log drum", "private school"],
    "RnB": ["rnb", "r&b", "soul", "neo-soul", "neo soul"],
    "Hip-Hop": ["hip-hop", "hip hop", "rap", "trap"],
    "Gqom": ["gqom"],
    "Afro House": ["afro house", "afrohouse", "afro-house"],
    "Jazz": ["jazz"],
    "Gospel": ["gospel", "praise", "worship"],
}

SOURCES = [
    {"name": "Ticketmaster", "slug": "ticketmaster", "is_active": True},
    {"name": "Quicket", "slug": "quicket", "is_active": False},
    {"name": "Howler", "slug": "howler", "is_active": False},
]


def seed(apps, schema_editor):
    Source = apps.get_model("catalog", "Source")
    Genre = apps.get_model("catalog", "Genre")
    GenreKeyword = apps.get_model("catalog", "GenreKeyword")

    for source in SOURCES:
        Source.objects.update_or_create(
            slug=source["slug"],
            defaults={"name": source["name"], "is_active": source["is_active"]},
        )

    for genre_name, keywords in GENRES.items():
        genre, _ = Genre.objects.update_or_create(
            slug=genre_name.lower().replace(" ", "-"), defaults={"name": genre_name}
        )
        for keyword in keywords:
            GenreKeyword.objects.get_or_create(genre=genre, keyword=keyword)


def unseed(apps, schema_editor):
    Source = apps.get_model("catalog", "Source")
    Genre = apps.get_model("catalog", "Genre")
    Source.objects.filter(slug__in=[s["slug"] for s in SOURCES]).delete()
    Genre.objects.filter(name__in=GENRES.keys()).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
