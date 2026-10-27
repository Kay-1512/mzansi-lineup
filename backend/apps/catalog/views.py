import logging

import requests
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.spotify_client import SpotifyClient, SpotifyError

from .models import (
    Genre,
    Source,
    UserGenre,
    UserSource,
    WatchedArtist,
    WatchedInstagramPage,
)
from .serializers import (
    ArtistSearchResponseSerializer,
    GenreSerializer,
    OnboardingGenresResponseSerializer,
    OnboardingSourcesResponseSerializer,
    SourceSerializer,
    UserGenreSelectionSerializer,
    UserSourceSelectionSerializer,
    WatchedArtistSerializer,
    WatchedInstagramPageSerializer,
)

logger = logging.getLogger(__name__)


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


class WatchedInstagramPageListCreateView(generics.ListCreateAPIView):
    """Instagram pages a user wants to hear about firsthand — a handful at
    most, not worth paginating."""

    serializer_class = WatchedInstagramPageSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WatchedInstagramPage.objects.none()
        return WatchedInstagramPage.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WatchedInstagramPageDeleteView(generics.DestroyAPIView):
    serializer_class = WatchedInstagramPageSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return WatchedInstagramPage.objects.none()
        return WatchedInstagramPage.objects.filter(user=self.request.user)


class ArtistSearchView(APIView):
    """Autocomplete suggestions for the watchlist search box, backed by
    Spotify's artist search (Client Credentials — public catalog only,
    no Spotify login). Returns an image per artist so the frontend can
    render them as cards, Spotify-onboarding style."""

    @extend_schema(responses=ArtistSearchResponseSerializer)
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"results": []})

        try:
            artists = SpotifyClient().search_artists(query)
        except (SpotifyError, requests.RequestException) as exc:
            # A missing key raises SpotifyError; a *wrong* key (or any other
            # Spotify-side failure) raises requests.HTTPError via
            # response.raise_for_status() instead — neither should ever 500
            # the watchlist search, same as every other external-API call
            # in this app degrading to empty results instead of crashing.
            logger.warning("Spotify artist search failed for %r: %s", query, exc)
            return Response({"results": []})

        results = [
            {
                "name": artist.get("name"),
                "external_id": artist.get("id"),
                "image_url": artist["images"][0]["url"] if artist.get("images") else "",
            }
            for artist in artists
        ]
        return Response({"results": results})
