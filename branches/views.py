from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from users.permissions import require_gym_membership
from users.models import Gym
from branches.models import Branch
from branches.serializers import BranchSerializer


class BranchListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        qs = Branch.objects.filter(gym_id=gym_id).order_by("-id")
        return Response(BranchSerializer(qs, many=True).data)

    def post(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        gym = get_object_or_404(Gym, id=gym_id)

        ser = BranchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        branch = ser.save(gym=gym)
        return Response(BranchSerializer(branch).data, status=status.HTTP_201_CREATED)


class BranchUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, gym_id: int, branch_id: int):
        require_gym_membership(request.user, gym_id)
        branch = get_object_or_404(Branch, id=branch_id, gym_id=gym_id)

        ser = BranchSerializer(branch, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(BranchSerializer(branch).data, status=200)