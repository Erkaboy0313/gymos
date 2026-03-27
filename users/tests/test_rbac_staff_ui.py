import pytest
from django.test import Client
from django.contrib.auth import get_user_model

from users.models import Gym, GymStaff


@pytest.mark.django_db
def test_staff_cannot_access_admin_only_pages():
    User = get_user_model()
    u = User.objects.create_user(username="staff", password="x")
    gym = Gym.objects.create(name="G1")
    GymStaff.objects.create(gym=gym, user=u, role=GymStaff.ROLE_STAFF, is_active=True)

    c = Client()
    c.force_login(u)

    assert c.get(f"/api/branches/app/gyms/{gym.id}/branches/").status_code in (403, 302)
    assert c.get(f"/api/subscriptions/app/gyms/{gym.id}/plans/").status_code in (403, 302)

    # allowed pages
    assert c.get(f"/api/users/app/gyms/{gym.id}/members/").status_code == 200
    assert c.get(f"/api/subscriptions/app/gyms/{gym.id}/renew/").status_code == 200