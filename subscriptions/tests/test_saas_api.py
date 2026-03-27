import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Gym, GymStaff
from subscriptions.models import GymSubscription


@pytest.mark.django_db
def test_staff_can_create_saas_plan_and_subscription_timed():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/subscriptions/gyms/{gym.id}/saas/plans/", {
        "name": "SaaS Monthly",
        "duration_days": 30,
        "price": "500000.00",
        "is_active": True,
    }, format="json")
    assert r.status_code == 201
    plan_id = r.json()["id"]

    r = client.post(f"/api/subscriptions/gyms/{gym.id}/saas/subscriptions/", {
        "plan_id": plan_id
    }, format="json")
    assert r.status_code == 201
    assert GymSubscription.objects.filter(gym=gym).count() == 1


@pytest.mark.django_db
def test_staff_can_create_lifetime_saas_subscription_end_at_null():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/subscriptions/gyms/{gym.id}/saas/plans/", {
        "name": "Lifetime",
        "duration_days": 0,
        "price": "5000000.00",
        "is_active": True,
    }, format="json")
    assert r.status_code == 201
    plan_id = r.json()["id"]

    r = client.post(f"/api/subscriptions/gyms/{gym.id}/saas/subscriptions/", {
        "plan_id": plan_id,
        "end_at": None
    }, format="json")
    assert r.status_code == 201

    sub = GymSubscription.objects.get(gym=gym)
    assert sub.end_at is None


@pytest.mark.django_db
def test_staff_cannot_manage_other_gym_saas():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")
    GymStaff.objects.create(gym=g1, user=staff, role=GymStaff.ROLE_ADMIN)

    client = APIClient()
    client.force_authenticate(user=staff)

    # try to create subscription for g2 (should be forbidden)
    r = client.post(f"/api/subscriptions/gyms/{g2.id}/saas/subscriptions/", {"plan_id": 999}, format="json")
    assert r.status_code == 403