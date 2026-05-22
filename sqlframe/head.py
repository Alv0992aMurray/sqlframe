from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import pandas as pd

if TYPE_CHECKING:
    from sqlframe.connection import Connection


class HeadFrame:
    """
    Represents a query that fetches the first N rows from a source query.
    Mirrors the behaviour of pandas DataFrame.head(n).
    """

    def __init__(
        self,
        conn: "Connection",
        source_sql: str,
        n: int = 5,
        params: Optional[list] = None,
    ) -> None:
        self._conn = conn
        self._source_sql = source_sql.rstrip(";")
        self._n = n
        self._params = params or []

    # ------------------------------------------------------------------
    # SQL construction
    # ------------------------------------------------------------------

    def _build_sql(self) -> str:
        """Wrap the source query in a LIMIT clause."""
        return f"SELECT * FROM ({self._source_sql}) AS _head_subq LIMIT {self._n}"

    # ------------------------------------------------------------------
    # Terminal actions
    # ------------------------------------------------------------------

    def to_pandas(self) -> pd.DataFrame:
        """Execute the head query and return a pandas DataFrame."""
        sql = self._build_sql()
        return self._conn.query(sql, params=self._params)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"HeadFrame(n={self._n}, sql={self._build_sql()!r})"
