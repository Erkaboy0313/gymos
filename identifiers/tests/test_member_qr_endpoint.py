import pytest
from rest_framework.test import APIClient

from users.models import Gym, Member
from users.services import make_tg_session
from identifiers.services import verify_member_qr_token


@pytest.mark.django_db
def test_member_qr_token_requires_gym_id_and_membership():
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")

    tg_id = 888
    m1 = Member.objects.create(gym=g1, full_name="Ali", phone="+998901234567", is_active=True, telegram_user_id=tg_id)
    Member.objects.create(gym=g2, full_name="Other", phone="+998907777777", is_active=True, telegram_user_id=999)

    session = make_tg_session(tg_id)
    client = APIClient()

    # missing gym_id
    r = client.post("/api/identifiers/member/qr-token/", {}, format="json", HTTP_X_MEMBER_SESSION=session)
    assert r.status_code == 400

    # gym where user not linked
    r = client.post("/api/identifiers/member/qr-token/", {"gym_id": g2.id}, format="json", HTTP_X_MEMBER_SESSION=session)
    assert r.status_code == 404

    # correct gym
    r = client.post("/api/identifiers/member/qr-token/", {"gym_id": g1.id}, format="json", HTTP_X_MEMBER_SESSION=session)
    assert r.status_code == 200
    token = r.json()["token"]

    ok, payload, reason = verify_member_qr_token(token)
    assert ok is True
    assert reason == "ok"
    assert payload["g"] == g1.id
    assert payload["m"] == m1.id