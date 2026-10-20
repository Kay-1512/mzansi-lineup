from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import Source, UserSource, WatchedArtist
from apps.events.models import Event, EventListing

pytestmark = pytest.mark.django_db

User = get_user_model()


def make_event_with_listing(source_slug, **kwargs):
    defaults = dict(
        title="Tyla Live",
        artists=["Tyla"],
        venue="Venue",
        city="Cape Town",
        start=timezone.now() + timedelta(days=10),
    )
    defaults.update(kwargs)
    event = Event.objects.create(
        dedupe_key=f"test-{source_slug}-{kwargs.get('venue', 'v')}", **defaults
    )
    EventListing.objects.create(
        event=event,
        source=Source.objects.get(slug=source_slug),
        external_id=f"ext-{event.id}",
    )
    return event


def setup_user_matching_everything():
    user = User.objects.create_user(
        username="filters@example.com", password="pw123456!"
    )
    WatchedArtist.objects.create(user=user, name="Tyla")
    client = APIClient()
    resp = client.post(
        "/api/auth/token/", {"username": "filters@example.com", "password": "pw123456!"}
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return user, client


class TestSourceFilter:
    def test_narrows_to_the_requested_source_within_onboarding_selection(self):
        user, client = setup_user_matching_everything()
        UserSource.objects.create(
            user=user, source=Source.objects.get(slug="ticketmaster")
        )
        UserSource.objects.create(user=user, source=Source.objects.get(slug="quicket"))
        make_event_with_listing("ticketmaster", venue="TM Venue")
        make_event_with_listing("quicket", venue="QK Venue")

        resp = client.get("/api/events/", {"source": "quicket"})

        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["venue"] == "QK Venue"

    def test_requesting_a_source_outside_onboarding_selection_returns_nothing(self):
        user, client = setup_user_matching_everything()
        UserSource.objects.create(
            user=user, source=Source.objects.get(slug="ticketmaster")
        )
        make_event_with_listing("ticketmaster", venue="TM Venue")
        make_event_with_listing("quicket", venue="QK Venue")

        resp = client.get("/api/events/", {"source": "quicket"})

        assert resp.status_code == 200
        assert resp.data["count"] == 0

    def test_no_onboarding_sources_selected_shows_every_source_by_default(self):
        _, client = setup_user_matching_everything()
        make_event_with_listing("ticketmaster", venue="TM Venue")
        make_event_with_listing("quicket", venue="QK Venue")

        resp = client.get("/api/events/")

        assert resp.status_code == 200
        assert resp.data["count"] == 2
