"""Tests for HeadFrame and the head() mixin method."""
from __future__ import annotations

import pandas as pd
import pytest

from sqlframe.head import HeadFrame


# ---------------------------------------------------------------------------
# Minimal fake connection
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql: str = ""
        self.last_params: list = []
        self._result = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})

    def query(self, sql: str, params=None) -> pd.DataFrame:
        self.last_sql = sql
        self.last_params = params or []
        return self._result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def head_frame(fake_conn):
    return HeadFrame(
        conn=fake_conn,
        source_sql="SELECT * FROM orders",
        n=5,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_build_sql_default_limit(head_frame):
    sql = head_frame._build_sql()
    assert "LIMIT 5" in sql
    assert "SELECT * FROM orders" in sql


def test_build_sql_custom_limit(fake_conn):
    hf = HeadFrame(conn=fake_conn, source_sql="SELECT * FROM sales", n=10)
    assert "LIMIT 10" in hf._build_sql()


def test_build_sql_wraps_in_subquery(head_frame):
    sql = head_frame._build_sql()
    # The original query must appear inside a subquery
    assert sql.startswith("SELECT * FROM (")
    assert "_head_subq" in sql


def test_to_pandas_returns_dataframe(head_frame, fake_conn):
    result = head_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)


def test_to_pandas_executes_correct_sql(head_frame, fake_conn):
    head_frame.to_pandas()
    assert "LIMIT 5" in fake_conn.last_sql


def test_source_sql_trailing_semicolon_stripped(fake_conn):
    hf = HeadFrame(conn=fake_conn, source_sql="SELECT 1;", n=3)
    sql = hf._build_sql()
    # Should not have double semicolons or malformed subquery
    assert ";;" not in sql
    assert "SELECT 1" in sql


def test_params_forwarded_to_connection(fake_conn):
    hf = HeadFrame(
        conn=fake_conn,
        source_sql="SELECT * FROM t WHERE region = %s",
        n=5,
        params=["west"],
    )
    hf.to_pandas()
    assert fake_conn.last_params == ["west"]


def test_default_n_is_five(fake_conn):
    hf = HeadFrame(conn=fake_conn, source_sql="SELECT * FROM t")
    assert hf._n == 5
