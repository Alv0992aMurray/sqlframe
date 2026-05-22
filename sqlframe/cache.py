"""Query result caching for SqlFrame."""
from __future__ import annotations

import hashlib
import time
from typing import Any, Optional

import pandas as pd


class QueryCache:
    """Simple in-memory LRU-style cache for query results."""

    def __init__(self, max_size: int = 128, ttl_seconds: float = 300.0):
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._store: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []

    @staticmethod
    def _make_key(sql: str, params: Optional[tuple] = None) -> str:
        raw = sql + (str(params) if params else "")
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, sql: str, params: Optional[tuple] = None) -> Optional[pd.DataFrame]:
        key = self._make_key(sql, params)
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() - entry["ts"] > self._ttl:
            self._evict(key)
            return None
        # Promote to most-recent
        self._order.remove(key)
        self._order.append(key)
        return entry["df"].copy()

    def set(self, sql: str, df: pd.DataFrame, params: Optional[tuple] = None) -> None:
        key = self._make_key(sql, params)
        if key in self._store:
            self._order.remove(key)
        elif len(self._store) >= self._max_size:
            oldest = self._order.pop(0)
            del self._store[oldest]
        self._store[key] = {"df": df.copy(), "ts": time.monotonic()}
        self._order.append(key)

    def _evict(self, key: str) -> None:
        self._store.pop(key, None)
        if key in self._order:
            self._order.remove(key)

    def invalidate(self) -> None:
        """Clear all cached entries."""
        self._store.clear()
        self._order.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"QueryCache(size={len(self)}, max_size={self._max_size}, ttl={self._ttl}s)"
