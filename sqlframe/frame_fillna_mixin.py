from __future__ import annotations
from typing import Any, Dict, Union


class FillNaMixin:
    """
    Mixin that adds .fillna() to SqlFrame and similar frame classes.
    """

    def fillna(
        self,
        value: Union[Any, Dict[str, Any]],
        subset: list = None,
    ) -> "FillNaFrame":
        """
        Replace NULL values with a fill value.

        Parameters
        ----------
        value:
            A scalar to fill all columns, or a dict mapping column names to
            fill values.
        subset:
            When *value* is a scalar, limit replacement to these columns.
            Ignored when *value* is a dict.

        Returns
        -------
        FillNaFrame
        """
        from sqlframe.fillna import FillNaFrame

        if isinstance(value, dict):
            fill_map = value
        else:
            cols = subset if subset is not None else self._get_columns()
            fill_map = {col: value for col in cols}

        return FillNaFrame(
            conn=self._conn,
            table=self._table,
            fill_map=fill_map,
        )

    def _get_columns(self) -> list:
        """Return column names known to this frame, falling back to schema inspection."""
        if hasattr(self, "_columns") and self._columns:
            return list(self._columns)
        # Attempt schema introspection via connection
        try:
            from sqlframe.schema import TableSchema
            schema = TableSchema(self._conn, self._table)
            return schema.column_names()
        except Exception:
            raise ValueError(
                "Cannot determine columns automatically. "
                "Pass a dict to fillna() or specify subset."
            )
