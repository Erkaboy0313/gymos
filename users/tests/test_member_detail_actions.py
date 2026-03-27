import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import Gym, GymStaff, Member
from branches.models import Branch
from subscriptions.models import MemberPlan, MemberSubscription

@pytest.mark.django_db
def test_member_actions_block_force_checkout_renew_freeze_unfreeze():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")

    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)
    branch = Branch.objects.create(gym=gym, name="Main")

    m = Member.objects.create(
        gym=gym, branch=branch, full_name="Ali", phone="+998901234567",
        is_active=True, is_inside=True, inside_since=timezone.now()
    )
    plan = MemberPlan.objects.create(gym=gym, name="Monthly", duration_days=30, price=100, is_active=True)

    c = Client()
    c.force_login(staff)

    # renew
    r = c.post(f"/api/users/app/gyms/{gym.id}/members/{m.id}/action/", {"action": "renew", "plan_id": plan.id})
    assert r.status_code in (302, 303)
    sub = MemberSubscription.objects.filter(member=m).order_by("-id").first()
    assert sub is not None

    # freeze
    r = c.post(f"/api/users/app/gyms/{gym.id}/members/{m.id}/action/", {"action": "freeze", "freeze_days": "3"})
    assert r.status_code in (302, 303)
    sub.refresh_from_db()
    assert sub.frozen_until is not None

    # unfreeze
    r = c.post(f"/api/users/app/gyms/{gym.id}/members/{m.id}/action/", {"action": "unfreeze"})
    assert r.status_code in (302, 303)
    sub.refresh_from_db()
    assert sub.frozen_until is None

    # force checkout
    r = c.post(f"/api/users/app/gyms/{gym.id}/members/{m.id}/action/", {"action": "force_checkout"})
    assert r.status_code in (302, 303)
    m.refresh_from_db()
    assert m.is_inside is False
    assert m.inside_since is None

    # block
    r = c.post(f"/api/users/app/gyms/{gym.id}/members/{m.id}/action/", {"action": "toggle_block"})
    assert r.status_code in (302, 303)
    m.refresh_from_db()
    assert m.is_active is False