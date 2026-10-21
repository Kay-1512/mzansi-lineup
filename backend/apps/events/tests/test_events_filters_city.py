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


def login_with_cities(cities, label="user"):
    user = User.objects.create_user(
        username=f"{label}@example.com", password="pw123456!"
    )
    WatchedArtist.objects.create(user=user, name="Tyla")
    user.profile.cities = cities
    user.profile.save()
    client = APIClient()
    resp = client.post(
        "/api/auth/token/",
        {"username": f"{label}@example.com", "password": "pw123456!"},
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


class TestCityFilterDefaultAndOverride:
    def test_no_city_param_defaults_to_the_profiles_single_city(self):
        client = login_with_cities(["Cape Town"], "single")
        make_event(city="Cape Town", venue="A")
        make_event(city="Johannesburg", venue="B")

        resp = client.get("/api/events/")

        assert resp.data["count"] == 1
        assert resp.data["results"][0]["city"] == "Cape Town"

    def test_no_city_param_defaults_to_every_one_of_several_profile_cities(self):
        client = login_with_cities(["Cape Town", "Durban"], "multi")
        make_event(city="Cape Town", venue="A")
        make_event(city="Durban", venue="B")
        make_event(city="Johannesburg", venue="C")

        resp = client.get("/api/events/")

        assert resp.data["count"] == 2
        assert {r["city"] for r in resp.data["results"]} == {"Cape Town", "Durban"}

    def test_empty_profile_cities_means_anywhere_in_sa(self):
        client = login_with_cities([], "anywhere")
        make_event(city="Cape Town", venue="A")
        make_event(city="Johannesburg", venue="B")

        resp = client.get("/api/events/")

        assert resp.data["count"] == 2

    def test_explicit_empty_city_param_overrides_profile_default_to_show_all(self):
        client = login_with_cities(["Cape Town"], "override-empty")
        make_event(city="Cape Town", venue="A")
        make_event(city="Johannesburg", venue="B")

        resp = client.get("/api/events/", {"city": ""})

        assert resp.data["count"] == 2

    def test_explicit_city_param_overrides_profile_default_to_another_city(self):
        client = login_with_cities(["Cape Town"], "override-one")
        make_event(city="Cape Town", venue="A")
        make_event(city="Johannesburg", venue="B")

        resp = client.get("/api/events/", {"city": "Johannesburg"})

        assert resp.data["count"] == 1
        assert resp.data["results"][0]["city"] == "Johannesburg"

    def test_explicit_comma_separated_cities_override_the_profile_default(self):
        client = login_with_cities(["Cape Town"], "override-multi")
        make_event(city="Cape Town", venue="A")
        make_event(city="Durban", venue="B")
        make_event(city="Pretoria", venue="C")

        resp = client.get("/api/events/", {"city": "Durban,Pretoria"})

        assert resp.data["count"] == 2
        assert {r["city"] for r in resp.data["results"]} == {"Durban", "Pretoria"}
