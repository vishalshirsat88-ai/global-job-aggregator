import json
import hashlib

_CACHE = {}

def make_cache_key(payload: dict) -> str:
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(payload_str.encode()).hexdigest()

def get_from_cache(key: str):
    return _CACHE.get(key)

def set_cache(key: str, value):
    _CACHE[key] = value
