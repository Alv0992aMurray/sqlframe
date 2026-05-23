from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlframe.withcolumn import WithColumnFrame


class WithColumnMixin:
    """Mixin that adds a with_column method to frame classes."""

    def with_column(self, col_name: str, expression: str) -> "WithColumnFrame":
        """Add or replace a column using a SQL expression.

        Parameters
        ----------
        col_name:
            Name of the new (or replacement) column.
        expression:
            SQL expression string, e.g. ``"price * 1.1"`` or
            ``"UPPER(name)"``.

        Returns
        -------
        WithColumnFrame
            A lazy frame that wraps the current query with the new column.

        Example
        -------
        >>> df.with_column("discounted", "price * 0.9").to_pandas()
        """
        from sqlframe.withcolumn import WithColumnFrame

        return WithColumnFrame(
            conn=self._conn,
            source=self,
            col_name=col_name,
            expression=expression,
        )
