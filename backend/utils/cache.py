import json
import hashlib
import time

# =========================
# CACHE STORAGE
# =========================

_CACHE = {}

# Cache lifetime (seconds)
CACHE_TTL = 1800   # 30 minutes


# =========================
# CACHE KEY GENERATION
# =========================

def make_cache_key(payload: dict) -> str:
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(payload_str.encode()).hexdigest()


# =========================
# CACHE READ
# =========================

def get_from_cache(key: str):
    data = _CACHE.get(key)

    if not data:
        print("🟡 CACHE MISS")
        return None

    value, timestamp = data

    age = time.time() - timestamp

    if age > CACHE_TTL:
        print("⏱️ CACHE EXPIRED → Refreshing from APIs")
        del _CACHE[key]
        return None

    print(f"⚡ CACHE HIT → Served instantly (age: {int(age)} sec)")
    return value


# =========================
# CACHE WRITE
# =========================

def set_cache(key: str, value):
    _CACHE[key] = (value, time.time())
    print("💾 CACHE SAVED")
