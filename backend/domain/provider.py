"""Provider and import domain objects (Backend v2.1 §9, ADR-10, §15 imports).

Model the provider registry, import batches and the discovery →
normalisation pipeline. Pure Python, immutable frozen dataclasses;
:class:`ImportBatch` state transitions return new instances via ``replace``.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    """Metadata describing an emission-factor provider plugin."""

    key: str
    name: str
    jurisdiction: str
    country_codes: tuple[str, ...]
    website: str
    license: str
    latest_version: str
    publisher: str
    language: str
    documentation_url: str


@dataclass(frozen=True, slots=True)
class ProviderVersion:
    """A released version of a provider's factor set."""

    provider_key: str
    version: str
    release_date: datetime
    status: str
    import_batch_id: Optional[str] = None
    row_count: int = 0
    checksum: str = ""


@dataclass(frozen=True, slots=True)
class ImportError:
    """A problem found while importing one row of a factor sheet."""

    row_number: int
    field: str
    message: str
    severity: str

    def __post_init__(self) -> None:
        if self.severity not in ("error", "warning"):
            raise ValueError(f"severity {self.severity!r} must be 'error' or 'warning'")
        if self.row_number < 1:
            raise ValueError("row_number must be >= 1")


@dataclass(frozen=True, slots=True)
class ImportBatch:
    """An import batch as stored in the RC2 ``import_batches`` table.

    Status values follow the RC2 ``import_batches`` state machine: ``pending``,
    ``importing``, ``completed``, ``failed``, ``rolled_back``.
    """

    id: str
    provider_key: str
    provider_version: str
    source_file: str
    source_checksum: str
    reporting_year: int
    status: str
    rows_total: int
    rows_imported: int
    rows_skipped: int
    rows_duplicate: int
    errors: tuple[ImportError, ...]
    is_active: bool
    created_at: datetime
    created_by: str
    rolled_back_from: Optional[str] = None

    def __post_init__(self) -> None:
        #: Status vocabulary is locked to the RC2 ``import_batches`` CHECK
        #: constraint: pending → importing → completed | failed | rolled_back.
        allowed = {"pending", "importing", "completed", "failed", "rolled_back"}
        if self.status not in allowed:
            raise ValueError(f"status {self.status!r} not in {sorted(allowed)}")
        for label, value in (
            ("rows_total", self.rows_total),
            ("rows_imported", self.rows_imported),
            ("rows_skipped", self.rows_skipped),
            ("rows_duplicate", self.rows_duplicate),
        ):
            if value < 0:
                raise ValueError(f"{label} must be >= 0")

    def activate(self) -> ImportBatch:
        """Return a copy marked as the active version for its provider/year."""
        return replace(
            self,
            status="completed",
            is_active=True,
        )

    def rollback(self, replaced_by: Optional[str]) -> ImportBatch:
        """Return a copy marked as rolled back, superseded by ``replaced_by``."""
        return replace(
            self,
            status="rolled_back",
            is_active=False,
            rolled_back_from=replaced_by,
        )


@dataclass(frozen=True, slots=True)
class DiscoveredSheet:
    """Structural information about one sheet in a provider workbook."""

    name: str
    sheet_type: str
    max_row: int
    max_col: int
    header_row: int
    columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """The result of inspecting a provider workbook before import."""

    provider_key: str
    provider_version: str
    source_path: str
    source_checksum: str
    reporting_year: int
    sheets: tuple[DiscoveredSheet, ...]

    def __post_init__(self) -> None:
        if not self.sheets:
            raise ValueError("discovery must find at least one sheet")


@dataclass(frozen=True, slots=True)
class RawFactorRow:
    """A raw row from a discovered sheet, prior to normalisation."""

    sheet_name: str
    row_number: int
    cells: dict[str, str]


@dataclass(frozen=True, slots=True)
class NormalisedFactor:
    """A raw row normalised into the canonical factor shape."""

    provider_key: str
    reporting_year: int
    activity_type: str
    co2e_multiplier: float
    unit: Optional[str] = None
    scope: Optional[str] = None
    country: str = "GB"
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.co2e_multiplier < 0:
            raise ValueError("co2e_multiplier must be >= 0")


@dataclass(frozen=True, slots=True)
class ImportResult:
    """The outcome of a completed import."""

    batch: ImportBatch
    rows_imported: int
    rows_skipped: int
    rows_duplicate: int
    errors: tuple[ImportError, ...]
    artifacts: dict[str, object]
