import re
import time, json, base64, hmac, hashlib
from django.conf import settings
from django.db import transaction
from users.models import Member


@transaction.atomic
def link_phone_to_telegram_across_gyms(raw_phone: str, telegram_user_id: int) -> dict:
    """
    Links ALL members with this phone to telegram_user_id (multi-gym),
    BUT never overwrites a different existing telegram_user_id (fraud rule).

    Returns:
      {
        "linked": [member_id,...],
        "blocked": [member_id,...],  # already linked to another tg id
        "not_found": bool
      }
    """
    phone = normalize_uz_phone(raw_phone)

    qs = Member.objects.select_for_update().filter(phone=phone)
    if not qs.exists():
        return {"linked": [], "blocked": [], "not_found": True}

    linked, blocked = [], []

    for m in qs:
        if not m.is_active:
            # v1: ignore inactive members for linking (don’t leak info)
            continue

        if m.telegram_user_id and m.telegram_user_id != telegram_user_id:
            blocked.append(m.id)
            continue

        if m.telegram_user_id == telegram_user_id:
            # already linked (idempotent)
            linked.append(m.id)
            continue

        m.telegram_user_id = telegram_user_id
        m.save(update_fields=["telegram_user_id"])
        linked.append(m.id)

    return {"linked": linked, "blocked": blocked, "not_found": False}

@transaction.atomic
def link_member_telegram(gym_id: int, raw_phone: str, telegram_user_id: int) -> str:
    phone = normalize_uz_phone(raw_phone)

    member = Member.objects.filter(gym_id=gym_id, phone=phone).select_for_update().first()
    if not member:
        return "not_found"
    if not member.is_active:
        return "inactive"

    # if already linked to someone else -> deny (fraud protection)
    if member.telegram_user_id and member.telegram_user_id != telegram_user_id:
        return "already_linked_other"

    # idempotent
    if member.telegram_user_id == telegram_user_id:
        return "ok"

    member.telegram_user_id = telegram_user_id
    member.save(update_fields=["telegram_user_id"])
    return "ok"

def normalize_uz_phone(raw: str) -> str:
    """
    Canonical format: +998XXXXXXXXX (12 chars incl +, 9 digits after 998)
    Accepts:
      901234567
      90 123 45 67
      998901234567
      +998901234567
    """
    if raw is None:
        return ""

    digits = re.sub(r"\D+", "", raw)

    # If starts with 0 and length 10 or 9? (common local variants)
    if digits.startswith("0"):
        digits = digits[1:]

    # If user typed 9 digits (e.g. 901234567) -> prepend 998
    if len(digits) == 9:
        digits = settings.UZ_COUNTRY + digits

    # If user typed 12 digits and starts with 998 -> ok
    if len(digits) == 12 and digits.startswith(settings.UZ_COUNTRY):
        return f"+{digits}"

    raise ValueError("Invalid Uzbekistan phone number")

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def make_tg_session(telegram_user_id: int) -> str:
    payload = {"tg": int(telegram_user_id), "ts": int(time.time())}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    sig = hmac.new(settings.SECRET_KEY.encode(), raw, hashlib.sha256).digest()
    return f"{_b64url(raw)}.{_b64url(sig)}"

def verify_tg_session(token: str) -> dict:
    try:
        p, s = token.split(".", 1)
        raw = base64.urlsafe_b64decode(p + "=" * (-len(p) % 4))
        sig = base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
    except Exception:
        raise ValueError("format")

    exp = hmac.new(settings.SECRET_KEY.encode(), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, exp):
        raise ValueError("badsig")

    payload = json.loads(raw.decode())
    if int(time.time()) - int(payload["ts"]) > settings.TG_SESSION_TTL:
        raise ValueError("expired")
    return payload

