import pytest
from django.utils import timezone
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def register_and_login(client, email="jo@example.com", password="correct-horse-1"):
    resp = client.post("/api/auth/register/", {"email": email, "password": password})
    assert resp.status_code == 201, resp.data

    resp = client.post("/api/auth/token/", {"username": email, "password": password})
    assert resp.status_code == 200, resp.data
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")


def test_full_onboarding_and_events_flow():
    client = APIClient()
    register_and_login(client)

    # Step 1: sources
    resp = client.put(
        "/api/onboarding/sources/", {"sources": ["ticketmaster"]}, format="json"
    )
    assert resp.status_code == 200
    assert resp.data["sources"] == ["ticketmaster"]

    # Step 2: genres + international toggle
    resp = client.put(
        "/api/onboarding/genres/",
        {"genres": ["amapiano", "jazz"], "international_acts": True},
        format="json",
    )
    assert resp.status_code == 200
    assert set(resp.data["genres"]) == {"amapiano", "jazz"}
    assert resp.data["international_acts"] is True

    # Step 3: watchlist
    resp = client.post("/api/artists/", {"name": "Tyla"}, format="json")
    assert resp.status_code == 201
    artist_id = resp.data["id"]

    # Step 4: cities + mark onboarding complete
    resp = client.patch(
        "/api/profile/",
        {"cities": ["Cape Town", "Durban"], "onboarding_complete": True},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["cities"] == ["Cape Town", "Durban"]
    assert resp.data["onboarding_complete"] is True
    assert resp.data["sources"] == [
        {"id": 1, "name": "Ticketmaster", "slug": "ticketmaster", "is_active": True}
    ]
    assert any(g["slug"] == "amapiano" for g in resp.data["genres"])
    assert resp.data["watched_artists"][0]["name"] == "Tyla"

    # Unwatch the artist, confirm it's gone from the profile view.
    resp = client.delete(f"/api/artists/{artist_id}/")
    assert resp.status_code == 204
    resp = client.get("/api/profile/")
    assert resp.data["watched_artists"] == []

    # No events exist yet — "for you" and manual events should both be empty.
    resp = client.get("/api/events/")
    assert resp.status_code == 200
    assert resp.data["results"] == []

    resp = client.post(
        "/api/manual-events/",
        {
            "title": "Friend's birthday set",
            "venue": "My house",
            "start": timezone.now().isoformat(),
        },
        format="json",
    )
    assert resp.status_code == 201
    resp = client.get("/api/manual-events/")
    assert len(resp.data) == 1


def test_save_and_hide_an_event():
    from apps.catalog.models import Source
    from apps.events.models import Event, HiddenEvent, SavedEvent

    client = APIClient()
    register_and_login(client, email="save-hide@example.com")

    event = Event.objects.create(
        title="Test Show",
        venue="Test Venue",
        city="Johannesburg",
        start=timezone.now() + timezone.timedelta(days=5),
        dedupe_key="test-show-key",
    )
    Source.objects.get(slug="ticketmaster")  # sanity: seed migration ran

    resp = client.post(f"/api/events/{event.id}/save/")
    assert resp.status_code == 204
    assert SavedEvent.objects.filter(event=event).exists()

    resp = client.post(f"/api/events/{event.id}/hide/")
    assert resp.status_code == 204
    assert HiddenEvent.objects.filter(event=event).exists()
    # Hiding should clear any existing save for the same event.
    assert not SavedEvent.objects.filter(event=event).exists()
