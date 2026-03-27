import pytest
from rest_framework.test import APIClient

from users.models import Gym, Member
from users.services import make_tg_session


@pytest.mark.django_db
def test_me_gyms_lists_all_linked_gyms():
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")

    tg_id = 777

    m1 = Member.objects.create(gym=g1, full_name="A", phone="+998901111111", is_active=True, telegram_user_id=tg_id)
    m2 = Member.objects.create(gym=g2, full_name="B", phone="+998902222222", is_active=True, telegram_user_id=tg_id)

    session = make_tg_session(tg_id)

    client = APIClient()
    r = client.get("/api/users/me/gyms/", HTTP_X_MEMBER_SESSION=session)

    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert {x["gym_id"] for x in data} == {g1.id, g2.id}
    assert {x["member_id"] for x in data} == {m1.id, m2.id}