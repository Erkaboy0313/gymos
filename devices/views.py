from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import models
from django.shortcuts import get_object_or_404

from users.permissions import require_gym_membership
from users.models import Gym
from devices.models import Device
from devices.serializers import DeviceSerializer


class DeviceListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)

        qs = Device.objects.filter(branch__gym_id=gym_id).select_related("branch").order_by("-id")

        branch_id = request.query_params.get("branch_id")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        q = request.query_params.get("q")
        if q:
            qs = qs.filter(models.Q(name__icontains=q))

        return Response(DeviceSerializer(qs, many=True).data)

    def post(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        gym = get_object_or_404(Gym, id=gym_id)

        ser = DeviceSerializer(data=request.data, context={"gym": gym})
        ser.is_valid(raise_exception=True)
        device = ser.save()
        return Response(DeviceSerializer(device).data, status=status.HTTP_201_CREATED)


class DeviceUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, gym_id: int, device_id: int):
        require_gym_membership(request.user, gym_id)
        gym = get_object_or_404(Gym, id=gym_id)

        device = get_object_or_404(Device, id=device_id, branch__gym_id=gym_id)

        ser = DeviceSerializer(device, data=request.data, partial=True, context={"gym": gym})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(DeviceSerializer(device).data, status=200)