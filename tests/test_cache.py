"""Tests for QueryCache and CacheMixin."""
import time

import pandas as pd
import pytest

from sqlframe.cache import QueryCache
from sqlframe.frame_cache_mixin import CacheMixin


# ---------------------------------------------------------------------------
# QueryCache unit tests
# ---------------------------------------------------------------------------

def make_df(val: int) -> pd.DataFrame:
    return pd.DataFrame({"v": [val]})


def test_cache_miss_returns_none():
    c = QueryCache()
    assert c.get("SELECT 1") is None


def test_cache_set_and_hit():
    c = QueryCache()
    c.set("SELECT 1", make_df(42))
    result = c.get("SELECT 1")
    assert result is not None
    assert result["v"].iloc[0] == 42


def test_cache_params_differentiate_keys():
    c = QueryCache()
    c.set("SELECT ?", make_df(1), params=(1,))
    c.set("SELECT ?", make_df(2), params=(2,))
    assert c.get("SELECT ?", params=(1,))["v"].iloc[0] == 1
    assert c.get("SELECT ?", params=(2,))["v"].iloc[0] == 2


def test_cache_ttl_expiry():
    c = QueryCache(ttl_seconds=0.05)
    c.set("SELECT 1", make_df(99))
    time.sleep(0.1)
    assert c.get("SELECT 1") is None


def test_cache_max_size_evicts_oldest():
    c = QueryCache(max_size=2)
    c.set("SELECT 1", make_df(1))
    c.set("SELECT 2", make_df(2))
    c.set("SELECT 3", make_df(3))  # should evict SELECT 1
    assert len(c) == 2
    assert c.get("SELECT 1") is None
    assert c.get("SELECT 2") is not None


def test_cache_invalidate():
    c = QueryCache()
    c.set("SELECT 1", make_df(1))
    c.invalidate()
    assert len(c) == 0


def test_cache_repr():
    c = QueryCache(max_size=64, ttl_seconds=60)
    assert "QueryCache" in repr(c)


# ---------------------------------------------------------------------------
# CacheMixin integration test via a minimal fake frame
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.calls = 0
        self.cache = None

    def query(self, sql, params=None):
        self.calls += 1
        return pd.DataFrame({"x": [self.calls]})


class FakeFrame(CacheMixin):
    def __init__(self, conn):
        self._conn = conn
        self._use_cache = False

    def _build_sql(self):
        return "SELECT x FROM t"

    def to_pandas(self):
        sql = self._build_sql()
        return self._cached_query(sql)


def test_mixin_caching_prevents_duplicate_queries():
    conn = FakeConn()
    frame = FakeFrame(conn)
    frame.cache(ttl_seconds=60)
    df1 = frame.to_pandas()
    df2 = frame.to_pandas()
    assert conn.calls == 1  # second call served from cache
    assert df1["x"].iloc[0] == df2["x"].iloc[0]


def test_mixin_uncache_clears_cache():
    conn = FakeConn()
    frame = FakeFrame(conn)
    frame.cache(ttl_seconds=60)
    frame.to_pandas()
    frame.uncache()
    assert conn.cache is None
    assert frame._use_cache is False
