"""Mixin that adds .schema and .dtypes helpers to frame classes."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlframe.schema import TableSchema


class SchemaMixin:
    """Requires self._conn (Connection) and self._table (str) on the host class."""

    def schema(self, force: bool = False) -> "TableSchema":
        """Return the TableSchema for the underlying table.

        Results are cached on the connection-level SchemaInspector so repeated
        calls within the same session are cheap.

        Args:
            force: If True, bypass the cache and re-query the database.

        Returns:
            A :class:`~sqlframe.schema.TableSchema` instance.
        """
        from sqlframe.schema import SchemaInspector

        if not hasattr(self._conn, "_schema_inspector"):
            self._conn._schema_inspector = SchemaInspector(self._conn)

        return self._conn._schema_inspector.inspect(self._table, force=force)

    def dtypes(self) -> dict:
        """Return a {column_name: data_type} mapping for the underlying table."""
        return self.schema().dtypes()

    def column_names(self) -> list:
        """Return an ordered list of column names for the underlying table."""
        return self.schema().column_names()
