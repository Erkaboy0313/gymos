import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Gym, GymStaff, Member

@pytest.mark.django_db
def test_staff_can_block_and_unblock_member():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    m = Member.objects.create(gym=gym, full_name="Ali", phone="+998901112233", is_active=True)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/users/gyms/{gym.id}/members/{m.id}/block/", {"is_active": False}, format="json")
    assert r.status_code == 200
    m.refresh_from_db()
    assert m.is_active is False

    r = client.post(f"/api/users/gyms/{gym.id}/members/{m.id}/block/", {"is_active": True}, format="json")
    assert r.status_code == 200
    m.refresh_from_db()
    assert m.is_active is True