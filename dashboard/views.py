from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.permissions import require_gym_membership
from dashboard.selectors import active_members_count, today_entries_count, expiring_soon_count, current_inside_count


class GymDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, gym_id: int):
        require_gym_membership(request.user, gym_id)

        days = request.query_params.get("days", "7")
        try:
            days = int(days)
        except ValueError:
            days = 7

        data = {
            "active_members_count": active_members_count(gym_id),
            "today_entries_count": today_entries_count(gym_id),
            "expiring_soon_count": expiring_soon_count(gym_id, days=days),
            "current_inside_count": current_inside_count(gym_id),
        }
        return Response(data, status=200)