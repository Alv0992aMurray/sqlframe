import pytest
import pandas as pd
from sqlframe.withcolumn import WithColumnFrame


class FakeConn:
    def __init__(self):
        self.last_sql = None
        self.last_params = None

    def query(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params
        return pd.DataFrame({"id": [1, 2], "price": [10.0, 20.0], "discounted": [9.0, 18.0]})


class FakeFrame:
    def __init__(self, conn, table="products"):
        self._conn = conn
        self._table = table
        self._wheres = []
        self._limit = None

    def _build_sql(self):
        return f"SELECT * FROM {self._table}"


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def with_col_frame(fake_conn):
    source = FakeFrame(fake_conn)
    return WithColumnFrame(
        conn=fake_conn,
        source=source,
        col_name="discounted",
        expression="price * 0.9",
    )


def test_build_sql_wraps_source(with_col_frame):
    sql = with_col_frame._build_sql()
    assert "price * 0.9" in sql
    assert "discounted" in sql
    assert "SELECT * FROM products" in sql


def test_build_sql_structure(with_col_frame):
    sql = with_col_frame._build_sql()
    # Should be a subquery pattern
    assert sql.strip().upper().startswith("SELECT")
    assert "AS discounted" in sql


def test_to_pandas_calls_query(fake_conn, with_col_frame):
    result = with_col_frame.to_pandas()
    assert fake_conn.last_sql is not None
    assert isinstance(result, pd.DataFrame)
    assert "discounted" in result.columns


def test_where_appended_to_sql(fake_conn):
    source = FakeFrame(fake_conn)
    frame = WithColumnFrame(
        conn=fake_conn,
        source=source,
        col_name="tax",
        expression="price * 0.2",
    )
    filtered = frame.where("price > 5")
    sql = filtered._build_sql()
    assert "price > 5" in sql
    assert "WHERE" in sql.upper()


def test_limit_appended_to_sql(fake_conn):
    source = FakeFrame(fake_conn)
    frame = WithColumnFrame(
        conn=fake_conn,
        source=source,
        col_name="tax",
        expression="price * 0.2",
    )
    limited = frame.limit(5)
    sql = limited._build_sql()
    assert "LIMIT 5" in sql


def test_repr(with_col_frame):
    r = repr(with_col_frame)
    assert "WithColumnFrame" in r
    assert "discounted" in r


def test_with_column_mixin(fake_conn):
    from sqlframe.frame_withcolumn_mixin import WithColumnMixin

    class MyFrame(WithColumnMixin):
        def __init__(self, conn):
            self._conn = conn
            self._table = "orders"

        def _build_sql(self):
            return "SELECT * FROM orders"

    frame = MyFrame(fake_conn)
    result = frame.with_column("total", "qty * unit_price")
    assert isinstance(result, WithColumnFrame)
    assert result._col_name == "total"
    assert result._expression == "qty * unit_price"
