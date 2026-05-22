from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlframe.union import UnionFrame


class UnionMixin:
    """
    Mixin that adds union() and union_all() methods to a frame class.
    The host class must expose `_conn` and implement `_build_sql()`.
    """

    def union(self, other) -> "UnionFrame":
        """
        Return a new UnionFrame combining self and other with UNION (deduplicates rows).

        Parameters
        ----------
        other:
            Another frame that implements _build_sql().
        """
        from sqlframe.union import UnionFrame
        return UnionFrame([self, other], self._conn, union_all=False)

    def union_all(self, other) -> "UnionFrame":
        """
        Return a new UnionFrame combining self and other with UNION ALL (keeps duplicates).

        Parameters
        ----------
        other:
            Another frame that implements _build_sql().
        """
        from sqlframe.union import UnionFrame
        return UnionFrame([self, other], self._conn, union_all=True)
