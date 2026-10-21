import pytest
import responses
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from apps.core.spotify_client import SEARCH_URL, TOKEN_URL, SpotifyClient

pytestmark = pytest.mark.django_db

User = get_user_model()

TOKEN_RESPONSE = {
    "access_token": "test-token",
    "token_type": "Bearer",
    "expires_in": 3600,
}

SEARCH_RESPONSE = {
    "artists": {
        "items": [
            {
                "id": "spotify-1",
                "name": "Tyla",
                "images": [
                    {"url": "https://example.com/tyla.jpg", "width": 640, "height": 640}
                ],
            },
            {"id": "spotify-2", "name": "No Image Artist", "images": []},
        ]
    }
}


@pytest.fixture(autouse=True)
def reset_token_cache():
    SpotifyClient._token = None
    SpotifyClient._token_expires_at = 0
    yield
    SpotifyClient._token = None
    SpotifyClient._token_expires_at = 0


def authed_client():
    User.objects.create_user(username="search@example.com", password="pw123456!")
    client = APIClient()
    resp = client.post(
        "/api/auth/token/", {"username": "search@example.com", "password": "pw123456!"}
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return client


class TestArtistSearchView:
    def test_short_queries_return_no_results_without_calling_spotify(self):
        resp = authed_client().get("/api/artists/search/", {"q": "a"})

        assert resp.status_code == 200
        assert resp.data["results"] == []

    @override_settings(SPOTIFY_CLIENT_ID="id", SPOTIFY_CLIENT_SECRET="secret")
    @responses.activate
    def test_returns_name_external_id_and_image_url(self):
        responses.add(responses.POST, TOKEN_URL, json=TOKEN_RESPONSE, status=200)
        responses.add(responses.GET, SEARCH_URL, json=SEARCH_RESPONSE, status=200)

        resp = authed_client().get("/api/artists/search/", {"q": "Tyla"})

        assert resp.status_code == 200
        assert resp.data["results"][0] == {
            "name": "Tyla",
            "external_id": "spotify-1",
            "image_url": "https://example.com/tyla.jpg",
        }

    @override_settings(SPOTIFY_CLIENT_ID="id", SPOTIFY_CLIENT_SECRET="secret")
    @responses.activate
    def test_an_artist_with_no_images_gets_an_empty_image_url_not_an_error(self):
        responses.add(responses.POST, TOKEN_URL, json=TOKEN_RESPONSE, status=200)
        responses.add(responses.GET, SEARCH_URL, json=SEARCH_RESPONSE, status=200)

        resp = authed_client().get("/api/artists/search/", {"q": "Tyla"})

        assert resp.data["results"][1] == {
            "name": "No Image Artist",
            "external_id": "spotify-2",
            "image_url": "",
        }

    def test_missing_spotify_credentials_degrades_to_empty_results(self):
        # No responses mocked, no SPOTIFY_CLIENT_ID in test settings — the
        # SpotifyError this raises should be swallowed, not a 500.
        resp = authed_client().get("/api/artists/search/", {"q": "Tyla"})

        assert resp.status_code == 200
        assert resp.data["results"] == []
