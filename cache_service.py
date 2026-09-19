import time
from typing import Any, Optional, Dict
from ..database import CacheRepo

class CacheService:
    _memory_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        # Check memory first
        if key in cls._memory_cache:
            entry = cls._memory_cache[key]
            if entry["expires_at"] > time.time():
                return entry["value"]
            else:
                del cls._memory_cache[key]

        # Check SQLite
        val = CacheRepo.get(key)
        if val is not None:
            cls._memory_cache[key] = {
                "value": val,
                "expires_at": time.time() + 3600
            }
            return val
        return None

    @classmethod
    def set(cls, key: str, value: Any, ttl_seconds: int = 3600):
        cls._memory_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds
        }
        try:
            CacheRepo.set(key, value, ttl_seconds)
        except Exception as e:
            print(f"CacheRepo.set warning: {e}")

    @classmethod
    def delete(cls, key: str):
        if key in cls._memory_cache:
            del cls._memory_cache[key]
        try:
            CacheRepo.delete(key)
        except Exception:
            pass

    @classmethod
    def clear(cls):
        cls._memory_cache.clear()

    @classmethod
    def count(cls) -> int:
        return len(cls._memory_cache)
