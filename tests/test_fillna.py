import pytest
import pandas as pd
from sqlframe.fillna import FillNaFrame


# ---------------------------------------------------------------------------
# Fake connection
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql = None

    def query(self, sql, params=None):
        self.last_sql = sql
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Fake frame with FillNaMixin
# ---------------------------------------------------------------------------

class FakeFrame:
    def __init__(self, conn, table, columns=None):
        self._conn = conn
        self._table = table
        self._columns = columns or []


from sqlframe.frame_fillna_mixin import FillNaMixin

class MixedFrame(FillNaMixin, FakeFrame):
    pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def conn():
    return FakeConn()


@pytest.fixture
def fillna_frame(conn):
    return FillNaFrame(
        conn=conn,
        table="sales",
        fill_map={"revenue": 0, "region": "unknown"},
    )


# ---------------------------------------------------------------------------
# FillNaFrame unit tests
# ---------------------------------------------------------------------------

def test_build_sql_numeric_fill(fillna_frame):
    sql = fillna_frame._build_sql()
    assert "COALESCE(revenue, 0) AS revenue" in sql
    assert "sales" in sql


def test_build_sql_string_fill(fillna_frame):
    sql = fillna_frame._build_sql()
    assert "COALESCE(region, 'unknown') AS region" in sql


def test_build_sql_with_where(conn):
    frame = FillNaFrame(conn, "orders", {"amount": 0.0}, where="status = 'open'")
    sql = frame._build_sql()
    assert "WHERE status = 'open'" in sql


def test_build_sql_with_limit(conn):
    frame = FillNaFrame(conn, "orders", {"amount": 0.0}, limit_val=50)
    sql = frame._build_sql()
    assert "LIMIT 50" in sql


def test_where_returns_new_frame(fillna_frame):
    new_frame = fillna_frame.where("region IS NOT NULL")
    assert isinstance(new_frame, FillNaFrame)
    assert new_frame._where == "region IS NOT NULL"
    assert fillna_frame._where is None


def test_limit_returns_new_frame(fillna_frame):
    new_frame = fillna_frame.limit(10)
    assert isinstance(new_frame, FillNaFrame)
    assert new_frame._limit_val == 10
    assert fillna_frame._limit_val is None


def test_to_pandas_executes_query(conn, fillna_frame):
    result = fillna_frame.to_pandas()
    assert conn.last_sql is not None
    assert "COALESCE" in conn.last_sql
    assert isinstance(result, pd.DataFrame)


def test_repr(fillna_frame):
    r = repr(fillna_frame)
    assert "FillNaFrame" in r
    assert "sales" in r


# ---------------------------------------------------------------------------
# FillNaMixin tests
# ---------------------------------------------------------------------------

def test_mixin_dict_value(conn):
    frame = MixedFrame(conn, "users", columns=["age", "score"])
    fn = frame.fillna({"age": -1, "score": 0.0})
    assert isinstance(fn, FillNaFrame)
    assert fn._fill_map == {"age": -1, "score": 0.0}


def test_mixin_scalar_with_subset(conn):
    frame = MixedFrame(conn, "users", columns=["age", "score", "name"])
    fn = frame.fillna(0, subset=["age", "score"])
    assert fn._fill_map == {"age": 0, "score": 0}


def test_mixin_scalar_uses_all_columns(conn):
    frame = MixedFrame(conn, "users", columns=["a", "b", "c"])
    fn = frame.fillna(99)
    assert set(fn._fill_map.keys()) == {"a", "b", "c"}
    assert all(v == 99 for v in fn._fill_map.values())


def test_mixin_no_columns_raises(conn):
    frame = MixedFrame(conn, "users", columns=[])
    with pytest.raises(ValueError, match="Cannot determine columns"):
        frame.fillna(0)
