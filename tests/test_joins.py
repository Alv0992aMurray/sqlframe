import pytest
import pandas as pd
from sqlframe.joins import JoinFrame
from sqlframe.frame import SqlFrame


class FakeConn:
    """Minimal connection stub that records the last SQL query executed."""

    def __init__(self):
        self.last_sql: str = ""

    def query(self, sql: str, params=None) -> pd.DataFrame:
        self.last_sql = sql
        return pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def join_frame(fake_conn):
    return JoinFrame(
        conn=fake_conn,
        left_table="orders",
        right_table="customers",
        on=["customer_id"],
        how="inner",
    )


# ------------------------------------------------------------------
# JoinFrame SQL generation
# ------------------------------------------------------------------

def test_default_join_sql(join_frame):
    sql = join_frame._build_sql()
    assert "INNER JOIN" in sql
    assert "orders AS l" in sql
    assert "customers AS r" in sql
    assert "l.customer_id = r.customer_id" in sql
    assert "SELECT *" in sql


def test_left_join_type(fake_conn):
    jf = JoinFrame(fake_conn, "orders", "customers", on=["customer_id"], how="left")
    assert "LEFT JOIN" in jf._build_sql()


def test_invalid_join_type_raises(fake_conn):
    with pytest.raises(ValueError, match="Invalid join type"):
        JoinFrame(fake_conn, "orders", "customers", on=["id"], how="cross")


def test_select_columns(join_frame):
    sql = join_frame.select("l.id", "r.name")._build_sql()
    assert "SELECT l.id, r.name" in sql


def test_where_clause(join_frame):
    sql = join_frame.where("l.amount > 100")._build_sql()
    assert "WHERE l.amount > 100" in sql


def test_multiple_where_clauses(join_frame):
    sql = join_frame.where("l.amount > 100").where("r.active = 1")._build_sql()
    assert "l.amount > 100" in sql
    assert "r.active = 1" in sql


def test_limit_clause(join_frame):
    sql = join_frame.limit(50)._build_sql()
    assert "LIMIT 50" in sql


def test_chaining_is_immutable(join_frame):
    """Verify that chained calls don't mutate the original JoinFrame."""
    filtered = join_frame.where("l.id > 1")
    assert "WHERE" not in join_frame._build_sql()
    assert "WHERE" in filtered._build_sql()


def test_to_pandas_returns_dataframe(join_frame, fake_conn):
    result = join_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert "INNER JOIN" in fake_conn.last_sql


def test_multi_column_join(fake_conn):
    jf = JoinFrame(fake_conn, "a", "b", on=["id", "region"])
    sql = jf._build_sql()
    assert "l.id = r.id" in sql
    assert "l.region = r.region" in sql


# ------------------------------------------------------------------
# SqlFrame.join integration
# ------------------------------------------------------------------

def test_sqlframe_join_returns_joinframe(fake_conn):
    sf = SqlFrame(fake_conn, "orders")
    result = sf.join("customers", on=["customer_id"], how="left")
    assert isinstance(result, JoinFrame)
    assert result._how == "left"
    assert result._left_table == "orders"
    assert result._right_table == "customers"
