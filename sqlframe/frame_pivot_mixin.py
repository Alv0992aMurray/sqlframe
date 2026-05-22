from __future__ import annotations
from typing import List, Optional


class PivotMixin:
    """
    Mixin that adds a .pivot() method to SqlFrame and JoinFrame.
    Expects the host class to expose `self._conn` and `self._table`.
    """

    def pivot(
        self,
        index: str,
        pivot_col: str,
        values: List[str],
        agg_func: str = "SUM",
    ) -> "PivotFrame":  # noqa: F821
        """Create a PivotFrame from the current frame.

        Args:
            index: Column to use as the row identifier (GROUP BY column).
            pivot_col: Column whose distinct values become new columns.
            values: Explicit list of values from *pivot_col* to pivot on.
            agg_func: Aggregation function to apply (default ``SUM``).

        Returns:
            A :class:`~sqlframe.pivot.PivotFrame` ready for execution.
        """
        from sqlframe.pivot import PivotFrame

        return PivotFrame(
            conn=self._conn,
            table=self._table,
            index=index,
            pivot_col=pivot_col,
            values=values,
            agg_func=agg_func,
        )
