from rest_framework import serializers
from users.models import Member
from branches.models import Branch
from users.services import normalize_uz_phone

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ["id", "gym", "branch", "full_name", "phone", "is_active", "created_at"]
        read_only_fields = ["id", "gym", "created_at"]

    def validate_phone(self, value: str) -> str:
        try:
            return normalize_uz_phone(value)
        except ValueError:
            raise serializers.ValidationError("Invalid phone number format.")

    def validate_branch(self, branch: Branch):
        gym = self.context["gym"]
        if branch and branch.gym_id != gym.id:
            raise serializers.ValidationError("Branch does not belong to this gym.")
        return branch