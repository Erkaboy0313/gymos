import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Gym, GymStaff, Member
from branches.models import Branch


@pytest.mark.django_db
def test_staff_can_create_member_in_own_gym():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=staff, role=GymStaff.ROLE_ADMIN)
    b = Branch.objects.create(gym=gym, name="Main")

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/users/gyms/{gym.id}/members/", {
        "full_name": "Ali Vali",
        "phone": "+998901112233",
        "branch": b.id
    }, format="json")

    assert r.status_code == 201
    assert Member.objects.filter(gym=gym, phone="+998901112233").exists()


@pytest.mark.django_db
def test_staff_cannot_create_member_in_other_gym():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")
    GymStaff.objects.create(gym=g1, user=staff, role=GymStaff.ROLE_ADMIN)

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/users/gyms/{g2.id}/members/", {
        "full_name": "Hacker",
        "phone": "+998900000000"
    }, format="json")

    assert r.status_code == 403


@pytest.mark.django_db
def test_phone_unique_per_gym_but_allowed_across_gyms():
    User = get_user_model()
    staff1 = User.objects.create_user(username="s1", password="x")
    staff2 = User.objects.create_user(username="s2", password="x")
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")
    GymStaff.objects.create(gym=g1, user=staff1, role=GymStaff.ROLE_ADMIN)
    GymStaff.objects.create(gym=g2, user=staff2, role=GymStaff.ROLE_ADMIN)
    branch = Branch.objects.create(gym = g1)
    c1 = APIClient(); c1.force_authenticate(user=staff1)
    c2 = APIClient(); c2.force_authenticate(user=staff2)

    phone = "+998901234567"

    assert c1.post(f"/api/users/gyms/{g1.id}/members/", {"full_name": "A", "phone": phone, "branch": branch.id}, format="json").status_code == 201
    assert c2.post(f"/api/users/gyms/{g2.id}/members/", {"full_name": "B", "phone": phone}, format="json").status_code == 201

    # same gym duplicate should fail (db constraint -> 400)
    r = c1.post(f"/api/users/gyms/{g1.id}/members/", {"full_name": "C", "phone": phone,"branch": branch.id}, format="json")
    assert r.status_code in (400, 409)


@pytest.mark.django_db
def test_branch_must_belong_to_gym():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")
    GymStaff.objects.create(gym=g1, user=staff, role=GymStaff.ROLE_ADMIN)

    other_branch = Branch.objects.create(gym=g2, name="OtherGymBranch")

    client = APIClient()
    client.force_authenticate(user=staff)

    r = client.post(f"/api/users/gyms/{g1.id}/members/", {
        "full_name": "Ali",
        "phone": "+998909999999",
        "branch": other_branch.id
    }, format="json")

    assert r.status_code == 400
    
@pytest.mark.django_db
def test_phone_normalization_prevents_format_duplicates_same_gym():
    User = get_user_model()
    staff = User.objects.create_user(username="s", password="x")
    g = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=g, user=staff, role=GymStaff.ROLE_ADMIN)
    branch = Branch.objects.create(gym = g)
    client = APIClient()
    client.force_authenticate(user=staff)

    assert client.post(
        f"/api/users/gyms/{g.id}/members/",
        {"full_name": "A", "phone": "90 123 45 67","branch":branch.id},
        format="json",
    ).status_code == 201

    r = client.post(
        f"/api/users/gyms/{g.id}/members/",
        {"full_name": "B", "phone": "+998901234567","branch":branch.id},
        format="json",
    )
    assert r.status_code in (400, 409)
