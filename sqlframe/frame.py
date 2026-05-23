from __future__ import annotations
from typing import Optional, TYPE_CHECKING

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
):
    """Lazy SQL-backed DataFrame wrapper."""

    def __init__(
        self,
        conn: "Connection",
        table: str,
        columns: Optional[list[str]] = None,
        where_clause: Optional[str] = None,
        params: Optional[list] = None,
        _limit: Optional[int] = None,
        _order_by: Optional[list[str]] = None,
    ):
        self._conn = conn
        self._table = table
        self._columns = columns or ["*"]
        self._where_clause = where_clause
        self._params = params or []
        self._limit = _limit
        self._order_by = _order_by or []

    def select(self, *columns: str) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, list(columns),
            self._where_clause, self._params, self._limit, self._order_by,
        )

    def where(self, condition: str, params: Optional[list] = None) -> "SqlFrame":
        extra = params or []
        combined = self._params + extra
        if self._where_clause:
            new_where = f"({self._where_clause}) AND ({condition})"
        else:
            new_where = condition
        return SqlFrame(
            self._conn, self._table, self._columns,
            new_where, combined, self._limit, self._order_by,
        )

    def order_by(self, *columns: str) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, self._columns,
            self._where_clause, self._params, self._limit, list(columns),
        )

    def limit(self, n: int) -> "SqlFrame":
        return SqlFrame(
            self._conn, self._table, self._columns,
            self._where_clause, self._params, n, self._order_by,
        )

    def _build_sql(self) -> tuple[str, list]:
        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"
        params = list(self._params)
        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        if self._order_by:
            order_str = ", ".join(self._order_by)
            sql += f" ORDER BY {order_str}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        return sql, params

    def to_pandas(self):
        sql, params = self._build_sql()
        return self._conn.query(sql, params=params)

    def agg(self, **aggregations):
        from sqlframe.aggregations import AggFrame
        return AggFrame(self._conn, self._table, aggregations, self._where_clause, self._params)

    def join(self, other: "SqlFrame", on: str, how: str = "inner"):
        from sqlframe.joins import JoinFrame
        return JoinFrame(self._conn, self._table, other._table, on, how)

    def sample(self, n: int = 100, method: str = "random"):
        from sqlframe.sampling import SampleFrame
        return SampleFrame(self._conn, self._table, n, method, self._where_clause, self._params)

    def __repr__(self) -> str:
        sql, params = self._build_sql()
        return f"SqlFrame(sql={sql!r}, params={params!r})"
