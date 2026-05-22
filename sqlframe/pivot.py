from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from sqlframe.connection import Connection


class PivotFrame:
    """
    Represents a pivot (crosstab) query built lazily against a base table or subquery.
    """

    def __init__(
        self,
        conn: "Connection",
        table: str,
        index: str,
        pivot_col: str,
        values: List[str],
        agg_func: str = "SUM",
        where_clause: Optional[str] = None,
    ):
        self._conn = conn
        self._table = table
        self._index = index
        self._pivot_col = pivot_col
        self._values = values
        self._agg_func = agg_func.upper()
        self._where_clause = where_clause

    def where(self, condition: str) -> "PivotFrame":
        """Apply a WHERE filter and return a new PivotFrame."""
        return PivotFrame(
            conn=self._conn,
            table=self._table,
            index=self._index,
            pivot_col=self._pivot_col,
            values=self._values,
            agg_func=self._agg_func,
            where_clause=condition,
        )

    def _build_sql(self) -> str:
        agg_exprs = ", ".join(
            f"{self._agg_func}(CASE WHEN {self._pivot_col} = '{v}' THEN 1 ELSE 0 END) AS \"{v}\""
            for v in self._values
        )
        sql = (
            f"SELECT {self._index}, {agg_exprs} "
            f"FROM {self._table}"
        )
        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        sql += f" GROUP BY {self._index}"
        return sql

    def to_pandas(self):
        """Execute the pivot query and return a pandas DataFrame."""
        sql = self._build_sql()
        return self._conn.query(sql)

    def __repr__(self) -> str:
        return f"PivotFrame(table={self._table!r}, index={self._index!r}, pivot_col={self._pivot_col!r}, values={self._values!r}, agg={self._agg_func!r})"
