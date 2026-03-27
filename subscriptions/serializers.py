from rest_framework import serializers
from subscriptions.models import MemberPlan
from users.models import Member
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from subscriptions.models import GymPlan

class MemberPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberPlan
        fields = ["id", "gym", "name", "duration_days", "price", "is_active", "created_at"]
        read_only_fields = ["id", "gym", "created_at"]

class MemberSubscriptionCreateSerializer(serializers.Serializer):
    member_id = serializers.IntegerField()
    plan_id = serializers.IntegerField()

    def validate(self, attrs):
        gym = self.context["gym"]

        member = Member.objects.filter(id=attrs["member_id"], gym=gym).first()
        if not member:
            raise serializers.ValidationError({"member_id": ["Member not found in this gym."]})

        plan = MemberPlan.objects.filter(id=attrs["plan_id"], gym=gym, is_active=True).first()
        if not plan:
            raise serializers.ValidationError({"plan_id": ["Plan not found/active in this gym."]})

        attrs["member"] = member
        attrs["plan"] = plan
        return attrs
    
class GymPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymPlan
        fields = ["id", "name", "duration_days", "price", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

class GymSubscriptionCreateSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    # optional: allow manual start/end. If end_at is omitted => computed.
    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        plan = GymPlan.objects.filter(id=attrs["plan_id"], is_active=True).first()
        if not plan:
            raise serializers.ValidationError({"plan_id": ["Plan not found/active."]})

        start_at = attrs.get("start_at") or timezone.now()

        # Lifetime if end_at explicitly null
        if "end_at" in attrs and attrs["end_at"] is None:
            attrs["plan"] = plan
            attrs["start_at"] = start_at
            attrs["end_at"] = None
            return attrs

        # If end_at provided, validate it's after start
        if "end_at" in attrs and attrs["end_at"] is not None:
            if attrs["end_at"] <= start_at:
                raise serializers.ValidationError({"end_at": ["Must be after start_at."]})
            attrs["plan"] = plan
            attrs["start_at"] = start_at
            return attrs

        # Otherwise compute end_at from duration_days
        attrs["plan"] = plan
        attrs["start_at"] = start_at
        attrs["end_at"] = start_at + timedelta(days=plan.duration_days)
        return attrs

