from datetime import datetime

from apps.core.ticketmaster_client import TicketmasterClient

from .base import BaseFetcher, NormalisedEvent

MAX_PAGES = 50  # safety cap so a bad response can't loop forever


class TicketmasterFetcher(BaseFetcher):
    source_slug = "ticketmaster"

    def __init__(self, client=None):
        self.client = client or TicketmasterClient()

    def fetch(self):
        items = []
        page = 0
        while page < MAX_PAGES:
            batch = self.client.search_events(page=page)
            if not batch:
                break
            items.extend(batch)
            page += 1
        return items

    def normalise(self, raw_item):
        try:
            start_str = raw_item["dates"]["start"].get("dateTime")
            if not start_str:
                # Ticketmaster sometimes only has a date with no confirmed
                # time yet ("localDate" only) — skip until it firms up.
                return None
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))

            venue_data = raw_item.get("_embedded", {}).get("venues", [{}])[0]
            venue = venue_data.get("name", "")
            city = venue_data.get("city", {}).get("name", "")

            attractions = raw_item.get("_embedded", {}).get("attractions", [])
            artists = [a["name"] for a in attractions if a.get("name")]

            images = raw_item.get("images", [])
            image_url = images[0]["url"] if images else ""

            return NormalisedEvent(
                external_id=raw_item["id"],
                title=raw_item.get("name", ""),
                description=raw_item.get("info") or raw_item.get("pleaseNote") or "",
                artists=artists,
                venue=venue,
                city=city,
                start=start,
                end=None,
                image_url=image_url,
                # Ticketmaster doesn't expose attraction nationality, so we
                # can't reliably detect "international act" here yet —
                # defaults to False; admins can correct it per event.
                is_international=False,
                ticket_url=raw_item.get("url", ""),
            )
        except (KeyError, IndexError, ValueError, TypeError):
            return None
