from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    # An empty list means "Anywhere in SA" — no city filter applied.
    # Stores canonical display names (settings.SOUTH_AFRICAN_CITIES) — the
    # same format Event.city is normalised to by apps.catalog.models'
    # CityAlias — so filtering never needs a slug<->display translation.
    cities = models.JSONField(default=list, blank=True)
    international_acts = models.BooleanField(default=False)
    onboarding_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile<{self.user.username}>"
