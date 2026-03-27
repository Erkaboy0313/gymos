from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import Gym, Member
from identifiers.services import generate_member_qr_token
from django.views import View
from django.shortcuts import render, get_object_or_404
from users.services import verify_tg_session
from django.conf import settings

class MemberWebAppView(View):
    def get(self, request):
        return render(request, "identifiers/member_qr.html", {"DEBUG": False})

class MemberQRPageView(View):
    def get(self, request, gym_id: int, member_id: int):
        member = get_object_or_404(Member, id=member_id, gym_id=gym_id, is_active=True)
        return render(request, "identifiers/member_qr.html", {
            "gym_id": gym_id,
            "member_id": member_id,
            "member_name": member.full_name,
        })
        
class MemberQRTokenView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        sess = request.headers.get("X-Member-Session")
        if not sess:
            return Response({"detail": "missing_member_session"}, status=401)

        try:
            payload = verify_tg_session(sess)
        except Exception:
            return Response({"detail": "invalid_member_session"}, status=401)

        tg_id = payload["tg"]
        gym_id = request.data.get("gym_id")
        if not gym_id:
            return Response({"detail": "gym_id required"}, status=400)

        member = Member.objects.filter(
            gym_id=gym_id,
            telegram_user_id=tg_id,
            is_active=True,
        ).first()

        if not member:
            return Response({"detail": "member_not_linked"}, status=404)

        token = generate_member_qr_token(gym_id=int(gym_id), member_id=member.id)
        return Response({"token": token}, status=200)
    
