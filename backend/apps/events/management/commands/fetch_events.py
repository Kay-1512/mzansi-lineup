from django.core.management.base import BaseCommand

from apps.catalog.models import Source
from apps.events.fetchers.howler import HowlerFetcher
from apps.events.fetchers.ticketmaster import TicketmasterFetcher

# Add an entry here when a new source gets a real fetcher (Quicket in Phase 2).
FETCHER_CLASSES = {
    "ticketmaster": TicketmasterFetcher,
    "howler": HowlerFetcher,
}


class Command(BaseCommand):
    help = (
        "Fetch South African music events from every active source into the "
        "shared Event table. Runs once for all users — never run per user."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", help="Only fetch from this one source slug.", default=None
        )

    def handle(self, *args, **options):
        sources = Source.objects.filter(is_active=True)
        if options["source"]:
            sources = sources.filter(slug=options["source"])

        if not sources.exists():
            self.stdout.write(self.style.WARNING("No matching active sources found."))
            return

        for source in sources:
            fetcher_cls = FETCHER_CLASSES.get(source.slug)
            if fetcher_cls is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"No fetcher implemented for '{source.slug}' — skipping."
                    )
                )
                continue

            self.stdout.write(f"Fetching {source.name}...")
            try:
                created, updated, skipped = fetcher_cls().run()
            except NotImplementedError as exc:
                self.stdout.write(self.style.WARNING(f"  {exc}"))
                continue
            except (
                Exception
            ) as exc:  # noqa: BLE001 - one source failing shouldn't kill the others
                self.stderr.write(self.style.ERROR(f"  Failed: {exc}"))
                continue

            self.stdout.write(
                self.style.SUCCESS(
                    f"  {created} new, {updated} updated, {skipped} skipped (no confirmed date)."
                )
            )
