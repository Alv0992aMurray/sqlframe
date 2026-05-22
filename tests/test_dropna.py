import pytest
import pandas as pd
from sqlframe.dropna import DropNaFrame


class FakeConn:
    def __init__(self):
        self.last_sql = None

    def query(self, sql, params=None):
        self.last_sql = sql
        if "LIMIT 0" in sql:
            return pd.DataFrame(columns=["id", "name", "score"])
        return pd.DataFrame({"id": [1], "name": ["Alice"], "score": [9.5]})


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def dropna_frame(fake_conn):
    return DropNaFrame(fake_conn, "users", columns=["name", "score"])


def test_invalid_how_raises(fake_conn):
    with pytest.raises(ValueError, match="how must be"):
        DropNaFrame(fake_conn, "users", how="none")


def test_build_sql_any(dropna_frame):
    sql = dropna_frame._build_sql(["name", "score"])
    assert "NOT (name IS NULL OR score IS NULL)" in sql
    assert "SELECT * FROM users" in sql


def test_build_sql_all(fake_conn):
    frame = DropNaFrame(fake_conn, "users", columns=["name", "score"], how="all")
    sql = frame._build_sql(["name", "score"])
    assert "name IS NOT NULL OR score IS NOT NULL" in sql


def test_build_sql_with_limit(dropna_frame):
    limited = dropna_frame.limit(10)
    sql = limited._build_sql(["name", "score"])
    assert "LIMIT 10" in sql


def test_build_sql_without_limit(dropna_frame):
    sql = dropna_frame._build_sql(["name", "score"])
    assert "LIMIT" not in sql


def test_where_adds_filter(dropna_frame):
    filtered = dropna_frame.where("id > 5")
    sql = filtered._build_sql(["name", "score"])
    assert "(id > 5)" in sql


def test_where_is_immutable(dropna_frame):
    filtered = dropna_frame.where("id > 5")
    assert dropna_frame._where_clauses == []
    assert filtered._where_clauses == ["id > 5"]


def test_limit_is_immutable(dropna_frame):
    limited = dropna_frame.limit(5)
    assert dropna_frame._limit_val is None
    assert limited._limit_val == 5


def test_to_pandas_with_explicit_columns(dropna_frame, fake_conn):
    result = dropna_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)
    sql = fake_conn.last_sql
    assert "name IS NULL" in sql
    assert "score IS NULL" in sql


def test_to_pandas_infers_columns(fake_conn):
    frame = DropNaFrame(fake_conn, "users")  # no columns specified
    result = frame.to_pandas()
    assert isinstance(result, pd.DataFrame)
    # Should have queried LIMIT 0 first to get columns
    assert "LIMIT 0" in fake_conn.last_sql or "IS NULL" in fake_conn.last_sql


def test_repr(dropna_frame):
    r = repr(dropna_frame)
    assert "DropNaFrame" in r
    assert "users" in r
    assert "any" in r


def test_multiple_where_clauses(dropna_frame):
    filtered = dropna_frame.where("age > 18").where("active = true")
    sql = filtered._build_sql(["name", "score"])
    assert "(age > 18)" in sql
    assert "(active = true)" in sql
