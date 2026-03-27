# import pytest
# from django.test import Client
# from django.contrib.auth import get_user_model

# from users.models import Gym, GymStaff


# @pytest.mark.django_db
# def test_staff_management_admin_only_and_add_staff():
#     User = get_user_model()
#     owner = User.objects.create_user(username="owner", password="x")
#     staff_user = User.objects.create_user(username="staff", password="x")

#     gym = Gym.objects.create(name="G1")
#     GymStaff.objects.create(gym=gym, user=owner, role=GymStaff.ROLE_ADMIN, is_active=True)
#     GymStaff.objects.create(gym=gym, user=staff_user, role=GymStaff.ROLE_STAFF, is_active=True)

#     c = Client()

#     # staff cannot open
#     c.force_login(staff_user)
#     assert c.get(f"/api/users/app/gyms/{gym.id}/staff/").status_code in (403, 302)

#     # admin can open
#     c.force_login(owner)
#     assert c.get(f"/api/users/app/gyms/{gym.id}/staff/").status_code == 200

#     # add another staff
#     r = c.post(f"/api/users/app/gyms/{gym.id}/staff/action/", {
#         "action": "add",
#         "username": "newguy",
#         "password": "x",
#         "role": GymStaff.ROLE_STAFF
#     })
#     assert r.status_code in (302, 303)
#     assert User.objects.filter(username="newguy").exists()
#     assert GymStaff.objects.filter(gym=gym, user__username="newguy").exists()