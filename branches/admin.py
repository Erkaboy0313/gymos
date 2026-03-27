from django.contrib import admin
from branches.models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "gym", "name", "address", "is_active")
    list_filter = ("gym", "is_active")
    search_fields = ("name", "gym__name")
    autocomplete_fields = ("gym",)