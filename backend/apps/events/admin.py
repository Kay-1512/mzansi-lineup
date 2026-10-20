from django.contrib import admin

from .models import Event, EventListing, HiddenEvent, ManualEvent, SavedEvent


class EventListingInline(admin.TabularInline):
    model = EventListing
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "venue", "city", "start", "is_international")
    list_filter = ("city", "is_international")
    search_fields = ("title", "venue", "description")
    inlines = [EventListingInline]


admin.site.register(ManualEvent)
admin.site.register(SavedEvent)
admin.site.register(HiddenEvent)
