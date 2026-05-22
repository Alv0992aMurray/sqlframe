from __future__ import annotations
from typing import Dict


class CastMixin:
    """Mixin that adds a .cast() method to SqlFrame and JoinFrame."""

    def cast(self, casts: Dict[str, str]) -> "CastFrame":  # noqa: F821
        """Return a CastFrame that wraps the current query with CAST expressions.

        Parameters
        ----------
        casts:
            Mapping of column name -> target type.  Type strings may be SQL
            types (``'VARCHAR'``) or friendly aliases (``'str'``, ``'int'``,
            ``'datetime'``, …).

        Example
        -------
        >>> df.cast({"age": "int", "score": "float"}).to_pandas()
        """
        from sqlframe.cast import CastFrame

        # Determine which columns are currently selected
        columns = list(getattr(self, "_columns", ["*"]))
        if not columns or columns == ["*"]:
            raise ValueError(
                "cast() requires explicit column selection; "
                "call .select(...) before .cast()."
            )

        unknown = set(casts) - set(columns)
        if unknown:
            raise ValueError(
                f"cast() references columns not in current selection: {unknown}"
            )

        frame = CastFrame(
            _conn=self._conn,
            _table=self._table,
            _columns=columns,
            _casts=casts,
            _where_clause=getattr(self, "_where_clause", None),
            _limit_val=getattr(self, "_limit_val", None),
            _params=list(getattr(self, "_params", [])),
        )
        return frame
