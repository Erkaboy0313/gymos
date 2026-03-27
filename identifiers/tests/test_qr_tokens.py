import pytest
import time

from identifiers.services import generate_member_qr_token, verify_member_qr_token


@pytest.mark.django_db
def test_qr_token_roundtrip_ok():
    token = generate_member_qr_token(gym_id=1, member_id=99)
    ok, payload, reason = verify_member_qr_token(token)

    assert ok is True
    assert reason == "ok"
    assert payload["g"] == 1
    assert payload["m"] == 99
    assert isinstance(payload["ts"], int)


@pytest.mark.django_db
def test_qr_token_tamper_fails_signature():
    token = generate_member_qr_token(gym_id=1, member_id=99)

    # tamper: change one character in payload part
    payload_part, sig_part = token.split(".", 1)
    tampered_payload_part = payload_part[:-1] + ("A" if payload_part[-1] != "A" else "B")

    tampered = tampered_payload_part + "." + sig_part
    ok, payload, reason = verify_member_qr_token(tampered)

    assert ok is False
    assert reason == "badsig"


@pytest.mark.django_db
def test_qr_token_expired():
    token = generate_member_qr_token(gym_id=1, member_id=99)

    # simulate time passing by sleeping just over ttl? too slow.
    # Instead: verify expects current time - ts > TTL, so patch by re-signing with old ts is better,
    # but for simplicity, accept tiny sleep only if TTL is small. If TTL=60, sleeping is trash.
    # So we just assert expiry by constructing an old token using internal functions.

    from identifiers.services import sign_qr_payload
    old_payload = {"g": 1, "m": 99, "ts": int(time.time()) - 9999}
    old_token = sign_qr_payload(old_payload)

    ok, payload, reason = verify_member_qr_token(old_token)
    assert ok is False
    assert reason == "expired"