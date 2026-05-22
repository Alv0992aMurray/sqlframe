"""Mixin that adds .cache() / .uncache() helpers to frame classes."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlframe.cache import QueryCache


class CacheMixin:
    """Mixin for SqlFrame, JoinFrame, WindowFrame, etc.

    Expects the host class to expose:
      - self._conn  – a Connection with an optional `.cache` attribute
      - self._build_sql() -> str
    """

    def cache(self, ttl_seconds: float = 300.0, max_size: int = 128) -> "CacheMixin":
        """Enable result caching for this frame.

        Attaches a QueryCache to the underlying connection if one does not
        already exist, then marks this frame as cache-enabled.

        Returns self for chaining.
        """
        from sqlframe.cache import QueryCache

        if not getattr(self._conn, "cache", None):
            self._conn.cache = QueryCache(max_size=max_size, ttl_seconds=ttl_seconds)
        self._use_cache = True
        return self

    def uncache(self) -> "CacheMixin":
        """Disable caching for this frame and remove any attached cache."""
        self._use_cache = False
        if hasattr(self._conn, "cache"):
            self._conn.cache.invalidate()
            self._conn.cache = None
        return self

    def _cached_query(self, sql: str, params=None):
        """Run *sql* through the cache when caching is enabled."""
        cache = getattr(self._conn, "cache", None)
        if self._use_cache and cache is not None:
            result = cache.get(sql, params)
            if result is not None:
                return result
            df = self._conn.query(sql, params)
            cache.set(sql, df, params)
            return df
        return self._conn.query(sql, params)
