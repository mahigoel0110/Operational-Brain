from typing import Dict, Any, List
from threading import Lock

class EntityCache:
    """
    A thread-safe in-memory cache to prevent reprocessing the same chunks or text 
    during entity and relationship extraction.
    In a distributed production system, this would be replaced with Redis.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any):
        with self._lock:
            self._cache[key] = value

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

    def clear(self):
        with self._lock:
            self._cache.clear()

entity_cache = EntityCache()
