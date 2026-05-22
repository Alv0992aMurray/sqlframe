from __future__ import annotations
from typing import List, Optional


class DistinctMixin:
    """Mixin that adds .distinct() to SqlFrame and JoinFrame."""

    def distinct(
        self, columns: Optional[List[str]] = None
    ) -> "DistinctFrame":  # noqa: F821
        """Return a DistinctFrame over the specified columns (or all columns).

        Parameters
        ----------
        columns:
            List of column names to include in SELECT DISTINCT.  When *None*
            all columns are selected (i.e. ``SELECT DISTINCT *``).

        Returns
        -------
        DistinctFrame
        """
        from sqlframe.distinct import DistinctFrame

        # Resolve the table/subquery reference from the host frame.
        table = getattr(self, "_table", None)
        if table is None:
            raise AttributeError(
                "DistinctMixin requires the host frame to expose a '_table' attribute."
            )

        return DistinctFrame(
            conn=self._conn,
            table=table,
            columns=columns or [],
        )
