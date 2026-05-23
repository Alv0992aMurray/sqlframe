from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    import pandas as pd


class TopNFrame:
    """Represents a TOP-N query: ORDER BY ... LIMIT n (with optional partition)."""

    def __init__(
        self,
        conn,
        table: str,
        columns: List[str],
        order_by: List[str],
        n: int,
        ascending: bool = True,
        where_clause: Optional[str] = None,
        params: Optional[dict] = None,
    ):
        self._conn = conn
        self._table = table
        self._columns = columns
        self._order_by = order_by
        self._n = n
        self._ascending = ascending
        self._where_clause = where_clause
        self._params = params or {}

    def where(self, condition: str, **params) -> "TopNFrame":
        merged = {**self._params, **params}
        clause = f"({self._where_clause}) AND ({condition})" if self._where_clause else condition
        return TopNFrame(
            self._conn, self._table, self._columns, self._order_by,
            self._n, self._ascending, clause, merged,
        )

    def _build_sql(self) -> str:
        cols = ", ".join(self._columns) if self._columns else "*"
        direction = "ASC" if self._ascending else "DESC"
        order_terms = ", ".join(f"{c} {direction}" for c in self._order_by)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        sql += f" ORDER BY {order_terms} LIMIT {self._n}"
        return sql

    def to_pandas(self) -> "pd.DataFrame":
        sql = self._build_sql()
        return self._conn.query(sql, self._params)

    def __repr__(self) -> str:
        direction = "ASC" if self._ascending else "DESC"
        return (
            f"TopNFrame(table={self._table!r}, order_by={self._order_by}, "
            f"direction={direction}, n={self._n})"
        )
