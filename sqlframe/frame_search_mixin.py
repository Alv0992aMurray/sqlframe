"""Mixin that adds .search() convenience method to frame classes.

Allows quick substring / pattern filtering on one or more string columns
without writing raw SQL LIKE / ILIKE expressions.

Example
-------
>>> df.search("name", "alice")          # WHERE name ILIKE '%alice%'
>>> df.search(["name", "email"], "corp") # WHERE (name ILIKE '%corp%' OR email ILIKE '%corp%')
>>> df.search("status", "^active", mode="regex")  # WHERE status ~ '^active'
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from sqlframe.search import SearchFrame


class SearchMixin:
    """Mixin that exposes a .search() method on any SqlFrame-like object."""

    def search(
        self,
        columns: Union[str, List[str]],
        pattern: str,
        *,
        case_sensitive: bool = False,
        mode: str = "contains",
    ) -> "SearchFrame":
        """Filter rows where *pattern* matches one or more *columns*.

        Parameters
        ----------
        columns:
            A single column name or a list of column names to search.
        pattern:
            The search string.  Interpreted according to *mode*.
        case_sensitive:
            When ``False`` (default) the comparison uses ``ILIKE`` (or the
            dialect equivalent).  When ``True`` plain ``LIKE`` is used.
        mode:
            One of:
            - ``"contains"``  – wraps the pattern with ``%…%``  (default)
            - ``"startswith"`` – appends a trailing ``%``
            - ``"endswith"``   – prepends a leading ``%``
            - ``"exact"``      – no wildcards added
            - ``"regex"``      – uses ``~`` (case-sensitive) or ``~*``
              (case-insensitive); requires a database that supports POSIX
              regex operators (e.g. PostgreSQL).

        Returns
        -------
        SearchFrame
            A lazy frame that resolves to the filtered query.

        Raises
        ------
        ValueError
            If *mode* is not one of the accepted values.
        """
        from sqlframe.search import SearchFrame

        return SearchFrame(
            conn=self._conn,
            source=self,
            columns=columns,
            pattern=pattern,
            case_sensitive=case_sensitive,
            mode=mode,
        )
