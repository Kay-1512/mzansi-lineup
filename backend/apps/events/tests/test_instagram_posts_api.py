import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.catalog.models import WatchedInstagramPage
from apps.events.models import InstagramPost

pytestmark = pytest.mark.django_db

User = get_user_model()


def authed_client(username):
    User.objects.create_user(username=username, password="pw123456!")
    client = APIClient()
    resp = client.post(
        "/api/auth/token/", {"username": username, "password": "pw123456!"}
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client, User.objects.get(username=username)


def make_post(handle, guid):
    return InstagramPost.objects.create(
        handle=handle, feed_url="https://rss.app/feeds/x.xml", guid=guid
    )


class TestInstagramPostListView:
    def test_only_returns_posts_from_pages_the_user_watches(self):
        client, user = authed_client("watcher@example.com")
        WatchedInstagramPage.objects.create(
            user=user, handle="milkandcookies", feed_url="https://rss.app/feeds/mac.xml"
        )
        make_post("milkandcookies", "mac-1")
        make_post("someoneelse", "other-1")

        resp = client.get("/api/instagram-posts/")

        handles = [p["handle"] for p in resp.data["results"]]
        assert handles == ["milkandcookies"]

    def test_a_user_watching_nothing_gets_an_empty_list(self):
        client, _ = authed_client("nobody@example.com")
        make_post("milkandcookies", "mac-1")

        resp = client.get("/api/instagram-posts/")

        assert resp.data["results"] == []
