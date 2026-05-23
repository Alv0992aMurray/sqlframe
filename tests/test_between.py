import pytest
import pandas as pd
from sqlframe.between import BetweenFrame


# ---------------------------------------------------------------------------
# Minimal fake connection
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql = None
        self.last_params = None

    def query(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params or []
        return pd.DataFrame({"id": [1, 2], "value": [10, 20]})


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def between_frame(fake_conn):
    return BetweenFrame(
        conn=fake_conn,
        table="sales",
        column="amount",
        low=100,
        high=500,
    )


# ---------------------------------------------------------------------------
# SQL generation tests
# ---------------------------------------------------------------------------

def test_basic_sql(between_frame):
    sql, params = between_frame._build_sql()
    assert "BETWEEN ? AND ?" in sql
    assert params == [100, 500]


def test_default_columns_is_star(between_frame):
    sql, _ = between_frame._build_sql()
    assert "SELECT *" in sql


def test_custom_columns():
    conn = FakeConn()
    bf = BetweenFrame(conn, "sales", "amount", 10, 50, columns=["id", "amount"])
    sql, _ = bf._build_sql()
    assert "SELECT id, amount" in sql


def test_where_appends_condition(between_frame):
    filtered = between_frame.where("region = 'EU'", params=[])
    sql, params = filtered._build_sql()
    assert "AND (region = 'EU')" in sql
    assert params[:2] == [100, 500]


def test_where_chaining(between_frame):
    filtered = between_frame.where("region = 'EU'").where("active = 1")
    sql, _ = filtered._build_sql()
    assert "region = 'EU'" in sql
    assert "active = 1" in sql


def test_limit_appends_clause(between_frame):
    limited = between_frame.limit(10)
    sql, _ = limited._build_sql()
    assert "LIMIT 10" in sql


def test_limit_not_present_by_default(between_frame):
    sql, _ = between_frame._build_sql()
    assert "LIMIT" not in sql


def test_to_pandas_calls_conn_query(fake_conn, between_frame):
    df = between_frame.to_pandas()
    assert fake_conn.last_sql is not None
    assert isinstance(df, pd.DataFrame)


def test_to_pandas_passes_correct_params(fake_conn, between_frame):
    between_frame.to_pandas()
    assert fake_conn.last_params == [100, 500]


def test_repr_contains_between(between_frame):
    r = repr(between_frame)
    assert "BetweenFrame" in r
    assert "BETWEEN" in r


def test_immutability_limit(between_frame):
    limited = between_frame.limit(5)
    assert between_frame._limit is None
    assert limited._limit == 5


def test_immutability_where(between_frame):
    filtered = between_frame.where("x = 1")
    assert between_frame._where_clause is None
    assert filtered._where_clause == "x = 1"
