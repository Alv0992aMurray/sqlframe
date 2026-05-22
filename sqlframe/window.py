"""Window function support for SqlFrame."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    import pandas as pd
    from sqlframe.connection import Connection


@dataclass
class WindowSpec:
    """Describes a OVER (...) clause."""

    partition_by: List[str] = field(default_factory=list)
    order_by: List[str] = field(default_factory=list)

    def _render(self) -> str:
        parts: List[str] = []
        if self.partition_by:
            cols = ", ".join(self.partition_by)
            parts.append(f"PARTITION BY {cols}")
        if self.order_by:
            cols = ", ".join(self.order_by)
            parts.append(f"ORDER BY {cols}")
        return "OVER (" + " ".join(parts) + ")"


class WindowFrame:
    """Wraps a base SQL expression with window function columns."""

    def __init__(
        self,
        conn: "Connection",
        base_sql: str,
        window_cols: List[str],
        extra_cols: Optional[List[str]] = None,
    ) -> None:
        self._conn = conn
        self._base_sql = base_sql
        self._window_cols = window_cols
        self._extra_cols = extra_cols or []
        self._limit: Optional[int] = None
        self._where: Optional[str] = None

    def where(self, condition: str) -> "WindowFrame":
        self._where = condition
        return self

    def limit(self, n: int) -> "WindowFrame":
        self._limit = n
        return self

    def _build_sql(self) -> str:
        select_cols = ", ".join(self._extra_cols + self._window_cols)
        sql = (
            f"SELECT {select_cols} "
            f"FROM ({self._base_sql}) AS _window_base"
        )
        if self._where:
            sql += f" WHERE {self._where}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        return sql

    def to_pandas(self) -> "pd.DataFrame":
        return self._conn.query(self._build_sql())

    def __repr__(self) -> str:  # pragma: no cover
        return f"WindowFrame(sql={self._build_sql()!r})"


def rank_over(partition_by: List[str], order_by: List[str]) -> str:
    spec = WindowSpec(partition_by=partition_by, order_by=order_by)
    return f"RANK() {spec._render()} AS rank"


def row_number_over(partition_by: List[str], order_by: List[str]) -> str:
    spec = WindowSpec(partition_by=partition_by, order_by=order_by)
    return f"ROW_NUMBER() {spec._render()} AS row_number"


def lag_over(
    col: str, offset: int, partition_by: List[str], order_by: List[str]
) -> str:
    spec = WindowSpec(partition_by=partition_by, order_by=order_by)
    return f"LAG({col}, {offset}) {spec._render()} AS lag_{col}"


def lead_over(
    col: str, offset: int, partition_by: List[str], order_by: List[str]
) -> str:
    spec = WindowSpec(partition_by=partition_by, order_by=order_by)
    return f"LEAD({col}, {offset}) {spec._render()} AS lead_{col}"
