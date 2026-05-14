"""Tiny in-process TTL cache for cheap memoisation of expensive operations.

Not a distributed cache — strictly per-worker. Fine for stabilising
retrieval-search latency when the same query is repeated within a few
minutes (common during interactive editing).
"""
from __future__ import annotations

import time
from threading import RLock
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    def __init__(self, ttl_seconds: float = 300.0, max_items: int = 256) -> None:
        self.ttl = float(ttl_seconds)
        self.max_items = int(max_items)
        self._store: Dict[Any, Tuple[float, Any]] = {}
        self._lock = RLock()

    def get(self, key: Any) -> Optional[Any]:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            ts, value = entry
            if now - ts > self.ttl:
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: Any, value: Any) -> None:
        with self._lock:
            if len(self._store) >= self.max_items:
                # Evict oldest
                oldest = min(self._store.items(), key=lambda kv: kv[1][0])[0]
                self._store.pop(oldest, None)
            self._store[key] = (time.monotonic(), value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
