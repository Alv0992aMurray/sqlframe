from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional, Union

if TYPE_CHECKING:
    from sqlframe.connection import Connection


class PercentileFrame:
    """Represents a percentile/quantile query against a single column."""

    def __init__(
        self,
        conn: "Connection",
        table: str,
        column: str,
        percentiles: List[float],
        where_clause: Optional[str] = None,
        interpolation: str = "linear",
    ):
        if not percentiles:
            raise ValueError("At least one percentile value is required.")
        for p in percentiles:
            if not (0.0 <= p <= 1.0):
                raise ValueError(f"Percentile values must be between 0 and 1, got {p}.")

        valid_interpolations = {"linear", "lower", "higher", "midpoint", "nearest"}
        if interpolation not in valid_interpolations:
            raise ValueError(
                f"interpolation must be one of {valid_interpolations}, got '{interpolation}'."
            )

        self._conn = conn
        self._table = table
        self._column = column
        self._percentiles = percentiles
        self._where_clause = where_clause
        self._interpolation = interpolation

    def where(self, condition: str) -> "PercentileFrame":
        """Apply an additional WHERE filter."""
        existing = self._where_clause
        new_clause = f"({existing}) AND ({condition})" if existing else condition
        return PercentileFrame(
            self._conn,
            self._table,
            self._column,
            self._percentiles,
            where_clause=new_clause,
            interpolation=self._interpolation,
        )

    def _build_sql(self) -> str:
        percentile_exprs = ", ".join(
            f"PERCENTILE_CONT({p}) WITHIN GROUP (ORDER BY {self._column}) AS p{str(p).replace('.', '_')}"
            for p in self._percentiles
        )
        sql = f"SELECT {percentile_exprs} FROM {self._table}"
        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        return sql

    def to_pandas(self):
        """Execute the percentile query and return a pandas DataFrame."""
        sql = self._build_sql()
        return self._conn.query(sql)

    def __repr__(self) -> str:
        return (
            f"PercentileFrame(table={self._table!r}, column={self._column!r}, "
            f"percentiles={self._percentiles!r}, interpolation={self._interpolation!r})"
        )
