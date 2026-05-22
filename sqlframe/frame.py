from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
import pandas as pd

if TYPE_CHECKING:
    from sqlframe.connection import Connection


class SqlFrame:
    """
    Lazy SQL query builder that wraps a table and supports
    method chaining for select, filter, limit, and join operations.
    """

    def __init__(self, conn: "Connection", table: str):
        self._conn = conn
        self._table = table
        self._select_cols: List[str] = []
        self._where_clauses: List[str] = []
        self._order_cols: List[str] = []
        self._limit_val: Optional[int] = None
        self._group_cols: List[str] = []

    # ------------------------------------------------------------------
    # Transformation methods (return new SqlFrame)
    # ------------------------------------------------------------------

    def select(self, *columns: str) -> "SqlFrame":
        """Choose which columns to return."""
        clone = self._clone()
        clone._select_cols = list(columns)
        return clone

    def where(self, condition: str) -> "SqlFrame":
        """Add a WHERE filter."""
        clone = self._clone()
        clone._where_clauses = self._where_clauses + [condition]
        return clone

    # Alias for where
    filter = where

    def order_by(self, *columns: str) -> "SqlFrame":
        """Add ORDER BY clause."""
        clone = self._clone()
        clone._order_cols = list(columns)
        return clone

    def limit(self, n: int) -> "SqlFrame":
        """Limit rows returned."""
        clone = self._clone()
        clone._limit_val = n
        return clone

    def group_by(self, *columns: str) -> "SqlFrame":
        """Add GROUP BY clause (used with agg)."""
        clone = self._clone()
        clone._group_cols = list(columns)
        return clone

    def join(
        self,
        right_table: str,
        on: List[str],
        how: str = "inner",
        left_alias: str = "l",
        right_alias: str = "r",
    ):
        """Return a JoinFrame for a deferred join against another table."""
        from sqlframe.joins import JoinFrame

        return JoinFrame(
            self._conn,
            self._table,
            right_table,
            on=on,
            how=how,
            left_alias=left_alias,
            right_alias=right_alias,
        )

    # ------------------------------------------------------------------
    # SQL building and execution
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        cols = ", ".join(self._select_cols) if self._select_cols else "*"
        sql = f"SELECT {cols} FROM {self._table}"
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        if self._group_cols:
            sql += " GROUP BY " + ", ".join(self._group_cols)
        if self._order_cols:
            sql += " ORDER BY " + ", ".join(self._order_cols)
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def to_pandas(self) -> pd.DataFrame:
        """Execute the query and return a pandas DataFrame."""
        return self._conn.query(self._build_sql())

    def _clone(self) -> "SqlFrame":
        new = SqlFrame(self._conn, self._table)
        new._select_cols = list(self._select_cols)
        new._where_clauses = list(self._where_clauses)
        new._order_cols = list(self._order_cols)
        new._limit_val = self._limit_val
        new._group_cols = list(self._group_cols)
        return new
