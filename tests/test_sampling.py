"""Tests for sqlframe.sampling.SampleFrame."""

from __future__ import annotations

import pandas as pd
import pytest

from sqlframe.sampling import SampleFrame


# ---------------------------------------------------------------------------
# Minimal fake objects
# ---------------------------------------------------------------------------

class FakeConn:
    """Records the last SQL string passed to query()."""

    def __init__(self) -> None:
        self.last_sql: str = ""

    def query(self, sql: str, params=None) -> pd.DataFrame:
        self.last_sql = sql
        return pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})


class FakeFrame:
    """Minimal stand-in for SqlFrame."""

    def __init__(self, conn: FakeConn) -> None:
        self._conn = conn
        self._table = "users"
        self._wheres: list[str] = []
        self._selects: list[str] = ["*"]
        self._limit_val: int | None = None

    def _build_sql(self) -> str:
        cols = ", ".join(self._selects)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._wheres:
            sql += " WHERE " + " AND ".join(self._wheres)
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_conn() -> FakeConn:
    return FakeConn()


@pytest.fixture()
def base_frame(fake_conn: FakeConn) -> FakeFrame:
    return FakeFrame(fake_conn)


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------

def test_raises_without_fraction_or_n(base_frame):
    with pytest.raises(ValueError, match="fraction.*n"):
        SampleFrame(base_frame)


def test_raises_on_invalid_fraction(base_frame):
    with pytest.raises(ValueError, match="fraction"):
        SampleFrame(base_frame, fraction=1.5)


def test_raises_on_zero_fraction(base_frame):
    with pytest.raises(ValueError, match="fraction"):
        SampleFrame(base_frame, fraction=0)


def test_raises_on_non_positive_n(base_frame):
    with pytest.raises(ValueError, match="positive"):
        SampleFrame(base_frame, n=0)


# ---------------------------------------------------------------------------
# SQL generation
# ---------------------------------------------------------------------------

def test_build_sql_with_n(base_frame):
    sf = SampleFrame(base_frame, n=10)
    sql = sf._build_sql()
    assert "ORDER BY RANDOM()" in sql
    assert "LIMIT 10" in sql
    assert "SELECT * FROM users" in sql


def test_build_sql_with_fraction(base_frame):
    sf = SampleFrame(base_frame, fraction=0.25)
    sql = sf._build_sql()
    assert "RANDOM() <= 0.25" in sql
    assert "SELECT * FROM users" in sql


def test_build_sql_includes_seed_comment(base_frame):
    sf = SampleFrame(base_frame, n=5, seed=42)
    sql = sf._build_sql()
    assert "seed=42" in sql


def test_no_seed_comment_when_seed_is_none(base_frame):
    sf = SampleFrame(base_frame, n=5)
    sql = sf._build_sql()
    assert "seed=" not in sql


# ---------------------------------------------------------------------------
# to_pandas integration
# ---------------------------------------------------------------------------

def test_to_pandas_returns_dataframe(base_frame, fake_conn):
    sf = SampleFrame(base_frame, n=3)
    result = sf.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["id", "val"]


def test_to_pandas_executes_correct_sql(base_frame, fake_conn):
    sf = SampleFrame(base_frame, fraction=0.5)
    sf.to_pandas()
    assert "RANDOM()" in fake_conn.last_sql
    assert "0.5" in fake_conn.last_sql
