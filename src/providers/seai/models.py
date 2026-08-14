"""Typed models for the CarbonTally SEAI 2025 emission-factor importer.

The SEAI workbook is a formula-driven energy conversion + emission factor
publication. This module defines the provider-side models exchanged by the
SEAI pipeline stages (parser -> mapper -> validator -> exporter -> loader).

The published workbook distinguishes **emission factors** (gCO2/kWh and the
derived kgCO2 per physical unit) from **conversion factors** (energy content,
density, primary-energy factor). Only the final per-physical-unit emission
factors become ``public.emission_factors`` rows; conversion values and notes
are retained in ``SeaiFactor`` metadata fields and the import-batch provenance.

SEAI factors are CO2-only (CH4/N2O are not published). The canonical import
stores them in the existing ``co2e_multiplier`` column (the calculation
contract); CO2-only semantics are preserved through ``factor_source='SEAI'``,
``factor_set='SEAI-2025'``, the ``(kg CO2)`` label suffix and batch provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Canonical import constants (approved Implementation Gate v1.0)
# ---------------------------------------------------------------------------

PROVIDER_KEY = "seai"
FACTOR_SOURCE = "SEAI"
FACTOR_SET = "SEAI-2025"
COUNTRY = "IE"
REPORTING_YEAR = 2025
PROVIDER_VERSION = "2025 (V1.7)"

EXPECTED_SOURCE_ROWS = 28
EXPECTED_IMPORTED = 20
EXPECTED_SKIPPED = 8

#: Canonical unit strings — must match existing CarbonTally units exactly
#: (the calculation engine requires exact unit equality). Reuses the DEFRA
#: dataset's canonical strings; no new spellings are introduced.
CANONICAL_UNITS = ("litres", "kg", "cubic metres", "kWh")

#: Top-level workbook sections -> canonical activity family label.
SECTION_FAMILY = {
    "Liquid": "Liquid fuels",
    "Solid": "Solid fuels",
    "Gas": "Gaseous fuels",
    "Electricity": "Electricity",
}

#: Section -> GHG Protocol scope for the canonical factor.
SECTION_SCOPE = {
    "Liquid": "Scope 1",
    "Solid": "Scope 1",
    "Gas": "Scope 1",
    "Electricity": "Scope 2",
}

#: Section -> canonical unit for the imported per-physical-unit factor.
SECTION_UNIT = {
    "Liquid": "litres",
    "Solid": "kg",
    "Gas": "cubic metres",
    "Electricity": "kWh",
}

#: Rows that are intentionally not importable and why.
SKIP_NO_FACTOR_VALUE = "no_factor_value"
SKIP_NON_CANONICAL_BASIS = "non_canonical_basis"


def to_jsonable(value: Any) -> Any:
    """Convert pipeline values into plain JSON-serialisable objects."""
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, set)):
        return [to_jsonable(v) for v in value]
    return value

# ---------------------------------------------------------------------------
# Workbook discovery / metadata
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SeaiWorkbookMeta:
    """Provenance metadata discovered from the workbook (QAQC + file)."""

    source_path: str
    file_sha256: str = ""
    file_size_bytes: Optional[int] = None
    title: str = ""
    reporting_year: Optional[int] = None
    latest_version: str = ""
    latest_version_date: str = ""
    status: str = ""
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
                "reporting_year": self.reporting_year,
                "latest_version": self.latest_version,
                "latest_version_date": self.latest_version_date,
                "status": self.status,
                "producer": self.producer,
                "contact": self.contact,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class SeaiWorksheetInfo:
    """Discovery result for one worksheet (classification for the report)."""

    name: str
    sheet_type: str  # 'data' | 'documentation' | 'reference'
    max_row: Optional[int]
    max_col: Optional[int]
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "name": self.name,
                "sheet_type": self.sheet_type,
                "max_row": self.max_row,
                "max_col": self.max_col,
                "notes": list(self.notes),
            }
        )


@dataclass(frozen=True, slots=True)
class SeaiWorkbookData:
    """Everything the parser extracts from the workbook."""

    meta: SeaiWorkbookMeta
    worksheets: tuple[SeaiWorksheetInfo, ...]
    authoritative_sheet: str
    rows: tuple["SeaiParsedRow", ...]

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "meta": self.meta.as_dict(),
                "worksheets": [w.as_dict() for w in self.worksheets],
                "authoritative_sheet": self.authoritative_sheet,
                "rows": [r.as_dict() for r in self.rows],
            }
        )


# ---------------------------------------------------------------------------
# Row-level data
# ---------------------------------------------------------------------------


def _dec(value: object) -> Optional[Decimal]:
    """Parse a workbook cell into a Decimal, or ``None`` for no-value cells.

    The workbook uses ``-`` as the "no value" placeholder; blank cells and
    ``None`` are also treated as missing. ``0`` remains a valid value.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip()
    if not text or text in ("-", "–", "—", "n/a", "N/A"):
        return None
    try:
        return Decimal(text)
    except Exception:  # noqa: BLE001 - unparseable -> treated as missing
        return None


