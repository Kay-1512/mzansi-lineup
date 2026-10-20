from django.utils.text import slugify

from apps.catalog.models import Source

from ..models import Event, EventListing


def compute_dedupe_key(title, start, venue):
    """Normalised title+date+venue — the same show listed on two platforms
    (possibly with slightly different titles/casing) should collapse to one key.
    Matching on the date (not datetime) tolerates small time discrepancies
    between platforms for the same show.
    """
    return "|".join([slugify(title), start.date().isoformat(), slugify(venue)])


def upsert_normalised_event(source_slug, normalised):
    """Insert or update the shared Event row for one normalised item, and
    attach/refresh its per-source EventListing. Returns (event, created).
    """
    source = Source.objects.get(slug=source_slug)
    dedupe_key = compute_dedupe_key(
        normalised.title, normalised.start, normalised.venue
    )

    fields = dict(
        title=normalised.title,
        description=normalised.description,
        artists=normalised.artists,
        venue=normalised.venue,
        city=normalised.city,
        start=normalised.start,
        end=normalised.end,
        image_url=normalised.image_url,
        is_international=normalised.is_international,
    )

    event, created = Event.objects.get_or_create(dedupe_key=dedupe_key, defaults=fields)
    if not created:
        for field_name, value in fields.items():
            setattr(event, field_name, value)
        event.save(update_fields=list(fields.keys()) + ["updated_at"])

    EventListing.objects.update_or_create(
        source=source,
        external_id=normalised.external_id,
        defaults={"event": event, "ticket_url": normalised.ticket_url},
    )
    return event, created
