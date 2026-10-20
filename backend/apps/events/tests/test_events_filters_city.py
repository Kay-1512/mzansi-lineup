from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.catalog.models import WatchedArtist
from apps.events.models import Event

pytestmark = pytest.mark.django_db

User = get_user_model()


def make_event(**kwargs):
    defaults = dict(
        title="Tyla Live",
        artists=["Tyla"],
        venue="Venue",
        city="Johannesburg",
        start=timezone.now() + timedelta(days=10),
    )
    defaults.update(kwargs)
    return Event.objects.create(
        dedupe_key=f"test-{kwargs.get('city', 'jhb')}-{kwargs.get('venue', 'v')}",
        **defaults,
    )


def login_with_city(city):
    user = User.objects.create_user(
        username=f"{city or 'none'}@example.com", password="pw123456!"
    )
    WatchedArtist.objects.create(user=user, name="Tyla")
    user.profile.city = city
    user.profile.save()
    client = APIClient()
    resp = client.post(
        "/api/auth/token/",
        {"username": f"{city or 'none'}@example.com", "password": "pw123456!"},
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


class TestCityFilterDefaultAndOverride:
    def test_no_city_param_defaults_to_profile_city(self):
        client = login_with_city("cape_town")
        make_event(city="Cape Town", venue="A")
        make_event(city="Johannesburg", venue="B")

        resp = client.get("/api/events/")

        assert resp.data["count"] == 1
        assert resp.data["results"][0]["city"] == "Cape Town"

    def test_explicit_empty_city_param_overrides_profile_default_to_show_all(self):
        client = login_with_city("cape_town")
        make_event(city="Cape Town", venue="A")
        make_event(city="Johannesburg", venue="B")

        resp = client.get("/api/events/", {"city": ""})

        assert resp.data["count"] == 2

    def test_explicit_city_param_overrides_profile_default_to_another_city(self):
        client = login_with_city("cape_town")
        make_event(city="Cape Town", venue="A")
        make_event(city="Johannesburg", venue="B")

        resp = client.get("/api/events/", {"city": "Johannesburg"})

        assert resp.data["count"] == 1
        assert resp.data["results"][0]["city"] == "Johannesburg"
