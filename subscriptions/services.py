from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from subscriptions.models import MemberPlan, MemberSubscription, FreezePeriod, GymSubscription
from users.models import Member
from django.db import IntegrityError
from users.models import Gym
from subscriptions.models import TelegramNotificationLog
from subscriptions.selectors import expiring_members_for_day
from datetime import datetime

def is_frozen(member: Member, at_time=None) -> bool:
    at_time = at_time or timezone.now()
    return FreezePeriod.objects.filter(
        member=member,
        start_at__lte=at_time,
        end_at__gt=at_time,
    ).exists()

def active_subscription(member: Member, at_time=None):
    at_time = at_time or timezone.now()
    return MemberSubscription.objects.filter(
        member=member,
        start_at__lte=at_time,
    ).filter(
        Q(end_at__isnull=True) | Q(end_at__gt=at_time)
    ).order_by("-end_at").first()

def is_member_active(member, at_time=None) -> bool:
    if isinstance(at_time,datetime):
        at_time = at_time.date()    
    
    at_time = at_time or timezone.now().date()

    if not member.is_active:
        return False

    sub = (
        MemberSubscription.objects
        .filter(member=member)
        .order_by("-start_at", "-id")
        .first()
    )
    if not sub:
        return False

    # freeze check
    if sub.frozen_until and sub.frozen_until > at_time:
        return False

    # lifetime
    if sub.end_at is None:
        return True

    return sub.end_at > at_time

@transaction.atomic
def create_subscription(member: Member, plan: MemberPlan, start_at=None) -> MemberSubscription:
    """
    v1 renewal rule:
      - If member has an active subscription now, extend from its end_at.
      - Otherwise start now (or provided start_at).
    """
    now = timezone.now().date()

    current = MemberSubscription.objects.filter(
        member=member,
        start_at__lte=now,
        end_at__gt=now,
    ).order_by("-end_at").first()

    if current:
        start_at = current.end_at
    else:
        start_at = start_at or now

    end_at = start_at + timedelta(days=plan.duration_days)

    return MemberSubscription.objects.create(
        member=member,
        plan=plan,
        start_at=start_at,
        end_at=end_at,
        price_snapshot=plan.price,
    )
    
def is_gym_active(gym, at_time=None) -> bool:
    at_time = at_time or timezone.now()
    return GymSubscription.objects.filter(
        gym=gym,
        start_at__lte=at_time,
    ).filter(
        Q(end_at__isnull=True) | Q(end_at__gt=at_time)
    ).exists()

def format_expiry_message(gym_name: str, days_before: int, plan_name: str, end_at):
    
    end_str = end_at.strftime("%Y-%m-%d")
    if days_before == 0:
        return (
            f"⏰ Your subscription at {gym_name} expires *today*.\n"
            f"Plan: {plan_name}\n"
            f"Renew to avoid blocked entry."
        )
    return (
        f"📅 Your subscription at {gym_name} expires in {days_before} day(s).\n"
        f"End date: {end_str}\n"
        f"Plan: {plan_name}\n"
        f"Renew in advance to keep access."
    )

def send_member_expiry_alerts(send_func, days_list=(0, 3, 7)):
    """
    send_func(chat_id:int, text:str) -> None
    """
    today = timezone.localdate()

    for gym in Gym.objects.all().only("id", "name"):
        for days_before in days_list:
            items = expiring_members_for_day(gym.id, days_before)
            for item in items:
                m = item["member"]
                try:
                    log = TelegramNotificationLog.objects.create(
                        type=TelegramNotificationLog.TYPE_EXPIRY,
                        member_id=m.id,
                        gym_id=gym.id,
                        days_before=days_before,
                        sent_on=today,
                    )
                except IntegrityError:
                    # already sent today
                    continue

                text = format_expiry_message(gym.name, days_before, item["plan_name"], item["end_at"])
                send_func(m.telegram_user_id, text, log)
























