"""Tests for IsInFrame and IsInMixin."""
from __future__ import annotations
from typing import Any, List, Optional

import pandas as pd
import pytest

from sqlframe.isin import IsInFrame
from sqlframe.frame_isin_mixin import IsInMixin


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql: Optional[str] = None
        self.last_params: Any = None

    def query(self, sql: str, params=None) -> pd.DataFrame:
        self.last_sql = sql
        self.last_params = params
        return pd.DataFrame({"id": [1, 2], "name": ["alice", "bob"]})


class FakeFrame(IsInMixin):
    def __init__(self, conn, table="orders"):
        self._conn = conn
        self._table = table
        self._filters: List[str] = []
        self._columns: List[str] = ["*"]
        self._limit: Optional[int] = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def isin_frame(fake_conn):
    return IsInFrame(
        conn=fake_conn,
        table="orders",
        column="status",
        values=["pending", "shipped"],
    )


# ---------------------------------------------------------------------------
# IsInFrame._build_sql
# ---------------------------------------------------------------------------

def test_build_sql_in_clause(isin_frame):
    sql = isin_frame._build_sql()
    assert "IN (%s, %s)" in sql
    assert "WHERE" in sql
    assert "orders" in sql


def test_build_sql_not_in_clause(fake_conn):
    frame = IsInFrame(
        conn=fake_conn,
        table="orders",
        column="status",
        values=["cancelled"],
        negate=True,
    )
    sql = frame._build_sql()
    assert "NOT IN (%s)" in sql


def test_build_sql_with_extra_filter(isin_frame):
    frame = isin_frame.where("amount > 100")
    sql = frame._build_sql()
    assert "amount > 100" in sql
    assert "IN" in sql


def test_build_sql_with_limit(isin_frame):
    frame = isin_frame.limit(5)
    sql = frame._build_sql()
    assert "LIMIT 5" in sql


def test_build_sql_no_limit_by_default(isin_frame):
    sql = isin_frame._build_sql()
    assert "LIMIT" not in sql


# ---------------------------------------------------------------------------
# IsInFrame.to_pandas
# ---------------------------------------------------------------------------

def test_to_pandas_calls_conn_with_values(fake_conn, isin_frame):
    df = isin_frame.to_pandas()
    assert fake_conn.last_params == ["pending", "shipped"]
    assert isinstance(df, pd.DataFrame)


# ---------------------------------------------------------------------------
# IsInMixin integration
# ---------------------------------------------------------------------------

def test_mixin_isin_returns_isin_frame(fake_conn):
    frame = FakeFrame(fake_conn)
    result = frame.isin("status", ["active", "inactive"])
    assert isinstance(result, IsInFrame)
    assert result._negate is False
    assert result._column == "status"


def test_mixin_notin_returns_negated_isin_frame(fake_conn):
    frame = FakeFrame(fake_conn)
    result = frame.notin("status", ["deleted"])
    assert isinstance(result, IsInFrame)
    assert result._negate is True


def test_mixin_inherits_existing_filters(fake_conn):
    frame = FakeFrame(fake_conn)
    frame._filters = ["region = 'US'"]
    result = frame.isin("status", ["active"])
    assert "region = 'US'" in result._filters


def test_chaining_where_does_not_mutate_original(isin_frame):
    chained = isin_frame.where("amount > 50")
    assert "amount > 50" not in isin_frame._filters
    assert "amount > 50" in chained._filters
