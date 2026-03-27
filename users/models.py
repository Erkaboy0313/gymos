from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Staff users live here. Members are NOT auth users in v1.
    """
    # keep it simple for now

class Gym(models.Model):
    ACCESS_ALL = "all"
    ACCESS_REGISTERED_ONLY = "registered_only"

    BRANCH_ACCESS_CHOICES = [
        (ACCESS_ALL, "All branches"),
        (ACCESS_REGISTERED_ONLY, "Registered branch only"),
    ]

    branch_access_mode = models.CharField(
        max_length=20,
        choices=BRANCH_ACCESS_CHOICES,
        default=ACCESS_ALL,
    )

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

class GymStaff(models.Model):
    ROLE_OWNER = "owner"
    ROLE_ADMIN = "admin"
    ROLE_STAFF = "staff"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_STAFF, "Staff"),
    ]

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="staff")
    branch = models.ForeignKey("branches.Branch",on_delete=models.CASCADE,blank=True,null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gym_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("gym", "user")]

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.gym.name} ({self.role})"

class Member(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="members")
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="members", null=True, blank=True)

    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)  # store normalized later
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    telegram_user_id = models.BigIntegerField(null=True, blank=True)
    is_inside = models.BooleanField(default=False)
    inside_since = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("gym", "phone"), ("gym", "telegram_user_id")]
        indexes = [
            models.Index(fields=["gym", "phone"]),
            models.Index(fields=["gym", "is_active"]),
            models.Index(fields=["gym", "telegram_user_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.phone})"
