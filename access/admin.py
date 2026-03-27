from django.contrib import admin
from access.models import EntryLog


@admin.register(EntryLog)
class EntryLogAdmin(admin.ModelAdmin):
    list_display = ("id", "gym", "member", "device", "allow", "reason", "created_at")
    list_filter = ("gym", "allow", "reason")
    search_fields = ("member__full_name", "member__phone")
    autocomplete_fields = ("gym", "member", "device")
    ordering = ("-id",)