"""Tests for the UNVERIFIED Quicket fetcher (see apps/core/quicket_client.py).

QUICKET_RAW_EVENT below pins down the response shape this fetcher currently
assumes. If you update QuicketFetcher.normalise() to match the real API,
update this fixture to match too — these tests exist to document the
assumption as much as to verify the code.
"""

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
import responses

from apps.core.quicket_client import QuicketClient
from apps.events.fetchers.quicket import QuicketFetcher
from apps.events.models import Event, EventListing

EVENTS_URL = "https://api.quicket.co.za/v1/events"

QUICKET_RAW_EVENT = {
    "id": 98765,
    "title": "Amapiano Sessions Vol. 4",
    "description": "A night of amapiano and afro house.",
    "url": "https://www.quicket.co.za/events/98765",
    "images": ["https://example.com/quicket-image.jpg"],
    "start_date": "2026-11-20T19:00:00Z",
    "venue": {"name": "The Barn", "city": "Johannesburg"},
    "performers": ["Kabza De Small"],
}

QUICKET_RAW_EVENT_NO_DATE = {**QUICKET_RAW_EVENT, "id": 11111, "start_date": None}


class TestQuicketFetcherNormalise:
    def test_normalises_a_full_event(self):
        normalised = QuicketFetcher().normalise(QUICKET_RAW_EVENT)

        assert normalised.external_id == "98765"
        assert normalised.title == "Amapiano Sessions Vol. 4"
        assert normalised.artists == ["Kabza De Small"]
        assert normalised.venue == "The Barn"
        assert normalised.city == "Johannesburg"
        assert normalised.start == datetime(2026, 11, 20, 19, 0, tzinfo=dt_timezone.utc)
        assert normalised.image_url == "https://example.com/quicket-image.jpg"
        assert normalised.ticket_url == "https://www.quicket.co.za/events/98765"
        assert normalised.is_international is False

    def test_skips_events_with_no_start_date(self):
        assert QuicketFetcher().normalise(QUICKET_RAW_EVENT_NO_DATE) is None

    def test_skips_malformed_items_instead_of_raising(self):
        assert QuicketFetcher().normalise({"id": "bad"}) is None


class TestQuicketFetcherFetch:
    @responses.activate
    def test_paginates_until_an_empty_page(self):
        responses.add(
            responses.GET, EVENTS_URL, json={"events": [QUICKET_RAW_EVENT]}, status=200
        )
        responses.add(responses.GET, EVENTS_URL, json={"events": []}, status=200)

        fetcher = QuicketFetcher(client=QuicketClient(api_key="test-key"))
        items = fetcher.fetch()

        assert items == [QUICKET_RAW_EVENT]
        assert len(responses.calls) == 2


@pytest.mark.django_db
class TestQuicketFetcherRun:
    @responses.activate
    def test_run_creates_an_event_and_its_listing(self):
        responses.add(
            responses.GET, EVENTS_URL, json={"events": [QUICKET_RAW_EVENT]}, status=200
        )
        responses.add(responses.GET, EVENTS_URL, json={"events": []}, status=200)

        fetcher = QuicketFetcher(client=QuicketClient(api_key="test-key"))
        created, updated, skipped = fetcher.run()

        assert (created, updated, skipped) == (1, 0, 0)
        event = Event.objects.get(title="Amapiano Sessions Vol. 4")
        assert event.listings.filter(
            source__slug="quicket", external_id="98765"
        ).exists()
        assert isinstance(EventListing.objects.get(external_id="98765").ticket_url, str)
