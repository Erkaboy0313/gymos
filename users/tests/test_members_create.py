import pytest
from django.test import Client
from django.contrib.auth import get_user_model

from users.models import Gym, GymStaff, Member
from branches.models import Branch



@pytest.mark.django_db
def test_member_create_duplicate_phone_handled_cleanly():
    User = get_user_model()
    admin = User.objects.create_user(username="a", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=admin, role=GymStaff.ROLE_ADMIN, is_active=True)
    branch = Branch.objects.create(gym=gym, name="Main")

    Member.objects.create(gym=gym, branch=branch, full_name="Ali", phone="+998901234567", is_active=True)

    c = Client()
    c.force_login(admin)

    r = c.post(f"/api/users/app/gyms/{gym.id}/members/create/", {
        "full_name": "Vali",
        "phone": "+998901234567",
        "branch_id": branch.id,
    })

    assert r.status_code in (302, 303)
    assert Member.objects.filter(gym=gym, phone="+998901234567").count() == 1