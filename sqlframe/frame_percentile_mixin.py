from __future__ import annotations
from typing import List, Union


class PercentileMixin:
    """Mixin that adds percentile/quantile analysis to a frame."""

    def percentile(
        self,
        column: str,
        percentiles: Union[float, List[float]],
        interpolation: str = "linear",
    ) -> "PercentileFrame":  # noqa: F821
        """Compute SQL percentile(s) for *column*.

        Parameters
        ----------
        column:
            Name of the numeric column to analyse.
        percentiles:
            A single float or list of floats in [0, 1].  Common examples::

                frame.percentile("salary", 0.5)          # median
                frame.percentile("salary", [0.25, 0.75]) # IQR bounds
        interpolation:
            Passed through to the SQL ``PERCENTILE_CONT`` / ``PERCENTILE_DISC``
            semantics.  Accepted values: ``'linear'`` (default), ``'lower'``,
            ``'higher'``, ``'midpoint'``, ``'nearest'``.

        Returns
        -------
        PercentileFrame
            A lazy frame that executes when ``.to_pandas()`` is called.
        """
        from sqlframe.percentile import PercentileFrame

        if isinstance(percentiles, float):
            percentiles = [percentiles]

        # Inherit any existing WHERE clause from the parent frame
        where_clause = getattr(self, "_where", None)

        return PercentileFrame(
            conn=self._conn,
            table=self._table,
            column=column,
            percentiles=percentiles,
            where_clause=where_clause,
            interpolation=interpolation,
        )
