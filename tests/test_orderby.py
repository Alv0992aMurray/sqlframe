import pytest
from sqlframe.orderby import OrderByFrame


class FakeConn:
    def __init__(self):
        self.last_sql = None
        self.last_params = None

    def query(self, sql, **params):
        self.last_sql = sql
        self.last_params = params
        import pandas as pd
        return pd.DataFrame()


@pytest.fixture
def conn():
    return FakeConn()


@pytest.fixture
def order_frame(conn):
    return OrderByFrame(conn, table="sales", columns=["amount"], ascending=True)


def test_single_column_asc(order_frame):
    sql = order_frame._build_sql()
    assert "ORDER BY amount ASC" in sql


def test_single_column_desc(conn):
    frame = OrderByFrame(conn, table="sales", columns=["amount"], ascending=False)
    assert "ORDER BY amount DESC" in frame._build_sql()


def test_multi_column_mixed(conn):
    frame = OrderByFrame(
        conn, table="sales", columns=["region", "amount"], ascending=[True, False]
    )
    sql = frame._build_sql()
    assert "region ASC" in sql
    assert "amount DESC" in sql


def test_ascending_length_mismatch_raises(conn):
    frame = OrderByFrame(
        conn, table="sales", columns=["a", "b"], ascending=[True]
    )
    with pytest.raises(ValueError, match="length must match"):
        frame._build_sql()


def test_limit_appended(conn):
    frame = OrderByFrame(conn, table="sales", columns=["amount"], ascending=True)
    limited = frame.limit(10)
    assert "LIMIT 10" in limited._build_sql()


def test_limit_does_not_mutate_original(order_frame):
    _ = order_frame.limit(5)
    assert order_frame._limit is None


def test_where_clause_included(conn):
    frame = OrderByFrame(conn, table="sales", columns=["amount"], ascending=True)
    filtered = frame.where("region = 'EU'")
    assert "WHERE region = 'EU'" in filtered._build_sql()


def test_to_pandas_calls_conn(conn):
    import pandas as pd
    frame = OrderByFrame(conn, table="sales", columns=["amount"], ascending=True)
    result = frame.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert "ORDER BY amount ASC" in conn.last_sql


def test_repr_contains_table_and_sql(order_frame):
    r = repr(order_frame)
    assert "sales" in r
    assert "ORDER BY" in r


def test_chained_where_and_limit(conn):
    frame = (
        OrderByFrame(conn, table="orders", columns=["created_at", "total"], ascending=[False, True])
        .where("status = 'active'")
        .limit(25)
    )
    sql = frame._build_sql()
    assert "WHERE status = 'active'" in sql
    assert "created_at DESC" in sql
    assert "total ASC" in sql
    assert "LIMIT 25" in sql
