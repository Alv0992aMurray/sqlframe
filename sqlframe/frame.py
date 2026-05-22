from __future__ import annotations
from typing import List, Optional

from sqlframe.frame_window_mixin import WindowMixin
from sqlframe.frame_pivot_mixin import PivotMixin
from sqlframe.frame_cache_mixin import CacheMixin
from sqlframe.frame_explain_mixin import ExplainMixin
from sqlframe.frame_export_mixin import ExportMixin
from sqlframe.frame_schema_mixin import SchemaMixin
from sqlframe.frame_distinct_mixin import DistinctMixin
from sqlframe.frame_cast_mixin import CastMixin
from sqlframe.frame_union_mixin import UnionMixin
from sqlframe.frame_fillna_mixin import FillNaMixin


class SqlFrame(
    WindowMixin,
    PivotMixin,
    CacheMixin,
    ExplainMixin,
    ExportMixin,
    SchemaMixin,
    DistinctMixin,
    CastMixin,
    UnionMixin,
    FillNaMixin,
):
    """Core lazy frame wrapping a single table query."""

    def __init__(
        self,
        conn,
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[str] = None,
        order: Optional[List[str]] = None,
        limit_val: Optional[int] = None,
    ):
        self._conn = conn
        self._table = table
        self._columns = columns or []
        self._where = where
        self._order = order or []
        self._limit_val = limit_val

    # ------------------------------------------------------------------
    # Transformation helpers
    # ------------------------------------------------------------------

    def select(self, *columns: str) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, list(columns),
            self._where, self._order, self._limit_val,
        )

    def where(self, condition: str) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, self._columns,
            condition, self._order, self._limit_val,
        )

    def order_by(self, *columns: str) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, self._columns,
            self._where, list(columns), self._limit_val,
        )

    def limit(self, n: int) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, self._columns,
            self._where, self._order, n,
        )

    # ------------------------------------------------------------------
    # SQL building
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        cols = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT {cols} FROM {self._table}"
        if self._where:
            sql += f" WHERE {self._where}"
        if self._order:
            sql += f" ORDER BY {', '.join(self._order)}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def to_pandas(self):
        return self._conn.query(self._build_sql())

    def agg(self, *args, **kwargs):
        from sqlframe.aggregations import AggFrame
        return AggFrame(self._conn, self._table, list(args) or list(kwargs.values()))

    def __repr__(self) -> str:
        return f"SqlFrame(table={self._table!r}, sql={self._build_sql()!r})"
