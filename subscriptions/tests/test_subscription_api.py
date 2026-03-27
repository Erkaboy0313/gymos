import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Gym, GymStaff, Member
from subscriptions.models import MemberPlan, MemberSubscription


@pytest.mark.django_db
def test_staff_can_create_plan_and_subscription_scoped():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    m = Member.objects.create(gym=gym, full_name="Ali", phone="+998901234567", is_active=True)

    client = APIClient()
    client.force_authenticate(user=staff)

    # create plan
    r = client.post(f"/api/subscriptions/gyms/{gym.id}/plans/", {
        "name": "Monthly",
        "duration_days": 30,
        "price": "100000.00",
        "is_active": True,
    }, format="json")
    assert r.status_code == 201
    plan_id = r.json()["id"]

    # create member subscription
    r = client.post(f"/api/subscriptions/gyms/{gym.id}/subscriptions/", {
        "member_id": m.id,
        "plan_id": plan_id,
    }, format="json")
    assert r.status_code == 201
    assert MemberSubscription.objects.filter(member=m).count() == 1


@pytest.mark.django_db
def test_staff_cannot_create_subscription_for_other_gym_member():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")

    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")
    GymStaff.objects.create(gym=g1, user=staff, role=GymStaff.ROLE_ADMIN)

    m2 = Member.objects.create(gym=g2, full_name="Other", phone="+998909999999", is_active=True)
    p1 = MemberPlan.objects.create(gym=g1, name="Monthly", duration_days=30, price=100, is_active=True)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/subscriptions/gyms/{g1.id}/subscriptions/", {
        "member_id": m2.id,
        "plan_id": p1.id,
    }, format="json")

    assert r.status_code == 400