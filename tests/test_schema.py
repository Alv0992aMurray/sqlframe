"""Tests for schema inspection (SchemaInspector, TableSchema, SchemaMixin)."""
import pytest
import pandas as pd
from sqlframe.schema import ColumnInfo, TableSchema, SchemaInspector


# ---------------------------------------------------------------------------
# Helpers / fakes
# ---------------------------------------------------------------------------

INFO_SCHEMA_ROWS = pd.DataFrame(
    {
        "column_name": ["id", "name", "score"],
        "data_type": ["integer", "varchar", "numeric"],
        "is_nullable": ["NO", "YES", "YES"],
    }
)


class FakeConn:
    def __init__(self):
        self.queries = []
        self._schema_inspector = None

    def query(self, sql, params=None):
        self.queries.append((sql, params))
        return INFO_SCHEMA_ROWS


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def inspector(fake_conn):
    return SchemaInspector(fake_conn)


# ---------------------------------------------------------------------------
# ColumnInfo
# ---------------------------------------------------------------------------

def test_column_info_repr_with_pk():
    col = ColumnInfo(name="id", dtype="integer", nullable=False, primary_key=True)
    assert "PK" in repr(col)
    assert "NOT NULL" in repr(col)


def test_column_info_repr_nullable():
    col = ColumnInfo(name="name", dtype="varchar")
    assert "NOT NULL" not in repr(col)
    assert "PK" not in repr(col)


# ---------------------------------------------------------------------------
# TableSchema
# ---------------------------------------------------------------------------

def test_table_schema_column_names():
    cols = [ColumnInfo("a", "int"), ColumnInfo("b", "text")]
    ts = TableSchema(table="t", columns=cols)
    assert ts.column_names() == ["a", "b"]


def test_table_schema_dtypes():
    cols = [ColumnInfo("a", "int"), ColumnInfo("b", "text")]
    ts = TableSchema(table="t", columns=cols)
    assert ts.dtypes() == {"a": "int", "b": "text"}


def test_table_schema_repr_contains_table_name():
    ts = TableSchema(table="users", columns=[])
    assert "users" in repr(ts)


# ---------------------------------------------------------------------------
# SchemaInspector
# ---------------------------------------------------------------------------

def test_inspect_returns_table_schema(inspector):
    result = inspector.inspect("users")
    assert isinstance(result, TableSchema)
    assert result.table == "users"
    assert len(result.columns) == 3


def test_inspect_maps_nullable_correctly(inspector):
    result = inspector.inspect("users")
    id_col = next(c for c in result.columns if c.name == "id")
    assert id_col.nullable is False
    name_col = next(c for c in result.columns if c.name == "name")
    assert name_col.nullable is True


def test_inspect_caches_result(inspector, fake_conn):
    inspector.inspect("users")
    inspector.inspect("users")
    assert len(fake_conn.queries) == 1  # second call hits cache


def test_inspect_force_bypasses_cache(inspector, fake_conn):
    inspector.inspect("users")
    inspector.inspect("users", force=True)
    assert len(fake_conn.queries) == 2


def test_clear_cache_forces_refetch(inspector, fake_conn):
    inspector.inspect("users")
    inspector.clear_cache()
    inspector.inspect("users")
    assert len(fake_conn.queries) == 2


# ---------------------------------------------------------------------------
# SchemaMixin integration
# ---------------------------------------------------------------------------

class FakeFrame:
    """Minimal frame that uses SchemaMixin."""
    from sqlframe.frame_schema_mixin import SchemaMixin

    def __init__(self, conn, table):
        self._conn = conn
        self._table = table

    # Attach mixin methods directly for test simplicity
    from sqlframe.frame_schema_mixin import SchemaMixin
    schema = SchemaMixin.schema
    dtypes = SchemaMixin.dtypes
    column_names = SchemaMixin.column_names


def test_mixin_schema(fake_conn):
    frame = FakeFrame(fake_conn, "users")
    s = frame.schema()
    assert s.table == "users"


def test_mixin_dtypes(fake_conn):
    frame = FakeFrame(fake_conn, "users")
    d = frame.dtypes()
    assert "id" in d
    assert d["id"] == "integer"


def test_mixin_column_names(fake_conn):
    frame = FakeFrame(fake_conn, "users")
    assert frame.column_names() == ["id", "name", "score"]


def test_mixin_creates_inspector_lazily(fake_conn):
    assert not hasattr(fake_conn, "_schema_inspector") or fake_conn._schema_inspector is None
    frame = FakeFrame(fake_conn, "users")
    frame.schema()
    assert hasattr(fake_conn, "_schema_inspector")
