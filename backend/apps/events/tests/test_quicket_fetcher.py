"""Tests for the Quicket fetcher, verified against https://docs.quicket.com
(2026-10-20). QUICKET_RAW_EVENT mirrors the real documented event shape —
see apps/core/quicket_client.py's module docstring for the one remaining
ambiguity (the `locality` level used as the city).
"""

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
import responses

from apps.core.quicket_client import QuicketClient
from apps.events.fetchers.quicket import QuicketFetcher
from apps.events.models import Event, EventListing

EVENTS_URL = "https://api.quicket.co.za/api/events"

QUICKET_RAW_EVENT = {
    "id": 98765,
    "name": "Amapiano Sessions Vol. 4",
    "description": "A night of amapiano and afro house.",
    "url": "https://www.quicket.co.za/events/98765-amapiano-sessions",
    "imageUrl": "https://example.com/quicket-image.jpg",
    "startDate": "2026-11-20T19:00:00Z",
    "endDate": "2026-11-21T02:00:00Z",
    "venue": {
        "id": 1,
        "name": "The Barn",
        "addressLine1": "1 Example Street",
        "addressLine2": "",
        "latitude": -26.2,
        "longitude": 28.0,
    },
    "locality": {
        "levelOne": "South Africa",
        "levelTwo": "Gauteng",
        "levelThree": "Johannesburg",
    },
    "categories": [{"id": 1, "name": "Music"}],
}

QUICKET_RAW_EVENT_NO_DATE = {**QUICKET_RAW_EVENT, "id": 11111, "startDate": None}

QUICKET_LIST_RESPONSE = {
    "results": [QUICKET_RAW_EVENT],
    "pageSize": 100,
    "pages": 1,
    "records": 1,
    "extras": {},
    "message": "",
    "statusCode": 200,
}


class TestQuicketFetcherNormalise:
    def test_normalises_a_full_event(self):
        normalised = QuicketFetcher().normalise(QUICKET_RAW_EVENT)

        assert normalised.external_id == "98765"
        assert normalised.title == "Amapiano Sessions Vol. 4"
        assert normalised.artists == []
        assert normalised.venue == "The Barn"
        assert normalised.city == "Johannesburg"
        assert normalised.start == datetime(2026, 11, 20, 19, 0, tzinfo=dt_timezone.utc)
        assert normalised.end == datetime(2026, 11, 21, 2, 0, tzinfo=dt_timezone.utc)
        assert normalised.image_url == "https://example.com/quicket-image.jpg"
        assert (
            normalised.ticket_url
            == "https://www.quicket.co.za/events/98765-amapiano-sessions"
        )
        assert normalised.is_international is False

    def test_skips_events_with_no_start_date(self):
        assert QuicketFetcher().normalise(QUICKET_RAW_EVENT_NO_DATE) is None

    def test_skips_malformed_items_instead_of_raising(self):
        assert QuicketFetcher().normalise({"id": "bad"}) is None

    def test_missing_venue_and_locality_dont_raise(self):
        item = {**QUICKET_RAW_EVENT, "venue": None, "locality": None}
        normalised = QuicketFetcher().normalise(item)
        assert normalised.venue == ""
        assert normalised.city == ""


class TestQuicketFetcherFetch:
    @responses.activate
    def test_stops_once_the_reported_page_count_is_reached(self):
        responses.add(responses.GET, EVENTS_URL, json=QUICKET_LIST_RESPONSE, status=200)

        fetcher = QuicketFetcher(client=QuicketClient(api_key="test-key"))
        items = fetcher.fetch()

        assert items == [QUICKET_RAW_EVENT]
        assert len(responses.calls) == 1

    @responses.activate
    def test_paginates_across_multiple_pages(self):
        page_one = {**QUICKET_LIST_RESPONSE, "pages": 2}
        page_two = {
            **QUICKET_LIST_RESPONSE,
            "pages": 2,
            "results": [{**QUICKET_RAW_EVENT, "id": 22222}],
        }
        responses.add(responses.GET, EVENTS_URL, json=page_one, status=200)
        responses.add(responses.GET, EVENTS_URL, json=page_two, status=200)

        fetcher = QuicketFetcher(client=QuicketClient(api_key="test-key"))
        items = fetcher.fetch()

        assert [item["id"] for item in items] == [98765, 22222]
        assert len(responses.calls) == 2


@pytest.mark.django_db
class TestQuicketFetcherRun:
    @responses.activate
    def test_run_creates_an_event_and_its_listing(self):
        responses.add(responses.GET, EVENTS_URL, json=QUICKET_LIST_RESPONSE, status=200)

        fetcher = QuicketFetcher(client=QuicketClient(api_key="test-key"))
        created, updated, skipped = fetcher.run()

        assert (created, updated, skipped) == (1, 0, 0)
        event = Event.objects.get(title="Amapiano Sessions Vol. 4")
        assert event.city == "Johannesburg"
        assert event.listings.filter(
            source__slug="quicket", external_id="98765"
        ).exists()
        assert isinstance(EventListing.objects.get(external_id="98765").ticket_url, str)
