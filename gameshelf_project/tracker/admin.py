from django.contrib import admin

from .models import CompletionLog, Game, Platform


class CompletionLogInline(admin.TabularInline):
    model = CompletionLog
    extra = 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "platform", "owner", "status", "times_beaten", "date_added")
    list_filter = ("status", "platform", "owner")
    search_fields = ("title", "owner__username")
    inlines = [CompletionLogInline]


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(CompletionLog)
class CompletionLogAdmin(admin.ModelAdmin):
    list_display = ("game", "date_beaten", "note")
    list_filter = ("date_beaten",)