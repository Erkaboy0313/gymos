from django.core.cache import cache

FAIL_LIMIT = 20          # attempts
WINDOW_SECONDS = 60      # per 60s
BAN_SECONDS = 300        # 5 minutes

def _keys(device_id: int, ip: str):
    base = f"kiosk:bf:dev:{device_id}:ip:{ip}"
    return base + ":fails", base + ":ban"

def is_banned(device_id: int, ip: str) -> bool:
    _, ban_key = _keys(device_id, ip)
    return bool(cache.get(ban_key))

def record_fail(device_id: int, ip: str) -> None:
    fails_key, ban_key = _keys(device_id, ip)

    fails = cache.get(fails_key)
    if fails is None:
        cache.set(fails_key, 1, WINDOW_SECONDS)
        return

    fails = int(fails) + 1
    cache.set(fails_key, fails, WINDOW_SECONDS)

    if fails >= FAIL_LIMIT:
        cache.set(ban_key, 1, BAN_SECONDS)
        cache.delete(fails_key)

def reset_fail(device_id: int, ip: str) -> None:
    fails_key, ban_key = _keys(device_id, ip)
    cache.delete(fails_key)
    # don't delete ban_key (ban should persist once triggered)