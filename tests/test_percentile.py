import pytest
import pandas as pd
from sqlframe.percentile import PercentileFrame
from sqlframe.frame_percentile_mixin import PercentileMixin


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql = None

    def query(self, sql, params=None):
        self.last_sql = sql
        return pd.DataFrame({"result": [42.0]})


class FakeFrame(PercentileMixin):
    def __init__(self, conn, table, where=None):
        self._conn = conn
        self._table = table
        self._where = where


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def pct_frame(fake_conn):
    return PercentileFrame(
        conn=fake_conn,
        table="employees",
        column="salary",
        percentiles=[0.25, 0.5, 0.75],
    )


# ---------------------------------------------------------------------------
# PercentileFrame unit tests
# ---------------------------------------------------------------------------

def test_build_sql_single_percentile(fake_conn):
    frame = PercentileFrame(fake_conn, "orders", "amount", [0.5])
    sql = frame._build_sql()
    assert "PERCENTILE_CONT(0.5)" in sql
    assert "FROM orders" in sql
    assert "WHERE" not in sql


def test_build_sql_multiple_percentiles(pct_frame):
    sql = pct_frame._build_sql()
    assert "PERCENTILE_CONT(0.25)" in sql
    assert "PERCENTILE_CONT(0.5)" in sql
    assert "PERCENTILE_CONT(0.75)" in sql
    assert "salary" in sql


def test_build_sql_with_where(fake_conn):
    frame = PercentileFrame(
        fake_conn, "employees", "salary", [0.5], where_clause="dept = 'eng'"
    )
    sql = frame._build_sql()
    assert "WHERE dept = 'eng'" in sql


def test_where_chains_condition(pct_frame):
    filtered = pct_frame.where("dept = 'sales'")
    sql = filtered._build_sql()
    assert "WHERE dept = 'sales'" in sql


def test_where_combines_existing_and_new(fake_conn):
    frame = PercentileFrame(
        fake_conn, "employees", "salary", [0.5], where_clause="region = 'us'"
    )
    filtered = frame.where("dept = 'eng'")
    sql = filtered._build_sql()
    assert "region = 'us'" in sql
    assert "dept = 'eng'" in sql
    assert "AND" in sql


def test_to_pandas_calls_query(pct_frame, fake_conn):
    result = pct_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert fake_conn.last_sql is not None


def test_invalid_percentile_raises():
    conn = FakeConn()
    with pytest.raises(ValueError, match="between 0 and 1"):
        PercentileFrame(conn, "t", "col", [1.5])


def test_empty_percentiles_raises():
    conn = FakeConn()
    with pytest.raises(ValueError, match="At least one"):
        PercentileFrame(conn, "t", "col", [])


def test_invalid_interpolation_raises():
    conn = FakeConn()
    with pytest.raises(ValueError, match="interpolation"):
        PercentileFrame(conn, "t", "col", [0.5], interpolation="bad")


def test_repr(pct_frame):
    r = repr(pct_frame)
    assert "PercentileFrame" in r
    assert "salary" in r


# ---------------------------------------------------------------------------
# PercentileMixin tests
# ---------------------------------------------------------------------------

def test_mixin_single_float(fake_conn):
    frame = FakeFrame(fake_conn, "sales")
    pf = frame.percentile("revenue", 0.5)
    assert isinstance(pf, PercentileFrame)
    assert pf._percentiles == [0.5]


def test_mixin_list_of_percentiles(fake_conn):
    frame = FakeFrame(fake_conn, "sales")
    pf = frame.percentile("revenue", [0.1, 0.9])
    assert pf._percentiles == [0.1, 0.9]


def test_mixin_inherits_where_clause(fake_conn):
    frame = FakeFrame(fake_conn, "sales", where="region = 'eu'")
    pf = frame.percentile("revenue", 0.5)
    assert pf._where_clause == "region = 'eu'"


def test_mixin_interpolation_forwarded(fake_conn):
    frame = FakeFrame(fake_conn, "sales")
    pf = frame.percentile("revenue", 0.5, interpolation="lower")
    assert pf._interpolation == "lower"
