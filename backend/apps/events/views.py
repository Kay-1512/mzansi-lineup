from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Genre, UserSource, WatchedInstagramPage

from .models import Event, HiddenEvent, InstagramPost, ManualEvent, SavedEvent
from .scoring.context import UserScoringContext
from .scoring.pipeline import score_event
from .serializers import (
    InstagramPostSerializer,
    ManualEventSerializer,
    ScoredEventSerializer,
)


def _attach_score(event, result, is_saved):
    # ScoredEventSerializer's score/match_reasons/is_saved fields read these
    # as plain attributes — they're computed per-request, never persisted.
    event.score = result.score
    event.match_reasons = result.reasons
    event.is_saved = is_saved
    return event


class EventListView(APIView):
    """The "For you" feed: the shared Event table, filtered and scored for
    whoever is asking. Never hits an external API — only reads our own DB.
    """

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "city",
                str,
                description=(
                    "Comma-separated city list, overriding the profile's cities. "
                    "Empty string means any city."
                ),
            ),
            OpenApiParameter("date_from", str, description="ISO date, inclusive."),
            OpenApiParameter("date_to", str, description="ISO date, inclusive."),
            OpenApiParameter(
                "genre", str, description="Genre slug to additionally filter by."
            ),
            OpenApiParameter(
                "source",
                str,
                description="Source slug to narrow to, within the user's onboarding sources.",
            ),
            OpenApiParameter("sort", str, description='"date" (default) or "match".'),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
        responses=ScoredEventSerializer(many=True),
    )
    def get(self, request):
        user = request.user
        context = UserScoringContext.for_user(user)

        qs = Event.objects.filter(start__gte=timezone.now()).prefetch_related(
            "listings__source"
        )

        source_slugs = set(
            UserSource.objects.filter(user=user).values_list("source__slug", flat=True)
        )
        requested_source = request.query_params.get("source")
        if requested_source:
            # The filter bar only ever offers the user's own onboarding
            # sources, so this always narrows within that set — including
            # down to zero results if, say, their onboarding selection
            # changed in another tab since the filter bar was last loaded.
            source_slugs = (
                {requested_source}
                if not source_slugs
                else source_slugs & {requested_source}
            )
            qs = qs.filter(listings__source__slug__in=source_slugs).distinct()
        elif source_slugs:
            qs = qs.filter(listings__source__slug__in=source_slugs).distinct()

        # An explicit `city=` (empty string — "Any city" in the filter bar)
        # must override the profile default, so this can't just be
        # `.get("city") or <default>` — that can't tell "not sent" apart
        # from "sent empty". A user can have several home cities now, so
        # both the override and the default are lists, matched with __in.
        if "city" in request.query_params:
            raw_cities = request.query_params.get("city", "")
            cities = [c.strip() for c in raw_cities.split(",") if c.strip()]
        else:
            cities = user.profile.cities
        if cities:
            qs = qs.filter(city__in=cities)

        date_from = parse_date(request.query_params.get("date_from", "") or "")
        date_to = parse_date(request.query_params.get("date_to", "") or "")
        if date_from:
            qs = qs.filter(start__date__gte=date_from)
        if date_to:
            qs = qs.filter(start__date__lte=date_to)

        keywords = None
        genre_slug = request.query_params.get("genre")
        if genre_slug:
            genre = Genre.objects.filter(slug=genre_slug).first()
            if genre is None:
                return Response({"count": 0, "page": 1, "page_size": 0, "results": []})
            keywords = [
                kw.lower() for kw in genre.keywords.values_list("keyword", flat=True)
            ]

        hidden_ids = set(
            HiddenEvent.objects.filter(user=user).values_list("event_id", flat=True)
        )
        saved_ids = set(
            SavedEvent.objects.filter(user=user).values_list("event_id", flat=True)
        )

        scored = []
        for event in qs.exclude(id__in=hidden_ids):
            if keywords is not None:
                # Genre browse filter can't be pushed into SQL across
                # title/description/artists cleanly, so it's done here,
                # in the same pass as scoring.
                haystack = " ".join(
                    filter(
                        None,
                        [event.title, event.description, " ".join(event.artists or [])],
                    )
                ).lower()
                if not any(kw in haystack for kw in keywords):
                    continue

            result = score_event(event, context)
            if result.score <= 0:
                continue
            scored.append((event, result))

        sort = request.query_params.get("sort", "date")
        if sort == "match":
            scored.sort(key=lambda pair: (-pair[1].score, pair[0].start))
        else:
            scored.sort(key=lambda pair: pair[0].start)

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
            page_size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
        except ValueError:
            page, page_size = 1, 20

        start_idx = (page - 1) * page_size
        page_items = scored[start_idx : start_idx + page_size]

        events = [
            _attach_score(event, result, event.id in saved_ids)
            for event, result in page_items
        ]
        serializer = ScoredEventSerializer(events, many=True)
        return Response(
            {
                "count": len(scored),
                "page": page,
                "page_size": page_size,
                "results": serializer.data,
            }
        )


class SavedEventListView(generics.ListAPIView):
    serializer_class = ScoredEventSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Event.objects.none()
        return Event.objects.filter(saved_by__user=self.request.user).prefetch_related(
            "listings__source"
        )

    def list(self, request, *args, **kwargs):
        context = UserScoringContext.for_user(request.user)
        events = [
            _attach_score(event, score_event(event, context), True)
            for event in self.get_queryset()
        ]
        serializer = self.get_serializer(events, many=True)
        return Response({"results": serializer.data})


class EventSaveView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        SavedEvent.objects.get_or_create(user=request.user, event=event)
        HiddenEvent.objects.filter(user=request.user, event=event).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        SavedEvent.objects.filter(user=request.user, event_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventHideView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        HiddenEvent.objects.get_or_create(user=request.user, event=event)
        SavedEvent.objects.filter(user=request.user, event=event).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(responses={204: None})
    def delete(self, request, pk):
        HiddenEvent.objects.filter(user=request.user, event_id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstagramPostListView(generics.ListAPIView):
    """Posts from the pages this user watches, newest first — the "they
    posted something" feed for pages that never make it onto a ticketing
    platform at all (see WatchedInstagramPage)."""

    serializer_class = InstagramPostSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return InstagramPost.objects.none()
        handles = WatchedInstagramPage.objects.filter(
            user=self.request.user
        ).values_list("handle", flat=True)
        return InstagramPost.objects.filter(handle__in=handles)


class ManualEventViewSet(viewsets.ModelViewSet):
    """A user's own events — not worth paginating in Phase 1."""

    serializer_class = ManualEventSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ManualEvent.objects.none()
        return ManualEvent.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
