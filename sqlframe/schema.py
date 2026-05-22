"""Schema inspection utilities for SqlFrame."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlframe.connection import Connection


@dataclass
class ColumnInfo:
    name: str
    dtype: str
    nullable: bool = True
    primary_key: bool = False

    def __repr__(self) -> str:
        pk = " PK" if self.primary_key else ""
        null = "" if self.nullable else " NOT NULL"
        return f"<ColumnInfo {self.name}: {self.dtype}{null}{pk}>"


@dataclass
class TableSchema:
    table: str
    columns: List[ColumnInfo] = field(default_factory=list)

    def column_names(self) -> List[str]:
        return [c.name for c in self.columns]

    def dtypes(self) -> dict:
        return {c.name: c.dtype for c in self.columns}

    def __repr__(self) -> str:
        col_lines = "\n  ".join(repr(c) for c in self.columns)
        return f"TableSchema({self.table}):\n  {col_lines}"

    def __str__(self) -> str:
        return repr(self)


class SchemaInspector:
    """Fetches and caches schema information from a live database connection."""

    def __init__(self, conn: "Connection") -> None:
        self._conn = conn
        self._cache: dict[str, TableSchema] = {}

    def inspect(self, table: str, force: bool = False) -> TableSchema:
        """Return TableSchema for *table*, using cached result unless *force* is True."""
        if not force and table in self._cache:
            return self._cache[table]

        sql = (
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_name = :table "
            "ORDER BY ordinal_position"
        )
        df = self._conn.query(sql, params={"table": table})
        columns = [
            ColumnInfo(
                name=row["column_name"],
                dtype=row["data_type"],
                nullable=row["is_nullable"].upper() == "YES",
            )
            for _, row in df.iterrows()
        ]
        schema = TableSchema(table=table, columns=columns)
        self._cache[table] = schema
        return schema

    def clear_cache(self) -> None:
        self._cache.clear()
