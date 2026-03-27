from django.db import models
from users.models import Gym, Member

class MemberPlan(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="member_plans")
    name = models.CharField(max_length=120)
    duration_days = models.PositiveIntegerField()  # 30, 90, 365
    price = models.DecimalField(max_digits=12, decimal_places=2)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("gym", "name")]
        indexes = [models.Index(fields=["gym", "is_active"])]

    def __str__(self):
        return f"{self.gym.name}: {self.name}"

class MemberSubscription(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(MemberPlan, on_delete=models.PROTECT, related_name="subscriptions")

    start_at = models.DateField()
    end_at = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    frozen_until = models.DateField(null=True, blank=True)
    
    price_snapshot = models.IntegerField(default=0)
    class Meta:
        indexes = [
            models.Index(fields=["member", "end_at"]),
            models.Index(fields=["member", "start_at"]),
        ]

    def __str__(self):
        return f"{self.member_id} {self.start_at:%Y-%m-%d} -> {self.end_at:%Y-%m-%d}"

class FreezePeriod(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="freezes")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["member", "start_at", "end_at"])]

    def clean(self):
        if self.end_at <= self.start_at:
            raise ValueError("Freeze end must be after start")
        
class GymPlan(models.Model):
    name = models.CharField(max_length=120)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=20,blank=True,null=True)

    def __str__(self):
        return self.name

class GymSubscription(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="saas_subscriptions")
    plan = models.ForeignKey(GymPlan, on_delete=models.PROTECT, related_name="subscriptions")

    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["gym", "end_at"])]

    def __str__(self):
        return f"{self.gym.name}: {self.start_at:%Y-%m-%d} -> {self.end_at:%Y-%m-%d}"

class TelegramNotificationLog(models.Model): 
    TYPE_EXPIRY = "expiry" 
    type = models.CharField(max_length=32, default=TYPE_EXPIRY) 
    member_id = models.IntegerField(db_index=True) 
    gym_id = models.IntegerField(db_index=True) 
    days_before = models.IntegerField() # 0,3,7 
    sent_on = models.DateField(db_index=True) 
    send = models.BooleanField(default=False)
    reason = models.TextField(blank=True,null=True)
    
    class Meta: 
        unique_together = [("type", "member_id", "gym_id", "days_before", "sent_on")]


