from django.utils.text import slugify

from apps.catalog.models import Source, normalize_city

from ..models import Event, EventListing


def compute_dedupe_key(title, start, venue):
    """Normalised title+date+venue — the same show listed on two platforms
    (possibly with slightly different titles/casing) should collapse to one key.
    Matching on the date (not datetime) tolerates small time discrepancies
    between platforms for the same show.
    """
    return "|".join([slugify(title), start.date().isoformat(), slugify(venue)])


def _find_cross_source_match(title, start, city):
    """Fallback for when two platforms list the same show under slightly
    different venue strings (e.g. "Grand Arena" vs "GrandWest Grand Arena"),
    so compute_dedupe_key()'s exact match misses it.

    Matches on same title-slug + same date, and — only when both sides have
    a city — the same city too, so two unrelated same-day, same-title events
    in different cities (a generic name like "Open Mic Night" could easily
    collide) aren't merged into one.
    """
    title_slug = slugify(title)
    candidates = Event.objects.filter(start__date=start.date())
    for candidate in candidates:
        if slugify(candidate.title) != title_slug:
            continue
        if (
            city
            and candidate.city
            and city.strip().lower() != candidate.city.strip().lower()
        ):
            continue
        return candidate
    return None


def upsert_normalised_event(source_slug, normalised, city_alias_map=None):
    """Insert or update the shared Event row for one normalised item, and
    attach/refresh its per-source EventListing. Returns (event, created).

    `city_alias_map` (from CityAlias.build_lookup_map()) resolves raw venue
    city strings like "Sandton" to a canonical city before it's stored or
    matched on — both the city filter and the cross-source match below
    benefit from it. Omit it (or pass {}) to skip normalisation, e.g. in a
    test that doesn't care about aliasing.
    """
    source = Source.objects.get(slug=source_slug)
    city = normalize_city(normalised.city, city_alias_map or {})
    dedupe_key = compute_dedupe_key(
        normalised.title, normalised.start, normalised.venue
    )

    fields = dict(
        title=normalised.title,
        description=normalised.description,
        artists=normalised.artists,
        venue=normalised.venue,
        city=city,
        start=normalised.start,
        end=normalised.end,
        image_url=normalised.image_url,
        is_international=normalised.is_international,
    )

    event = Event.objects.filter(dedupe_key=dedupe_key).first()
    if event is None:
        event = _find_cross_source_match(normalised.title, normalised.start, city)

    if event is None:
        event = Event.objects.create(dedupe_key=dedupe_key, **fields)
        created = True
    else:
        created = False
        for field_name, value in fields.items():
            setattr(event, field_name, value)
        event.save(update_fields=list(fields.keys()) + ["updated_at"])

    EventListing.objects.update_or_create(
        source=source,
        external_id=normalised.external_id,
        defaults={"event": event, "ticket_url": normalised.ticket_url},
    )
    return event, created
