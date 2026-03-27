import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Gym, GymStaff, Member
from branches.models import Branch

@pytest.mark.django_db
def test_member_list_filters_active_and_search_and_branch():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)

    b1 = Branch.objects.create(gym=gym, name="B1")
    b2 = Branch.objects.create(gym=gym, name="B2")

    Member.objects.create(gym=gym, branch=b1, full_name="Ali Vali", phone="+998901111111", is_active=True)
    Member.objects.create(gym=gym, branch=b2, full_name="Bob", phone="+998902222222", is_active=False)
    Member.objects.create(gym=gym, branch=b1, full_name="Aziz", phone="+998903333333", is_active=True)

    client = APIClient()
    client.force_authenticate(user=staff)

    # active only
    r = client.get(f"/api/users/gyms/{gym.id}/members/?is_active=true")
    assert r.status_code == 200
    assert len(r.json()) == 2

    # branch filter
    r = client.get(f"/api/users/gyms/{gym.id}/members/?branch_id={b2.id}")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["full_name"] == "Bob"

    # search by name
    r = client.get(f"/api/users/gyms/{gym.id}/members/?q=Ali")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # search by phone partial
    r = client.get(f"/api/users/gyms/{gym.id}/members/?q=3333")
    assert r.status_code == 200
    assert len(r.json()) == 1