from django.conf import settings
from django.db import models

from apps.catalog.models import Source


class Event(models.Model):
    """One real-world event, de-duplicated across every platform it's listed on.

    `dedupe_key` is a normalised title+date+venue slug (see
    fetchers/dedupe.py) used to match the same show seen on two platforms
    into a single row — the per-platform link lives on EventListing.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # List of artist/act names. Ticketmaster's "attractions" rarely cover
    # every support act, so genre keyword matching also searches title+description.
    artists = models.JSONField(default=list, blank=True)
    venue = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    image_url = models.URLField(blank=True)
    # Best-effort flag (see TicketmasterFetcher) — admins can correct it.
    is_international = models.BooleanField(default=False)
    dedupe_key = models.CharField(max_length=512, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start"]
        indexes = [
            models.Index(fields=["start"]),
            models.Index(fields=["city"]),
            models.Index(fields=["dedupe_key"]),
        ]

    def __str__(self):
        return f"{self.title} @ {self.venue} ({self.start:%Y-%m-%d})"


class EventListing(models.Model):
    """One platform's listing of an Event — an event can have several, one per source."""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="listings")
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=255)
    ticket_url = models.URLField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"], name="unique_source_external_id"
            )
        ]

    def __str__(self):
        return f"{self.event.title} on {self.source.name}"


class SavedEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_events"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "event"], name="unique_saved_event")
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.event.title}"


class HiddenEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hidden_events"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="hidden_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event"], name="unique_hidden_event"
            )
        ]

    def __str__(self):
        return f"{self.user.username} hid {self.event.title}"


class ManualEvent(models.Model):
    """A user's own event, not sourced from any platform."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="manual_events"
    )
    title = models.CharField(max_length=255)
    venue = models.CharField(max_length=255, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return f"{self.title} ({self.user.username})"
