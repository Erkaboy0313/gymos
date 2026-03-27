from rest_framework import serializers
from branches.models import Branch


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "gym", "name", "address", "is_active", "created_at"]
        read_only_fields = ["id", "gym", "created_at"]