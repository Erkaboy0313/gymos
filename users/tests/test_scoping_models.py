import pytest
from django.contrib.auth import get_user_model
from users.models import Gym, GymStaff
from branches.models import Branch


@pytest.mark.django_db
def test_user_can_be_staff_in_one_gym_once():
    User = get_user_model()
    u = User.objects.create_user(username="s1", password="x")
    gym = Gym.objects.create(name="Gym A")

    GymStaff.objects.create(gym=gym, user=u, role=GymStaff.ROLE_ADMIN)

    with pytest.raises(Exception):
        # unique_together should break
        GymStaff.objects.create(gym=gym, user=u, role=GymStaff.ROLE_STAFF)


@pytest.mark.django_db
def test_branch_belongs_to_gym():
    gym1 = Gym.objects.create(name="Gym A")
    gym2 = Gym.objects.create(name="Gym B")

    b1 = Branch.objects.create(gym=gym1, name="Branch 1")
    b2 = Branch.objects.create(gym=gym2, name="Branch 1")

    assert b1.gym_id != b2.gym_id


@pytest.mark.django_db
def test_branch_name_unique_per_gym():
    gym1 = Gym.objects.create(name="Gym A")
    Branch.objects.create(gym=gym1, name="Main")

    with pytest.raises(Exception):
        Branch.objects.create(gym=gym1, name="Main")
        



