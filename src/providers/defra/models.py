"""Typed data models shared across the DEFRA importer pipeline.

Every pipeline stage exchanges these dataclasses. Values are kept close to the
published workbook wherever possible and are only normalised where the target
``emission_factors`` table requires it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------
def to_jsonable(value: Any) -> Any:
    """Convert pipeline values into plain JSON-serialisable objects."""
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, set)):
        return [to_jsonable(v) for v in value]
    return value


# ---------------------------------------------------------------------------
# Workbook discovery
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class WorkbookMeta:
    """Metadata discovered on the workbook's meta (front) sheet(s)."""

    source_path: str
    file_sha256: str = ""
    file_size_bytes: Optional[int] = None
    title: str = ""
    version: str = ""
    year: Optional[int] = None
    status: str = ""
    next_publication_date: str = ""
    factor_set_label: str = ""
    producer: str = ""
    contact: str = ""
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "source_path": self.source_path,
                "file_sha256": self.file_sha256,
                "file_size_bytes": self.file_size_bytes,
                "title": self.title,
                "version": self.version,
                "year": self.year,
                "status": self.status,
                "next_publication_date": self.next_publication_date,
                "factor_set_label": self.factor_set_label,
                "producer": self.producer,
                "contact": self.contact,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class WorksheetInfo:
    """Discovery result for a single worksheet."""

    name: str
    sheet_type: str  # 'metadata' | 'data' | 'other'
    max_row: Optional[int]
    max_col: Optional[int]
    header_row: Optional[int] = None  # 1-based header row (data sheets)
    columns: tuple[tuple[str, int], ...] = ()  # (column_label, 1-based index)
    data_row_count: Optional[int] = None
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "name": self.name,
                "sheet_type": self.sheet_type,
                "max_row": self.max_row,
                "max_col": self.max_col,
                "header_row": self.header_row,
                "columns": [{"label": label, "index": idx} for label, idx in self.columns],
                "data_row_count": self.data_row_count,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class WorkbookAnalysis:
    """Top-level analysis of the workbook (meta + worksheet inventory)."""

    meta: WorkbookMeta
    worksheets: tuple[WorksheetInfo, ...]
    data_sheet_names: tuple[str, ...]
    reporting_year: Optional[int]

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "meta": self.meta.as_dict(),
                "worksheets": [w.as_dict() for w in self.worksheets],
                "data_sheet_names": list(self.data_sheet_names),
                "reporting_year": self.reporting_year,
            }
        )


# ---------------------------------------------------------------------------
# Row-level data
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class RawRow:
    """A raw worksheet row (values only) with provenance."""

    sheet_name: str
    row_number: int
    cells: tuple[Any, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "sheet_name": self.sheet_name,
            "row_number": self.row_number,
            "cells": [to_jsonable(c) for c in self.cells],
        }


@dataclass(slots=True)
class EmissionFactor:
    """A normalised emission factor ready for validation and loading.

    Carries both the DB-facing fields and the full published row so the
    JSON/report outputs preserve every DEFRA detail exactly as published.
    """

    reporting_year: int
    activity_type: str
    co2e_multiplier: Decimal
    unit: Optional[str]
    scope: Optional[str]
    factor_source: str
    factor_set: str
    country: str

    # published-row fidelity
    defra_id: str
    level1: str
    level2: str
    level3: str
    level4: str
    column_text: str
    uom: str
    ghg_unit: str
    row_number: int
    sheet_name: str

    # pipeline metadata
    natural_key: tuple[str, ...] = field(default_factory=tuple)
    skip_reason: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "reporting_year": self.reporting_year,
                "activity_type": self.activity_type,
                "co2e_multiplier": self.co2e_multiplier,
                "unit": self.unit,
                "scope": self.scope,
                "factor_source": self.factor_source,
                "factor_set": self.factor_set,
                "country": self.country,
                "defra_id": self.defra_id,
                "level1": self.level1,
                "level2": self.level2,
                "level3": self.level3,
                "level4": self.level4,
                "column_text": self.column_text,
                "uom": self.uom,
                "ghg_unit": self.ghg_unit,
                "row_number": self.row_number,
                "sheet_name": self.sheet_name,
                "natural_key": list(self.natural_key),
            }
        )


