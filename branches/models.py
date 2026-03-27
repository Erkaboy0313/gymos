from django.db import models
from users.models import Gym


class Branch(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("gym", "name")]

    def __str__(self) -> str:
        return f"{self.gym.name} — {self.name}"