"""UNVERIFIED — see apps/core/quicket_client.py for why, and what to fix
once you have a real API key and the actual docs in front of you. The
assumed response shape is documented (and pinned down) by
apps/events/tests/test_quicket_fetcher.py's QUICKET_RAW_EVENT fixture.
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
            batch = self.client.search_events(page=page)
            if not batch:
                break
            items.extend(batch)
            page += 1
        return items

    def normalise(self, raw_item):
        try:
            start_str = raw_item["start_date"]
            if not start_str:
                return None
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))

            venue = raw_item.get("venue", {})
            images = raw_item.get("images", [])

            return NormalisedEvent(
                external_id=str(raw_item["id"]),
                title=raw_item.get("title", ""),
                description=raw_item.get("description") or "",
                artists=raw_item.get("performers", []),
                venue=venue.get("name", ""),
                city=venue.get("city", ""),
                start=start,
                end=None,
                image_url=images[0] if images else "",
                # Same limitation as the Ticketmaster fetcher — no reliable
                # nationality signal from the API, defaults to False.
                is_international=False,
                ticket_url=raw_item.get("url", ""),
            )
        except (KeyError, IndexError, ValueError, TypeError):
            return None
