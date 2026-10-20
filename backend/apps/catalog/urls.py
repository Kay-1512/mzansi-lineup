from django.urls import path

from . import views

urlpatterns = [
    path("sources/", views.SourceListView.as_view(), name="source-list"),
    path("genres/", views.GenreListView.as_view(), name="genre-list"),
    path(
        "onboarding/sources/",
        views.OnboardingSourcesView.as_view(),
        name="onboarding-sources",
    ),
    path(
        "onboarding/genres/",
        views.OnboardingGenresView.as_view(),
        name="onboarding-genres",
    ),
    path(
        "artists/",
        views.WatchedArtistListCreateView.as_view(),
        name="watched-artist-list",
    ),
    path(
        "artists/<int:pk>/",
        views.WatchedArtistDeleteView.as_view(),
        name="watched-artist-delete",
    ),
    path("artists/search/", views.ArtistSearchView.as_view(), name="artist-search"),
]
