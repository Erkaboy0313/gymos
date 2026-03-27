import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Gym, GymStaff


@pytest.mark.django_db
def test_staff_can_create_and_list_branches_scoped():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/branches/gyms/{gym.id}/branches/", {"name": "Main", "address": "Tashkent"}, format="json")
    assert r.status_code == 201
    assert r.json()["name"] == "Main"

    r = client.get(f"/api/branches/gyms/{gym.id}/branches/")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.django_db
def test_staff_cannot_access_other_gym_branches():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")
    GymStaff.objects.create(gym=g1, user=staff, role=GymStaff.ROLE_ADMIN)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.get(f"/api/branches/gyms/{g2.id}/branches/")
    assert r.status_code == 403