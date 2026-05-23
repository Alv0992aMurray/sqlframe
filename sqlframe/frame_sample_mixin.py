from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from sqlframe.sampling import SampleFrame


class SampleMixin:
    """Mixin that adds .sample() to SqlFrame, JoinFrame, etc."""

    def sample(
        self,
        n: Optional[int] = None,
        frac: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> "SampleFrame":
        """Return a random sample of rows.

        Parameters
        ----------
        n:
            Exact number of rows to return (mutually exclusive with *frac*).
        frac:
            Fraction of rows to return, e.g. ``0.1`` for 10 %.
            Translated to ``TABLESAMPLE (10 PERCENT)`` where supported.
        seed:
            Optional random seed passed to the underlying SQL dialect.
            Ignored when the dialect does not support seeded sampling.

        Raises
        ------
        ValueError
            If both *n* and *frac* are supplied, or neither is supplied.
        """
        if n is not None and frac is not None:
            raise ValueError("Specify either 'n' or 'frac', not both.")
        if n is None and frac is None:
            raise ValueError("One of 'n' or 'frac' must be provided.")
        if frac is not None and not (0.0 < frac <= 1.0):
            raise ValueError("'frac' must be in the range (0, 1].")
        if n is not None and n < 1:
            raise ValueError("'n' must be a positive integer.")

        from sqlframe.sampling import SampleFrame

        return SampleFrame(
            conn=self._conn,
            source=self,
            n=n,
            frac=frac,
            seed=seed,
        )
