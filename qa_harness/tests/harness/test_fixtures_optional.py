"""Harness self-tests: browser fixtures + optional-dependency degradation (spec §35, §36)."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from qa_harness.browser.fixtures.generate import (
    QA_FIXTURE_PREFIX,
    make_csv_fixture,
    make_pdf_fixture,
    make_xlsx_fixture,
    write_fixture,
)
from qa_harness.config.loader import ConfigLoadError, load_yaml
from qa_harness.core.status import RunStatus, ToolUnavailable


def test_csv_fixture() -> None:
    csv_text = make_csv_fixture()
    assert csv_text.startswith("date,activity,quantity,unit")
    assert "Diesel" in csv_text
    assert "4258.9" in csv_text
    assert "L" in csv_text  # unit alias 'L' — matches the shared demo record


def test_pdf_fixture() -> None:
    pdf = make_pdf_fixture()
    assert pdf.startswith(b"%PDF")
    assert b"%%EOF" in pdf


def test_xlsx_fixture_is_valid_zip() -> None:
    data = make_xlsx_fixture()
    with zipfile.ZipFile(__import__("io").BytesIO(data)) as archive:
        names = archive.namelist()
        assert "[Content_Types].xml" in names
        assert "xl/workbook.xml" in names


def test_write_fixture(tmp_path: Path) -> None:
    path = write_fixture("csv", directory=tmp_path)
    assert path.exists()
    assert path.name.startswith(QA_FIXTURE_PREFIX)
    assert path.suffix == ".csv"


def test_tool_unavailable_semantics() -> None:
    exc = ToolUnavailable("axe")
    assert exc.tool == "axe"
    assert RunStatus.TOOL_UNAVAILABLE.value == "SKIPPED — TOOL UNAVAILABLE"


def test_missing_yaml_reports_config_error(monkeypatch) -> None:
    import qa_harness.config.loader as loader

    monkeypatch.setattr(loader, "_YAML_AVAILABLE", False)
    with pytest.raises(ConfigLoadError):
        load_yaml(Path(__file__).parent.parent / "fixtures" / "sample_manifest.json")


def test_graceful_config_fallback_in_table_rules() -> None:
    from qa_harness.rules.tables import build_table_rules

    rules = build_table_rules()
    # Never raises even when the config directory cannot be loaded.
    assert isinstance(rules, dict)
