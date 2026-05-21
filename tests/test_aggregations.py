"""Tests for group_by / AggFrame aggregation feature."""

from __future__ import annotations

import pandas as pd
import pytest

from sqlframe.aggregations import AggFrame
from sqlframe.frame import SqlFrame


# ---------------------------------------------------------------------------
# Minimal fake connection
# ---------------------------------------------------------------------------

class FakeConn:
    """Records the last SQL sent and returns a canned DataFrame."""

    def __init__(self, return_df: pd.DataFrame) -> None:
        self.last_sql: str = ""
        self._return_df = return_df

    def query(self, sql: str) -> pd.DataFrame:
        self.last_sql = sql
        return self._return_df


@pytest.fixture()
def agg_df() -> pd.DataFrame:
    return pd.DataFrame({"category": ["A", "B"], "total": [100, 200]})


@pytest.fixture()
def fake_conn(agg_df):
    return FakeConn(return_df=agg_df)


@pytest.fixture()
def frame(fake_conn) -> SqlFrame:
    return SqlFrame(fake_conn, "sales")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_group_by_returns_agg_frame(frame):
    result = frame.group_by("category").agg(total="sum(amount)")
    assert isinstance(result, AggFrame)


def test_agg_sql_contains_group_by(frame):
    agg = frame.group_by("category").agg(total="sum(amount)")
    sql = agg._build_sql()
    assert "GROUP BY category" in sql
    assert "sum(amount) AS total" in sql


def test_agg_sql_contains_select_columns(frame):
    agg = frame.group_by("category", "region").agg(cnt="count(id)")
    sql = agg._build_sql()
    assert "category" in sql
    assert "region" in sql
    assert "count(id) AS cnt" in sql


def test_agg_to_pandas_calls_conn(frame, fake_conn, agg_df):
    result = frame.group_by("category").agg(total="sum(amount)").to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert fake_conn.last_sql != ""
    pd.testing.assert_frame_equal(result, agg_df)


def test_agg_order_by_appended_to_sql(frame, fake_conn):
    agg = frame.group_by("category").agg(total="sum(amount)").order_by("total DESC")
    agg.to_pandas()
    assert "ORDER BY total DESC" in fake_conn.last_sql


def test_agg_no_group_by(frame):
    """Aggregation without GROUP BY columns should omit the GROUP BY clause."""
    agg = frame.group_by().agg(grand_total="sum(amount)")
    sql = agg._build_sql()
    assert "GROUP BY" not in sql
    assert "sum(amount) AS grand_total" in sql
