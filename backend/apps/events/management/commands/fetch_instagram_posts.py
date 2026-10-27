from django.core.management.base import BaseCommand

from apps.events.fetchers.instagram import fetch_instagram_posts


class Command(BaseCommand):
    help = "Poll every watched Instagram page's RSS feed for new posts."

    def handle(self, *args, **options):
        created, updated, skipped = fetch_instagram_posts()
        self.stdout.write(
            self.style.SUCCESS(
                f"{created} new, {updated} updated, {skipped} skipped (no guid)."
            )
        )
