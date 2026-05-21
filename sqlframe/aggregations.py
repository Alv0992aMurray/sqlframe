"""Aggregation helpers for SqlFrame — wraps GROUP BY / aggregate SQL patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Union

import pandas as pd

if TYPE_CHECKING:
    from sqlframe.frame import SqlFrame


AGG_FUNCTIONS = {"sum", "avg", "min", "max", "count"}


class AggFrame:
    """Represents a pending GROUP BY + aggregation query built on top of a SqlFrame."""

    def __init__(
        self,
        parent: "SqlFrame",
        group_by: List[str],
        agg_specs: Dict[str, str],
    ) -> None:
        self._parent = parent
        self._group_by = group_by
        # agg_specs: {alias: "func(column)"} e.g. {"total": "sum(amount)"}
        self._agg_specs = agg_specs

    # ------------------------------------------------------------------
    # SQL construction
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        base = self._parent._build_sql()
        group_cols = ", ".join(self._group_by)
        select_parts = list(self._group_by) + [
            f"{expr} AS {alias}" for alias, expr in self._agg_specs.items()
        ]
        select_clause = ", ".join(select_parts)
        sql = f"SELECT {select_clause} FROM ({base}) _agg_subq"
        if self._group_by:
            sql += f" GROUP BY {group_cols}"
        return sql

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def order_by(self, *columns: str) -> "AggFrame":
        """Append an ORDER BY clause (returns a new AggFrame wrapper)."""
        # Lightweight: store order and emit in _build_sql via subclass trick
        clone = AggFrame(self._parent, self._group_by, self._agg_specs)
        clone._order_cols = list(columns)  # type: ignore[attr-defined]
        return clone

    def to_pandas(self) -> pd.DataFrame:
        """Execute the aggregation and return a pandas DataFrame."""
        sql = self._build_sql()
        order_cols = getattr(self, "_order_cols", [])
        if order_cols:
            sql += " ORDER BY " + ", ".join(order_cols)
        return self._parent._conn.query(sql)

    def __repr__(self) -> str:  # pragma: no cover
        return f"AggFrame(group_by={self._group_by}, aggs={list(self._agg_specs.keys())})"
