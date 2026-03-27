from rest_framework import serializers


class DeviceValidateSerializer(serializers.Serializer):
    device_id = serializers.IntegerField()
    api_key = serializers.CharField()
    token = serializers.CharField()