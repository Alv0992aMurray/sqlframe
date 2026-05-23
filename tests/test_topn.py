import pytest
import pandas as pd
from sqlframe.topn import TopNFrame
from sqlframe.frame_topn_mixin import TopNMixin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql = None
        self.last_params = None

    def query(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        self.last_sql = sql
        self.last_params = params or {}
        return pd.DataFrame({"id": [1, 2, 3], "score": [99, 88, 77]})


class FakeFrame(TopNMixin):
    def __init__(self, conn, table, where_clause=None, params=None):
        self._conn = conn
        self._table = table
        self._where_clause = where_clause
        self._params = params or {}


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def frame(fake_conn):
    return FakeFrame(fake_conn, "scores")


# ---------------------------------------------------------------------------
# TopNFrame._build_sql
# ---------------------------------------------------------------------------

def test_build_sql_top_all_columns(fake_conn):
    f = TopNFrame(fake_conn, "scores", [], ["score"], 5, ascending=False)
    assert f._build_sql() == "SELECT * FROM scores ORDER BY score DESC LIMIT 5"


def test_build_sql_top_specific_columns(fake_conn):
    f = TopNFrame(fake_conn, "scores", ["id", "score"], ["score"], 3, ascending=True)
    assert f._build_sql() == "SELECT id, score FROM scores ORDER BY score ASC LIMIT 3"


def test_build_sql_with_where(fake_conn):
    f = TopNFrame(fake_conn, "scores", [], ["score"], 10, ascending=False,
                  where_clause="region = 'EU'")
    sql = f._build_sql()
    assert "WHERE region = 'EU'" in sql
    assert "ORDER BY score DESC LIMIT 10" in sql


def test_build_sql_multi_order_by(fake_conn):
    f = TopNFrame(fake_conn, "scores", [], ["region", "score"], 5, ascending=True)
    assert "ORDER BY region ASC, score ASC" in f._build_sql()


# ---------------------------------------------------------------------------
# TopNFrame.where chaining
# ---------------------------------------------------------------------------

def test_where_returns_new_topn_frame(fake_conn):
    f = TopNFrame(fake_conn, "scores", [], ["score"], 5)
    f2 = f.where("score > 50")
    assert isinstance(f2, TopNFrame)
    assert f2 is not f


def test_where_accumulates_conditions(fake_conn):
    f = TopNFrame(fake_conn, "scores", [], ["score"], 5, where_clause="active = 1")
    f2 = f.where("score > 50")
    assert "active = 1" in f2._build_sql()
    assert "score > 50" in f2._build_sql()


# ---------------------------------------------------------------------------
# TopNFrame.to_pandas
# ---------------------------------------------------------------------------

def test_to_pandas_returns_dataframe(fake_conn):
    f = TopNFrame(fake_conn, "scores", [], ["score"], 3, ascending=False)
    result = f.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert fake_conn.last_sql is not None


# ---------------------------------------------------------------------------
# TopNMixin helpers
# ---------------------------------------------------------------------------

def test_top_n_ascending(frame, fake_conn):
    tn = frame.top_n(5, "score")
    assert isinstance(tn, TopNFrame)
    assert tn._ascending is True
    assert tn._n == 5
    sql = tn._build_sql()
    assert "ASC" in sql and "LIMIT 5" in sql


def test_bottom_n_descending(frame, fake_conn):
    bn = frame.bottom_n(3, "score")
    assert bn._ascending is False
    assert "DESC" in bn._build_sql()


def test_top_n_inherits_where_clause(fake_conn):
    f = FakeFrame(fake_conn, "scores", where_clause="active = 1")
    tn = f.top_n(10, "score")
    assert "WHERE active = 1" in tn._build_sql()


def test_top_n_columns_list(frame):
    tn = frame.top_n(5, "score", columns=["id", "score"])
    assert "SELECT id, score" in tn._build_sql()


def test_top_n_columns_string(frame):
    tn = frame.top_n(5, "score", columns="score")
    assert "SELECT score" in tn._build_sql()


# ---------------------------------------------------------------------------
# repr
# ---------------------------------------------------------------------------

def test_repr(fake_conn):
    f = TopNFrame(fake_conn, "scores", [], ["score"], 5, ascending=False)
    r = repr(f)
    assert "TopNFrame" in r
    assert "scores" in r
    assert "DESC" in r
