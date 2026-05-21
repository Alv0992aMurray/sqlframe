"""SqlFrame – a lazy SQL-backed DataFrame-like object."""

from __future__ import annotations

from typing import List, Optional, Sequence

import pandas as pd

from sqlframe.connection import Connection


class SqlFrame:
    """Represents a SQL query that can be refined before execution.

    Instances are created via :func:`sqlframe.read_table` or
    :meth:`Connection.query`; they are *not* meant to be constructed directly.
    """

    def __init__(self, connection: Connection, sql: str) -> None:
        self._conn = connection
        self._sql = sql
        self._limit: Optional[int] = None
        self._where: Optional[str] = None
        self._columns: Optional[List[str]] = None

    # ------------------------------------------------------------------
    # Chainable transformations (return new SqlFrame)
    # ------------------------------------------------------------------

    def select(self, *columns: str) -> "SqlFrame":
        """Project specific columns."""
        clone = self._clone()
        clone._columns = list(columns)
        return clone

    def where(self, condition: str) -> "SqlFrame":
        """Append a WHERE / AND clause."""
        clone = self._clone()
        clone._where = condition
        return clone

    def limit(self, n: int) -> "SqlFrame":
        """Restrict the number of rows returned."""
        clone = self._clone()
        clone._limit = n
        return clone

    # ------------------------------------------------------------------
    # Terminal actions
    # ------------------------------------------------------------------

    def to_pandas(self) -> pd.DataFrame:
        """Execute the query and return a :class:`pandas.DataFrame`."""
        return self._conn.query(self._build_sql())

    def show(self, n: int = 20) -> None:  # pragma: no cover
        """Print the first *n* rows to stdout."""
        print(self.limit(n).to_pandas().to_string(index=False))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        cols = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT {cols} FROM ({self._sql}) AS _sf_subquery"
        if self._where:
            sql += f" WHERE {self._where}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        return sql

    def _clone(self) -> "SqlFrame":
        clone = SqlFrame(self._conn, self._sql)
        clone._limit = self._limit
        clone._where = self._where
        clone._columns = list(self._columns) if self._columns else None
        return clone

    def __repr__(self) -> str:  # pragma: no cover
        return f"SqlFrame(sql={self._build_sql()!r})"
