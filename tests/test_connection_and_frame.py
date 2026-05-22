"""Tests for Connection and SqlFrame using an in-memory SQLite database."""

import pytest
import pandas as pd

from sqlframe import Connection, SqlFrame, read_table


@pytest.fixture()
def conn():
    """Provide a Connection backed by an in-memory SQLite DB with sample data."""
    c = Connection.from_url("sqlite:///:memory:")
    c.execute(
        "CREATE TABLE sales (id INTEGER PRIMARY KEY, product TEXT, amount REAL)"
    )
    for row in [
        (1, "apple", 10.0),
        (2, "banana", 5.5),
        (3, "cherry", 20.0),
        (4, "apple", 15.0),
    ]:
        c.execute(
            "INSERT INTO sales (id, product, amount) VALUES (:id, :p, :a)",
            {"id": row[0], "p": row[1], "a": row[2]},
        )
    return c


# ------------------------------------------------------------------
# Connection tests
# ------------------------------------------------------------------

def test_connection_query_returns_dataframe(conn):
    df = conn.query("SELECT * FROM sales")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert list(df.columns) == ["id", "product", "amount"]


def test_connection_query_with_params(conn):
    df = conn.query("SELECT * FROM sales WHERE product = :p", {"p": "apple"})
    assert len(df) == 2
    assert (df["product"] == "apple").all()


# ------------------------------------------------------------------
# SqlFrame tests
# ------------------------------------------------------------------

def test_read_table_returns_sqlframe(conn):
    sf = read_table(conn, "sales")
    assert isinstance(sf, SqlFrame)


def test_sqlframe_to_pandas(conn):
    df = read_table(conn, "sales").to_pandas()
    assert len(df) == 4


def test_sqlframe_limit(conn):
    df = read_table(conn, "sales").limit(2).to_pandas()
    assert len(df) == 2


def test_sqlframe_where(conn):
    df = read_table(conn, "sales").where("amount > 10").to_pandas()
    assert all(df["amount"] > 10)


def test_sqlframe_select(conn):
    df = read_table(conn, "sales").select("product", "amount").to_pandas()
    assert list(df.columns) == ["product", "amount"]


def test_sqlframe_chaining(conn):
    df = (
        read_table(conn, "sales")
        .where("product = 'apple'")
        .select("id", "amount")
        .limit(1)
        .to_pandas()
    )
    assert len(df) == 1
    assert list(df.columns) == ["id", "amount"]


def test_sqlframe_immutable_chaining(conn):
    """Chaining should not mutate the original SqlFrame."""
    base = read_table(conn, "sales")
    _ = base.limit(1)
    df = base.to_pandas()
    assert len(df) == 4  # original unchanged


def test_sqlframe_where_no_results(conn):
    """A where clause matching no rows should return an empty DataFrame."""
    df = read_table(conn, "sales").where("amount > 9999").to_pandas()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert list(df.columns) == ["id", "product", "amount"]
