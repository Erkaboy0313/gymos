import pytest
from datetime import timedelta
from django.utils import timezone

from users.models import Gym, Member
from subscriptions.models import MemberPlan, FreezePeriod
from subscriptions.services import create_subscription, is_member_active


@pytest.mark.django_db
def test_member_active_with_valid_subscription():
    gym = Gym.objects.create(name="G1")
    m = Member.objects.create(gym=gym, full_name="Ali", phone="+998901234567", is_active=True)
    plan = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100)

    now = timezone.now()
    create_subscription(m, plan, start_at=now - timedelta(days=1))

    assert is_member_active(m, now) is True


@pytest.mark.django_db
def test_member_inactive_even_with_subscription():
    gym = Gym.objects.create(name="G1")
    m = Member.objects.create(gym=gym, full_name="Ali", phone="+998901234567", is_active=False)
    plan = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100)

    now = timezone.now()
    create_subscription(m, plan, start_at=now - timedelta(days=1))

    assert is_member_active(m, now) is False


@pytest.mark.django_db
def test_member_not_active_when_subscription_expired():
    gym = Gym.objects.create(name="G1")
    m = Member.objects.create(gym=gym, full_name="Ali", phone="+998901234567", is_active=True)
    plan = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100)

    past = timezone.now() - timedelta(days=40)
    create_subscription(m, plan, start_at=past)

    now = timezone.now()
    assert is_member_active(m, now) is False


@pytest.mark.django_db
def test_freeze_blocks_access_even_if_subscription_active_v1_rule():
    gym = Gym.objects.create(name="G1")
    m = Member.objects.create(gym=gym, full_name="Ali", phone="+998901234567", is_active=True)
    plan = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100)

    now = timezone.now()
    member_sub = create_subscription(m, plan, start_at=now - timedelta(days=1))
    
    member_sub.frozen_until = now + timedelta(days=1)
    member_sub.save()

    assert is_member_active(m, now) is False