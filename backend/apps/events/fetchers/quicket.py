"""Verified against https://docs.quicket.com (2026-10-20) — see
apps/core/quicket_client.py's module docstring for the one remaining
ambiguity (which `locality` level is the city).
"""

from datetime import datetime

from apps.core.quicket_client import QuicketClient

from .base import BaseFetcher, NormalisedEvent

MAX_PAGES = 50  # safety cap so a bad response can't loop forever


class QuicketFetcher(BaseFetcher):
    source_slug = "quicket"

    def __init__(self, client=None):
        self.client = client or QuicketClient()

    def fetch(self):
        items = []
        page = 1
        while page <= MAX_PAGES:
            data = self.client.list_events(page=page)
            batch = data.get("results", [])
            if not batch:
                break
            items.extend(batch)
            if page >= data.get("pages", page):
                break
            page += 1
        return items

    def normalise(self, raw_item):
        try:
            start_str = raw_item["startDate"]
            if not start_str:
                return None
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))

            end_str = raw_item.get("endDate")
            end = (
                datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                if end_str
                else None
            )

            venue = raw_item.get("venue") or {}
            locality = raw_item.get("locality") or {}

            return NormalisedEvent(
                external_id=str(raw_item["id"]),
                title=raw_item.get("name", ""),
                description=raw_item.get("description") or "",
                # Quicket's event object has no artist/performer field —
                # WatchedArtistStep already falls back to matching the
                # title when the artists list doesn't have a hit, so this
                # isn't a dead end for scoring.
                artists=[],
                venue=venue.get("name", ""),
                city=locality.get("levelThree", ""),
                start=start,
                end=end,
                image_url=raw_item.get("imageUrl") or "",
                # Same limitation as the Ticketmaster fetcher — no reliable
                # nationality signal from the API, defaults to False.
                is_international=False,
                ticket_url=raw_item.get("url", ""),
            )
        except (KeyError, IndexError, ValueError, TypeError):
            return None
