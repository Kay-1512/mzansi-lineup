from rest_framework import serializers

from .models import (
    Genre,
    Source,
    UserGenre,
    UserSource,
    WatchedArtist,
    WatchedInstagramPage,
)


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "name", "slug", "is_active"]


class GenreSerializer(serializers.ModelSerializer):
    # Keywords are admin-only matching data — never exposed to users.
    class Meta:
        model = Genre
        fields = ["id", "name", "slug"]


class WatchedArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedArtist
        fields = ["id", "name", "external_id", "image_url", "created_at"]
        read_only_fields = ["id", "created_at"]


class WatchedInstagramPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedInstagramPage
        fields = ["id", "handle", "feed_url", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_handle(self, value):
        return value.strip().lstrip("@")


class ArtistSearchResultSerializer(serializers.Serializer):
    name = serializers.CharField()
    external_id = serializers.CharField(allow_null=True)
    image_url = serializers.CharField(allow_blank=True)


class ArtistSearchResponseSerializer(serializers.Serializer):
    results = ArtistSearchResultSerializer(many=True)


class OnboardingSourcesResponseSerializer(serializers.Serializer):
    sources = serializers.ListField(child=serializers.SlugField())


class OnboardingGenresResponseSerializer(serializers.Serializer):
    genres = serializers.ListField(child=serializers.SlugField())
    international_acts = serializers.BooleanField()


class UserSourceSelectionSerializer(serializers.Serializer):
    """Write-only: replaces the caller's full set of selected source slugs."""

    sources = serializers.ListField(child=serializers.SlugField(), allow_empty=True)

    def save(self, user):
        slugs = self.validated_data["sources"]
        sources = list(Source.objects.filter(slug__in=slugs, is_active=True))
        found = {s.slug for s in sources}
        missing = set(slugs) - found
        if missing:
            raise serializers.ValidationError(
                {
                    "sources": f"Unknown or inactive source slug(s): {', '.join(sorted(missing))}"
                }
            )
        UserSource.objects.filter(user=user).delete()
        UserSource.objects.bulk_create(
            [UserSource(user=user, source=s) for s in sources]
        )
        return sources


class UserGenreSelectionSerializer(serializers.Serializer):
    """Write-only: replaces the caller's full set of selected genre slugs."""

    genres = serializers.ListField(child=serializers.SlugField(), allow_empty=True)
    international_acts = serializers.BooleanField(required=False)

    def save(self, user):
        slugs = self.validated_data["genres"]
        genres = list(Genre.objects.filter(slug__in=slugs))
        found = {g.slug for g in genres}
        missing = set(slugs) - found
        if missing:
            raise serializers.ValidationError(
                {"genres": f"Unknown genre slug(s): {', '.join(sorted(missing))}"}
            )
        UserGenre.objects.filter(user=user).delete()
        UserGenre.objects.bulk_create([UserGenre(user=user, genre=g) for g in genres])

        if "international_acts" in self.validated_data:
            profile = user.profile
            profile.international_acts = self.validated_data["international_acts"]
            profile.save(update_fields=["international_acts"])

        return genres
