"""Thin wrapper around the Quicket API.

UNVERIFIED — docs.quicket.com is a JS-rendered site that couldn't be read
during development, so the base URL, auth header and events-endpoint shape
below are a best-effort guess based on common REST/3scale-managed-API
conventions (Quicket's developer portal confirms it's 3scale-managed), not a
confirmed contract. Before relying on this in production:

1. Get an API key at https://developer.quicket.co.za
2. Read the real docs at https://docs.quicket.com and fix, in this file:
   - `BASE_URL` (currently guessed)
   - the auth scheme in `_get()` (currently a Bearer header — 3scale APIs
     often use an `api_key` query param or an app id/key pair instead)
   - the `/events` path, its query params, and the response envelope
3. Update `QuicketFetcher.normalise()` in
   `apps/events/fetchers/quicket.py` to match the real field names, and
   update `apps/events/tests/test_quicket_fetcher.py`'s fixture to match —
   the test suite documents the assumed shape, so keep it in sync.
"""

import requests
from django.conf import settings

DEFAULT_TIMEOUT = 10


class QuicketError(Exception):
    pass


class QuicketClient:
    def __init__(self, api_key=None, base_url=None, timeout=DEFAULT_TIMEOUT):
        self.api_key = api_key if api_key is not None else settings.QUICKET_API_KEY
        self.base_url = base_url or settings.QUICKET_API_BASE_URL
        self.timeout = timeout

    def _get(self, path, params):
        if not self.api_key:
            raise QuicketError("QUICKET_API_KEY is not configured.")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(
            f"{self.base_url}{path}",
            params=params,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def search_events(self, country="ZA", category="music", page=1, per_page=100):
        """One page of SA music events. Caller loops `page` until the page comes back empty."""
        data = self._get(
            "/events",
            {
                "country": country,
                "category": category,
                "page": page,
                "per_page": per_page,
            },
        )
        return data.get("events", [])
