"""Tests for sqlframe.rename.RenameFrame."""

import pandas as pd
import pytest
from sqlframe.rename import RenameFrame


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self):
        self.last_sql = None
        self.last_params = None

    def query(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params
        return pd.DataFrame()


class FakeFrame:
    """Minimal stand-in for SqlFrame / JoinFrame."""

    def __init__(self, sql, params=None, columns=None):
        self._sql = sql
        self._params = params or []
        self._columns = columns
        self.conn = FakeConn()

    def _build_sql(self):
        return self._sql, self._params


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_frame():
    return FakeFrame(
        sql="SELECT id, first_name, salary FROM employees",
        columns=["id", "first_name", "salary"],
    )


@pytest.fixture
def rename_frame(base_frame):
    return RenameFrame(base_frame, {"first_name": "name", "salary": "pay"})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rename_wraps_inner_query(rename_frame):
    sql, _ = rename_frame._build_sql()
    assert "_renamed" in sql
    assert "SELECT id, first_name AS name, salary AS pay" in sql


def test_rename_preserves_unmapped_columns(rename_frame):
    sql, _ = rename_frame._build_sql()
    # 'id' should appear without an alias
    assert "id" in sql
    assert "id AS" not in sql


def test_rename_params_forwarded(base_frame):
    base_frame._params = [42]
    rf = RenameFrame(base_frame, {"first_name": "name"})
    _, params = rf._build_sql()
    assert params == [42]


def test_empty_mapping_returns_original_sql(base_frame):
    rf = RenameFrame(base_frame, {})
    sql, params = rf._build_sql()
    assert sql == base_frame._sql
    assert params == base_frame._params


def test_rename_without_columns_falls_back_to_star(base_frame):
    base_frame._columns = None
    rf = RenameFrame(base_frame, {"first_name": "name"})
    sql, _ = rf._build_sql()
    assert "*" in sql
    assert "first_name AS name" in sql


def test_to_pandas_calls_conn_query(rename_frame):
    result = rename_frame.to_pandas()
    assert isinstance(result, pd.DataFrame)
    assert rename_frame.conn.last_sql is not None
    assert "_renamed" in rename_frame.conn.last_sql


def test_conn_is_inherited_from_parent(base_frame):
    rf = RenameFrame(base_frame, {"id": "pk"})
    assert rf.conn is base_frame.conn
