from __future__ import annotations
from typing import Any, List, Optional

import pandas as pd


class IsInFrame:
    """Represents a SELECT … WHERE col [NOT] IN (…) query."""

    def __init__(
        self,
        conn,
        table: str,
        column: str,
        values: List[Any],
        negate: bool = False,
        existing_filters: Optional[List[str]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> None:
        self._conn = conn
        self._table = table
        self._column = column
        self._values = list(values)
        self._negate = negate
        self._filters: List[str] = list(existing_filters or [])
        self._columns: List[str] = columns if columns else ["*"]
        self._limit: Optional[int] = limit

    # ------------------------------------------------------------------
    # Chaining helpers
    # ------------------------------------------------------------------

    def where(self, condition: str) -> "IsInFrame":
        """Append an additional WHERE clause fragment."""
        clone = self._clone()
        clone._filters.append(condition)
        return clone

    def limit(self, n: int) -> "IsInFrame":
        clone = self._clone()
        clone._limit = n
        return clone

    # ------------------------------------------------------------------
    # SQL building
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        cols = ", ".join(self._columns)
        placeholders = ", ".join("%s" for _ in self._values)
        keyword = "NOT IN" if self._negate else "IN"
        isin_clause = f"{self._column} {keyword} ({placeholders})"

        all_filters = self._filters + [isin_clause]
        where_sql = " AND ".join(f"({f})" for f in all_filters)

        sql = f"SELECT {cols} FROM {self._table} WHERE {where_sql}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        return sql

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def to_pandas(self) -> pd.DataFrame:
        sql = self._build_sql()
        return self._conn.query(sql, params=self._values)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _clone(self) -> "IsInFrame":
        return IsInFrame(
            conn=self._conn,
            table=self._table,
            column=self._column,
            values=self._values,
            negate=self._negate,
            existing_filters=list(self._filters),
            columns=list(self._columns),
            limit=self._limit,
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"IsInFrame(table={self._table!r}, column={self._column!r}, negate={self._negate})"
