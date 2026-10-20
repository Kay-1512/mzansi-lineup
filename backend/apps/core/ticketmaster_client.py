"""Thin wrapper around the Ticketmaster Discovery API.

Shared by the events fetcher (bulk event sync) and the catalog app's artist
autocomplete endpoint (attraction search), so the base URL, auth and
pagination-unwrapping logic live in exactly one place.
"""

import requests
from django.conf import settings

BASE_URL = "https://app.ticketmaster.com/discovery/v2"
DEFAULT_TIMEOUT = 10


class TicketmasterError(Exception):
    pass


class TicketmasterClient:
    def __init__(self, api_key=None, timeout=DEFAULT_TIMEOUT):
        self.api_key = api_key if api_key is not None else settings.TICKETMASTER_API_KEY
        self.timeout = timeout

    def _get(self, path, params):
        if not self.api_key:
            raise TicketmasterError("TICKETMASTER_API_KEY is not configured.")
        query = {**params, "apikey": self.api_key}
        response = requests.get(f"{BASE_URL}{path}", params=query, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def search_events(self, country_code="ZA", segment_name="Music", size=200, page=0):
        """One page of SA music events. Caller loops `page` until `_embedded` is empty."""
        data = self._get(
            "/events.json",
            {
                "countryCode": country_code,
                "segmentName": segment_name,
                "size": size,
                "page": page,
            },
        )
        return data.get("_embedded", {}).get("events", [])

    def search_attractions(self, keyword, size=10):
        """Artist/attraction name suggestions for the watchlist autocomplete box."""
        data = self._get("/attractions.json", {"keyword": keyword, "size": size})
        return data.get("_embedded", {}).get("attractions", [])
