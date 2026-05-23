from __future__ import annotations
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from sqlframe.isin import IsInFrame


class IsInMixin:
    """Mixin that adds .isin() and .notin() filter helpers to a frame."""

    def isin(self, column: str, values: List[Any]) -> "IsInFrame":
        """Return rows where *column* value is in *values*.

        Parameters
        ----------
        column:
            Column name to filter on.
        values:
            List of values to match against.
        """
        from sqlframe.isin import IsInFrame

        return IsInFrame(
            conn=self._conn,
            table=self._table,
            column=column,
            values=values,
            negate=False,
            existing_filters=getattr(self, "_filters", []),
            columns=getattr(self, "_columns", ["*"]),
            limit=getattr(self, "_limit", None),
        )

    def notin(self, column: str, values: List[Any]) -> "IsInFrame":
        """Return rows where *column* value is NOT in *values*."""
        from sqlframe.isin import IsInFrame

        return IsInFrame(
            conn=self._conn,
            table=self._table,
            column=column,
            values=values,
            negate=True,
            existing_filters=getattr(self, "_filters", []),
            columns=getattr(self, "_columns", ["*"]),
            limit=getattr(self, "_limit", None),
        )
