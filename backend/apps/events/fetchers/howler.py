from .base import BaseFetcher

NO_API_MESSAGE = (
    "Howler has no public API yet. This stub exists so Howler can be wired up "
    "identically to the other fetchers once API access is granted (Phase 4) — "
    "see BaseFetcher for the interface it will implement."
)


class HowlerFetcher(BaseFetcher):
    source_slug = "howler"

    def fetch(self):
        raise NotImplementedError(NO_API_MESSAGE)

    def normalise(self, raw_item):
        raise NotImplementedError(NO_API_MESSAGE)