@dataclass(frozen=True, slots=True)
class SeaiParsedRow:
    """A data row on the authoritative sheet, as published (pre-mapping)."""

    row_number: int
    name: str
    top_section: str  # Liquid | Solid | Gas | Electricity
    # conversion attributes (workbook columns C..E, J..L)
    toe_per_t: Optional[Decimal] = None
    mj_per_kg: Optional[Decimal] = None
    mj_per_l: Optional[Decimal] = None
    density_kg_m3: Optional[Decimal] = None
    specific_vol_l_per_t: Optional[Decimal] = None
    pe_factor: Optional[Decimal] = None
    # emission-factor attributes (columns F..I)
    gco2_per_kwh: Optional[Decimal] = None
    gco2_per_mj: Optional[Decimal] = None
    kgco2_per_mass_unit: Optional[Decimal] = None  # kgCO2/kg (liquid/solid); kgCO2/m^3 (gas)
    kgco2_per_l: Optional[Decimal] = None
    # note column and reported year
    note: str = ""
    year: Optional[int] = None

    @property
    def has_numeric_emission_factor(self) -> bool:
        return (
            self.gco2_per_kwh is not None
            or self.gco2_per_mj is not None
            or self.kgco2_per_mass_unit is not None
            or self.kgco2_per_l is not None
        )

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "row_number": self.row_number,
                "name": self.name,
                "top_section": self.top_section,
                "toe_per_t": self.toe_per_t,
                "mj_per_kg": self.mj_per_kg,
                "mj_per_l": self.mj_per_l,
                "density_kg_m3": self.density_kg_m3,
                "specific_vol_l_per_t": self.specific_vol_l_per_t,
                "pe_factor": self.pe_factor,
                "gco2_per_kwh": self.gco2_per_kwh,
                "gco2_per_mj": self.gco2_per_mj,
                "kgco2_per_mass_unit": self.kgco2_per_mass_unit,
                "kgco2_per_l": self.kgco2_per_l,
                "note": self.note,
                "year": self.year,
            }
        )


# ---------------------------------------------------------------------------
# Mapped / validation outcomes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SeaiFactor:
    """A canonical SEAI emission factor after mapping (pre-persistence)."""

    reporting_year: int
    activity_type: str
    co2e_multiplier: Decimal
    unit: Optional[str]
    scope: Optional[str]
    factor_source: str
    factor_set: str
    country: str
    provider_key: str = PROVIDER_KEY
    import_batch_id: Optional[str] = None
    # provenance / semantic metadata (not persisted per-factor in v1)
    source_row: int = 0
    source_name: str = ""
    basis: str = ""  # kgCO2/l | kgCO2/kg | kgCO2/m^3 | kgCO2/kWh
    co2_only: bool = True
    provisional: bool = False
    note: str = ""
    natural_key: tuple[str, ...] = ()

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
                "provider_key": self.provider_key,
                "source_row": self.source_row,
                "source_name": self.source_name,
                "basis": self.basis,
                "co2_only": self.co2_only,
                "provisional": self.provisional,
                "note": self.note,
                "natural_key": list(self.natural_key),
            }
        )


@dataclass(frozen=True, slots=True)
class SeaiSkip:
    """A workbook row that is read but intentionally not imported."""

    row_number: int
    name: str
    section: str
    reason: str
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "row_number": self.row_number,
                "name": self.name,
                "section": self.section,
                "reason": self.reason,
                "detail": self.detail,
            }
        )


@dataclass(slots=True)
class SeaiValidationIssue:
    """A validation finding (severity: warning | error)."""

    severity: str
    message: str


@dataclass(slots=True)
class SeaiValidationReport:
    """Outcome of validation: factors, skipped rows, duplicates, issues."""

    factors: list[SeaiFactor] = field(default_factory=list)
    skipped: list[SeaiSkip] = field(default_factory=list)
    duplicates: list[SeaiFactor] = field(default_factory=list)
    issues: list[SeaiValidationIssue] = field(default_factory=list)

    @property
    def warnings(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def errors(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def ok(self) -> bool:
        return self.errors == 0


@dataclass(slots=True)
class SeaiImportResult:
    """Everything an import run produces (exporter + CLI)."""

    workbook: SeaiWorkbookData
    validation: SeaiValidationReport
    config: dict[str, Any] = field(default_factory=dict)
    db: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0

    def as_dict(self) -> dict[str, Any]:
        return to_jsonable(
            {
                "workbook": self.workbook.as_dict(),
                "validation": {
                    "factors": [f.as_dict() for f in self.validation.factors],
                    "skipped": [s.as_dict() for s in self.validation.skipped],
                    "duplicates": [f.as_dict() for f in self.validation.duplicates],
                    "issues": [
                        {"severity": i.severity, "message": i.message}
                        for i in self.validation.issues
                    ],
                    "warnings": self.validation.warnings,
                    "errors": self.validation.errors,
                },
                "config": self.config,
                "db": self.db,
                "execution_time_ms": self.execution_time_ms,
            }
        )

