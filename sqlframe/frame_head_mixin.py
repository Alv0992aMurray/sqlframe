from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlframe.head import HeadFrame


class HeadMixin:
    """Mixin that adds a .head() convenience method to frame classes."""

    def head(self, n: int = 5) -> "HeadFrame":
        """Return the first *n* rows as a HeadFrame.

        Parameters
        ----------
        n:
            Number of rows to fetch.  Defaults to 5, mirroring pandas.

        Returns
        -------
        HeadFrame
            A lazy frame that will execute ``SELECT … LIMIT n`` when
            ``.to_pandas()`` is called.

        Example
        -------
        >>> df = read_table(conn, "orders")
        >>> df.head(10).to_pandas()
        """
        from sqlframe.head import HeadFrame

        if not isinstance(n, int) or n < 1:
            raise ValueError(f"n must be a positive integer, got {n!r}")

        return HeadFrame(frame=self, n=n)
