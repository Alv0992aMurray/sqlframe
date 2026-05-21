"""sqlframe – pandas-to-SQL patterns for live database exploration."""

from sqlframe.connection import Connection
from sqlframe.frame import SqlFrame

__all__ = ["Connection", "SqlFrame", "read_table"]
__version__ = "0.1.0"


def read_table(connection: Connection, table: str) -> SqlFrame:
    """Return a :class:`SqlFrame` backed by *table*.

    Parameters
    ----------
    connection:
        An active :class:`~sqlframe.connection.Connection`.
    table:
        Fully-qualified table name (e.g. ``"public.orders"`` or just
        ``"orders"``).

    Examples
    --------
    >>> conn = Connection.from_url("sqlite:///sales.db")
    >>> df = read_table(conn, "orders").where("amount > 100").limit(50)
    >>> df.to_pandas()
    """
    sql = f"SELECT * FROM {table}"
    return SqlFrame(connection, sql)
