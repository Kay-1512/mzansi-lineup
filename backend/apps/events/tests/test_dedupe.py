from datetime import timedelta

import pytest
from django.utils import timezone

from apps.catalog.models import CityAlias
from apps.events.fetchers.base import NormalisedEvent
from apps.events.fetchers.dedupe import upsert_normalised_event
from apps.events.models import Event, EventListing

pytestmark = pytest.mark.django_db


def make_normalised(**kwargs):
    defaults = dict(
        external_id="1",
        title="Black Coffee Live",
        description="",
        artists=["Black Coffee"],
        venue="Grand Arena",
        city="Cape Town",
        start=timezone.now() + timedelta(days=10),
        end=None,
        image_url="",
        is_international=False,
        ticket_url="",
    )
    defaults.update(kwargs)
    return NormalisedEvent(**defaults)


class TestExactMatch:
    def test_same_source_refetch_updates_instead_of_duplicating(self):
        # Title/date/venue (the dedupe key's inputs) stay the same across
        # the two fetches — only a display field changes, as on a real
        # refetch where the venue updates the event's image.
        upsert_normalised_event("ticketmaster", make_normalised())
        event, created = upsert_normalised_event(
            "ticketmaster", make_normalised(image_url="https://example.com/new.jpg")
        )

        assert created is False
        assert Event.objects.count() == 1
        assert event.image_url == "https://example.com/new.jpg"


class TestCrossSourceMatch:
    def test_same_title_date_and_city_merges_despite_different_venue_string(self):
        first, created_first = upsert_normalised_event(
            "ticketmaster", make_normalised(external_id="tm-1", venue="Grand Arena")
        )
        second, created_second = upsert_normalised_event(
            "quicket",
            make_normalised(external_id="qk-1", venue="GrandWest Grand Arena"),
        )

        assert created_first is True
        assert created_second is False
        assert first.id == second.id
        assert Event.objects.count() == 1
        assert EventListing.objects.filter(event=first).count() == 2
        assert set(
            EventListing.objects.filter(event=first).values_list(
                "source__slug", flat=True
            )
        ) == {
            "ticketmaster",
            "quicket",
        }

    def test_same_title_and_date_but_different_city_does_not_merge(self):
        # Different venue too, so the exact dedupe key doesn't already match
        # on its own — this isolates the fuzzy fallback's city guard.
        upsert_normalised_event(
            "ticketmaster",
            make_normalised(external_id="tm-1", venue="Grand Arena", city="Cape Town"),
        )
        _, created = upsert_normalised_event(
            "quicket",
            make_normalised(external_id="qk-1", venue="The Dome", city="Johannesburg"),
        )

        assert created is True
        assert Event.objects.count() == 2

    def test_different_title_on_same_date_does_not_merge(self):
        upsert_normalised_event("ticketmaster", make_normalised(external_id="tm-1"))
        _, created = upsert_normalised_event(
            "quicket", make_normalised(external_id="qk-1", title="Unrelated Jazz Night")
        )

        assert created is True
        assert Event.objects.count() == 2


class TestCityAliasNormalisation:
    def test_stores_the_canonical_city_not_the_raw_alias(self):
        alias_map = CityAlias.build_lookup_map()  # seeded: Sandton -> Johannesburg
        event, _ = upsert_normalised_event(
            "ticketmaster", make_normalised(city="Sandton"), alias_map
        )

        assert event.city == "Johannesburg"

    def test_an_aliased_city_still_merges_across_sources(self):
        # Different venue strings (so the exact key misses) and one source's
        # city is an alias for the other's canonical form — without
        # normalisation this would fail the fuzzy match's city guard.
        alias_map = CityAlias.build_lookup_map()
        first, created_first = upsert_normalised_event(
            "ticketmaster",
            make_normalised(
                external_id="tm-1", venue="Grand Arena", city="Johannesburg"
            ),
            alias_map,
        )
        second, created_second = upsert_normalised_event(
            "quicket",
            make_normalised(external_id="qk-1", venue="The Dome", city="Sandton"),
            alias_map,
        )

        assert created_first is True
        assert created_second is False
        assert first.id == second.id
        assert Event.objects.count() == 1
