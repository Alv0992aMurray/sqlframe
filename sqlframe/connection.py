"""Database connection management for sqlframe."""

from __future__ import annotations

from typing import Optional
import sqlalchemy
from sqlalchemy import Engine, text
import pandas as pd


class Connection:
    """Wraps a SQLAlchemy engine and exposes pandas-friendly query helpers."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_url(cls, url: str, **kwargs) -> "Connection":
        """Create a Connection from a SQLAlchemy connection URL.

        Examples
        --------
        >>> conn = Connection.from_url("sqlite:///mydb.db")
        >>> conn = Connection.from_url("postgresql+psycopg2://user:pw@host/db")
        """
        engine = sqlalchemy.create_engine(url, **kwargs)
        return cls(engine)

    # ------------------------------------------------------------------
    # Core query interface
    # ------------------------------------------------------------------

    def query(self, sql: str, params: Optional[dict] = None) -> pd.DataFrame:
        """Execute *sql* and return the result as a :class:`pandas.DataFrame`.

        Parameters
        ----------
        sql:
            Raw SQL string (may contain ``:name`` bind parameters).
        params:
            Optional mapping of bind-parameter names to values.
        """
        with self._engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            return pd.DataFrame(result.fetchall(), columns=list(result.keys()))

    def execute(self, sql: str, params: Optional[dict] = None) -> None:
        """Execute a non-SELECT statement (DDL / DML)."""
        with self._engine.begin() as conn:
            conn.execute(text(sql), params or {})

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def engine(self) -> Engine:
        """Underlying SQLAlchemy engine."""
        return self._engine

    def __repr__(self) -> str:  # pragma: no cover
        return f"Connection(url={self._engine.url!r})"
