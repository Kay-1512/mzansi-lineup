from django.contrib import admin

from .models import (
    CityAlias,
    Genre,
    GenreKeyword,
    Source,
    UserGenre,
    UserSource,
    WatchedArtist,
)


class GenreKeywordInline(admin.TabularInline):
    model = GenreKeyword
    extra = 1


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "keyword_count")
    search_fields = ("name",)
    inlines = [GenreKeywordInline]

    def keyword_count(self, obj):
        return obj.keywords.count()


@admin.register(GenreKeyword)
class GenreKeywordAdmin(admin.ModelAdmin):
    list_display = ("keyword", "genre")
    list_filter = ("genre",)
    search_fields = ("keyword",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    list_filter = ("is_active",)


@admin.register(CityAlias)
class CityAliasAdmin(admin.ModelAdmin):
    list_display = ("alias", "canonical_city")
    list_filter = ("canonical_city",)
    search_fields = ("alias",)


admin.site.register(UserSource)
admin.site.register(UserGenre)
admin.site.register(WatchedArtist)
