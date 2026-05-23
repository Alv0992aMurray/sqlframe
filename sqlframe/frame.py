"""Core SqlFrame — wraps a table reference and builds SELECT queries."""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

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
from sqlframe.frame_orderby_mixin import OrderByMixin
from sqlframe.frame_head_mixin import HeadMixin
from sqlframe.frame_describe_mixin import DescribeMixin
from sqlframe.frame_topn_mixin import TopNMixin

if TYPE_CHECKING:
    import pandas as pd


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
    OrderByMixin,
    HeadMixin,
    DescribeMixin,
    TopNMixin,
):
    """Lazy representation of a SQL SELECT against a single table."""

    def __init__(
        self,
        conn,
        table: str,
        columns: Optional[List[str]] = None,
        where_clause: Optional[str] = None,
        order_clause: Optional[str] = None,
        limit_val: Optional[int] = None,
        params: Optional[dict] = None,
    ):
        self._conn = conn
        self._table = table
        self._columns = columns or []
        self._where_clause = where_clause
        self._order_clause = order_clause
        self._limit_val = limit_val
        self._params = params or {}

    # ------------------------------------------------------------------
    # Builder methods
    # ------------------------------------------------------------------

    def select(self, *columns: str) -> "SqlFrame":
        return SqlFrame(self._conn, self._table, list(columns),
                        self._where_clause, self._order_clause,
                        self._limit_val, self._params)

    def where(self, condition: str, **params) -> "SqlFrame":
        merged = {**self._params, **params}
        clause = (f"({self._where_clause}) AND ({condition})"
                  if self._where_clause else condition)
        return SqlFrame(self._conn, self._table, self._columns,
                        clause, self._order_clause, self._limit_val, merged)

    def order_by(self, *columns: str) -> "SqlFrame":
        clause = ", ".join(columns)
        return SqlFrame(self._conn, self._table, self._columns,
                        self._where_clause, clause, self._limit_val, self._params)

    def limit(self, n: int) -> "SqlFrame":
        return SqlFrame(self._conn, self._table, self._columns,
                        self._where_clause, self._order_clause, n, self._params)

    # ------------------------------------------------------------------
    # SQL / execution
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        cols = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT {cols} FROM {self._table}"
        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        if self._order_clause:
            sql += f" ORDER BY {self._order_clause}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def to_pandas(self) -> "pd.DataFrame":
        return self._conn.query(self._build_sql(), self._params)

    def groupby(self, *columns: str):
        from sqlframe.aggregations import AggFrame
        return AggFrame(self._conn, self._table, list(columns),
                        self._where_clause, self._params)

    def join(self, other: "SqlFrame", on: str, how: str = "inner"):
        from sqlframe.joins import JoinFrame
        return JoinFrame(self._conn, self._table, other._table,
                         on, how, self._params)

    def sample(self, n: int = 100):
        from sqlframe.sampling import SampleFrame
        return SampleFrame(self._conn, self._table, n,
                           self._where_clause, self._params)

    def __repr__(self) -> str:
        return f"SqlFrame(table={self._table!r}, sql={self._build_sql()!r})"
