"""Polls RSS feeds for watched Instagram pages. Instagram's own API won't
grant access to a page you don't own, so each feed_url here comes from a
third-party Instagram-to-RSS proxy the user points at the page themselves
(e.g. rss.app, Bazaar) — see WatchedInstagramPage. This deliberately doesn't
use BaseFetcher: that class's run() is built around Event's dedupe/upsert
(title+date+venue matching across sources), which doesn't apply to a post
that has no venue or confirmed date, just a caption and a timestamp.
"""

import calendar
import logging
from datetime import datetime, timezone

import feedparser

from apps.catalog.models import WatchedInstagramPage

from ..models import InstagramPost

logger = logging.getLogger(__name__)


def _entry_posted_at(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    # feedparser normalises these to UTC struct_time, so timegm (not
    # mktime, which assumes local time) is the correct way back to epoch.
    return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)


def _entry_image_url(entry):
    media = entry.get("media_content") or []
    if media and media[0].get("url"):
        return media[0]["url"]
    for link in entry.get("links") or []:
        if link.get("type", "").startswith("image") and link.get("href"):
            return link["href"]
    return ""


def fetch_instagram_posts():
    """Fetch every distinct watched feed once and upsert new posts into the
    shared InstagramPost table, keyed by handle rather than per-user — the
    same feed is fetched once even if several users watch that page.
    Returns (created, updated, skipped), matching the other fetchers'
    run() return shape.
    """
    feeds = WatchedInstagramPage.objects.values("handle", "feed_url").distinct()

    created = updated = skipped = 0
    for feed in feeds:
        handle, feed_url = feed["handle"], feed["feed_url"]
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:  # noqa: BLE001 - one bad feed shouldn't kill the rest
            logger.warning("Instagram feed fetch failed for @%s: %s", handle, exc)
            continue

        if not parsed.entries and parsed.get("bozo"):
            logger.warning(
                "Instagram feed for @%s returned no parsable entries: %s",
                handle,
                parsed.get("bozo_exception"),
            )
            continue

        for entry in parsed.entries:
            guid = entry.get("id") or entry.get("link")
            if not guid:
                skipped += 1
                continue

            _, was_created = InstagramPost.objects.update_or_create(
                guid=guid,
                defaults=dict(
                    handle=handle,
                    feed_url=feed_url,
                    caption=entry.get("summary", "") or entry.get("title", ""),
                    post_url=entry.get("link", ""),
                    image_url=_entry_image_url(entry),
                    posted_at=_entry_posted_at(entry),
                ),
            )
            created += int(was_created)
            updated += int(not was_created)

    return created, updated, skipped
