from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
import responses

from apps.core.ticketmaster_client import TicketmasterClient
from apps.events.fetchers.howler import HowlerFetcher
from apps.events.fetchers.ticketmaster import TicketmasterFetcher
from apps.events.models import Event, EventListing

EVENTS_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

RAW_EVENT = {
    "id": "TM12345",
    "name": "Black Coffee Live",
    "info": "An amapiano/afro house night.",
    "url": "https://ticketmaster.co.za/event/TM12345",
    "images": [{"url": "https://example.com/image.jpg"}],
    "dates": {"start": {"dateTime": "2026-12-05T18:00:00Z"}},
    "_embedded": {
        "venues": [{"name": "The Venue", "city": {"name": "Cape Town"}}],
        "attractions": [{"name": "Black Coffee", "id": "K123"}],
    },
}

RAW_EVENT_NO_CONFIRMED_TIME = {
    **RAW_EVENT,
    "id": "TM99999",
    "dates": {"start": {"localDate": "2026-12-05"}},
}


class TestTicketmasterFetcherNormalise:
    def test_normalises_a_full_event(self):
        normalised = TicketmasterFetcher().normalise(RAW_EVENT)

        assert normalised.external_id == "TM12345"
        assert normalised.title == "Black Coffee Live"
        assert normalised.artists == ["Black Coffee"]
        assert normalised.venue == "The Venue"
        assert normalised.city == "Cape Town"
        assert normalised.start == datetime(2026, 12, 5, 18, 0, tzinfo=dt_timezone.utc)
        assert normalised.image_url == "https://example.com/image.jpg"
        assert normalised.ticket_url == "https://ticketmaster.co.za/event/TM12345"
        # Ticketmaster doesn't expose attraction nationality (see fetcher comment).
        assert normalised.is_international is False

    def test_skips_events_with_no_confirmed_start_time(self):
        assert TicketmasterFetcher().normalise(RAW_EVENT_NO_CONFIRMED_TIME) is None

    def test_skips_malformed_items_instead_of_raising(self):
        assert TicketmasterFetcher().normalise({"id": "bad", "dates": {}}) is None


class TestTicketmasterFetcherFetch:
    @responses.activate
    def test_paginates_until_an_empty_page(self):
        responses.add(
            responses.GET,
            EVENTS_URL,
            json={"_embedded": {"events": [RAW_EVENT]}},
            status=200,
        )
        responses.add(responses.GET, EVENTS_URL, json={}, status=200)

        fetcher = TicketmasterFetcher(client=TicketmasterClient(api_key="test-key"))
        items = fetcher.fetch()

        assert items == [RAW_EVENT]
        assert len(responses.calls) == 2


@pytest.mark.django_db
class TestTicketmasterFetcherRun:
    @responses.activate
    def test_run_creates_an_event_and_its_listing(self):
        responses.add(
            responses.GET,
            EVENTS_URL,
            json={"_embedded": {"events": [RAW_EVENT]}},
            status=200,
        )
        responses.add(responses.GET, EVENTS_URL, json={}, status=200)

        fetcher = TicketmasterFetcher(client=TicketmasterClient(api_key="test-key"))
        created, updated, skipped = fetcher.run()

        assert (created, updated, skipped) == (1, 0, 0)
        event = Event.objects.get(title="Black Coffee Live")
        assert event.listings.filter(
            source__slug="ticketmaster", external_id="TM12345"
        ).exists()

    @responses.activate
    def test_running_twice_updates_instead_of_duplicating(self):
        for _ in range(2):
            responses.add(
                responses.GET,
                EVENTS_URL,
                json={"_embedded": {"events": [RAW_EVENT]}},
                status=200,
            )
            responses.add(responses.GET, EVENTS_URL, json={}, status=200)

        client = TicketmasterClient(api_key="test-key")
        TicketmasterFetcher(client=client).run()
        created, updated, _ = TicketmasterFetcher(client=client).run()

        assert created == 0
        assert updated == 1
        assert Event.objects.count() == 1
        assert EventListing.objects.count() == 1

    @responses.activate
    def test_skips_items_with_no_confirmed_time(self):
        responses.add(
            responses.GET,
            EVENTS_URL,
            json={"_embedded": {"events": [RAW_EVENT_NO_CONFIRMED_TIME]}},
            status=200,
        )
        responses.add(responses.GET, EVENTS_URL, json={}, status=200)

        fetcher = TicketmasterFetcher(client=TicketmasterClient(api_key="test-key"))
        created, updated, skipped = fetcher.run()

        assert (created, updated, skipped) == (0, 0, 1)
        assert Event.objects.count() == 0


class TestHowlerFetcherStub:
    def test_fetch_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            HowlerFetcher().fetch()

    def test_normalise_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            HowlerFetcher().normalise({})
