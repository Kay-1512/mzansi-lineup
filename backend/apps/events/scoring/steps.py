"""Scoring steps, highest priority first. Each is a pluggable unit so an LLM
classifier can be dropped in later (e.g. for ambiguous listings with no
genre keyword hits) without touching the others.
"""


class ScoringStep:
    weight: int = 0

    def score(self, event, context):
        """Return (points, reason) — reason is None when this step didn't match."""
        raise NotImplementedError


class WatchedArtistStep(ScoringStep):
    """Highest priority: the user explicitly follows one of the performing artists."""

    weight = 100

    def score(self, event, context):
        if not context.watched_artist_names:
            return 0, None

        event_artists_lower = {a.lower() for a in (event.artists or [])}
        title_lower = event.title.lower()
        # Quicket's events never populate `artists` (see QuicketFetcher.normalise),
        # and even Ticketmaster attractions miss support acts — a watched name is
        # often only ever named in the description (lineup/support-act text), not
        # the title, so that's checked too rather than just title+artists.
        description_lower = (event.description or "").lower()

        # Compare lowercased, but report back the artist's original casing
        # (e.g. "Tyla") so match reasons read naturally.
        matched = {
            name
            for name in context.watched_artist_names
            if name.lower() in event_artists_lower
            or name.lower() in title_lower
            or name.lower() in description_lower
        }

        if matched:
            return self.weight, f"Because you follow {', '.join(sorted(matched))}"
        return 0, None


class GenreKeywordStep(ScoringStep):
    """Medium priority: title/description/artists match a keyword for a genre
    the user picked during onboarding."""

    weight = 50

    def score(self, event, context):
        haystack = " ".join(
            filter(
                None, [event.title, event.description, " ".join(event.artists or [])]
            )
        ).lower()

        matched_genres = [
            genre_name
            for genre_name in context.user_genre_names
            if any(kw in haystack for kw in context.genre_keywords.get(genre_name, []))
        ]

        if matched_genres:
            return (
                self.weight,
                f"Matches your {', '.join(sorted(matched_genres))} taste",
            )
        return 0, None


class InternationalActStep(ScoringStep):
    """Medium priority: an international act in SA, only if the user opted in."""

    weight = 50

    def score(self, event, context):
        if context.international_acts and event.is_international:
            return self.weight, "International act playing in SA"
        return 0, None


DEFAULT_PIPELINE = [WatchedArtistStep(), GenreKeywordStep(), InternationalActStep()]
