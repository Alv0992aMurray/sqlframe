"""Core SqlFrame – wraps a lazily-built SELECT statement."""
from __future__ import annotations
from typing import List, Optional

from sqlframe.frame_window_mixin import WindowMixin


class SqlFrame(WindowMixin):
    """Lazy representation of a SQL SELECT query."""

    def __init__(self, conn, table: str) -> None:
        self._conn = conn
        self._table = table
        self._columns: List[str] = ["*"]
        self._where_clauses: List[str] = []
        self._order_cols: List[str] = []
        self._limit_val: Optional[int] = None

    # ------------------------------------------------------------------ #
    # Builder methods                                                       #
    # ------------------------------------------------------------------ #

    def select(self, *columns: str) -> "SqlFrame":
        self._columns = list(columns)
        return self

    def where(self, condition: str) -> "SqlFrame":
        self._where_clauses.append(condition)
        return self

    def order_by(self, *columns: str) -> "SqlFrame":
        self._order_cols = list(columns)
        return self

    def limit(self, n: int) -> "SqlFrame":
        self._limit_val = n
        return self

    def join(
        self,
        other: "SqlFrame",
        on: str,
        how: str = "inner",
    ):
        from sqlframe.joins import JoinFrame

        return JoinFrame(
            conn=self._conn,
            left_sql=self._build_sql(),
            right_sql=other._build_sql(),
            on=on,
            how=how,
        )

    def groupby(self, *columns: str):
        from sqlframe.aggregations import AggFrame

        return AggFrame(
            conn=self._conn,
            base_sql=self._build_sql(),
            group_cols=list(columns),
        )

    # ------------------------------------------------------------------ #
    # SQL construction                                                      #
    # ------------------------------------------------------------------ #

    def _build_sql(self) -> str:
        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(
                f"({c})" for c in self._where_clauses
            )
        if self._order_cols:
            sql += " ORDER BY " + ", ".join(self._order_cols)
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    # ------------------------------------------------------------------ #
    # Execution                                                             #
    # ------------------------------------------------------------------ #

    def to_pandas(self):
        return self._conn.query(self._build_sql())

    def count(self) -> int:
        sql = f"SELECT COUNT(*) AS n FROM ({self._build_sql()}) AS _c"
        df = self._conn.query(sql)
        return int(df.iloc[0, 0])

    def head(self, n: int = 5):
        return self.limit(n).to_pandas()

    def __repr__(self) -> str:  # pragma: no cover
        return f"SqlFrame(sql={self._build_sql()!r})"
