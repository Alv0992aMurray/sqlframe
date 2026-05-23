from __future__ import annotations
from typing import Any, Optional


class BetweenMixin:
    """Mixin that adds a .between() convenience method to frame classes."""

    def between(
        self,
        column: str,
        low: Any,
        high: Any,
        columns: Optional[list[str]] = None,
    ) -> "BetweenFrame":  # noqa: F821
        """Return rows where *column* is between *low* and *high* (inclusive).

        Parameters
        ----------
        column:
            Name of the column to filter on.
        low:
            Lower bound (inclusive).
        high:
            Upper bound (inclusive).
        columns:
            Optional list of columns to project. Defaults to all columns.

        Returns
        -------
        BetweenFrame
            A lazy frame that will execute the BETWEEN query on materialisation.
        """
        from sqlframe.between import BetweenFrame

        return BetweenFrame(
            conn=self._conn,
            table=self._table,
            column=column,
            low=low,
            high=high,
            columns=columns,
        )
