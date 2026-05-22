from __future__ import annotations
from typing import Any, Dict, Optional, Union


class FillNaFrame:
    """
    Represents a query that replaces NULL values in specified columns.
    """

    def __init__(
        self,
        conn,
        table: str,
        fill_map: Dict[str, Any],
        where: Optional[str] = None,
        limit_val: Optional[int] = None,
    ):
        self._conn = conn
        self._table = table
        self._fill_map = fill_map  # {column: fill_value}
        self._where = where
        self._limit_val = limit_val

    def where(self, condition: str) -> "FillNaFrame":
        """Apply a WHERE filter to the query."""
        return FillNaFrame(
            self._conn,
            self._table,
            self._fill_map,
            where=condition,
            limit_val=self._limit_val,
        )

    def limit(self, n: int) -> "FillNaFrame":
        """Limit the number of rows returned."""
        return FillNaFrame(
            self._conn,
            self._table,
            self._fill_map,
            where=self._where,
            limit_val=n,
        )

    def _build_sql(self) -> str:
        """Build the SELECT SQL with COALESCE expressions for each fill column."""
        coalesce_exprs = []
        for col, val in self._fill_map.items():
            if isinstance(val, str):
                literal = f"'{val}'"
            elif isinstance(val, bool):
                literal = "TRUE" if val else "FALSE"
            else:
                literal = str(val)
            coalesce_exprs.append(f"COALESCE({col}, {literal}) AS {col}")

        select_parts = ["*"] + coalesce_exprs
        # Override duplicate columns by selecting fill columns last
        # Build a clean column list: non-fill columns as-is, fill columns via COALESCE
        fill_cols = set(self._fill_map.keys())
        coalesce_only = ", ".join(
            f"COALESCE({col}, {repr(val) if isinstance(val, str) else (str(val).upper() if isinstance(val, bool) else str(val))}) AS {col}"
            for col, val in self._fill_map.items()
        )
        sql = f"SELECT * REPLACE ({', '.join(self._build_replace_exprs())}) FROM {self._table}"

        if self._where:
            sql += f" WHERE {self._where}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def _build_replace_exprs(self):
        exprs = []
        for col, val in self._fill_map.items():
            if isinstance(val, str):
                literal = f"'{val}'"
            elif isinstance(val, bool):
                literal = "TRUE" if val else "FALSE"
            else:
                literal = str(val)
            exprs.append(f"COALESCE({col}, {literal}) AS {col}")
        return exprs

    def to_pandas(self):
        """Execute the query and return a pandas DataFrame."""
        sql = self._build_sql()
        return self._conn.query(sql)

    def __repr__(self) -> str:
        return f"FillNaFrame(table={self._table!r}, fill_map={self._fill_map!r})"
