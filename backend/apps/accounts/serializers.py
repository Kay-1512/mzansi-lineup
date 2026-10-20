from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.catalog.serializers import (
    GenreSerializer,
    SourceSerializer,
    WatchedArtistSerializer,
)

from .models import UserProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password"]

    def validate(self, attrs):
        attrs["username"] = attrs["email"]
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """Full read view of a user's preferences, for the "edit later" profile page."""

    sources = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    watched_artists = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "email",
            "city",
            "international_acts",
            "onboarding_complete",
            "sources",
            "genres",
            "watched_artists",
        ]

    @extend_schema_field(SourceSerializer(many=True))
    def get_sources(self, obj):
        return SourceSerializer(
            [us.source for us in obj.user.sources.select_related("source")],
            many=True,
        ).data

    @extend_schema_field(GenreSerializer(many=True))
    def get_genres(self, obj):
        return GenreSerializer(
            [ug.genre for ug in obj.user.genres.select_related("genre")], many=True
        ).data

    @extend_schema_field(WatchedArtistSerializer(many=True))
    def get_watched_artists(self, obj):
        return WatchedArtistSerializer(obj.user.watched_artists.all(), many=True).data


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["city", "international_acts", "onboarding_complete"]
