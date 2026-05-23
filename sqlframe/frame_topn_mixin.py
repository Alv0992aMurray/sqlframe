from __future__ import annotations
from typing import List, Union


class TopNMixin:
    """Mixin that adds top_n() / bottom_n() helpers to frame classes."""

    def top_n(
        self,
        n: int,
        order_by: Union[str, List[str]],
        columns: Union[str, List[str], None] = None,
    ) -> "TopNFrame":  # noqa: F821
        """Return the top *n* rows ordered by *order_by* ascending.

        Parameters
        ----------
        n:
            Number of rows to return.
        order_by:
            Column name(s) to sort by (ascending).
        columns:
            Columns to select.  Defaults to all columns (**).
        """
        from sqlframe.topn import TopNFrame

        if isinstance(order_by, str):
            order_by = [order_by]
        if isinstance(columns, str):
            columns = [columns]
        cols = columns or []

        return TopNFrame(
            conn=self._conn,
            table=self._table,
            columns=cols,
            order_by=order_by,
            n=n,
            ascending=True,
            where_clause=getattr(self, "_where_clause", None),
            params=getattr(self, "_params", {}),
        )

    def bottom_n(
        self,
        n: int,
        order_by: Union[str, List[str]],
        columns: Union[str, List[str], None] = None,
    ) -> "TopNFrame":  # noqa: F821
        """Return the bottom *n* rows ordered by *order_by* descending."""
        from sqlframe.topn import TopNFrame

        if isinstance(order_by, str):
            order_by = [order_by]
        if isinstance(columns, str):
            columns = [columns]
        cols = columns or []

        return TopNFrame(
            conn=self._conn,
            table=self._table,
            columns=cols,
            order_by=order_by,
            n=n,
            ascending=False,
            where_clause=getattr(self, "_where_clause", None),
            params=getattr(self, "_params", {}),
        )
