from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from sqlframe.connection import Connection

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
from sqlframe.frame_between_mixin import BetweenMixin
from sqlframe.frame_sample_mixin import SampleMixin
from sqlframe.frame_withcolumn_mixin import WithColumnMixin
from sqlframe.frame_isin_mixin import IsInMixin
from sqlframe.frame_search_mixin import SearchMixin
from sqlframe.frame_percentile_mixin import PercentileMixin


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
    BetweenMixin,
    SampleMixin,
    WithColumnMixin,
    IsInMixin,
    SearchMixin,
    PercentileMixin,
):
    """Lazy SQL-backed DataFrame-like object."""

    def __init__(
        self,
        conn: "Connection",
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[str] = None,
        limit_val: Optional[int] = None,
        order: Optional[List[str]] = None,
    ):
        self._conn = conn
        self._table = table
        self._columns = columns or ["*"]
        self._where = where
        self._limit_val = limit_val
        self._order = order or []

    # ------------------------------------------------------------------
    # Core query-building helpers
    # ------------------------------------------------------------------

    def select(self, *columns: str) -> "SqlFrame":
        return SqlFrame(self._conn, self._table, list(columns), self._where, self._limit_val, self._order)

    def where(self, condition: str) -> "SqlFrame":
        existing = self._where
        new_clause = f"({existing}) AND ({condition})" if existing else condition
        return SqlFrame(self._conn, self._table, self._columns, new_clause, self._limit_val, self._order)

    def order_by(self, *columns: str) -> "SqlFrame":
        return SqlFrame(self._conn, self._table, self._columns, self._where, self._limit_val, list(columns))

    def limit(self, n: int) -> "SqlFrame":
        return SqlFrame(self._conn, self._table, self._columns, self._where, n, self._order)

    # ------------------------------------------------------------------
    # SQL generation
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._where:
            sql += f" WHERE {self._where}"
        if self._order:
            sql += " ORDER BY " + ", ".join(self._order)
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def to_pandas(self):
        return self._conn.query(self._build_sql())

    def __repr__(self) -> str:
        return f"SqlFrame(table={self._table!r}, sql={self._build_sql()!r})"
