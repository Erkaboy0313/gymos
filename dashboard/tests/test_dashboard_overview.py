import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from users.models import Gym, GymStaff, Member
from branches.models import Branch
from devices.models import Device
from access.models import EntryLog
from subscriptions.models import MemberPlan
from subscriptions.services import create_subscription


@pytest.mark.django_db
def test_dashboard_overview_counts_scoped():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    branch = Branch.objects.create(gym=gym, name="Main")
    device = Device.objects.create(branch=branch, name="Gate 1")

    m1 = Member.objects.create(gym=gym, branch=branch, full_name="A", phone="+998901111111", is_active=True)
    m2 = Member.objects.create(gym=gym, branch=branch, full_name="B", phone="+998902222222", is_active=True)

    # One entry today
    EntryLog.objects.create(gym=gym, branch=branch, device=device, event = EntryLog.EVENT_IN, member=m1, allow=True, reason="ok")

    # Expiring soon
    plan = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100, is_active=True)
    now = timezone.now()
    create_subscription(m1, plan, start_at=now - timedelta(days=25))  # ends in ~5 days

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.get(f"/api/dashboard/gyms/{gym.id}/overview/?days=7")
    assert r.status_code == 200
    data = r.json()

    assert data["active_members_count"] == 2
    assert data["today_entries_count"] == 1
    assert data["expiring_soon_count"] == 1


@pytest.mark.django_db
def test_dashboard_denies_other_gym():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")
    GymStaff.objects.create(gym=g1, user=staff, role=GymStaff.ROLE_ADMIN)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.get(f"/api/dashboard/gyms/{g2.id}/overview/")
    assert r.status_code == 403