"""Export utilities for SqlFrame results."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    import pandas as pd


class ExportResult:
    """Holds the result of an export operation."""

    def __init__(self, path: Optional[str], content: Optional[str], fmt: str):
        self.path = path
        self.content = content
        self.fmt = fmt

    def __repr__(self) -> str:
        if self.path:
            return f"<ExportResult fmt={self.fmt!r} path={self.path!r}>"
        return f"<ExportResult fmt={self.fmt!r} in-memory>"


class Exporter:
    """Handles exporting a DataFrame to various formats."""

    SUPPORTED_FORMATS = ("csv", "json", "tsv")

    def __init__(self, df: "pd.DataFrame"):
        self._df = df

    def to_csv(
        self,
        path: Optional[str] = None,
        index: bool = False,
        **kwargs,
    ) -> ExportResult:
        if path:
            self._df.to_csv(path, index=index, **kwargs)
            return ExportResult(path=path, content=None, fmt="csv")
        buf = io.StringIO()
        self._df.to_csv(buf, index=index, **kwargs)
        return ExportResult(path=None, content=buf.getvalue(), fmt="csv")

    def to_json(
        self,
        path: Optional[str] = None,
        orient: str = "records",
        indent: int = 2,
        **kwargs,
    ) -> ExportResult:
        content = self._df.to_json(orient=orient, indent=indent, **kwargs)
        if path:
            Path(path).write_text(content)
            return ExportResult(path=path, content=None, fmt="json")
        return ExportResult(path=None, content=content, fmt="json")

    def to_tsv(
        self,
        path: Optional[str] = None,
        index: bool = False,
        **kwargs,
    ) -> ExportResult:
        kwargs["sep"] = "\t"
        return self.to_csv(path=path, index=index, **kwargs)
