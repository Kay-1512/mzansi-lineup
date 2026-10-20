from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Source(models.Model):
    """A ticketing platform events can be fetched from (Ticketmaster, Quicket, Howler)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    # Flips off a source without deleting it (and the events/listings tied to it) —
    # used for Howler, which has no fetcher implementation yet.
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UserSource(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sources"
    )
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "source"], name="unique_user_source"
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.source.name}"


class Genre(models.Model):
    """Admin-managed. Users only ever see `name` — keyword matching is internal."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class GenreKeyword(models.Model):
    """A keyword matched (case-insensitively) against event title/description/artists."""

    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name="keywords")
    keyword = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["genre", "keyword"], name="unique_genre_keyword"
            )
        ]
        indexes = [models.Index(fields=["keyword"])]

    def __str__(self):
        return f"{self.genre.name}: {self.keyword}"


class UserGenre(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="genres"
    )
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "genre"], name="unique_user_genre")
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.genre.name}"


class CityAlias(models.Model):
    """Maps an as-fetched venue city string (e.g. "Sandton") to one of the
    app's four canonical cities, so events normalise to the same names the
    city filter and onboarding's city choices use. Looked up
    case-insensitively at event-ingestion time (see
    apps/events/fetchers/dedupe.py) — adding an alias here fixes future
    fetches (and cross-source de-dup matches) without a code change.
    """

    alias = models.CharField(max_length=100, unique=True)
    canonical_city = models.CharField(
        max_length=100, choices=[(c, c) for c in settings.SOUTH_AFRICAN_CITIES]
    )

    class Meta:
        ordering = ["alias"]
        verbose_name_plural = "city aliases"

    def __str__(self):
        return f"{self.alias} -> {self.canonical_city}"

    @classmethod
    def build_lookup_map(cls):
        """{alias lowercased: canonical city}, loaded once per fetch run
        rather than queried per event — see BaseFetcher.run()."""
        return dict(
            (alias.lower(), canonical)
            for alias, canonical in cls.objects.values_list("alias", "canonical_city")
        )


def normalize_city(raw_city, alias_map):
    """Resolve a raw venue-data city string to its canonical form via
    `alias_map` (from CityAlias.build_lookup_map()), falling back to the
    raw value (stripped) when there's no matching alias."""
    if not raw_city:
        return raw_city
    stripped = raw_city.strip()
    return alias_map.get(stripped.lower(), stripped)


class WatchedArtist(models.Model):
    """An artist a user follows. external_id is the Ticketmaster attraction ID, when known."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watched_artists",
    )
    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_user_watched_artist"
            )
        ]

    def __str__(self):
        return f"{self.user.username} watches {self.name}"
