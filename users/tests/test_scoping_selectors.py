import pytest
from django.contrib.auth import get_user_model
from users.models import Gym, GymStaff
from branches.models import Branch
from users.selectors import gyms_for_user, staff_membership, branches_for_user


@pytest.mark.django_db
def test_gyms_for_user_returns_only_user_gyms():
    User = get_user_model()
    u1 = User.objects.create_user(username="u1", password="x")
    u2 = User.objects.create_user(username="u2", password="x")

    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")

    GymStaff.objects.create(gym=g1, user=u1, role=GymStaff.ROLE_ADMIN)
    GymStaff.objects.create(gym=g2, user=u2, role=GymStaff.ROLE_ADMIN)

    ids = set(gyms_for_user(u1).values_list("id", flat=True))
    assert ids == {g1.id}


@pytest.mark.django_db
def test_staff_membership_none_if_not_member_or_inactive():
    User = get_user_model()
    u1 = User.objects.create_user(username="u1", password="x")
    g1 = Gym.objects.create(name="G1")

    assert staff_membership(u1, g1.id) is None

    ms = GymStaff.objects.create(gym=g1, user=u1, role=GymStaff.ROLE_STAFF, is_active=False)
    assert staff_membership(u1, g1.id) is None

    ms.is_active = True
    ms.save()
    assert staff_membership(u1, g1.id) is not None


@pytest.mark.django_db
def test_branches_for_user_scoped_to_gym_membership():
    User = get_user_model()
    u1 = User.objects.create_user(username="u1", password="x")

    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")

    b11 = Branch.objects.create(gym=g1, name="B1")
    Branch.objects.create(gym=g2, name="B2")

    # No membership => no branches
    assert branches_for_user(u1, g1.id).count() == 0

    GymStaff.objects.create(gym=g1, user=u1, role=GymStaff.ROLE_ADMIN)

    ids = set(branches_for_user(u1, g1.id).values_list("id", flat=True))
    assert ids == {b11.id}