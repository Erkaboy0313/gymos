from django.shortcuts import get_object_or_404,redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import models
from users.models import Gym, Member
from users.permissions import require_gym_membership
from users.serializers import MemberSerializer
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from .selectors import gyms_for_user

@login_required
def home(request):
    gyms = gyms_for_user(request.user)
    gym = gyms.first()
    if not gym:
        return redirect("/admin/")
    return redirect(f"/api/dashboard/app/gyms/{gym.id}/")

def initial(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("/admin/")
        else:
            return redirect("/api/users/")
    else:
        return redirect("/accounts/login/")

class MemberListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)

        qs = Member.objects.filter(gym_id=gym_id)

        # filters
        is_active = request.query_params.get("is_active")
        if is_active in ("true", "false"):
            qs = qs.filter(is_active=(is_active == "true"))

        branch_id = request.query_params.get("branch_id")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        q = request.query_params.get("q")
        if q:
            # search by phone or name (simple icontains)
            qs = qs.filter(models.Q(phone__icontains=q) | models.Q(full_name__icontains=q))

        qs = qs.order_by("-id")
        return Response(MemberSerializer(qs, many=True).data)

    def post(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)
        gym = get_object_or_404(Gym, id=gym_id)

        ser = MemberSerializer(data=request.data, context={"gym": gym})
        ser.is_valid(raise_exception=True)
        try:
            member = ser.save(gym=gym)
        except IntegrityError:
            raise ValidationError({"phone": ["This phone already exists in this gym."]})
        return Response(MemberSerializer(member).data, status=status.HTTP_201_CREATED)

class MemberUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, gym_id: int, member_id: int):
        require_gym_membership(request.user, gym_id)
        gym = get_object_or_404(Gym, id=gym_id)
        member = get_object_or_404(Member, id=member_id, gym_id=gym_id)

        ser = MemberSerializer(member, data=request.data, partial=True, context={"gym": gym})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(MemberSerializer(member).data)
    
class MemberBlockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, gym_id: int, member_id: int):
        require_gym_membership(request.user, gym_id)
        member = get_object_or_404(Member, id=member_id, gym_id=gym_id)

        # expects {"is_active": false} or true
        is_active = request.data.get("is_active", None)
        if is_active is None:
            return Response({"is_active": ["This field is required."]}, status=400)

        member.is_active = bool(is_active)
        member.save(update_fields=["is_active"])
        return Response({"id": member.id, "is_active": member.is_active})

