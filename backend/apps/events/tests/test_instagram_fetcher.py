from datetime import datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from apps.catalog.models import WatchedInstagramPage
from apps.events.fetchers.instagram import fetch_instagram_posts
from apps.events.models import InstagramPost

User = get_user_model()

pytestmark = pytest.mark.django_db

FEED_URL = "https://rss.app/feeds/milkandcookies.xml"

PUBLISHED = (2026, 10, 20, 12, 0, 0, 0, 0, 0)  # struct_time-shaped tuple, UTC


def make_entry(guid, **overrides):
    entry = {
        "id": guid,
        "link": f"https://instagram.com/p/{guid}",
        "title": "New post",
        "summary": "Headlined by Olivia Dean",
        "published_parsed": PUBLISHED,
    }
    entry.update(overrides)
    return entry


class FakeParsed:
    def __init__(self, entries, bozo=False):
        self.entries = entries
        self.bozo = bozo

    def get(self, key, default=None):
        return getattr(self, key, default)


_watcher_count = 0


def watch(handle="milkandcookies", feed_url=FEED_URL):
    global _watcher_count
    _watcher_count += 1
    user = User.objects.create_user(
        username=f"watcher-{_watcher_count}", password="pw123456!"
    )
    WatchedInstagramPage.objects.create(user=user, handle=handle, feed_url=feed_url)
    return user


class TestFetchInstagramPosts:
    def test_creates_a_post_from_a_feed_entry(self):
        watch()
        entry = make_entry("abc123")

        with patch(
            "apps.events.fetchers.instagram.feedparser.parse",
            return_value=FakeParsed([entry]),
        ):
            created, updated, skipped = fetch_instagram_posts()

        assert (created, updated, skipped) == (1, 0, 0)
        post = InstagramPost.objects.get(guid="abc123")
        assert post.handle == "milkandcookies"
        assert post.caption == "Headlined by Olivia Dean"
        assert post.post_url == "https://instagram.com/p/abc123"
        assert post.posted_at == datetime(2026, 10, 20, 12, 0, tzinfo=dt_timezone.utc)

    def test_rerunning_updates_rather_than_duplicates(self):
        watch()
        entry = make_entry("abc123", summary="Updated caption")

        with patch(
            "apps.events.fetchers.instagram.feedparser.parse",
            return_value=FakeParsed([entry]),
        ):
            fetch_instagram_posts()
            created, updated, skipped = fetch_instagram_posts()

        assert (created, updated, skipped) == (0, 1, 0)
        assert InstagramPost.objects.count() == 1
        assert InstagramPost.objects.get().caption == "Updated caption"

    def test_fetches_each_distinct_feed_url_once_regardless_of_watcher_count(self):
        # Two users watching the same handle/feed shouldn't double-fetch it.
        watch(handle="milkandcookies")
        watch(handle="milkandcookies")
        entry = make_entry("abc123")

        with patch(
            "apps.events.fetchers.instagram.feedparser.parse",
            return_value=FakeParsed([entry]),
        ) as mock_parse:
            fetch_instagram_posts()

        assert mock_parse.call_count == 1

    def test_entry_with_no_guid_or_link_is_skipped_not_errored(self):
        watch()
        entry = {"title": "No id", "summary": "..."}

        with patch(
            "apps.events.fetchers.instagram.feedparser.parse",
            return_value=FakeParsed([entry]),
        ):
            created, updated, skipped = fetch_instagram_posts()

        assert (created, updated, skipped) == (0, 0, 1)

    def test_a_feed_that_fails_to_fetch_is_skipped_not_raised(self):
        watch()

        with patch(
            "apps.events.fetchers.instagram.feedparser.parse",
            side_effect=Exception("boom"),
        ):
            created, updated, skipped = fetch_instagram_posts()

        assert (created, updated, skipped) == (0, 0, 0)
        assert InstagramPost.objects.count() == 0
