import pytest
import pandas as pd
from sqlframe.union import UnionFrame


class FakeConn:
    def __init__(self):
        self.last_query = None

    def query(self, sql, params=None):
        self.last_query = sql
        return pd.DataFrame({"id": [1, 2], "val": ["a", "b"]})


class FakeFrame:
    def __init__(self, table: str, conn):
        self._table = table
        self._conn = conn

    def _build_sql(self) -> str:
        return f"SELECT * FROM {self._table}"


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def frame_a(fake_conn):
    return FakeFrame("table_a", fake_conn)


@pytest.fixture
def frame_b(fake_conn):
    return FakeFrame("table_b", fake_conn)


@pytest.fixture
def union_frame(frame_a, frame_b, fake_conn):
    return UnionFrame([frame_a, frame_b], fake_conn, union_all=False)


def test_union_requires_at_least_two_frames(fake_conn, frame_a):
    with pytest.raises(ValueError, match="at least two frames"):
        UnionFrame([frame_a], fake_conn)


def test_union_builds_correct_sql(union_frame):
    sql = union_frame._build_sql()
    assert "UNION" in sql
    assert "UNION ALL" not in sql
    assert "SELECT * FROM table_a" in sql
    assert "SELECT * FROM table_b" in sql


def test_union_all_builds_correct_sql(frame_a, frame_b, fake_conn):
    uf = UnionFrame([frame_a, frame_b], fake_conn, union_all=True)
    sql = uf._build_sql()
    assert "UNION ALL" in sql


def test_union_where_appends_clause(union_frame):
    filtered = union_frame.where("id > 1")
    sql = filtered._build_sql()
    assert "WHERE id > 1" in sql


def test_union_limit_appends_clause(union_frame):
    limited = union_frame.limit(10)
    sql = limited._build_sql()
    assert "LIMIT 10" in sql


def test_union_where_does_not_mutate_original(union_frame):
    _ = union_frame.where("id = 1")
    assert union_frame._where_clause is None


def test_union_to_pandas_calls_conn(union_frame, fake_conn):
    result = union_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert fake_conn.last_query is not None
    assert "UNION" in fake_conn.last_query


def test_union_repr_contains_keyword(union_frame):
    r = repr(union_frame)
    assert "UnionFrame" in r
    assert "UNION" in r


def test_union_mixin_union_method(fake_conn):
    from sqlframe.frame_union_mixin import UnionMixin

    class MixedFrame(UnionMixin):
        def __init__(self, table, conn):
            self._table = table
            self._conn = conn

        def _build_sql(self):
            return f"SELECT * FROM {self._table}"

    fa = MixedFrame("t1", fake_conn)
    fb = MixedFrame("t2", fake_conn)
    uf = fa.union(fb)
    assert isinstance(uf, UnionFrame)
    assert "UNION ALL" not in uf._build_sql()


def test_union_mixin_union_all_method(fake_conn):
    from sqlframe.frame_union_mixin import UnionMixin

    class MixedFrame(UnionMixin):
        def __init__(self, table, conn):
            self._table = table
            self._conn = conn

        def _build_sql(self):
            return f"SELECT * FROM {self._table}"

    fa = MixedFrame("t1", fake_conn)
    fb = MixedFrame("t2", fake_conn)
    uf = fa.union_all(fb)
    assert isinstance(uf, UnionFrame)
    assert "UNION ALL" in uf._build_sql()
