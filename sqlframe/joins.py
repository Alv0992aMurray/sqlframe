from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
import pandas as pd

if TYPE_CHECKING:
    from sqlframe.connection import Connection


JOIN_TYPES = {"inner", "left", "right", "full"}


class JoinFrame:
    """
    Represents a deferred JOIN operation between two tables/subqueries.
    Supports method chaining for filtering, column selection, and execution.
    """

    def __init__(
        self,
        conn: "Connection",
        left_table: str,
        right_table: str,
        on: List[str],
        how: str = "inner",
        left_alias: str = "l",
        right_alias: str = "r",
    ):
        if how not in JOIN_TYPES:
            raise ValueError(f"Invalid join type '{how}'. Must be one of {JOIN_TYPES}.")
        self._conn = conn
        self._left_table = left_table
        self._right_table = right_table
        self._on = on
        self._how = how
        self._left_alias = left_alias
        self._right_alias = right_alias
        self._select_cols: List[str] = []
        self._where_clauses: List[str] = []
        self._limit_val: Optional[int] = None

    def select(self, *columns: str) -> "JoinFrame":
        """Specify columns to SELECT. Defaults to * if not called."""
        clone = self._clone()
        clone._select_cols = list(columns)
        return clone

    def where(self, condition: str) -> "JoinFrame":
        """Add a WHERE clause filter."""
        clone = self._clone()
        clone._where_clauses = self._where_clauses + [condition]
        return clone

    def limit(self, n: int) -> "JoinFrame":
        """Limit the number of returned rows."""
        clone = self._clone()
        clone._limit_val = n
        return clone

    def _build_sql(self) -> str:
        cols = ", ".join(self._select_cols) if self._select_cols else "*"
        join_keyword = f"{self._how.upper()} JOIN"
        on_clause = " AND ".join(
            f"{self._left_alias}.{col} = {self._right_alias}.{col}"
            for col in self._on
        )
        sql = (
            f"SELECT {cols} FROM {self._left_table} AS {self._left_alias} "
            f"{join_keyword} {self._right_table} AS {self._right_alias} "
            f"ON {on_clause}"
        )
        if self._where_clauses:
            sql += " WHERE " + " AND ".join(self._where_clauses)
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def to_pandas(self) -> pd.DataFrame:
        """Execute the join query and return results as a DataFrame."""
        return self._conn.query(self._build_sql())

    def _clone(self) -> "JoinFrame":
        new = JoinFrame(
            self._conn,
            self._left_table,
            self._right_table,
            self._on,
            self._how,
            self._left_alias,
            self._right_alias,
        )
        new._select_cols = list(self._select_cols)
        new._where_clauses = list(self._where_clauses)
        new._limit_val = self._limit_val
        return new
