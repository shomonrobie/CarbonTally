"""Customer-owned emission factor domain objects (V3, ADR-V3-002 — DECIDED).

Pure Python, immutable frozen dataclasses mirroring the V3M-3
``customer_factors`` table. Customer factors are org-isolated and are a
**distinct surface** from CarbonTally-managed ``emission_factors`` (they are
never auto-promoted into the global database).

Status lifecycle (D-cf-3 — DECIDED): ``draft`` → ``active`` (org Admin/Owner
approval) → ``inactive``/``archived`` (soft-deactivate; no hard delete).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

#: Factor statuses permitted by ``customer_factors.status`` (V3M-3 CHECK).
CUSTOMER_FACTOR_STATUSES = ("draft", "active", "inactive", "archived")

#: Countries permitted by the V3M-3 CHECK.
CUSTOMER_FACTOR_COUNTRIES = ("GB", "IE")

#: Source label stamped on every customer factor (V3M-3 DEFAULT).
CUSTOMER_FACTOR_SOURCE = "CUSTOMER"

#: Approval/soft-deactivate transitions (D-cf-3 — the DB enforces vocabulary,
#: the service enforces authority).
_CUSTOMER_FACTOR_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "draft": ("active", "inactive", "archived"),
    "active": ("inactive", "archived"),
    "inactive": ("active", "archived"),
    "archived": (),
}


@dataclass(frozen=True, slots=True)
class CustomerFactor:
    """A customer-owned emission factor (V3M-3 row).

    Attributes:
        id: Primary key (UUID string).
        organization_id: Owning organisation (FK ``organizations.id``).
        name: Factor display name.
        activity_type: Activity the factor applies to (RC2 label style).
        co2e_multiplier: Emissions per unit (kg CO2e), ``>= 0`` (CHECK).
        reporting_year: The reporting year the factor applies to.
        unit: Consumption unit the multiplier applies to.
        scope: GHG Protocol scope label.
        country: Jurisdiction (``GB``/``IE`` — V3M-3 CHECK).
        factor_source: Always ``CUSTOMER`` for this surface.
        status: Lifecycle status (see :data:`CUSTOMER_FACTOR_STATUSES`).
        version: Version within the factor family (per-version UNIQUE index).
        description: Optional description.
        metadata: Free-form metadata (evidence links etc.).
        created_at / updated_at: Row timestamps.
        created_by / updated_by: Actors.
    """

    id: str
    organization_id: str
    name: str
    activity_type: str
    co2e_multiplier: Any
    reporting_year: int
    unit: Optional[str] = None
    scope: Optional[str] = None
    country: str = "GB"
    factor_source: str = CUSTOMER_FACTOR_SOURCE
    status: str = "draft"
    version: int = 1
    description: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    def __post_init__(self) -> None:
        from decimal import Decimal

        if not self.id:
            raise ValueError("id must not be empty")
        if not self.organization_id:
            raise ValueError("organization_id must not be empty")
        if not self.name:
            raise ValueError("name must not be empty")
        if not self.activity_type:
            raise ValueError("activity_type must not be empty")
        if Decimal(str(self.co2e_multiplier)) < 0:
            raise ValueError("co2e_multiplier must be >= 0")
        if not (1990 <= self.reporting_year <= 2100):
            raise ValueError(
                f"reporting_year {self.reporting_year} outside supported range 1990-2100"
            )
        if self.country not in CUSTOMER_FACTOR_COUNTRIES:
            raise ValueError(
                f"country {self.country!r} not in {CUSTOMER_FACTOR_COUNTRIES}"
            )
        if self.status not in CUSTOMER_FACTOR_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in {CUSTOMER_FACTOR_STATUSES}"
            )
        if self.version < 1:
            raise ValueError("version must be >= 1")

    def can_transition_to(self, new_status: str) -> bool:
        """Return ``True`` when ``new_status`` is a permitted lifecycle step."""
        if new_status == self.status:
            return True
        return new_status in _CUSTOMER_FACTOR_TRANSITIONS.get(self.status, ())
