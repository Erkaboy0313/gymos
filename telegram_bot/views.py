import json
from rest_framework.views import APIView
from rest_framework.response import Response

from telegram_bot.services import verify_telegram_webapp_init_data
from users.models import Member
from users.services import make_tg_session


class WebAppAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        init_data = request.data.get("init_data")
        if not init_data:
            return Response({"detail": "init_data required"}, status=400)

        try:
            data = verify_telegram_webapp_init_data(init_data)
            tg_user = json.loads(data["user"])
            
            tg_id = int(tg_user["id"])
        except Exception:
            return Response({"detail": "invalid_init_data"}, status=401)

        session = make_tg_session(tg_id)
        return Response({"telegram_user_id": tg_id, "session": session}, status=200)