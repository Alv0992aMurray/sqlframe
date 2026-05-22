import pytest
import pandas as pd
from sqlframe.pivot import PivotFrame
from sqlframe.frame_pivot_mixin import PivotMixin


# ---------------------------------------------------------------------------
# Fake connection
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql = None

    def query(self, sql: str) -> pd.DataFrame:
        self.last_sql = sql
        return pd.DataFrame({"region": ["north", "south"], "electronics": [10, 5], "clothing": [3, 8]})


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def pivot_frame(fake_conn):
    return PivotFrame(
        conn=fake_conn,
        table="sales",
        index="region",
        pivot_col="category",
        values=["electronics", "clothing"],
        agg_func="SUM",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_build_sql_basic(pivot_frame):
    sql = pivot_frame._build_sql()
    assert "SELECT region" in sql
    assert "CASE WHEN category = 'electronics'" in sql
    assert "CASE WHEN category = 'clothing'" in sql
    assert "GROUP BY region" in sql
    assert "WHERE" not in sql


def test_build_sql_with_where(pivot_frame):
    filtered = pivot_frame.where("year = 2024")
    sql = filtered._build_sql()
    assert "WHERE year = 2024" in sql
    assert "GROUP BY region" in sql


def test_where_returns_new_pivot_frame(pivot_frame):
    filtered = pivot_frame.where("year = 2023")
    assert isinstance(filtered, PivotFrame)
    assert filtered is not pivot_frame
    assert pivot_frame._where_clause is None
    assert filtered._where_clause == "year = 2023"


def test_to_pandas_executes_query(pivot_frame, fake_conn):
    df = pivot_frame.to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert fake_conn.last_sql is not None
    assert "sales" in fake_conn.last_sql


def test_agg_func_uppercase(fake_conn):
    pf = PivotFrame(fake_conn, "orders", "status", "type", ["A", "B"], agg_func="count")
    sql = pf._build_sql()
    assert "COUNT(" in sql


def test_repr(pivot_frame):
    r = repr(pivot_frame)
    assert "PivotFrame" in r
    assert "sales" in r


def test_pivot_mixin_returns_pivot_frame(fake_conn):
    class FakeFrame(PivotMixin):
        def __init__(self, conn, table):
            self._conn = conn
            self._table = table

    frame = FakeFrame(fake_conn, "transactions")
    pf = frame.pivot("store", "product", ["shoes", "hats"], agg_func="MAX")
    assert isinstance(pf, PivotFrame)
    assert pf._agg_func == "MAX"
    assert pf._table == "transactions"
