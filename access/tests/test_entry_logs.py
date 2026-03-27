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
from access.models import EntryLog


@pytest.mark.django_db
def test_entry_log_created_on_allow():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")

    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    branch = Branch.objects.create(gym=gym, name="Main")
    device = Device.objects.create(branch=branch, name="Gate 1", mode=Device.MODE_KIOSK)

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
    r = client.post(f"/api/access/gyms/{gym.id}/devices/{device.id}/kiosk/validate/", {"token": token}, format="json")
    assert r.status_code == 200
    assert r.json()["allow"] is True

    log = EntryLog.objects.order_by("-id").first()
    assert log is not None
    assert log.allow is True
    assert log.reason == "ok"
    assert log.member_id == member.id


@pytest.mark.django_db
def test_entry_log_created_on_deny():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")

    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    branch = Branch.objects.create(gym=gym, name="Main")
    device = Device.objects.create(branch=branch, name="Gate 1", mode=Device.MODE_KIOSK)

    # Deny because no saas subscription
    member = Member.objects.create(gym=gym, branch=branch, full_name="Ali", phone="+998901234567", is_active=True)
    token = generate_member_qr_token(gym_id=gym.id, member_id=member.id)

    client = APIClient()
    client.force_authenticate(user=staff)
    r = client.post(f"/api/access/gyms/{gym.id}/devices/{device.id}/kiosk/validate/", {"token": token}, format="json")
    assert r.status_code == 200
    assert r.json()["allow"] is False

    log = EntryLog.objects.order_by("-id").first()
    assert log is not None
    assert log.allow is False
    assert log.reason == "gym_subscription_inactive"