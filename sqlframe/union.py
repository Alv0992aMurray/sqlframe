from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    import pandas as pd


class UnionFrame:
    """
    Represents a UNION (or UNION ALL) of two or more SqlFrame-like objects.
    """

    def __init__(self, frames, conn, union_all: bool = False):
        if len(frames) < 2:
            raise ValueError("UnionFrame requires at least two frames.")
        self._frames = frames
        self._conn = conn
        self._union_all = union_all
        self._where_clause: Optional[str] = None
        self._limit_val: Optional[int] = None

    def where(self, condition: str) -> "UnionFrame":
        """Apply a WHERE filter to the entire union result."""
        clone = self._clone()
        clone._where_clause = condition
        return clone

    def limit(self, n: int) -> "UnionFrame":
        """Limit the number of rows returned."""
        clone = self._clone()
        clone._limit_val = n
        return clone

    def _build_sql(self) -> str:
        keyword = "UNION ALL" if self._union_all else "UNION"
        parts = []
        for frame in self._frames:
            if hasattr(frame, "_build_sql"):
                parts.append(f"({frame._build_sql()})")
            else:
                raise TypeError(f"Cannot union object of type {type(frame)}")
        union_sql = f" {keyword} ".join(parts)
        sql = f"SELECT * FROM ({union_sql}) AS _union_result"
        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def to_pandas(self) -> "pd.DataFrame":
        """Execute the union query and return a DataFrame."""
        return self._conn.query(self._build_sql())

    def count(self) -> int:
        """Return the number of rows in the union result.

        Wraps the union SQL in a COUNT query so that only a single
        aggregate row is fetched rather than the full result set.
        """
        keyword = "UNION ALL" if self._union_all else "UNION"
        parts = []
        for frame in self._frames:
            if hasattr(frame, "_build_sql"):
                parts.append(f"({frame._build_sql()})")
            else:
                raise TypeError(f"Cannot union object of type {type(frame)}")
        union_sql = f" {keyword} ".join(parts)
        count_sql = f"SELECT COUNT(*) AS _count FROM ({union_sql}) AS _union_result"
        if self._where_clause:
            count_sql += f" WHERE {self._where_clause}"
        result = self._conn.query(count_sql)
        return int(result["_count"].iloc[0])

    def _clone(self) -> "UnionFrame":
        clone = UnionFrame(self._frames, self._conn, self._union_all)
        clone._where_clause = self._where_clause
        clone._limit_val = self._limit_val
        return clone

    def __repr__(self) -> str:
        keyword = "UNION ALL" if self._union_all else "UNION"
        return f"UnionFrame({keyword}, frames={len(self._frames)}, sql={self._build_sql()!r})"
