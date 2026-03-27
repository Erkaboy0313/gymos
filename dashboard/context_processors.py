from django.utils import timezone
from subscriptions.models import GymSubscription
from users.models import GymStaff
from branches.models import Branch

def gym_saas_banner(request):
    """
    Adds SaaS subscription status to templates when gym_id exists in URL kwargs.
    Works for all staff template pages automatically.
    """
    gym_id = None
    try:
        gym_id = request.resolver_match.kwargs.get("gym_id")
    except Exception:
        gym_id = None

    if not gym_id:
        return {}

    now = timezone.now()
    sub = (
        GymSubscription.objects
        .filter(gym_id=gym_id)
        .select_related("plan", "gym")
        .order_by("-start_at", "-id")
        .first()
    )
    gs = GymStaff.objects.filter(gym_id=gym_id, user=request.user, is_active=True).first()
    role = gs.role if gs else None
    has_multiple_branch = True if Branch.objects.filter(gym_id = gym_id).count()> 1 else False
    if not sub:
        return {
            "staff_role": role,
            "has_multiple_branch":has_multiple_branch,
            "is_admin_role": role in (GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER),
            "saas": {
                "gym_id": gym_id,
                "status": "missing",
                "active": False,
                "message": "SaaS subscription not set. Contact GymOS support.",
                "end_at": None,
                "plan_name": None,
            }
        }

    active = (sub.end_at is None) or (sub.end_at > now)

    return {
        "staff_role": role,
        "has_multiple_branch":has_multiple_branch,
        "is_admin_role": role in (GymStaff.ROLE_ADMIN, GymStaff.ROLE_OWNER),
        "saas": {
            "gym_id": gym_id,
            "status": "active" if active else "expired",
            "active": active,
            "message": (
                f"Plan: {sub.plan.name}. Active."
                if active else
                f"Plan: {sub.plan.name}. EXPIRED — renew to restore access control."
            ),
            "end_at": sub.end_at,
            "plan_name": sub.plan.name,
        }
    }