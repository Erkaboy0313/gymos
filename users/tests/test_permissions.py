import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from users.models import Gym, GymStaff
from users.permissions import require_gym_membership


@pytest.mark.django_db
def test_require_gym_membership_denies_if_not_member():
    User = get_user_model()
    u = User.objects.create_user(username="u", password="x")
    g = Gym.objects.create(name="G1")

    with pytest.raises(PermissionDenied):
        require_gym_membership(u, g.id)


@pytest.mark.django_db
def test_require_gym_membership_allows_if_member():
    User = get_user_model()
    u = User.objects.create_user(username="u", password="x")
    g = Gym.objects.create(name="G1")

    GymStaff.objects.create(gym=g, user=u, role=GymStaff.ROLE_ADMIN)

    ms = require_gym_membership(u, g.id)
    assert ms.gym_id == g.id
    assert ms.user_id == u.id