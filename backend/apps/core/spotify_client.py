"""Thin wrapper around the Spotify Web API's artist search.

Uses the Client Credentials flow — this only reads public catalog data
(artist name + image), no user login needed:
https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow
"""

import time

import requests
from django.conf import settings

TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"
DEFAULT_TIMEOUT = 10


class SpotifyError(Exception):
    pass


class SpotifyClient:
    # Class-level so the access token (valid ~1hr) is shared across
    # requests in the same process instead of re-fetched per search.
    _token = None
    _token_expires_at = 0

    def __init__(self, client_id=None, client_secret=None, timeout=DEFAULT_TIMEOUT):
        self.client_id = (
            client_id if client_id is not None else settings.SPOTIFY_CLIENT_ID
        )
        self.client_secret = (
            client_secret
            if client_secret is not None
            else settings.SPOTIFY_CLIENT_SECRET
        )
        self.timeout = timeout

    def _get_token(self):
        if SpotifyClient._token and time.time() < SpotifyClient._token_expires_at:
            return SpotifyClient._token

        if not self.client_id or not self.client_secret:
            raise SpotifyError(
                "SPOTIFY_CLIENT_ID/SPOTIFY_CLIENT_SECRET are not configured."
            )

        response = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        SpotifyClient._token = data["access_token"]
        # Refresh a little early so a token already in flight never expires mid-request.
        SpotifyClient._token_expires_at = time.time() + data["expires_in"] - 30
        return SpotifyClient._token

    def search_artists(self, query, limit=10):
        token = self._get_token()
        response = requests.get(
            SEARCH_URL,
            params={"q": query, "type": "artist", "limit": limit},
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json().get("artists", {}).get("items", [])
