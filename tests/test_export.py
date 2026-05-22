"""Tests for the export feature."""
from __future__ import annotations

import json
import os
import tempfile

import pandas as pd
import pytest

from sqlframe.export import Exporter, ExportResult
from sqlframe.frame_export_mixin import ExportMixin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_DF = pd.DataFrame(
    {"id": [1, 2, 3], "name": ["Alice", "Bob", "Carol"], "score": [9.1, 8.5, 7.0]}
)


class FakeFrame(ExportMixin):
    """Minimal frame stub that satisfies ExportMixin.to_pandas()."""

    def __init__(self, df: pd.DataFrame):
        self._df = df

    def to_pandas(self) -> pd.DataFrame:
        return self._df


@pytest.fixture
def frame() -> FakeFrame:
    return FakeFrame(SAMPLE_DF.copy())


@pytest.fixture
def exporter() -> Exporter:
    return Exporter(SAMPLE_DF.copy())


# ---------------------------------------------------------------------------
# Exporter unit tests
# ---------------------------------------------------------------------------

def test_exporter_csv_in_memory(exporter):
    result = exporter.to_csv()
    assert isinstance(result, ExportResult)
    assert result.fmt == "csv"
    assert result.path is None
    assert "Alice" in result.content
    assert "id,name,score" in result.content


def test_exporter_csv_to_file(exporter, tmp_path):
    dest = str(tmp_path / "out.csv")
    result = exporter.to_csv(path=dest)
    assert result.path == dest
    assert result.content is None
    assert os.path.exists(dest)
    loaded = pd.read_csv(dest)
    assert list(loaded["name"]) == ["Alice", "Bob", "Carol"]


def test_exporter_json_in_memory(exporter):
    result = exporter.to_json()
    assert result.fmt == "json"
    parsed = json.loads(result.content)
    assert len(parsed) == 3
    assert parsed[0]["name"] == "Alice"


def test_exporter_json_to_file(exporter, tmp_path):
    dest = str(tmp_path / "out.json")
    result = exporter.to_json(path=dest)
    assert result.path == dest
    assert os.path.exists(dest)


def test_exporter_tsv_in_memory(exporter):
    result = exporter.to_tsv()
    assert result.fmt == "tsv"
    assert "\t" in result.content


# ---------------------------------------------------------------------------
# ExportMixin integration tests
# ---------------------------------------------------------------------------

def test_mixin_csv(frame):
    result = frame.export("csv")
    assert "Bob" in result.content


def test_mixin_json(frame):
    result = frame.export("json")
    parsed = json.loads(result.content)
    assert any(r["id"] == 2 for r in parsed)


def test_mixin_tsv(frame):
    result = frame.export("tsv")
    assert "\t" in result.content


def test_mixin_unsupported_format_raises(frame):
    with pytest.raises(ValueError, match="Unsupported format"):
        frame.export("xlsx")


def test_export_result_repr_with_path():
    r = ExportResult(path="/tmp/x.csv", content=None, fmt="csv")
    assert "/tmp/x.csv" in repr(r)


def test_export_result_repr_in_memory():
    r = ExportResult(path=None, content="a,b", fmt="csv")
    assert "in-memory" in repr(r)
