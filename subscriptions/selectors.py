from django.utils import timezone
from subscriptions.models import GymSubscription
from subscriptions.saas import FEATURES_BY_PLAN_CODE, SaaSFeatures
from subscriptions.models import MemberSubscription
from datetime import timedelta

def get_gym_features(gym_id: int) -> SaaSFeatures:
    now = timezone.now()
    sub = (
        GymSubscription.objects
        .filter(gym_id=gym_id)
        .select_related("plan")
        .order_by("-start_at", "-id")
        .first()
    )

    # If no subscription or expired -> treat as "starter" features OR strict lock.
    # IMPORTANT: you already block access at gate when inactive. Here we only limit admin ops.
    if not sub:
        return FEATURES_BY_PLAN_CODE["starter"]

    active = (sub.end_at is None) or (sub.end_at > now)
    if not active:
        return FEATURES_BY_PLAN_CODE["starter"]

    code = getattr(sub.plan, "code", None)
    return FEATURES_BY_PLAN_CODE.get(code, FEATURES_BY_PLAN_CODE["starter"])


def expiring_members_for_day(gym_id: int, days_before: int):
    today = timezone.localdate()
    target_date = today + timedelta(days=days_before)

    qs = (
        MemberSubscription.objects
        .filter(
            member__gym_id=gym_id,
            member__is_active=True,
            member__telegram_user_id__isnull=False,
            start_at__lte=today,
            end_at__gte=today,
            end_at=target_date,
        )
        .select_related("member", "plan")
        .only(
            "end_at",
            "member__id",
            "member__telegram_user_id",
            "plan__name",
        )
    )

    return [
        {
            "member": s.member,
            "end_at": s.end_at,
            "plan_name": s.plan.name,
        }
        for s in qs
    ]

