import pytest
from datetime import timedelta
from django.utils import timezone

from users.models import Gym, Member
from subscriptions.models import MemberPlan
from subscriptions.services import create_subscription


@pytest.mark.django_db
def test_early_renew_extends_from_current_end():
    gym = Gym.objects.create(name="G1")
    m = Member.objects.create(gym=gym, full_name="Ali", phone="+998901234567", is_active=True)
    plan = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100)

    now = timezone.now().date()

    s1 = create_subscription(m, plan, start_at=now - timedelta(days=1))
    assert s1.start_at < now < s1.end_at

    s2 = create_subscription(m, plan)  # early renew
    assert s2.start_at == s1.end_at
    assert s2.end_at == s2.start_at + timedelta(days=30)


@pytest.mark.django_db
def test_new_subscription_starts_now_if_no_active():
    gym = Gym.objects.create(name="G1")
    m = Member.objects.create(gym=gym, full_name="Ali", phone="+998901234567", is_active=True)
    plan = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100)

    now = timezone.now()
    s = create_subscription(m, plan, start_at=now)
    # allow small timing drift, just assert it's close
    assert abs((s.start_at - now).total_seconds()) < 5