import pandas as pd
import pytest

from sqlframe.head import HeadFrame


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class FakeConn:
    """Records the last SQL string passed to .query()."""

    def __init__(self):
        self.last_sql = None
        self.last_params = None

    def query(self, sql: str, params=None):
        self.last_sql = sql
        self.last_params = params
        return pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})


class FakeFrame:
    """Minimal stand-in for SqlFrame."""

    def __init__(self, conn, table="orders", columns=None, where_clauses=None):
        self._conn = conn
        self._table = table
        self._columns = columns or ["*"]
        self._where_clauses = where_clauses or []

    def _build_sql(self):
        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        return sql


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def head_frame(fake_conn):
    frame = FakeFrame(fake_conn)
    return HeadFrame(frame=frame, n=3)


# ---------------------------------------------------------------------------
# HeadFrame._build_sql
# ---------------------------------------------------------------------------

def test_build_sql_contains_limit(head_frame):
    sql = head_frame._build_sql()
    assert "LIMIT 3" in sql


def test_build_sql_wraps_base_query(head_frame):
    sql = head_frame._build_sql()
    assert "SELECT * FROM orders" in sql


def test_build_sql_default_n(fake_conn):
    frame = FakeFrame(fake_conn)
    hf = HeadFrame(frame=frame, n=5)
    assert "LIMIT 5" in hf._build_sql()


# ---------------------------------------------------------------------------
# HeadFrame.to_pandas
# ---------------------------------------------------------------------------

def test_to_pandas_returns_dataframe(head_frame, fake_conn):
    result = head_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)


def test_to_pandas_executes_correct_sql(head_frame, fake_conn):
    head_frame.to_pandas()
    assert fake_conn.last_sql is not None
    assert "LIMIT 3" in fake_conn.last_sql


# ---------------------------------------------------------------------------
# HeadMixin.head
# ---------------------------------------------------------------------------

def test_head_mixin_returns_head_frame(fake_conn):
    from sqlframe.frame_head_mixin import HeadMixin

    class MixedFrame(HeadMixin, FakeFrame):
        pass

    mf = MixedFrame(fake_conn)
    result = mf.head(7)
    assert isinstance(result, HeadFrame)
    assert result._n == 7


def test_head_mixin_default_n(fake_conn):
    from sqlframe.frame_head_mixin import HeadMixin

    class MixedFrame(HeadMixin, FakeFrame):
        pass

    mf = MixedFrame(fake_conn)
    result = mf.head()
    assert result._n == 5


def test_head_mixin_invalid_n_raises(fake_conn):
    from sqlframe.frame_head_mixin import HeadMixin

    class MixedFrame(HeadMixin, FakeFrame):
        pass

    mf = MixedFrame(fake_conn)
    with pytest.raises(ValueError):
        mf.head(0)

    with pytest.raises(ValueError):
        mf.head(-3)


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------

def test_repr_contains_n(head_frame):
    r = repr(head_frame)
    assert "3" in r
