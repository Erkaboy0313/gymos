import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Gym, GymStaff
from branches.models import Branch
from devices.models import Device


@pytest.mark.django_db
def test_staff_can_create_and_list_devices_scoped():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    branch = Branch.objects.create(gym=gym, name="Main")

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/devices/gyms/{gym.id}/devices/", {
        "branch": branch.id,
        "name": "Gate 1",
        "mode": Device.MODE_KIOSK,
        "cooldown_seconds": 300,
        "is_active": True,
    }, format="json")
    assert r.status_code == 201
    assert r.json()["name"] == "Gate 1"

    r = client.get(f"/api/devices/gyms/{gym.id}/devices/")
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.django_db
def test_staff_cannot_create_device_in_other_gym_branch():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")
    GymStaff.objects.create(gym=g1, user=staff, role=GymStaff.ROLE_ADMIN)

    other_branch = Branch.objects.create(gym=g2, name="Other")

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/devices/gyms/{g1.id}/devices/", {
        "branch": other_branch.id,
        "name": "Hacker Gate",
        "mode": Device.MODE_KIOSK,
        "cooldown_seconds": 300,
        "is_active": True,
    }, format="json")

    assert r.status_code == 400


@pytest.mark.django_db
def test_staff_can_update_device():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    branch = Branch.objects.create(gym=gym, name="Main")
    d = Device.objects.create(branch=branch, name="Gate 1", mode=Device.MODE_KIOSK, cooldown_seconds=300)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.patch(f"/api/devices/gyms/{gym.id}/devices/{d.id}/", {"cooldown_seconds": 120}, format="json")
    assert r.status_code == 200
    assert r.json()["cooldown_seconds"] == 120