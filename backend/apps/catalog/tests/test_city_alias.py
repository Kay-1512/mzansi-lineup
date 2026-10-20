import pytest

from apps.catalog.models import CityAlias, normalize_city

pytestmark = pytest.mark.django_db


class TestNormalizeCity:
    def test_resolves_a_known_alias_case_insensitively(self):
        alias_map = {"sandton": "Johannesburg"}
        assert normalize_city("Sandton", alias_map) == "Johannesburg"
        assert normalize_city("SANDTON", alias_map) == "Johannesburg"

    def test_falls_back_to_the_stripped_raw_value_when_no_alias_matches(self):
        assert normalize_city("  Hermanus  ", {}) == "Hermanus"

    def test_passes_through_blank_values_unchanged(self):
        assert normalize_city("", {}) == ""
        assert normalize_city(None, {}) is None


class TestCityAliasBuildLookupMap:
    def test_builds_a_lowercased_alias_to_canonical_map(self):
        CityAlias.objects.all().delete()  # start from a clean slate, ignoring the seed data
        CityAlias.objects.create(alias="Stellenbosch", canonical_city="Cape Town")
        CityAlias.objects.create(alias="Hillcrest", canonical_city="Durban")

        lookup = CityAlias.build_lookup_map()

        assert lookup == {"stellenbosch": "Cape Town", "hillcrest": "Durban"}

    def test_starter_aliases_are_seeded_by_migration(self):
        # apps/catalog/migrations/0005_seed_city_aliases.py
        assert CityAlias.objects.filter(
            alias="Sandton", canonical_city="Johannesburg"
        ).exists()
        assert CityAlias.objects.filter(
            alias="Centurion", canonical_city="Pretoria"
        ).exists()
