"""Mixin that adds .explain() to SqlFrame, JoinFrame, WindowFrame, etc."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from sqlframe.explain import ExplainResult


class ExplainMixin:
    """Mixin providing an explain() method to any frame that has
    ``_build_sql()`` / ``_sql`` and ``_conn`` attributes.
    """

    # Subclasses must expose these (already true for all existing frames).
    _conn: Any
    _params: List[Any]

    def _get_sql(self) -> str:
        """Resolve the current SQL regardless of frame type."""
        if callable(getattr(self, "_build_sql", None)):
            return self._build_sql()  # type: ignore[attr-defined]
        if hasattr(self, "_sql"):
            return self._sql  # type: ignore[attr-defined]
        raise AttributeError(
            f"{type(self).__name__} has neither _build_sql() nor _sql attribute."
        )

    def explain(
        self,
        dialect: Optional[str] = None,
        params: Optional[List[Any]] = None,
    ) -> "ExplainResult":
        """Run EXPLAIN on the frame's current SQL and return an ExplainResult.

        Parameters
        ----------
        dialect:
            One of 'postgresql', 'mysql', 'sqlite', or 'generic' (default).
            When *None* the connection's dialect attribute is used if present.
        params:
            Optional parameter list; falls back to the frame's own ``_params``.
        """
        from sqlframe.explain import Explainer

        resolved_dialect = (
            dialect
            or getattr(self._conn, "dialect", None)
            or "generic"
        )
        explainer = Explainer(self._conn, dialect=resolved_dialect)
        resolved_params = params if params is not None else getattr(self, "_params", [])
        sql = self._get_sql()
        return explainer.explain(sql, params=resolved_params)
