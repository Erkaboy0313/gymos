import pytest
from rest_framework.test import APIClient

from users.models import Gym, Member
from users.services import make_tg_session


@pytest.mark.django_db
def test_link_phone_links_across_multiple_gyms():
    g1 = Gym.objects.create(name="G1")
    g2 = Gym.objects.create(name="G2")

    phone = "+998901234567"
    m1 = Member.objects.create(gym=g1, full_name="A", phone=phone, is_active=True)
    m2 = Member.objects.create(gym=g2, full_name="B", phone=phone, is_active=True)

    tg_id = 111
    session = make_tg_session(tg_id)

    client = APIClient()
    r = client.post(
        "/api/users/me/link-phone/",
        {"phone": phone},
        format="json",
        HTTP_X_MEMBER_SESSION=session,
    )

    assert r.status_code == 200
    data = r.json()
    assert set(data["linked"]) == {m1.id, m2.id}
    assert data["blocked"] == []
    assert data["not_found"] is False

    m1.refresh_from_db()
    m2.refresh_from_db()
    assert m1.telegram_user_id == tg_id
    assert m2.telegram_user_id == tg_id


@pytest.mark.django_db
def test_link_phone_blocks_if_already_linked_to_other_tg():
    g1 = Gym.objects.create(name="G1")

    phone = "+998901234567"
    m = Member.objects.create(gym=g1, full_name="A", phone=phone, is_active=True, telegram_user_id=999)

    tg_id = 111
    session = make_tg_session(tg_id)

    client = APIClient()
    r = client.post(
        "/api/users/me/link-phone/",
        {"phone": phone},
        format="json",
        HTTP_X_MEMBER_SESSION=session,
    )

    assert r.status_code == 200
    data = r.json()
    assert data["linked"] == []
    assert data["blocked"] == [m.id]

    m.refresh_from_db()
    assert m.telegram_user_id == 999


@pytest.mark.django_db
def test_link_phone_404_when_phone_not_found():
    tg_id = 111
    session = make_tg_session(tg_id)

    client = APIClient()
    r = client.post(
        "/api/users/me/link-phone/",
        {"phone": "+998909999999"},
        format="json",
        HTTP_X_MEMBER_SESSION=session,
    )
    assert r.status_code == 404