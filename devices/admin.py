from django.contrib import admin
from devices.models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "branch", "mode", "cooldown_seconds", "is_active")
    list_filter = ("mode", "is_active", "branch__gym")
    search_fields = ("name", "branch__name")
    autocomplete_fields = ("branch",)
    readonly_fields = ("api_key","created_at")