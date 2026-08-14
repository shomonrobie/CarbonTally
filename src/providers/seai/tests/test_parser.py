"""Unit tests: SEAI workbook reader / parser.

These tests run against the real SEAI workbook (offline, no database).
"""
from __future__ import annotations

import hashlib
import pytest

from src.providers.seai import workbook_sha256
from src.providers.seai.parser import AUTHORITATIVE_SHEET, QAQC_SHEET

EXPECTED_SOURCE_ROWS = 28

#: name -> top-level section for every parsed source row (as published).
EXPECTED_ROW_NAMES = [
    ("Crude oil", "Liquid"),
    ("Gasoline / petrol (100% petroleum)", "Liquid"),
    ("Kerosene", "Liquid"),
    ("Jet Kerosene", "Liquid"),
    ("Diesel / gasoil (100% petroleum)", "Liquid"),
    ("Residual fuel oil / fuel oil", "Liquid"),
    ("LPG", "Liquid"),
    ("Bioethanol", "Liquid"),
    ("Biodiesel ME", "Liquid"),
    ("Biodiesel HVO", "Liquid"),
    ("Biodiesel CHVO", "Liquid"),
    ("Biopropane", "Liquid"),
    ("Biojet HVO", "Liquid"),
    ("Road diesel (avg. biofuel content)", "Liquid"),
    ("Road petrol (avg. biofuel content)", "Liquid"),
    ("Petroleum coke", "Solid"),
    ("Bituminous coal", "Solid"),
    ("Anthracite", "Solid"),
    ("Lignite", "Solid"),
    ("Milled peat", "Solid"),
    ("Sod peat", "Solid"),
    ("Peat briquettes", "Solid"),
    ("Wood pellets & briquettes", "Solid"),
    ("Wood logs & chips", "Solid"),
    ("Natural gas (GCV)", "Gas"),
    ("Natural gas (NCV)", "Gas"),
    ("Electricity consumption", "Electricity"),
    ("Gross electricity supply", "Electricity"),
]


def test_workbook_exists(workbook_path):
    assert workbook_path.exists()
    assert workbook_path.stat().st_size > 10_000


def test_workbook_sha256_is_sha256_hexdigest(workbook_path):
    digest = workbook_sha256(workbook_path)
    assert len(digest) == 64
    assert digest == hashlib.sha256(workbook_path.read_bytes()).hexdigest()


def test_parser_returns_28_source_rows(seai_data):
    assert len(seai_data.rows) == EXPECTED_SOURCE_ROWS


def test_parser_row_names_and_sections(seai_data):
    actual = [(row.name, row.top_section) for row in seai_data.rows]
    assert actual == EXPECTED_ROW_NAMES


def test_parser_authoritative_sheet_only(seai_data):
    assert seai_data.authoritative_sheet == AUTHORITATIVE_SHEET
    types = {ws.sheet_type for ws in seai_data.worksheets}
    assert "data" in types
    data_sheets = [ws for ws in seai_data.worksheets if ws.sheet_type == "data"]
    assert len(data_sheets) == 1
    assert data_sheets[0].name == AUTHORITATIVE_SHEET


def test_parser_metadata_discovered(seai_data, workbook_path):
    assert seai_data.meta.file_sha256
    assert seai_data.meta.source_path == str(workbook_path)
    assert seai_data.meta.title


def test_open_workbook_reads_cached_values(seai_data):
    """Cached values are exposed through the parsed rows (read-only load)."""
    assert seai_data.rows[0].name == "Crude oil"
    assert seai_data.rows[0].top_section == "Liquid"
    electricity = [r for r in seai_data.rows if r.top_section == "Electricity"]
    assert {r.name for r in electricity} == {"Electricity consumption", "Gross electricity supply"}
    for row in electricity:
        assert row.gco2_per_kwh is not None


def test_no_other_sheet_produces_factors(seai_data):
    """Single-source-of-truth: only the authoritative sheet is a data sheet."""
    for ws in seai_data.worksheets:
        if ws.name == AUTHORITATIVE_SHEET:
            assert ws.sheet_type == "data"
        elif ws.name == QAQC_SHEET:
            assert ws.sheet_type == "documentation"
        else:
            assert ws.sheet_type == "reference"
