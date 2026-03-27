import pytest
from users.models import Gym, Member
from users.services import link_member_telegram


@pytest.mark.django_db
def test_link_member_telegram_ok_and_idempotent():
    gym = Gym.objects.create(name="G1")
    m = Member.objects.create(
        gym=gym,
        full_name="Ali",
        phone="+998901234567",
        is_active=True,
        telegram_user_id=None,
    )

    r1 = link_member_telegram(gym.id, "+998901234567", 111)
    assert r1 == "ok"
    m.refresh_from_db()
    assert m.telegram_user_id == 111

    # idempotent
    r2 = link_member_telegram(gym.id, "90 123 45 67", 111)
    assert r2 == "ok"
    m.refresh_from_db()
    assert m.telegram_user_id == 111


@pytest.mark.django_db
def test_link_member_telegram_not_found():
    gym = Gym.objects.create(name="G1")
    r = link_member_telegram(gym.id, "+998901234567", 111)
    assert r == "not_found"


@pytest.mark.django_db
def test_link_member_telegram_inactive_member():
    gym = Gym.objects.create(name="G1")
    Member.objects.create(
        gym=gym,
        full_name="Ali",
        phone="+998901234567",
        is_active=False,
    )
    r = link_member_telegram(gym.id, "+998901234567", 111)
    assert r == "inactive"


@pytest.mark.django_db
def test_link_member_telegram_denies_if_already_linked_to_other():
    gym = Gym.objects.create(name="G1")
    m = Member.objects.create(
        gym=gym,
        full_name="Ali",
        phone="+998901234567",
        is_active=True,
        telegram_user_id=222,
    )

    r = link_member_telegram(gym.id, "+998901234567", 111)
    assert r == "already_linked_other"
    m.refresh_from_db()
    assert m.telegram_user_id == 222  # unchanged