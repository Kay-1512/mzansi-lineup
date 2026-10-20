from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class NormalisedEvent:
    """What every fetcher must reduce a raw API item down to, regardless of source."""

    external_id: str
    title: str
    description: str
    artists: List[str]
    venue: str
    city: str
    start: datetime
    end: Optional[datetime]
    image_url: str
    is_international: bool
    ticket_url: str


class BaseFetcher:
    """One subclass per ticketing platform. Keeps platform-specific HTTP/parsing
    code isolated behind `fetch()` + `normalise()`, so `run()` (and the dedupe
    and upsert logic it calls) never changes when a new source is added.
    """

    source_slug: str = None

    def fetch(self) -> list:
        """Return raw items from the external API. One call per source per run —
        never call this per-user; see dedupe.upsert_normalised_event."""
        raise NotImplementedError

    def normalise(self, raw_item) -> Optional[NormalisedEvent]:
        """Convert one raw item into a NormalisedEvent, or None to skip it
        (e.g. a listing with no confirmed date yet)."""
        raise NotImplementedError

    def run(self):
        from .dedupe import upsert_normalised_event

        if not self.source_slug:
            raise ValueError(f"{type(self).__name__} must set source_slug")

        created = updated = skipped = 0
        for raw_item in self.fetch():
            normalised = self.normalise(raw_item)
            if normalised is None:
                skipped += 1
                continue
            _, was_created = upsert_normalised_event(self.source_slug, normalised)
            created += int(was_created)
            updated += int(not was_created)
        return created, updated, skipped
