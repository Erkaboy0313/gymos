import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from users.models import Gym, GymStaff, Member
from branches.models import Branch
from devices.models import Device
from subscriptions.models import GymPlan, GymSubscription, MemberPlan
from subscriptions.services import create_subscription
from identifiers.services import generate_member_qr_token


@pytest.mark.django_db
def test_cooldown_blocks_second_entry_within_window():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")

    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    branch = Branch.objects.create(gym=gym, name="Main")
    device = Device.objects.create(branch=branch, name="Gate 1", mode=Device.MODE_KIOSK, cooldown_seconds=300)

    # SaaS active
    gp = GymPlan.objects.create(name="SaaS Monthly", duration_days=30, price=500000, is_active=True)
    now = timezone.now()
    GymSubscription.objects.create(gym=gym, plan=gp, start_at=now - timedelta(days=1), end_at=now + timedelta(days=29))

    # Member active sub
    member = Member.objects.create(gym=gym, branch=branch, full_name="Ali", phone="+998901234567", is_active=True)
    mp = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100, is_active=True)
    create_subscription(member, mp, start_at=now - timedelta(days=1))

    token = generate_member_qr_token(gym_id=gym.id, member_id=member.id)

    client = APIClient()
    client.force_authenticate(user=staff)

    # First entry allowed
    r1 = client.post(f"/api/access/gyms/{gym.id}/devices/{device.id}/kiosk/validate/", {"token": token}, format="json")
    assert r1.status_code == 200
    assert r1.json()["allow"] is True

    # Second entry blocked by cooldown
    token2 = generate_member_qr_token(gym_id=gym.id, member_id=member.id)
    r2 = client.post(f"/api/access/gyms/{gym.id}/devices/{device.id}/kiosk/validate/", {"token": token2}, format="json")
    assert r2.status_code == 200
    assert r2.json()["allow"] is False
    assert r2.json()["reason"] == "cooldown_active"