from django.contrib import admin
from subscriptions.models import (
    MemberPlan,
    MemberSubscription,
    GymPlan,
    GymSubscription,
    FreezePeriod,
    TelegramNotificationLog
)



admin.site.register(FreezePeriod)
admin.site.register(TelegramNotificationLog)

@admin.register(MemberPlan)
class MemberPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "gym", "name", "duration_days", "price", "is_active")
    list_filter = ("gym", "is_active")
    search_fields = ("name", "gym__name")
    autocomplete_fields = ("gym",)


@admin.register(MemberSubscription)
class MemberSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("member","id",  "plan", "start_at", "end_at", "created_at")
    readonly_fields = ('created_at',)
    list_filter = ("plan__gym",)
    search_fields = ("member__full_name", "member__phone")
    autocomplete_fields = ("member", "plan")
    ordering = ("-id","created_at")


@admin.register(GymPlan)
class GymPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "duration_days", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(GymSubscription)
class GymSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "gym", "plan", "start_at", "end_at")
    list_filter = ("gym",)
    search_fields = ("gym__name",)
    autocomplete_fields = ("gym", "plan")