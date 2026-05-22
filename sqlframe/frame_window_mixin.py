"""Mixin that adds .window() to SqlFrame."""
from __future__ import annotations
from typing import List, Optional

from sqlframe.window import WindowFrame


class WindowMixin:
    """Mix into SqlFrame to expose window-function helpers.

    Requires the host class to expose:
        - self._conn  : Connection
        - self._build_sql() -> str   (the current query as a subquery-safe SQL)
        - self._columns : list[str]  (selected column names, or ['*'])
    """

    def window(
        self,
        window_cols: List[str],
        extra_cols: Optional[List[str]] = None,
    ) -> "WindowFrame":
        """Wrap the current frame in a window-function query.

        Parameters
        ----------
        window_cols:
            Fully-rendered window expressions, e.g. the output of
            ``window.rank_over([...], [...])``.  Each expression should
            already include an alias.
        extra_cols:
            Plain column names to carry through from the inner query.
            Defaults to all columns already selected on this frame.
        """
        if extra_cols is None:
            cols = getattr(self, "_columns", ["*"])
            extra_cols = cols if cols else ["*"]

        base_sql = self._build_sql()  # type: ignore[attr-defined]
        return WindowFrame(
            conn=self._conn,  # type: ignore[attr-defined]
            base_sql=base_sql,
            window_cols=window_cols,
            extra_cols=extra_cols,
        )
