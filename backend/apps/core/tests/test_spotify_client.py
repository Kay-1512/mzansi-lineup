import pytest
import responses

from apps.core.spotify_client import SEARCH_URL, TOKEN_URL, SpotifyClient, SpotifyError

TOKEN_RESPONSE = {
    "access_token": "test-access-token",
    "token_type": "Bearer",
    "expires_in": 3600,
}

SEARCH_RESPONSE = {
    "artists": {
        "items": [
            {
                "id": "spotify-artist-1",
                "name": "Tyla",
                "images": [
                    {
                        "url": "https://example.com/tyla-large.jpg",
                        "width": 640,
                        "height": 640,
                    },
                    {
                        "url": "https://example.com/tyla-small.jpg",
                        "width": 64,
                        "height": 64,
                    },
                ],
            }
        ]
    }
}


@pytest.fixture(autouse=True)
def reset_token_cache():
    # The token cache is a class attribute (shared across requests in the
    # same process by design) — reset it so tests don't leak state into
    # each other depending on run order.
    SpotifyClient._token = None
    SpotifyClient._token_expires_at = 0
    yield
    SpotifyClient._token = None
    SpotifyClient._token_expires_at = 0


class TestSpotifyClientAuth:
    def test_raises_without_credentials(self):
        client = SpotifyClient(client_id="", client_secret="")
        with pytest.raises(SpotifyError):
            client.search_artists("Tyla")

    @responses.activate
    def test_fetches_and_reuses_the_token_across_calls(self):
        responses.add(responses.POST, TOKEN_URL, json=TOKEN_RESPONSE, status=200)
        responses.add(responses.GET, SEARCH_URL, json=SEARCH_RESPONSE, status=200)
        responses.add(responses.GET, SEARCH_URL, json=SEARCH_RESPONSE, status=200)

        client = SpotifyClient(client_id="id", client_secret="secret")
        client.search_artists("Tyla")
        client.search_artists("Tyla")

        token_calls = [c for c in responses.calls if c.request.url == TOKEN_URL]
        assert len(token_calls) == 1  # second search reused the cached token

    @responses.activate
    def test_sends_the_token_as_a_bearer_header(self):
        responses.add(responses.POST, TOKEN_URL, json=TOKEN_RESPONSE, status=200)
        responses.add(responses.GET, SEARCH_URL, json=SEARCH_RESPONSE, status=200)

        SpotifyClient(client_id="id", client_secret="secret").search_artists("Tyla")

        search_call = responses.calls[-1]
        assert (
            search_call.request.headers["Authorization"] == "Bearer test-access-token"
        )


class TestSpotifyClientSearch:
    @responses.activate
    def test_returns_the_artist_items(self):
        responses.add(responses.POST, TOKEN_URL, json=TOKEN_RESPONSE, status=200)
        responses.add(responses.GET, SEARCH_URL, json=SEARCH_RESPONSE, status=200)

        results = SpotifyClient(client_id="id", client_secret="secret").search_artists(
            "Tyla"
        )

        assert results == SEARCH_RESPONSE["artists"]["items"]
