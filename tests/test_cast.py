import pytest
import pandas as pd
from sqlframe.cast import CastFrame, resolve_type
from sqlframe.frame_cast_mixin import CastMixin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql = None

    def query(self, sql, params=None):
        self.last_sql = sql
        return pd.DataFrame()


class FakeFrame(CastMixin):
    def __init__(self, columns, table="orders", where=None, limit=None):
        self._conn = FakeConn()
        self._table = table
        self._columns = columns
        self._where_clause = where
        self._limit_val = limit
        self._params = []


@pytest.fixture
def frame():
    return FakeFrame(columns=["id", "amount", "created_at"])


# ---------------------------------------------------------------------------
# resolve_type
# ---------------------------------------------------------------------------

def test_resolve_type_alias_int():
    assert resolve_type("int") == "INTEGER"


def test_resolve_type_alias_str():
    assert resolve_type("str") == "VARCHAR"


def test_resolve_type_alias_datetime():
    assert resolve_type("datetime") == "TIMESTAMP"


def test_resolve_type_unknown_passthrough():
    assert resolve_type("JSONB") == "JSONB"


# ---------------------------------------------------------------------------
# CastFrame._build_sql
# ---------------------------------------------------------------------------

def test_build_sql_single_cast(frame):
    cf = frame.cast({"amount": "float"})
    sql = cf._build_sql()
    assert "CAST(amount AS FLOAT) AS amount" in sql
    assert "id" in sql
    assert "created_at" in sql


def test_build_sql_multiple_casts(frame):
    cf = frame.cast({"amount": "numeric", "id": "int"})
    sql = cf._build_sql()
    assert "CAST(amount AS NUMERIC) AS amount" in sql
    assert "CAST(id AS INTEGER) AS id" in sql


def test_build_sql_with_where(frame):
    cf = frame.cast({"amount": "float"})
    cf.where("amount > 0")
    sql = cf._build_sql()
    assert "WHERE amount > 0" in sql


def test_build_sql_with_limit(frame):
    cf = frame.cast({"amount": "float"})
    cf.limit(50)
    sql = cf._build_sql()
    assert "LIMIT 50" in sql


def test_build_sql_no_cast_columns_unchanged(frame):
    cf = frame.cast({"amount": "float"})
    sql = cf._build_sql()
    # id and created_at should appear without CAST
    assert "CAST(id" not in sql
    assert "CAST(created_at" not in sql


# ---------------------------------------------------------------------------
# CastMixin validation
# ---------------------------------------------------------------------------

def test_cast_unknown_column_raises(frame):
    with pytest.raises(ValueError, match="not in current selection"):
        frame.cast({"nonexistent": "int"})


def test_cast_wildcard_raises():
    f = FakeFrame(columns=["*"])
    with pytest.raises(ValueError, match="explicit column selection"):
        f.cast({"amount": "int"})


# ---------------------------------------------------------------------------
# to_pandas delegates to connection
# ---------------------------------------------------------------------------

def test_to_pandas_calls_conn(frame):
    cf = frame.cast({"amount": "float"})
    result = cf.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert cf._conn.last_sql is not None
    assert "CAST(amount AS FLOAT)" in cf._conn.last_sql


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------

def test_repr(frame):
    cf = frame.cast({"amount": "float"})
    r = repr(cf)
    assert "CastFrame" in r
    assert "orders" in r
