from dataclasses import dataclass
from typing import Dict, Set

from apps.catalog.models import Genre


@dataclass
class UserScoringContext:
    """Everything the scoring pipeline needs about one user, fetched once per
    request rather than re-queried for every event being scored.
    """

    watched_artist_names: Set[str]
    user_genre_names: Set[str]
    genre_keywords: Dict[str, list]  # genre name -> lowercased keywords
    international_acts: bool

    @classmethod
    def for_user(cls, user):
        # Kept in their original casing (e.g. "Tyla") so match reasons read
        # naturally — steps lowercase their own side of any comparison.
        watched = set(user.watched_artists.values_list("name", flat=True))
        user_genre_names = set(
            user.genres.select_related("genre").values_list("genre__name", flat=True)
        )
        genre_keywords = {
            genre.name: [
                kw.lower() for kw in genre.keywords.values_list("keyword", flat=True)
            ]
            for genre in Genre.objects.prefetch_related("keywords")
        }
        return cls(
            watched_artist_names=watched,
            user_genre_names=user_genre_names,
            genre_keywords=genre_keywords,
            international_acts=user.profile.international_acts,
        )
