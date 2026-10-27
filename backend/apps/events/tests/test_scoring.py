import uuid
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.catalog.models import Genre, UserGenre, WatchedArtist
from apps.events.models import Event
from apps.events.scoring.context import UserScoringContext
from apps.events.scoring.pipeline import score_event
from apps.events.scoring.steps import (
    GenreKeywordStep,
    InternationalActStep,
    WatchedArtistStep,
)

User = get_user_model()


def make_user(username):
    return User.objects.create_user(
        username=username, email=f"{username}@example.com", password="pw123456!"
    )


def make_event(**kwargs):
    defaults = dict(
        title="Some Show",
        description="",
        artists=[],
        venue="Venue",
        city="Johannesburg",
        start=timezone.now() + timedelta(days=10),
        dedupe_key=f"test-{uuid.uuid4()}",
    )
    defaults.update(kwargs)
    return Event.objects.create(**defaults)


@pytest.mark.django_db
class TestWatchedArtistStep:
    def test_scores_when_artist_in_event_artists_list(self):
        user = make_user("u1")
        WatchedArtist.objects.create(user=user, name="Tyla")
        event = make_event(title="Tyla Live", artists=["Tyla"])
        context = UserScoringContext.for_user(user)

        points, reason = WatchedArtistStep().score(event, context)

        assert points == 100
        assert "Tyla" in reason

    def test_falls_back_to_matching_against_the_title(self):
        # Ticketmaster doesn't always embed every attraction, so a watched
        # name appearing only in the title should still score.
        user = make_user("u2")
        WatchedArtist.objects.create(user=user, name="Tyla")
        event = make_event(title="Tyla Live in Durban", artists=[])
        context = UserScoringContext.for_user(user)

        points, _ = WatchedArtistStep().score(event, context)

        assert points == 100

    def test_falls_back_to_matching_against_the_description(self):
        # Quicket events never populate `artists` (no performer field in
        # their API), so a support/headliner named only in the description
        # (not the title) must still score.
        user = make_user("u2b")
        WatchedArtist.objects.create(user=user, name="Olivia Dean")
        event = make_event(
            title="Milk + Cookies Festival",
            artists=[],
            description="Headlined by Olivia Dean, with support from...",
        )
        context = UserScoringContext.for_user(user)

        points, reason = WatchedArtistStep().score(event, context)

        assert points == 100
        assert "Olivia Dean" in reason

    def test_no_match_scores_zero_with_no_reason(self):
        user = make_user("u3")
        WatchedArtist.objects.create(user=user, name="Tyla")
        event = make_event(title="Someone Else", artists=["Other Artist"])
        context = UserScoringContext.for_user(user)

        points, reason = WatchedArtistStep().score(event, context)

        assert points == 0
        assert reason is None


@pytest.mark.django_db
class TestGenreKeywordStep:
    def test_scores_when_a_selected_genres_keyword_matches(self):
        user = make_user("u4")
        UserGenre.objects.create(user=user, genre=Genre.objects.get(slug="amapiano"))
        event = make_event(title="Piano Night", description="A log drum heavy set.")
        context = UserScoringContext.for_user(user)

        points, reason = GenreKeywordStep().score(event, context)

        assert points == 50
        assert "Amapiano" in reason

    def test_keyword_match_outside_selected_genres_is_ignored(self):
        # The event is clearly Amapiano, but this user only follows Jazz —
        # source genre tags are unreliable, so we never guess beyond their picks.
        user = make_user("u5")
        UserGenre.objects.create(user=user, genre=Genre.objects.get(slug="jazz"))
        event = make_event(title="Amapiano Night", description="log drum all night")
        context = UserScoringContext.for_user(user)

        points, reason = GenreKeywordStep().score(event, context)

        assert points == 0
        assert reason is None


@pytest.mark.django_db
class TestInternationalActStep:
    def test_scores_when_toggle_on_and_event_is_international(self):
        user = make_user("u6")
        user.profile.international_acts = True
        user.profile.save()
        event = make_event(is_international=True)
        context = UserScoringContext.for_user(user)

        points, _ = InternationalActStep().score(event, context)

        assert points == 50

    def test_no_score_when_toggle_is_off(self):
        user = make_user("u7")
        event = make_event(is_international=True)
        context = UserScoringContext.for_user(user)

        points, reason = InternationalActStep().score(event, context)

        assert points == 0
        assert reason is None

    def test_no_score_when_event_is_not_international(self):
        user = make_user("u8")
        user.profile.international_acts = True
        user.profile.save()
        event = make_event(is_international=False)
        context = UserScoringContext.for_user(user)

        points, _ = InternationalActStep().score(event, context)

        assert points == 0


@pytest.mark.django_db
class TestScoreEventPipeline:
    def test_combines_points_and_reasons_from_every_matching_step(self):
        user = make_user("u9")
        WatchedArtist.objects.create(user=user, name="Black Coffee")
        UserGenre.objects.create(user=user, genre=Genre.objects.get(slug="amapiano"))
        user.profile.international_acts = True
        user.profile.save()

        event = make_event(
            title="Black Coffee presents Piano Fest",
            artists=["Black Coffee"],
            description="log drum all night",
            is_international=True,
        )
        context = UserScoringContext.for_user(user)

        result = score_event(event, context)

        assert result.score == 100 + 50 + 50
        assert len(result.reasons) == 3

    def test_event_matching_nothing_scores_zero(self):
        user = make_user("u10")
        event = make_event(title="Random Show", description="nothing relevant here")
        context = UserScoringContext.for_user(user)

        result = score_event(event, context)

        assert result.score == 0
        assert result.reasons == []
