from rest_framework import serializers

from .models import Event, EventListing, ManualEvent


class EventListingSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)
    source_slug = serializers.CharField(source="source.slug", read_only=True)

    class Meta:
        model = EventListing
        fields = ["source_name", "source_slug", "ticket_url"]


class EventSerializer(serializers.ModelSerializer):
    listings = EventListingSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "artists",
            "venue",
            "city",
            "start",
            "end",
            "image_url",
            "is_international",
            "listings",
        ]


class ScoredEventSerializer(EventSerializer):
    """EventSerializer plus the per-request-user fields the frontend needs to
    render a match card — never persisted, computed fresh every call.
    """

    score = serializers.IntegerField()
    match_reasons = serializers.ListField(child=serializers.CharField())
    is_saved = serializers.BooleanField()

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ["score", "match_reasons", "is_saved"]


class ManualEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManualEvent
        fields = ["id", "title", "venue", "start", "end", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]
