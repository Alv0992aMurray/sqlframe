"""Query explanation / profiling utilities for SqlFrame."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from sqlframe.connection import Connection


@dataclass
class ExplainResult:
    """Holds the raw explain output and parsed metadata."""

    sql: str
    plan_rows: List[str] = field(default_factory=list)
    estimated_rows: Optional[int] = None
    dialect: str = "generic"

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"SQL: {self.sql}", "Plan:"]
        lines.extend(f"  {row}" for row in self.plan_rows)
        if self.estimated_rows is not None:
            lines.append(f"Estimated rows: {self.estimated_rows}")
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"ExplainResult(dialect={self.dialect!r}, estimated_rows={self.estimated_rows})"


class Explainer:
    """Runs EXPLAIN against a live connection and parses the result."""

    _EXPLAIN_PREFIX: Dict[str, str] = {
        "postgresql": "EXPLAIN (FORMAT TEXT)",
        "mysql": "EXPLAIN",
        "sqlite": "EXPLAIN QUERY PLAN",
        "generic": "EXPLAIN",
    }

    def __init__(self, conn: "Connection", dialect: str = "generic") -> None:
        self._conn = conn
        self.dialect = dialect.lower()

    def explain(self, sql: str, params: Optional[List[Any]] = None) -> ExplainResult:
        """Return an ExplainResult for *sql*."""
        prefix = self._EXPLAIN_PREFIX.get(self.dialect, self._EXPLAIN_PREFIX["generic"])
        explain_sql = f"{prefix} {sql}"
        df = self._conn.query(explain_sql, params=params or [])

        plan_rows: List[str] = []
        for _, row in df.iterrows():
            plan_rows.append(" | ".join(str(v) for v in row.values))

        estimated_rows = self._parse_estimated_rows(plan_rows)
        return ExplainResult(
            sql=sql,
            plan_rows=plan_rows,
            estimated_rows=estimated_rows,
            dialect=self.dialect,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_estimated_rows(self, plan_rows: List[str]) -> Optional[int]:
        """Best-effort extraction of row-count estimate from plan text."""
        import re

        pattern = re.compile(r"rows=(\d+)", re.IGNORECASE)
        for row in plan_rows:
            m = pattern.search(row)
            if m:
                return int(m.group(1))
        return None
