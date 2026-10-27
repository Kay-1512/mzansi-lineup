import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import WatchedInstagramPage

pytestmark = pytest.mark.django_db

User = get_user_model()


def authed_client(username="ig@example.com"):
    User.objects.create_user(username=username, password="pw123456!")
    client = APIClient()
    resp = client.post(
        "/api/auth/token/", {"username": username, "password": "pw123456!"}
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


class TestWatchedInstagramPageListCreateView:
    def test_creates_a_watched_page(self):
        resp = authed_client().post(
            "/api/instagram-pages/",
            {"handle": "@milkandcookies", "feed_url": "https://rss.app/feeds/mac.xml"},
        )

        assert resp.status_code == 201
        # Leading "@" is stripped so it matches handles as stored by the fetcher.
        assert resp.data["handle"] == "milkandcookies"
        assert WatchedInstagramPage.objects.count() == 1

    def test_lists_only_the_requesting_users_pages(self):
        client = authed_client("u1@example.com")
        other_client = authed_client("u2@example.com")
        client.post(
            "/api/instagram-pages/",
            {"handle": "mine", "feed_url": "https://rss.app/feeds/mine.xml"},
        )
        other_client.post(
            "/api/instagram-pages/",
            {"handle": "theirs", "feed_url": "https://rss.app/feeds/theirs.xml"},
        )

        resp = client.get("/api/instagram-pages/")

        assert [p["handle"] for p in resp.data] == ["mine"]


class TestWatchedInstagramPageDeleteView:
    def test_deletes_a_watched_page(self):
        client = authed_client()
        create_resp = client.post(
            "/api/instagram-pages/",
            {"handle": "milkandcookies", "feed_url": "https://rss.app/feeds/mac.xml"},
        )

        resp = client.delete(f"/api/instagram-pages/{create_resp.data['id']}/")

        assert resp.status_code == 204
        assert WatchedInstagramPage.objects.count() == 0
