from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from users.permissions import require_gym_membership
from users.models import Gym
from subscriptions.models import MemberPlan
from subscriptions.serializers import (
    MemberPlanSerializer,
    MemberSubscriptionCreateSerializer,
)
from subscriptions.services import create_subscription
from django.shortcuts import get_object_or_404
from subscriptions.models import GymPlan, GymSubscription
from subscriptions.serializers import GymPlanSerializer, GymSubscriptionCreateSerializer

class MemberPlanListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        qs = MemberPlan.objects.filter(gym_id=gym_id).order_by("-id")
        return Response(MemberPlanSerializer(qs, many=True).data)

    def post(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        gym = Gym.objects.get(id=gym_id)

        ser = MemberPlanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        plan = ser.save(gym=gym)
        return Response(MemberPlanSerializer(plan).data, status=status.HTTP_201_CREATED)

class MemberSubscriptionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        gym = Gym.objects.get(id=gym_id)

        ser = MemberSubscriptionCreateSerializer(data=request.data, context={"gym": gym})
        ser.is_valid(raise_exception=True)

        sub = create_subscription(ser.validated_data["member"], ser.validated_data["plan"])
        return Response(
            {
                "id": sub.id,
                "member_id": sub.member_id,
                "plan_id": sub.plan_id,
                "start_at": sub.start_at,
                "end_at": sub.end_at,
            },
            status=status.HTTP_201_CREATED,
        )
        
class GymPlanListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        qs = GymPlan.objects.all().order_by("-id")  # global plans for now
        return Response(GymPlanSerializer(qs, many=True).data)

    def post(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        ser = GymPlanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        plan = ser.save()
        return Response(GymPlanSerializer(plan).data, status=status.HTTP_201_CREATED)

class GymSubscriptionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        gym = get_object_or_404(Gym, id=gym_id)

        ser = GymSubscriptionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        sub = GymSubscription.objects.create(
            gym=gym,
            plan=ser.validated_data["plan"],
            start_at=ser.validated_data["start_at"],
            end_at=ser.validated_data["end_at"],
        )

        return Response(
            {
                "id": sub.id,
                "gym_id": sub.gym_id,
                "plan_id": sub.plan_id,
                "start_at": sub.start_at,
                "end_at": sub.end_at,
            },
            status=status.HTTP_201_CREATED,
        )
