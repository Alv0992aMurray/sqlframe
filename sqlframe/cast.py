from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    import pandas as pd

# Mapping from friendly type aliases to SQL type strings
TYPE_ALIASES: Dict[str, str] = {
    "int": "INTEGER",
    "integer": "INTEGER",
    "float": "FLOAT",
    "double": "DOUBLE PRECISION",
    "str": "VARCHAR",
    "string": "VARCHAR",
    "text": "TEXT",
    "bool": "BOOLEAN",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "datetime": "TIMESTAMP",
    "timestamp": "TIMESTAMP",
    "numeric": "NUMERIC",
    "decimal": "DECIMAL",
}


def resolve_type(type_str: str) -> str:
    """Resolve a friendly type alias to a SQL type string."""
    return TYPE_ALIASES.get(type_str.lower(), type_str.upper())


@dataclass
class CastFrame:
    """Represents a SELECT with CAST expressions applied to chosen columns."""

    _conn: object
    _table: str
    _columns: list
    _casts: Dict[str, str] = field(default_factory=dict)
    _where_clause: Optional[str] = None
    _limit_val: Optional[int] = None
    _params: list = field(default_factory=list)

    def where(self, condition: str) -> "CastFrame":
        """Filter rows by a SQL condition string."""
        self._where_clause = condition
        return self

    def limit(self, n: int) -> "CastFrame":
        self._limit_val = n
        return self

    def _build_sql(self) -> str:
        parts = []
        for col in self._columns:
            if col in self._casts:
                sql_type = resolve_type(self._casts[col])
                parts.append(f"CAST({col} AS {sql_type}) AS {col}")
            else:
                parts.append(col)

        select_clause = ", ".join(parts)
        sql = f"SELECT {select_clause} FROM {self._table}"

        if self._where_clause:
            sql += f" WHERE {self._where_clause}"
        if self._limit_val is not None:
            sql += f" LIMIT {self._limit_val}"
        return sql

    def to_pandas(self) -> "pd.DataFrame":
        sql = self._build_sql()
        return self._conn.query(sql, params=self._params)

    def __repr__(self) -> str:
        return f"CastFrame(table={self._table!r}, casts={self._casts})"
