"""Thin wrapper around the Quicket API.

Verified against https://docs.quicket.com (2026-10-20) — base URL, the
query-string auth scheme, the `/events` list endpoint, its params and the
response envelope below all match the real docs, not a guess.

One genuine ambiguity remains: an event's `locality` object has
`levelOne`/`levelTwo`/`levelThree` string fields with no further
documentation on what each represents. `levelThree` is used as the city in
`QuicketFetcher.normalise()` (apps/events/fetchers/quicket.py) on the most
plausible reading of a country > province > city hierarchy for South
Africa — if real responses show otherwise, fix it there.
"""

import requests
from django.conf import settings

BASE_URL = "https://api.quicket.co.za/api"
DEFAULT_TIMEOUT = 10


class QuicketError(Exception):
    pass


class QuicketClient:
    def __init__(self, api_key=None, timeout=DEFAULT_TIMEOUT):
        self.api_key = api_key if api_key is not None else settings.QUICKET_API_KEY
        self.timeout = timeout

    def _get(self, path, params):
        if not self.api_key:
            raise QuicketError("QUICKET_API_KEY is not configured.")
        # The API key goes in the query string, not a header.
        query = {**params, "api_key": self.api_key}
        response = requests.get(f"{BASE_URL}{path}", params=query, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def list_events(self, page=1, page_size=100):
        """One page of the full events envelope ({"results": [...], "pages": N, ...}).
        Quicket is a South-Africa-only platform — there's no country filter
        to pass, unlike Ticketmaster."""
        return self._get("/events", {"page": page, "pageSize": page_size})
