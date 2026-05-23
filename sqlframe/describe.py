from __future__ import annotations

from typing import List, Optional

import pandas as pd


_STAT_QUERIES = [
    ("count", "COUNT({col})"),
    ("mean", "AVG({col})"),
    ("min", "MIN({col})"),
    ("max", "MAX({col})"),
    ("stddev", "STDDEV({col})"),
]


class DescribeFrame:
    """Computes summary statistics for numeric columns via SQL aggregation."""

    def __init__(
        self,
        conn,
        source_sql: str,
        columns: List[str],
        percentiles: Optional[List[float]] = None,
    ) -> None:
        self._conn = conn
        self._source_sql = source_sql
        self._columns = columns
        self._percentiles = percentiles or []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        """Build a single SELECT that computes all stats for all columns."""
        if not self._columns:
            raise ValueError(
                "describe() requires at least one column to be specified "
                "or present in the source frame."
            )

        agg_exprs = []
        for col in self._columns:
            for stat_name, template in _STAT_QUERIES:
                expr = template.format(col=col)
                alias = f"{stat_name}__{col}"
                agg_exprs.append(f"{expr} AS {alias}")

            for p in self._percentiles:
                pct_label = str(p).replace(".", "_")
                expr = f"PERCENTILE_CONT({p}) WITHIN GROUP (ORDER BY {col})"
                alias = f"pct{pct_label}__{col}"
                agg_exprs.append(f"{expr} AS {alias}")

        select_clause = ",\n    ".join(agg_exprs)
        return f"SELECT\n    {select_clause}\nFROM ({self._source_sql}) AS _describe_src"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def to_pandas(self) -> pd.DataFrame:
        """Execute the describe query and pivot results into a tidy DataFrame.

        Returns a DataFrame indexed by statistic name with one column per
        described column (mirrors pandas DataFrame.describe() layout).
        """
        sql = self._build_sql()
        raw: pd.DataFrame = self._conn.query(sql)

        if raw.empty:
            return raw

        # raw has one row; column names are "<stat>__<col>"
        result: dict = {col: {} for col in self._columns}
        for flat_col in raw.columns:
            if "__" not in flat_col:
                continue
            stat, col = flat_col.split("__", 1)
            if col in result:
                result[col][stat] = raw.iloc[0][flat_col]

        return pd.DataFrame(result)

    def __repr__(self) -> str:  # pragma: no cover
        cols = ", ".join(self._columns)
        return f"DescribeFrame(columns=[{cols}])"
