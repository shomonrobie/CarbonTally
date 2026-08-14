"""Typed models for the CarbonTally DEFRA 2025 emission-factor importer.

Every pipeline stage (parser -> mapper -> validator -> exporter) exchanges these
dataclasses. The models deliberately keep the *full* published DEFRA row so no
information is discarded: fields without a column in ``public.emission_factors``
are preserved in ``EmissionFactor.metadata`` (exported as JSON).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

# Sheet classifications produced by the parser.
SHEET_DATA = "data"
SHEET_DOCUMENTATION = "documentation"
SHEET_UNSUPPORTED = "unsupported"


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
    """Metadata discovered on the workbook's documentation sheet(s)."""

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
    sheet_type: str  # data | documentation | unsupported
    max_row: Optional[int]
    max_col: Optional[int]
    header_row: Optional[int] = None
    columns: tuple[tuple[str, int], ...] = ()
    data_row_count: Optional[int] = None
    blank_rows: int = 0
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
                "blank_rows": self.blank_rows,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class WorkbookAnalysis:
    """Top-level analysis: metadata + worksheet inventory + reporting year."""

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
class ParsedRow:
    """A row parsed from a data worksheet, as published (pre-mapping)."""

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
            }
        )


@dataclass(slots=True)
class EmissionFactor:
    """A mapped emission factor.

    Carries the DB-facing fields plus the full published row. DEFRA fields with
    no column in ``public.emission_factors`` (defra_id, level hierarchy, column
    text, GHG/Unit breakdown, provenance) live in ``metadata`` so nothing is
    lost; ``skip_reason`` marks rows the mapper could not map.
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
    metadata: dict[str, Any] = field(default_factory=dict)

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
                "row_number": self.row_number,
                "sheet_name": self.sheet_name,
                "natural_key": list(self.natural_key),
                "metadata": self.metadata,
            }
        )


# ---------------------------------------------------------------------------
# Validation / outcomes
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class SkippedRow:
    """A workbook row that was read but is not importable."""

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
class ValidationIssue:
    """A validation finding against a single row (severity: warning | error)."""

    row_number: int
    defra_id: str
    field: str
    severity: str
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

    @property
    def warnings(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def errors(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

# ---------------------------------------------------------------------------
# Run statistics / result
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class ImportStats:
    """Aggregate counts for the import run."""

    sheets_processed: int = 0
    data_sheets: int = 0
    documentation_sheets: int = 0
    unsupported_sheets: int = 0
    rows_scanned: int = 0
    rows_parsed: int = 0
    blank_rows: int = 0
    end_marker_rows: int = 0
    rows_with_id: int = 0
    factors_with_value: int = 0
    skipped_no_factor: int = 0
    skipped_invalid_factor: int = 0
    skipped_no_activity_name: int = 0
    skipped_no_id: int = 0
    skipped_validation: int = 0
    duplicates: int = 0
    imported: int = 0
    warnings: int = 0
    errors: int = 0

    def as_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return to_jsonable(asdict(self))


@dataclass(slots=True)
class ImportResult:
    """Everything a run produced, consumed by the exporter and CLI."""

    analysis: WorkbookAnalysis
    validation: ValidationReport
    stats: ImportStats
    config: dict[str, Any] = field(default_factory=dict)
    db: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0
    sheet_stats: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "analysis": self.analysis.as_dict(),
                "validation": self.validation.as_dict(),
                "stats": self.stats.as_dict(),
                "config": self.config,
                "db": self.db,
                "execution_time_ms": self.execution_time_ms,
                "sheet_stats": self.sheet_stats,
            }
        )


    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "factors": [f.as_dict() for f in self.factors],
                "skipped": [s.as_dict() for s in self.skipped],
                "duplicates": [d.as_dict() for d in self.duplicates],
                "issues": [i.as_dict() for i in self.issues],
                "warnings": self.warnings,
                "errors": self.errors,
            }
        )

