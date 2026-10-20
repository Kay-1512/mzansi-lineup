from django.conf import settings
from django.db import models

SOUTH_AFRICAN_CITIES = [
    ("johannesburg", "Johannesburg"),
    ("pretoria", "Pretoria"),
    ("cape_town", "Cape Town"),
    ("durban", "Durban"),
]


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    # Blank/null city means "Anywhere in SA" — no city filter applied.
    city = models.CharField(
        max_length=20, choices=SOUTH_AFRICAN_CITIES, blank=True, null=True
    )
    international_acts = models.BooleanField(default=False)
    onboarding_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile<{self.user.username}>"
