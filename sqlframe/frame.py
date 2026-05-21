"""Core SqlFrame class — lazy SQL builder with pandas-compatible surface."""

from __future__ import annotations

from typing import Dict, List, Optional, Union

import pandas as pd


class SqlFrame:
    """Lazy wrapper around a SQL query that mimics a pandas DataFrame API."""

    def __init__(self, conn, table: str, sql: Optional[str] = None) -> None:
        self._conn = conn
        self._table = table
        self._sql = sql  # overrides table when set
        self._columns: List[str] = ["*"]
        self._filters: List[str] = []
        self._limit_val: Optional[int] = None

    # ------------------------------------------------------------------
    # Internal SQL builder
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        select_clause = ", ".join(self._columns)
        source = f"({self._sql}) _sub" if self._sql else self._table
        sql = f"SELECT {select_clause} FROM {source}"
        if self._filters:
            where_clause = " AND ".join(f"({f})" for f in self._filters)
            sql += f" WHERE {where_clause}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def _clone(self) -> "SqlFrame":
        clone = SqlFrame(self._conn, self._table, self._sql)
        clone._columns = list(self._columns)
        clone._filters = list(self._filters)
        clone._limit_val = self._limit_val
        return clone

    # ------------------------------------------------------------------
    # Transformation API
    # ------------------------------------------------------------------

    def select(self, *columns: str) -> "SqlFrame":
        clone = self._clone()
        clone._columns = list(columns)
        return clone

    def where(self, condition: str) -> "SqlFrame":
        clone = self._clone()
        clone._filters.append(condition)
        return clone

    def limit(self, n: int) -> "SqlFrame":
        clone = self._clone()
        clone._limit_val = n
        return clone

    # ------------------------------------------------------------------
    # Aggregation API
    # ------------------------------------------------------------------

    def group_by(self, *columns: str) -> "_GroupByProxy":
        """Return a proxy that accepts .agg() to build an AggFrame."""
        return _GroupByProxy(self, list(columns))

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def to_pandas(self) -> pd.DataFrame:
        return self._conn.query(self._build_sql())

    def head(self, n: int = 5) -> pd.DataFrame:
        return self.limit(n).to_pandas()

    def count(self) -> int:
        sql = f"SELECT COUNT(*) AS _cnt FROM ({self._build_sql()}) _count_sub"
        result = self._conn.query(sql)
        return int(result.iloc[0, 0])

    def __repr__(self) -> str:  # pragma: no cover
        return f"SqlFrame(table={self._table!r}, sql={self._build_sql()!r})"


class _GroupByProxy:
    """Intermediate object returned by SqlFrame.group_by()."""

    def __init__(self, parent: SqlFrame, group_by: List[str]) -> None:
        self._parent = parent
        self._group_by = group_by

    def agg(self, **kwargs: str) -> "sqlframe.aggregations.AggFrame":  # type: ignore[name-defined]
        from sqlframe.aggregations import AggFrame

        return AggFrame(self._parent, self._group_by, kwargs)
