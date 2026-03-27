import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from users.models import Gym, GymStaff, Member
from branches.models import Branch


@pytest.mark.django_db
def test_dashboard_current_inside_count():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")

    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    branch = Branch.objects.create(gym=gym, name="Main")

    Member.objects.create(gym=gym, branch=branch, full_name="A", phone="+998901111111", is_active=True, is_inside=True)
    Member.objects.create(gym=gym, branch=branch, full_name="B", phone="+998902222222", is_active=True, is_inside=False)
    Member.objects.create(gym=gym, branch=branch, full_name="C", phone="+998903333333", is_active=False, is_inside=True)  # ignored

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.get(f"/api/dashboard/gyms/{gym.id}/overview/")
    assert r.status_code == 200
    assert r.json()["current_inside_count"] == 1