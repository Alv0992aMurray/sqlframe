"""sqlframe — pandas-to-SQL exploratory data analysis toolkit."""
from __future__ import annotations
from typing import Optional

from sqlframe.connection import Connection
from sqlframe.frame import SqlFrame


def read_table(
    table: str,
    *,
    conn: Optional[Connection] = None,
    url: Optional[str] = None,
) -> SqlFrame:
    """Return a lazy :class:`SqlFrame` pointing at *table*.

    Provide either an existing *conn* or a connection *url*; if both are given
    *conn* takes precedence.

    Example::

        import sqlframe
        df = sqlframe.read_table("orders", url="postgresql://user:pass@host/db")
        df.schema()          # inspect columns
        df.limit(5).to_pandas()
    """
    if conn is None and url is None:
        raise ValueError("Provide either 'conn' or 'url'.")
    if conn is None:
        conn = Connection.from_url(url)
    return SqlFrame(table=table, conn=conn)
