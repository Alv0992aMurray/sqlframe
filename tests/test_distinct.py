import pytest
import pandas as pd
from sqlframe.distinct import DistinctFrame


# ---------------------------------------------------------------------------
# Minimal fake connection
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql: str = ""
        self.last_params = None

    def query(self, sql: str, params=None) -> pd.DataFrame:
        self.last_sql = sql
        self.last_params = params
        return pd.DataFrame({"col": ["a", "b", "c"]})


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def distinct_frame(fake_conn):
    return DistinctFrame(
        conn=fake_conn,
        table="orders",
        columns=["status"],
    )


# ---------------------------------------------------------------------------
# SQL generation
# ---------------------------------------------------------------------------

def test_build_sql_with_columns(distinct_frame):
    assert distinct_frame._build_sql() == "SELECT DISTINCT status FROM orders"


def test_build_sql_no_columns(fake_conn):
    df = DistinctFrame(fake_conn, "orders", [])
    assert df._build_sql() == "SELECT DISTINCT * FROM orders"


def test_build_sql_multiple_columns(fake_conn):
    df = DistinctFrame(fake_conn, "orders", ["status", "region"])
    assert df._build_sql() == "SELECT DISTINCT status, region FROM orders"


def test_build_sql_with_where(fake_conn):
    df = DistinctFrame(fake_conn, "orders", ["status"], where_clause="amount > 100")
    assert "WHERE amount > 100" in df._build_sql()


def test_build_sql_with_limit(fake_conn):
    df = DistinctFrame(fake_conn, "orders", ["status"], limit_val=10)
    assert df._build_sql().endswith("LIMIT 10")


def test_build_sql_where_and_limit(fake_conn):
    df = DistinctFrame(
        fake_conn, "orders", ["status"],
        where_clause="active = 1", limit_val=5
    )
    sql = df._build_sql()
    assert "WHERE active = 1" in sql
    assert sql.endswith("LIMIT 5")


# ---------------------------------------------------------------------------
# Fluent API
# ---------------------------------------------------------------------------

def test_where_returns_new_distinct_frame(distinct_frame):
    filtered = distinct_frame.where("amount > 50")
    assert isinstance(filtered, DistinctFrame)
    assert filtered._where_clause == "amount > 50"


def test_where_does_not_mutate_original(distinct_frame):
    distinct_frame.where("x = 1")
    assert distinct_frame._where_clause is None


def test_limit_returns_new_distinct_frame(distinct_frame):
    limited = distinct_frame.limit(20)
    assert isinstance(limited, DistinctFrame)
    assert limited._limit_val == 20


# ---------------------------------------------------------------------------
# to_pandas / execution
# ---------------------------------------------------------------------------

def test_to_pandas_calls_conn_query(distinct_frame, fake_conn):
    result = distinct_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert fake_conn.last_sql == "SELECT DISTINCT status FROM orders"


def test_to_pandas_passes_params(fake_conn):
    df = DistinctFrame(
        fake_conn, "orders", ["status"],
        where_clause="amount > %s", params=[100]
    )
    df.to_pandas()
    assert fake_conn.last_params == [100]


# ---------------------------------------------------------------------------
# Mixin integration
# ---------------------------------------------------------------------------

def test_distinct_mixin_on_fake_frame(fake_conn):
    from sqlframe.frame_distinct_mixin import DistinctMixin

    class FakeFrame(DistinctMixin):
        def __init__(self, conn):
            self._conn = conn
            self._table = "products"

    frame = FakeFrame(fake_conn)
    d = frame.distinct(["category"])
    assert isinstance(d, DistinctFrame)
    assert d._table == "products"
    assert d._columns == ["category"]


def test_distinct_mixin_no_table_raises(fake_conn):
    from sqlframe.frame_distinct_mixin import DistinctMixin

    class BadFrame(DistinctMixin):
        def __init__(self, conn):
            self._conn = conn

    with pytest.raises(AttributeError):
        BadFrame(fake_conn).distinct()
