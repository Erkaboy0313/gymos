from rest_framework import serializers
from devices.models import Device
from branches.models import Branch


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            "id", "branch", "name", "mode", "cooldown_seconds",
            "api_key", "is_active", "created_at"
        ]
        read_only_fields = ["id", "api_key", "created_at"]

    def validate_branch(self, branch: Branch):
        gym = self.context["gym"]
        if branch.gym_id != gym.id:
            raise serializers.ValidationError("Branch does not belong to this gym.")
        return branch