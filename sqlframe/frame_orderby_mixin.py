from __future__ import annotations
from typing import List, Union


class OrderByMixin:
    """Mixin that adds a fluent sort_values / order_by method to frame classes."""

    def sort_values(
        self,
        by: Union[str, List[str]],
        ascending: Union[bool, List[bool]] = True,
    ) -> "OrderByFrame":  # noqa: F821
        """Return an OrderByFrame sorted by *by* column(s).

        Parameters
        ----------
        by:
            Column name or list of column names to sort by.
        ascending:
            Single bool or list of bools (one per column).
        """
        from sqlframe.orderby import OrderByFrame

        if isinstance(by, str):
            by = [by]

        table = getattr(self, "_table", None) or getattr(self, "_from", None)
        if table is None:
            raise AttributeError(
                "Frame must expose '_table' or '_from' to use sort_values."
            )

        where_clause = getattr(self, "_where_clause", None)
        params = getattr(self, "_params", {}) or {}
        limit = getattr(self, "_limit", None)

        return OrderByFrame(
            conn=self._conn,
            table=table,
            columns=by,
            ascending=ascending,
            limit=limit,
            where_clause=where_clause,
            params=params,
        )
