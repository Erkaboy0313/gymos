from django.contrib import admin
from users.models import Gym, GymStaff, Member
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "username", "email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("-id",)

@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("-id",)

@admin.register(GymStaff)
class GymStaffAdmin(admin.ModelAdmin):
    list_display = ("id", "gym", "user", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("user__username", "gym__name")
    autocomplete_fields = ("gym", "user")

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "gym", "full_name", "phone", "is_active", "telegram_user_id")
    list_filter = ("gym", "is_active")
    search_fields = ("full_name", "phone")
    autocomplete_fields = ("gym",)
    ordering = ("-id",)
    
