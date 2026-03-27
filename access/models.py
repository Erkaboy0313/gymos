from django.db import models
from django.utils import timezone

from users.models import Gym, Member
from branches.models import Branch
from devices.models import Device


class EntryLog(models.Model):
    EVENT_IN = "in"
    EVENT_OUT = "out"
    EVENT_CHOICES = [(EVENT_IN, "IN"), (EVENT_OUT, "OUT")]

    event = models.CharField(max_length=8, choices=EVENT_CHOICES, null=True, blank=True)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="entry_logs")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="entry_logs")
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="entry_logs")

    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="entry_logs")

    allow = models.BooleanField(default=False)
    reason = models.CharField(max_length=64)

    token_member_id = models.IntegerField(null=True, blank=True)
    token_gym_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["gym", "created_at"]),
            models.Index(fields=["member", "created_at"]),
            models.Index(fields=["device", "created_at"]),
        ]