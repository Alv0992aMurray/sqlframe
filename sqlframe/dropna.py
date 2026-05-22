from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlframe.connection import Connection


class DropNaFrame:
    """Represents a query that filters out rows containing NULL values."""

    def __init__(
        self,
        conn: "Connection",
        table: str,
        columns: Optional[List[str]] = None,
        how: str = "any",
        where_clauses: Optional[List[str]] = None,
        limit_val: Optional[int] = None,
    ):
        if how not in ("any", "all"):
            raise ValueError("how must be 'any' or 'all'")
        self._conn = conn
        self._table = table
        self._columns = columns  # None means all columns
        self._how = how
        self._where_clauses = where_clauses or []
        self._limit_val = limit_val

    def where(self, condition: str) -> "DropNaFrame":
        """Add an additional WHERE filter."""
        return DropNaFrame(
            self._conn,
            self._table,
            self._columns,
            self._how,
            self._where_clauses + [condition],
            self._limit_val,
        )

    def limit(self, n: int) -> "DropNaFrame":
        """Limit the number of returned rows."""
        return DropNaFrame(
            self._conn,
            self._table,
            self._columns,
            self._how,
            self._where_clauses,
            n,
        )

    def _build_sql(self, columns: List[str]) -> str:
        """Build the SQL string for the dropna operation."""
        if self._how == "any":
            null_checks = " OR ".join(f"{col} IS NULL" for col in columns)
            not_null_filter = f"NOT ({null_checks})"
        else:  # all
            not_null_filter = " OR ".join(f"{col} IS NOT NULL" for col in columns)

        all_filters = [not_null_filter] + self._where_clauses
        where_clause = " AND ".join(f"({f})" for f in all_filters)

        sql = f"SELECT * FROM {self._table} WHERE {where_clause}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def to_pandas(self):
        """Execute the query and return a pandas DataFrame."""
        if self._columns:
            cols = self._columns
        else:
            # Introspect column names from the table
            sample = self._conn.query(f"SELECT * FROM {self._table} LIMIT 0")
            cols = list(sample.columns)

        sql = self._build_sql(cols)
        return self._conn.query(sql)

    def __repr__(self) -> str:
        cols = self._columns or "<all>"
        return (
            f"DropNaFrame(table={self._table!r}, columns={cols}, "
            f"how={self._how!r}, where={self._where_clauses}, "
            f"limit={self._limit_val})"
        )
