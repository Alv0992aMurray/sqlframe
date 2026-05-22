"""Tests for window function support."""
import pytest
import pandas as pd

from sqlframe.window import (
    WindowFrame,
    WindowSpec,
    rank_over,
    row_number_over,
    lag_over,
    lead_over,
)
from sqlframe.frame import SqlFrame


# ---------------------------------------------------------------------------
# Minimal fake connection
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql: str = ""

    def query(self, sql: str) -> pd.DataFrame:
        self.last_sql = sql
        return pd.DataFrame({"result": [1]})


@pytest.fixture()
def fake_conn():
    return FakeConn()


@pytest.fixture()
def base_frame(fake_conn):
    return SqlFrame(conn=fake_conn, table="sales")


# ---------------------------------------------------------------------------
# WindowSpec tests
# ---------------------------------------------------------------------------

def test_window_spec_full():
    spec = WindowSpec(partition_by=["dept"], order_by=["revenue DESC"])
    rendered = spec._render()
    assert "PARTITION BY dept" in rendered
    assert "ORDER BY revenue DESC" in rendered


def test_window_spec_order_only():
    spec = WindowSpec(order_by=["ts"])
    rendered = spec._render()
    assert "PARTITION BY" not in rendered
    assert "ORDER BY ts" in rendered


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

def test_rank_over_renders():
    expr = rank_over(partition_by=["dept"], order_by=["salary DESC"])
    assert expr.startswith("RANK()")
    assert "PARTITION BY dept" in expr
    assert "AS rank" in expr


def test_row_number_over_renders():
    expr = row_number_over(partition_by=["region"], order_by=["date"])
    assert "ROW_NUMBER()" in expr
    assert "AS row_number" in expr


def test_lag_over_renders():
    expr = lag_over("revenue", 1, partition_by=["dept"], order_by=["month"])
    assert "LAG(revenue, 1)" in expr
    assert "AS lag_revenue" in expr


def test_lead_over_renders():
    expr = lead_over("revenue", 2, partition_by=["dept"], order_by=["month"])
    assert "LEAD(revenue, 2)" in expr
    assert "AS lead_revenue" in expr


# ---------------------------------------------------------------------------
# WindowFrame tests
# ---------------------------------------------------------------------------

def test_window_frame_builds_sql(fake_conn):
    wf = WindowFrame(
        conn=fake_conn,
        base_sql="SELECT dept, salary FROM employees",
        window_cols=[rank_over(["dept"], ["salary DESC"])],
        extra_cols=["dept", "salary"],
    )
    sql = wf._build_sql()
    assert "RANK()" in sql
    assert "FROM (SELECT dept, salary FROM employees)" in sql


def test_window_frame_where_and_limit(fake_conn):
    wf = WindowFrame(
        conn=fake_conn,
        base_sql="SELECT * FROM t",
        window_cols=[row_number_over([], ["id"])],
        extra_cols=["*"],
    )
    wf.where("row_number <= 3").limit(10)
    sql = wf._build_sql()
    assert "WHERE row_number <= 3" in sql
    assert "LIMIT 10" in sql


def test_window_frame_to_pandas_calls_conn(fake_conn):
    wf = WindowFrame(
        conn=fake_conn,
        base_sql="SELECT * FROM t",
        window_cols=[rank_over(["x"], ["y"])],
        extra_cols=["x", "y"],
    )
    result = wf.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert fake_conn.last_sql != ""


# ---------------------------------------------------------------------------
# WindowMixin integration on SqlFrame
# ---------------------------------------------------------------------------

def test_sqlframe_window_returns_window_frame(base_frame):
    wf = base_frame.select("dept", "salary").window(
        window_cols=[rank_over(["dept"], ["salary DESC"])],
    )
    assert isinstance(wf, WindowFrame)


def test_sqlframe_window_sql_contains_inner_query(base_frame, fake_conn):
    wf = base_frame.select("dept", "salary").window(
        window_cols=[rank_over(["dept"], ["salary DESC"])],
        extra_cols=["dept", "salary"],
    )
    sql = wf._build_sql()
    assert "FROM (SELECT dept, salary FROM sales)" in sql
    assert "RANK()" in sql
