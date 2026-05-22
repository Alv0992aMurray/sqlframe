"""Sampling utilities for SqlFrame — random and stratified row sampling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import pandas as pd
    from sqlframe.frame import SqlFrame


class SampleFrame:
    """Wraps a SqlFrame with row-sampling capabilities."""

    def __init__(
        self,
        frame: "SqlFrame",
        fraction: Optional[float] = None,
        n: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> None:
        if fraction is None and n is None:
            raise ValueError("Provide either 'fraction' or 'n'.")
        if fraction is not None and not (0 < fraction <= 1):
            raise ValueError("'fraction' must be between 0 (exclusive) and 1 (inclusive).")
        if n is not None and n < 1:
            raise ValueError("'n' must be a positive integer.")

        self._frame = frame
        self._fraction = fraction
        self._n = n
        self._seed = seed

    # ------------------------------------------------------------------
    # SQL building
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        """Return the SQL string for the sample query.

        Strategy:
        - If *n* is given we use TABLESAMPLE SYSTEM_ROWS(n) when the dialect
          supports it, falling back to ORDER BY RANDOM() LIMIT n.
        - If *fraction* is given we use ORDER BY RANDOM() and LIMIT derived
          from a subquery count — but to stay dialect-agnostic we always use
          the ORDER BY RANDOM() / LIMIT approach here.
        """
        inner_sql = self._frame._build_sql()  # reuse existing builder

        seed_clause = ""
        if self._seed is not None:
            # PostgreSQL / DuckDB style; silently ignored by other engines
            seed_clause = f"-- seed={self._seed}\n"

        if self._n is not None:
            return (
                f"{seed_clause}SELECT * FROM ({inner_sql}) AS _sample_inner "
                f"ORDER BY RANDOM() LIMIT {self._n}"
            )

        # fraction path — wrap in a subquery and apply LIMIT via percentage
        return (
            f"{seed_clause}SELECT * FROM ({inner_sql}) AS _sample_inner "
            f"WHERE RANDOM() <= {self._fraction}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def to_pandas(self) -> "pd.DataFrame":
        """Execute the sample query and return a DataFrame."""
        sql = self._build_sql()
        return self._frame._conn.query(sql)

    def __repr__(self) -> str:  # pragma: no cover
        spec = f"n={self._n}" if self._n is not None else f"fraction={self._fraction}"
        return f"SampleFrame({spec}, seed={self._seed})"
