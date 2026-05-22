from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
import pandas as pd

if TYPE_CHECKING:
    from sqlframe.connection import Connection


class DistinctFrame:
    """Wraps a SELECT DISTINCT query against a base table or subquery."""

    def __init__(
        self,
        conn: "Connection",
        table: str,
        columns: List[str],
        where_clause: Optional[str] = None,
        params: Optional[list] = None,
        limit_val: Optional[int] = None,
    ):
        self._conn = conn
        self._table = table
        self._columns = columns
        self._where_clause = where_clause
        self._params = params or []
        self._limit_val = limit_val

    def where(self, condition: str, params: Optional[list] = None) -> "DistinctFrame":
        """Apply a WHERE filter to the distinct query."""
        return DistinctFrame(
            self._conn,
            self._table,
            self._columns,
            where_clause=condition,
            params=params or [],
            limit_val=self._limit_val,
        )

    def limit(self, n: int) -> "DistinctFrame":
        """Limit the number of distinct rows returned."""
        return DistinctFrame(
            self._conn,
            self._table,
            self._columns,
            where_clause=self._where_clause,
            params=self._params,
            limit_val=n,
        )

    def _build_sql(self) -> str:
        cols = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT DISTINCT {cols} FROM {self._table}"
        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def to_pandas(self) -> pd.DataFrame:
        """Execute the distinct query and return a DataFrame."""
        sql = self._build_sql()
        return self._conn.query(sql, params=self._params if self._params else None)

    def __repr__(self) -> str:
        return f"DistinctFrame(sql={self._build_sql()!r})"
