from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlframe.connection import Connection


class BetweenFrame:
    """Represents a SQL query filtering rows where a column value falls between two bounds."""

    def __init__(
        self,
        conn: "Connection",
        table: str,
        column: str,
        low: Any,
        high: Any,
        columns: Optional[list[str]] = None,
        where_clause: Optional[str] = None,
        params: Optional[list] = None,
        _limit: Optional[int] = None,
    ):
        self._conn = conn
        self._table = table
        self._column = column
        self._low = low
        self._high = high
        self._columns = columns or ["*"]
        self._where_clause = where_clause
        self._params = params or []
        self._limit = _limit

    def where(self, condition: str, params: Optional[list] = None) -> "BetweenFrame":
        """Add an additional WHERE filter on top of the BETWEEN clause."""
        extra = params or []
        combined_params = self._params + extra
        if self._where_clause:
            new_where = f"({self._where_clause}) AND ({condition})"
        else:
            new_where = condition
        return BetweenFrame(
            self._conn, self._table, self._column, self._low, self._high,
            self._columns, new_where, combined_params, self._limit,
        )

    def limit(self, n: int) -> "BetweenFrame":
        """Limit the number of returned rows."""
        return BetweenFrame(
            self._conn, self._table, self._column, self._low, self._high,
            self._columns, self._where_clause, self._params, n,
        )

    def _build_sql(self) -> tuple[str, list]:
        cols = ", ".join(self._columns)
        params: list = [self._low, self._high]
        sql = (
            f"SELECT {cols} FROM {self._table} "
            f"WHERE {self._column} BETWEEN ? AND ?"
        )
        if self._where_clause:
            sql += f" AND ({self._where_clause})"
            params += list(self._params)
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        return sql, params

    def to_pandas(self):
        sql, params = self._build_sql()
        return self._conn.query(sql, params=params)

    def __repr__(self) -> str:
        sql, params = self._build_sql()
        return f"BetweenFrame(sql={sql!r}, params={params!r})"
