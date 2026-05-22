"""Tests for sqlframe.explain and ExplainMixin."""
from __future__ import annotations

from typing import Any, List, Optional

import pandas as pd
import pytest

from sqlframe.explain import Explainer, ExplainResult
from sqlframe.frame_explain_mixin import ExplainMixin


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class FakeConn:
    """Returns a configurable DataFrame from .query()."""

    dialect = "postgresql"

    def __init__(self, rows: List[dict]) -> None:
        self._rows = rows
        self.last_sql: str = ""

    def query(self, sql: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        self.last_sql = sql
        return pd.DataFrame(self._rows)


class FakeFrame(ExplainMixin):
    """Minimal frame that satisfies ExplainMixin contract."""

    def __init__(self, conn: FakeConn, sql: str, params: Optional[List[Any]] = None) -> None:
        self._conn = conn
        self._sql = sql
        self._params = params or []


class FakeFrameWithBuildSql(ExplainMixin):
    """Frame that uses _build_sql() instead of _sql."""

    def __init__(self, conn: FakeConn, sql: str) -> None:
        self._conn = conn
        self._sql_template = sql
        self._params: List[Any] = []

    def _build_sql(self) -> str:
        return self._sql_template


# ---------------------------------------------------------------------------
# ExplainResult tests
# ---------------------------------------------------------------------------

def test_explain_result_stores_fields():
    result = ExplainResult(sql="SELECT 1", plan_rows=["Seq Scan rows=10"], dialect="postgresql")
    assert result.sql == "SELECT 1"
    assert result.plan_rows == ["Seq Scan rows=10"]
    assert result.dialect == "postgresql"


# ---------------------------------------------------------------------------
# Explainer tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def pg_conn():
    return FakeConn([{"QUERY PLAN": "Seq Scan on orders  (cost=0.00..1.01 rows=1 width=8)"}])


def test_explainer_prepends_correct_prefix(pg_conn):
    explainer = Explainer(pg_conn, dialect="postgresql")
    explainer.explain("SELECT * FROM orders")
    assert pg_conn.last_sql.startswith("EXPLAIN (FORMAT TEXT)")


def test_explainer_generic_prefix():
    conn = FakeConn([{"detail": "scan"}])
    explainer = Explainer(conn, dialect="generic")
    explainer.explain("SELECT 1")
    assert conn.last_sql.startswith("EXPLAIN SELECT 1")


def test_explainer_parses_estimated_rows(pg_conn):
    explainer = Explainer(pg_conn, dialect="postgresql")
    result = explainer.explain("SELECT * FROM orders")
    assert result.estimated_rows == 1


def test_explainer_no_estimated_rows_when_absent():
    conn = FakeConn([{"detail": "no row estimate here"}])
    explainer = Explainer(conn, dialect="sqlite")
    result = explainer.explain("SELECT 1")
    assert result.estimated_rows is None


# ---------------------------------------------------------------------------
# ExplainMixin tests
# ---------------------------------------------------------------------------

def test_mixin_uses_sql_attribute(pg_conn):
    frame = FakeFrame(pg_conn, "SELECT id FROM users")
    result = frame.explain()
    assert "SELECT id FROM users" in pg_conn.last_sql
    assert isinstance(result, ExplainResult)


def test_mixin_uses_build_sql(pg_conn):
    frame = FakeFrameWithBuildSql(pg_conn, "SELECT * FROM events")
    result = frame.explain()
    assert "SELECT * FROM events" in pg_conn.last_sql
    assert isinstance(result, ExplainResult)


def test_mixin_dialect_override(pg_conn):
    frame = FakeFrame(pg_conn, "SELECT 1")
    frame.explain(dialect="mysql")
    assert pg_conn.last_sql.startswith("EXPLAIN SELECT 1")


def test_mixin_uses_conn_dialect_by_default(pg_conn):
    frame = FakeFrame(pg_conn, "SELECT 1")
    frame.explain()  # pg_conn.dialect == 'postgresql'
    assert pg_conn.last_sql.startswith("EXPLAIN (FORMAT TEXT)")


def test_mixin_raises_on_missing_sql():
    class BadFrame(ExplainMixin):
        _conn = FakeConn([])
        _params: List[Any] = []

    with pytest.raises(AttributeError):
        BadFrame().explain()
