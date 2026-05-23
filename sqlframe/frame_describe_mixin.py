from __future__ import annotations
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    pass


class DescribeMixin:
    """Mixin that adds a describe() method for summary statistics on a SqlFrame."""

    def describe(self, columns: Optional[List[str]] = None, percentiles: Optional[List[float]] = None) -> "DescribeFrame":
        """Return a summary-statistics frame for numeric columns.

        Parameters
        ----------
        columns:
            Subset of columns to describe.  Defaults to all columns in the
            current SELECT list (or '*' when none are specified).
        percentiles:
            Quantile values to include, e.g. [0.25, 0.75].  Not all
            databases support PERCENTILE_CONT; unsupported dialects will
            silently omit those rows.
        """
        from sqlframe.describe import DescribeFrame

        # Resolve column list from the frame's current select columns when
        # the caller does not supply an explicit list.
        resolved_columns = columns or getattr(self, "_columns", None) or []

        return DescribeFrame(
            conn=self._conn,
            source_sql=self._build_sql(),
            columns=resolved_columns,
            percentiles=percentiles or [],
        )
