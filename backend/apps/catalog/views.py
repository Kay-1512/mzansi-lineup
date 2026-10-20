from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.ticketmaster_client import TicketmasterClient, TicketmasterError

from .models import Genre, Source, UserGenre, UserSource, WatchedArtist
from .serializers import (
    ArtistSearchResponseSerializer,
    GenreSerializer,
    OnboardingGenresResponseSerializer,
    OnboardingSourcesResponseSerializer,
    SourceSerializer,
    UserGenreSelectionSerializer,
    UserSourceSelectionSerializer,
    WatchedArtistSerializer,
)


class SourceListView(generics.ListAPIView):
    """All platforms the app knows about, active or not (so the UI can show
    Howler as "coming soon" rather than hiding it). A small fixed reference
    list — not worth paginating.
    """

    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    pagination_class = None


class GenreListView(generics.ListAPIView):
    """Admin-managed, handful of rows — not worth paginating."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None


class OnboardingSourcesView(APIView):
    @extend_schema(responses=OnboardingSourcesResponseSerializer)
    def get(self, request):
        slugs = list(
            UserSource.objects.filter(user=request.user).values_list(
                "source__slug", flat=True
            )
        )
        return Response({"sources": slugs})

    @extend_schema(
        request=UserSourceSelectionSerializer,
        responses=OnboardingSourcesResponseSerializer,
    )
    def put(self, request):
        serializer = UserSourceSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return self.get(request)


class OnboardingGenresView(APIView):
    @extend_schema(responses=OnboardingGenresResponseSerializer)
    def get(self, request):
        slugs = list(
            UserGenre.objects.filter(user=request.user).values_list(
                "genre__slug", flat=True
            )
        )
        return Response(
            {
                "genres": slugs,
                "international_acts": request.user.profile.international_acts,
            }
        )

    @extend_schema(
        request=UserGenreSelectionSerializer,
        responses=OnboardingGenresResponseSerializer,
    )
    def put(self, request):
        serializer = UserGenreSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return self.get(request)


class WatchedArtistListCreateView(generics.ListCreateAPIView):
    """A user's watchlist — a handful of artists at most, not worth paginating."""

    serializer_class = WatchedArtistSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WatchedArtist.objects.none()
        return WatchedArtist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WatchedArtistDeleteView(generics.DestroyAPIView):
    serializer_class = WatchedArtistSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WatchedArtist.objects.none()
        return WatchedArtist.objects.filter(user=self.request.user)


class ArtistSearchView(APIView):
    """Autocomplete suggestions for the watchlist search box, backed by
    Ticketmaster's attractions endpoint."""

    @extend_schema(responses=ArtistSearchResponseSerializer)
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"results": []})

        try:
            attractions = TicketmasterClient().search_attractions(query)
        except TicketmasterError:
            return Response({"results": []})

        results = [
            {"name": a.get("name"), "external_id": a.get("id")} for a in attractions
        ]
        return Response({"results": results})
