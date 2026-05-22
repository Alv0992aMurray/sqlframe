from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    import pandas as pd


class OrderByFrame:
    """Wraps a SqlFrame/query with explicit multi-column ORDER BY and optional LIMIT."""

    def __init__(
        self,
        conn,
        table: str,
        columns: List[str],
        ascending: bool | List[bool] = True,
        limit: Optional[int] = None,
        where_clause: Optional[str] = None,
        params: Optional[dict] = None,
    ):
        self._conn = conn
        self._table = table
        self._columns = columns
        self._ascending = ascending
        self._limit = limit
        self._where_clause = where_clause
        self._params = params or {}

    def _build_order_terms(self) -> str:
        if isinstance(self._ascending, bool):
            directions = [self._ascending] * len(self._columns)
        else:
            if len(self._ascending) != len(self._columns):
                raise ValueError(
                    "'ascending' length must match number of sort columns."
                )
            directions = list(self._ascending)

        terms = [
            f"{col} {'ASC' if asc else 'DESC'}"
            for col, asc in zip(self._columns, directions)
        ]
        return ", ".join(terms)

    def _build_sql(self) -> str:
        sql = f"SELECT * FROM {self._table}"
        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        sql += f" ORDER BY {self._build_order_terms()}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        return sql

    def limit(self, n: int) -> "OrderByFrame":
        return OrderByFrame(
            self._conn,
            self._table,
            self._columns,
            self._ascending,
            limit=n,
            where_clause=self._where_clause,
            params=self._params,
        )

    def where(self, condition: str, **params) -> "OrderByFrame":
        merged = {**self._params, **params}
        return OrderByFrame(
            self._conn,
            self._table,
            self._columns,
            self._ascending,
            limit=self._limit,
            where_clause=condition,
            params=merged,
        )

    def to_pandas(self) -> "pd.DataFrame":
        sql = self._build_sql()
        return self._conn.query(sql, **self._params)

    def __repr__(self) -> str:
        return f"OrderByFrame(table={self._table!r}, columns={self._columns!r}, sql={self._build_sql()!r})"