# ---------------------------------------------------------------------------
# Validation / outcomes
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class SkippedRow:
    """A workbook row that was read but not imported."""

    row_number: int
    sheet_name: str
    defra_id: str
    reason: str
    detail: str = ""
    activity_type: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "row_number": self.row_number,
                "sheet_name": self.sheet_name,
                "defra_id": self.defra_id,
                "reason": self.reason,
                "detail": self.detail,
                "activity_type": self.activity_type,
            }
        )


@dataclass(slots=True)
class DuplicateRow:
    """A row whose natural key already appeared earlier in the batch."""

    row_number: int
    sheet_name: str
    defra_id: str
    natural_key: tuple[str, ...]
    activity_type: str
    first_row_number: int
    first_defra_id: str

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "row_number": self.row_number,
                "sheet_name": self.sheet_name,
                "defra_id": self.defra_id,
                "natural_key": list(self.natural_key),
                "activity_type": self.activity_type,
                "first_row_number": self.first_row_number,
                "first_defra_id": self.first_defra_id,
            }
        )

@dataclass(slots=True)
class ParsedRow:
    """A row parsed from a data worksheet, as published (pre-normalisation)."""

    sheet_name: str
    row_number: int
    defra_id: str
    scope: str
    level1: str
    level2: str
    level3: str
    level4: str
    column_text: str
    uom: str
    ghg_unit: str
    factor_raw: Any
    parse_issue: Optional[str] = None  # set when a non-empty factor cannot be parsed

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "sheet_name": self.sheet_name,
                "row_number": self.row_number,
                "defra_id": self.defra_id,
                "scope": self.scope,
                "level1": self.level1,
                "level2": self.level2,
                "level3": self.level3,
                "level4": self.level4,
                "column_text": self.column_text,
                "uom": self.uom,
                "ghg_unit": self.ghg_unit,
                "factor_raw": self.factor_raw,
                "parse_issue": self.parse_issue,
            }
        )


@dataclass(slots=True)
class ValidationIssue:
    """A validation finding against a single row."""

    row_number: int
    defra_id: str
    field: str
    severity: str  # 'error' | 'warning'
    message: str

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "row_number": self.row_number,
                "defra_id": self.defra_id,
                "field": self.field,
                "severity": self.severity,
                "message": self.message,
            }
        )


@dataclass(slots=True)
class ValidationReport:
    """Outcome of validation: what will be loaded, skipped and why."""

    factors: list[EmissionFactor] = field(default_factory=list)
    skipped: list[SkippedRow] = field(default_factory=list)
    duplicates: list[DuplicateRow] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "factors": [f.as_dict() for f in self.factors],
                "skipped": [s.as_dict() for s in self.skipped],
                "duplicates": [d.as_dict() for d in self.duplicates],
                "issues": [i.as_dict() for i in self.issues],
            }
        )


@dataclass(slots=True)
class ImportStats:
    """Aggregate counts for the import run."""

    rows_scanned: int = 0
    rows_parsed: int = 0
    empty_rows: int = 0
    end_marker_rows: int = 0
    rows_with_id: int = 0
    factors_with_value: int = 0
    skipped_no_factor: int = 0
    skipped_unparseable: int = 0
    skipped_no_label: int = 0
    skipped_no_id: int = 0
    skipped_validation: int = 0
    duplicates: int = 0
    imported: int = 0

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "rows_scanned": self.rows_scanned,
                "rows_parsed": self.rows_parsed,
                "empty_rows": self.empty_rows,
                "end_marker_rows": self.end_marker_rows,
                "rows_with_id": self.rows_with_id,
                "factors_with_value": self.factors_with_value,
                "skipped_no_factor": self.skipped_no_factor,
                "skipped_unparseable": self.skipped_unparseable,
                "skipped_no_label": self.skipped_no_label,
                "skipped_no_id": self.skipped_no_id,
                "skipped_validation": self.skipped_validation,
                "duplicates": self.duplicates,
                "imported": self.imported,
            }
        )


@dataclass(slots=True)
class ImportResult:
    """Everything a run produced, consumed by the loader/command/reporters."""

    analysis: WorkbookAnalysis
    validation: ValidationReport
    stats: ImportStats
    config: dict[str, Any] = field(default_factory=dict)
    db: dict[str, Any] = field(default_factory=dict)  # loader outcome details

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "analysis": self.analysis.as_dict(),
                "validation": self.validation.as_dict(),
                "stats": self.stats.as_dict(),
                "config": self.config,
                "db": self.db,
            }
        )
