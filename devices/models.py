import secrets
from django.db import models
from branches.models import Branch
from django.db.models import Q

class Device(models.Model):
    MODE_KIOSK = "kiosk"
    MODE_API = "api"

    MODE_CHOICES = [
        (MODE_KIOSK, "Kiosk (Browser + Scanner)"),
        (MODE_API, "API Device (Hardware)"),
    ]

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="devices"
    )

    name = models.CharField(max_length=120)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_KIOSK)

    api_key = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        editable=False,
    )

    is_active = models.BooleanField(default=True)
    cooldown_seconds = models.PositiveIntegerField(default=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "name"],
                name="unique_device_name_per_branch",
            ),
            models.UniqueConstraint(
                fields=["api_key"],
                condition=Q(api_key__isnull=False),
                name="unique_non_null_api_key",
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "mode"]),
        ]

    def save(self, *args, **kwargs):
        if self.mode == self.MODE_API:
            if not self.api_key:
                self.api_key = secrets.token_hex(32)
        else:
            self.api_key = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.branch.name} - {self.name} ({self.mode})"
