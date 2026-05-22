"""Core SqlFrame class — wraps a lazy SQL query and exposes a pandas-like API."""
from __future__ import annotations

from typing import List, Optional, Union

from sqlframe.frame_cache_mixin import CacheMixin
from sqlframe.frame_explain_mixin import ExplainMixin
from sqlframe.frame_export_mixin import ExportMixin
from sqlframe.frame_pivot_mixin import PivotMixin
from sqlframe.frame_window_mixin import WindowMixin


class SqlFrame(CacheMixin, ExplainMixin, ExportMixin, PivotMixin, WindowMixin):
    """Lazy SQL-backed frame."""

    def __init__(
        self,
        conn,
        table: str,
        columns: str = "*",
        where_clause: Optional[str] = None,
        order_clause: Optional[str] = None,
        limit_val: Optional[int] = None,
        params: Optional[list] = None,
    ):
        self._conn = conn
        self._table = table
        self._columns = columns
        self._where = where_clause
        self._order = order_clause
        self._limit = limit_val
        self._params = params or []

    # ------------------------------------------------------------------
    # Query builders
    # ------------------------------------------------------------------

    def select(self, *columns: str) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, ", ".join(columns),
            self._where, self._order, self._limit, self._params,
        )

    def where(self, condition: str, params: Optional[list] = None) -> "SqlFrame":
        extra = params or []
        new_params = self._params + extra
        clause = f"({self._where}) AND ({condition})" if self._where else condition
        return SqlFrame(
            self._conn, self._table, self._columns,
            clause, self._order, self._limit, new_params,
        )

    def order_by(self, *columns: str) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, self._columns,
            self._where, ", ".join(columns), self._limit, self._params,
        )

    def limit(self, n: int) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, self._columns,
            self._where, self._order, n, self._params,
        )

    # ------------------------------------------------------------------
    # SQL generation
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        sql = f"SELECT {self._columns} FROM {self._table}"
        if self._where:
            sql += f" WHERE {self._where}"
        if self._order:
            sql += f" ORDER BY {self._order}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        return sql

    # ------------------------------------------------------------------
    # Aggregations
    # ------------------------------------------------------------------

    def groupby(self, *columns: str):
        from sqlframe.aggregations import AggFrame
        return AggFrame(self._conn, self._table, list(columns), self._where, self._params)

    def agg(self, **kwargs):
        return self.groupby().agg(**kwargs)

    # ------------------------------------------------------------------
    # Materialisation
    # ------------------------------------------------------------------

    def to_pandas(self):
        return self._conn.query(self._build_sql(), params=self._params)

    def __repr__(self) -> str:
        return f"<SqlFrame sql={self._build_sql()!r}>"
