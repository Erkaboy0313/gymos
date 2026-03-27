import pytest
from datetime import timedelta
from django.utils import timezone

from users.models import Gym
from subscriptions.models import GymPlan, GymSubscription
from subscriptions.services import is_gym_active


@pytest.mark.django_db
def test_gym_inactive_when_no_subscription():
    gym = Gym.objects.create(name="G1")
    now = timezone.now()
    assert is_gym_active(gym, now) is False


@pytest.mark.django_db
def test_gym_active_with_valid_timed_subscription():
    gym = Gym.objects.create(name="G1")
    plan = GymPlan.objects.create(name="SaaS Monthly", duration_days=30, price=500000)

    now = timezone.now()
    GymSubscription.objects.create(
        gym=gym,
        plan=plan,
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=29),
    )

    assert is_gym_active(gym, now) is True


@pytest.mark.django_db
def test_gym_inactive_when_expired():
    gym = Gym.objects.create(name="G1")
    plan = GymPlan.objects.create(name="SaaS Monthly", duration_days=30, price=500000)

    now = timezone.now()
    GymSubscription.objects.create(
        gym=gym,
        plan=plan,
        start_at=now - timedelta(days=40),
        end_at=now - timedelta(days=10),
    )

    assert is_gym_active(gym, now) is False


@pytest.mark.django_db
def test_gym_active_with_lifetime_subscription_end_at_null():
    gym = Gym.objects.create(name="G1")
    plan = GymPlan.objects.create(name="Lifetime", duration_days=0, price=5000000)

    now = timezone.now()
    GymSubscription.objects.create(
        gym=gym,
        plan=plan,
        start_at=now - timedelta(days=1),
        end_at=None,  # lifetime
    )

    assert is_gym_active(gym, now) is True
    assert is_gym_active(gym, now + timedelta(days=3650)) is True  # ~10 years later