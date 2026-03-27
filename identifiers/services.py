import base64,hmac,hashlib,json,time
from typing import Tuple
from django.conf import settings
from identifiers.constants import QR_TTL_SECONDS

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + pad).encode("ascii"))

def sign_qr_payload(payload: dict) -> str:
    """
    Returns token: base64url(payload_json) + "." + base64url(sig)
    """
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), raw, hashlib.sha256).digest()
    return f"{_b64url_encode(raw)}.{_b64url_encode(sig)}"

def generate_member_qr_token(gym_id: int, member_id: int) -> str:
    payload = {
        "g": gym_id,
        "m": member_id,
        "ts": int(time.time()),
    }
    return sign_qr_payload(payload)

def verify_member_qr_token(token: str) -> Tuple[bool, dict, str]:
    """
    Returns: (ok, payload, reason)
    reason in: ok, format, badsig, expired
    """
    try:
        part_payload, part_sig = token.split(".", 1)
        raw = _b64url_decode(part_payload)
        sig = _b64url_decode(part_sig)
    except Exception:
        return False, {}, "format"

    expected = hmac.new(settings.SECRET_KEY.encode("utf-8"), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return False, {}, "badsig"

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return False, {}, "format"

    ts = payload.get("ts")
    if not isinstance(ts, int):
        return False, {}, "format"

    now = int(time.time())
    if now - ts > QR_TTL_SECONDS:
        return False, payload, "expired"

    return True, payload, "ok"
