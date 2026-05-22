"""Mixin that adds .export() to SqlFrame and similar frame classes."""
from __future__ import annotations

from typing import Optional

from sqlframe.export import ExportResult, Exporter


class ExportMixin:
    """Provides export() helper that converts the frame to pandas then exports."""

    def export(
        self,
        fmt: str = "csv",
        path: Optional[str] = None,
        **kwargs,
    ) -> ExportResult:
        """Export query results to *fmt* (csv | json | tsv).

        Parameters
        ----------
        fmt:
            Output format.  One of ``'csv'``, ``'json'``, or ``'tsv'``.
        path:
            File path to write to.  When *None* the serialised content is
            returned inside :class:`ExportResult` without touching the
            filesystem.
        **kwargs:
            Extra keyword arguments forwarded to the underlying pandas
            serialisation method.

        Returns
        -------
        ExportResult
        """
        if fmt not in Exporter.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format {fmt!r}. "
                f"Choose from: {Exporter.SUPPORTED_FORMATS}"
            )

        df = self.to_pandas()
        exporter = Exporter(df)

        method = getattr(exporter, f"to_{fmt}")
        return method(path=path, **kwargs)
