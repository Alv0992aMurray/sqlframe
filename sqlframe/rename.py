"""Column renaming support for SqlFrame via .rename() method."""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    pass


class RenameFrame:
    """Wraps a base frame and applies column aliases in the outermost SELECT."""

    def __init__(self, parent, mapping: Dict[str, str]):
        """
        Parameters
        ----------
        parent:
            A SqlFrame, JoinFrame, or similar object that exposes
            ``_build_sql()`` and ``conn``.
        mapping:
            Dict of {old_name: new_name} column renames.
        """
        self._parent = parent
        self._mapping = mapping
        self.conn = parent.conn

    # ------------------------------------------------------------------
    # SQL construction
    # ------------------------------------------------------------------

    def _build_sql(self) -> tuple[str, list]:
        """Wrap the parent query and apply aliases."""
        inner_sql, params = self._parent._build_sql()

        if not self._mapping:
            return inner_sql, params

        # We need to know which columns exist; derive from parent if possible.
        # Fall back to SELECT * with explicit aliases for mapped columns.
        alias_parts = []
        # Build a column list: renamed cols get AS, others pass through.
        # Because we don't always know all columns at build time we use a
        # sub-select approach: SELECT *, renamed AS alias ... is not portable,
        # so we wrap with SELECT <col_list> FROM (<inner>) sq.
        # We rely on parent exposing _columns when available.
        columns = getattr(self._parent, '_columns', None)

        if columns:
            for col in columns:
                alias = self._mapping.get(col)
                if alias:
                    alias_parts.append(f"{col} AS {alias}")
                else:
                    alias_parts.append(col)
            col_clause = ", ".join(alias_parts)
        else:
            # No column list available — emit explicit renames only.
            for old, new in self._mapping.items():
                alias_parts.append(f"{old} AS {new}")
            col_clause = "*, " + ", ".join(alias_parts) if alias_parts else "*"

        sql = f"SELECT {col_clause} FROM ({inner_sql}) _renamed"
        return sql, params

    # ------------------------------------------------------------------
    # Terminal operations
    # ------------------------------------------------------------------

    def to_pandas(self):
        """Execute and return a pandas DataFrame with renamed columns."""
        sql, params = self._build_sql()
        return self.conn.query(sql, params)

    def __repr__(self) -> str:  # pragma: no cover
        sql, _ = self._build_sql()
        return f"RenameFrame(sql={sql!r})"
