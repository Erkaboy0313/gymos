import hmac
import hashlib
from urllib.parse import parse_qsl
from django.conf import settings


def verify_telegram_webapp_init_data(init_data: str) -> dict:
    """
    Returns parsed data dict if valid, otherwise raises ValueError.
    """
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_received = data.pop("hash", None)
    if not hash_received:
        raise ValueError("Missing hash")

    # Build data_check_string
    pairs = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(pairs)

    # secret_key = HMAC_SHA256("WebAppData", bot_token)
    bot_token = settings.TELEGRAM_BOT_TOKEN
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    hash_expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(hash_expected, hash_received):
        raise ValueError("Bad signature")

    return data