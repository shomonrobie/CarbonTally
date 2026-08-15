"""Calculation domain objects (Backend v2.1 §9, ADR-10, §13 verification).

Pure Python, immutable frozen dataclasses. Reproducibility is verified by
recomputing emissions from inputs and comparing against the stored result.
"""
from __future__ import annotations

import datetime
import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Optional

from core.types import DateRange
from domain.customer_factor import CustomerFactor
from domain.factor import EmissionFactor


class CalculationMethodology(StrEnum):
    """Methodology used to compute an emissions figure."""

    DIRECT_MULTIPLY = "direct_multiply"
    DISTANCE_BASED = "distance_based"
    SPEND_BASED = "spend_based"
    AREA_BASED = "area_based"
    MASS_BALANCE = "mass_balance"


@dataclass(frozen=True, slots=True)
class CalculationSnapshot:
    """An immutable record of a single emissions calculation.

    Stored in the RC2 ``calculation_snapshots`` table so every reported figure
    can be reproduced and audited. V3 (O1 / ADR-V3-014): a snapshot references
    exactly one factor source — ``factor_kind='emission_factor'`` +
    ``factor_id``, or ``factor_kind='customer_factor'`` +
    ``customer_factor_id`` (DB exactly-one-source CHECK).
    """

    id: str
    match_request_id: str
    organization_id: str
    factor_id: Optional[str]
    quantity: Decimal
    quantity_unit: str
    co2e_multiplier: Decimal
    co2e_kg: Decimal
    scope: Optional[str]
    date: datetime.date
    reporting_year: int
    methodology: str
    algorithm_version: str
    created_at: datetime.date
    content_hash: str = ""
    factor_kind: str = "emission_factor"
    customer_factor_id: Optional[str] = None
    source_file: Optional[str] = None
    source_page: Optional[int] = None

    def _canonical(self) -> str:
        """Canonical serialisation of every input that affects the result."""
        return "|".join(
            [
                str(self.quantity),
                self.quantity_unit,
                str(self.co2e_multiplier),
                self.factor_kind,
                self.factor_id or "",
                self.customer_factor_id or "",
                self.scope or "",
                self.date.isoformat(),
                str(self.reporting_year),
                self.methodology,
                self.algorithm_version,
            ]
        )

    def build_content_hash(self) -> str:
        """Compute the SHA-256 content hash of the snapshot's inputs."""
        return hashlib.sha256(self._canonical().encode("utf-8")).hexdigest()

    def verify_reproducibility(self, recomputed: Decimal) -> bool:
        """Return ``True`` when ``recomputed`` matches the stored result.

        The caller recomputes ``co2e_kg`` from the factor and quantity using the
        same rounding as the original calculation.
        """
        return recomputed == self.co2e_kg


@dataclass(frozen=True, slots=True)
class CalculationResult:
    """The outcome of a calculation, including the exact inputs used.

    ``factor_used`` is the CarbonTally-managed factor (emission-factor path);
    ``customer_factor`` is populated when the calculation used a customer-owned
    factor (O1 — exactly one of the two sources applies).
    """

    co2e_kg: Decimal
    co2e_tonnes: Decimal
    snapshot: CalculationSnapshot
    methodology: CalculationMethodology
    factor_used: Optional[EmissionFactor] = None
    customer_factor: Optional[CustomerFactor] = None


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Outcome of an audit-time reproducibility check (Backend v2.1 §13)."""

    match: bool
    discrepancy: Optional[Decimal] = None
    tampered: bool = False


@dataclass(frozen=True, slots=True)
class EmissionLog:
    """An operational emissions record (RC2 ``emissions_logs`` row).

    Represents one logged consumption event. ``quantity`` is the raw consumption
    figure and ``calculated_kg_co2e`` the resulting emissions. ``factor_id`` is
    the ``emission_factors`` id for CarbonTally-managed factors; it is ``None``
    for customer-factor calculations (O1 — the snapshot carries
    ``customer_factor_id``; the column is nullable in the RC2 schema). The
    repository layer persists the record; the Calculation Engine (Phase 6)
    writes the calculated figure through ``save``.
    """

    id: str
    organization_id: str
    factor_id: Optional[str]
    quantity: Decimal
    date: datetime.date
    unit: Optional[str] = None
    scope: Optional[str] = None
    asset_id: Optional[str] = None
    facility_id: Optional[str] = None
    snapshot_id: Optional[str] = None
    calculated_kg_co2e: Decimal = Decimal("0")
    created_at: Optional[datetime.datetime] = None

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("quantity must be >= 0")
        if self.calculated_kg_co2e < 0:
            raise ValueError("calculated_kg_co2e must be >= 0")
        if not self.id:
            raise ValueError("id must not be empty")


@dataclass(frozen=True, slots=True)
class EmissionsAggregate:
    """Aggregated emissions for an organisation over a period (Backend v2.1 §10).

    ``by_scope`` breaks the total down per GHG Protocol scope label and
    ``by_group`` per the requested grouping dimension (``scope``, ``month``,
    ``year`` or ``asset``).
    """

    organization_id: str
    period: DateRange
    group_by: str
    total_co2e_kg: Decimal
    total_rows: int
    by_scope: dict[str, Decimal] = field(default_factory=dict)
    by_group: dict[str, Decimal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.total_co2e_kg < 0:
            raise ValueError("total_co2e_kg must be >= 0")
        if self.total_rows < 0:
            raise ValueError("total_rows must be >= 0")
        if not self.group_by:
            raise ValueError("group_by must not be empty")
