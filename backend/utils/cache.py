import time
import hashlib
import json

_CACHE = {}
_TTL_SECONDS = 600   # 10 minutes (safe default)


def _now():
    return time.time()


def make_cache_key(payload: dict) -> str:
    """
    Create a deterministic hash from request payload
    """
    normalized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()


def get_from_cache(key: str):
    entry = _CACHE.get(key)
    if not entry:
        return None

    data, expiry = entry
    if _now() > expiry:
        del _CACHE[key]
        return None

    return data


def set_cache(key: str, value):
    _CACHE[key] = (value, _now() + _TTL_SECONDS)
