"""P17 contractual instruments and allocations (P17-C, DC-09).

Pure Python. No framework, database or infrastructure imports.

A contractual instrument is a *claim* about where energy came from. Claiming one
twice is double counting, and claiming one the organization did not receive is
fabrication. Three guards follow from that:

1. **Eligibility** — the instrument must be active and must cover the geography
   and vintage. (:mod:`domain.scope2` owns that rule.)
2. **Quantity (DC-09)** — the sum of allocations on an instrument must never
   exceed its quantity. This cannot be a single-row CHECK, so it is enforced here
   and detected in the database by ``p17_instrument_over_allocated``.
3. **Identity** — one allocation of one instrument to one result, for one period.

The module deliberately does NOT map an instrument to a factor. Instrument
eligibility and factor selection are different decisions, and conflating them
would let a certificate silently select an emission factor.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Optional, Sequence

from core.exceptions import AccountingDimensionError, InstrumentOverAllocatedError

from .scope2 import assert_instrument_eligible

__all__ = [
    "InstrumentType",
    "RetirementStatus",
    "INSTRUMENT_TYPES",
    "FULLY_MARKET_BASED",
    "ContractualInstrument",
    "InstrumentAllocation",
    "assert_allocation_within_quantity",
    "remaining_quantity",
]


class InstrumentType(StrEnum):
    """Generic instrument vocabulary (deliberately provider-neutral)."""

    ENERGY_ATTRIBUTE_CERTIFICATE = "energy_attribute_certificate"
    GUARANTEE_OF_ORIGIN = "guarantee_of_origin"
    SUPPLIER_SPECIFIC_CONTRACT = "supplier_specific_contract"
    PPA = "ppa"
    REC = "rec"
    GREEN_TARIFF = "green_tariff"
    OTHER = "other"


class RetirementStatus(StrEnum):
    """Whether the instrument has already been claimed."""

    ACTIVE = "active"
    RETIRED = "retired"
    CANCELLED = "cancelled"


#: Frozen vocabulary, matching ``contractual_instruments_type_check``.
INSTRUMENT_TYPES: tuple[str, ...] = tuple(t.value for t in InstrumentType)

#: A market-based claim is only complete when instrument quantity covers the
#: consumption. A named constant so callers state the intent rather than
#: repeating a magic number.
FULLY_MARKET_BASED = Decimal("1.0")


@dataclass(frozen=True, slots=True)
class ContractualInstrument:
    """A contractual instrument claimed by one organization.

    Attributes:
        organization_id: The CLAIMANT organization (conceptual name
            ``claimant_organization_id``; physical column ``organization_id``).
        instrument_type: The generic instrument kind.
        identifier: Certificate/contract serial.
        geography: Market/geography of validity.
        quantity: The instrument's quantity in ``unit``.
        unit: Unit the quantity is expressed in.
        vintage_year: Generation vintage.
        retirement_status: Whether it has already been claimed.
        issuer: Issuing/provider entity.
        source_facility: Generation/source facility where available.
        valid_from: Start of the validity window.
        valid_to: End of the validity window.
    """

    organization_id: str
    instrument_type: str
    identifier: str
    geography: str
    quantity: Decimal
    unit: str
    vintage_year: Optional[int] = None
    retirement_status: str = RetirementStatus.ACTIVE.value
    issuer: Optional[str] = None
    source_facility: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

    def __post_init__(self) -> None:
        if self.instrument_type not in INSTRUMENT_TYPES:
            raise AccountingDimensionError(
                f"invalid instrument type {self.instrument_type!r}; expected one of "
                f"{INSTRUMENT_TYPES}",
                details={"field": "instrument_type", "received": self.instrument_type},
            )
        if self.quantity <= 0:
            raise AccountingDimensionError(
                "an instrument quantity must be greater than zero",
                details={"field": "quantity", "received": str(self.quantity)},
            )

    @property
    def is_claimable(self) -> bool:
        """True when the instrument has not already been retired or cancelled."""
        return self.retirement_status == RetirementStatus.ACTIVE.value

    def assert_can_support(
        self,
        *,
        method: Optional[str],
        consumption_geography: Optional[str] = None,
        consumption_vintage_year: Optional[int] = None,
        instrument_method: Optional[str] = None,
    ) -> None:
        """Raise unless this instrument may back the given market-based result."""
        assert_instrument_eligible(
            method=method,
            instrument_method=instrument_method,
            instrument_retirement_status=self.retirement_status,
            instrument_geography=self.geography,
            consumption_geography=consumption_geography,
            instrument_vintage_year=self.vintage_year,
            consumption_vintage_year=consumption_vintage_year,
        )


@dataclass(frozen=True, slots=True)
class InstrumentAllocation:
    """One allocation of instrument quantity to a market-based result.

    Attributes:
        organization_id: Must equal the parent instrument's organization — the
            database enforces this with a composite foreign key.
        instrument_id: The instrument being claimed.
        allocated_quantity: Quantity allocated. Must be > 0.
        allocated_unit: Unit of the allocated quantity.
        allocation_period_start: Start of the applicable consumption period.
        allocation_period_end: End of the applicable consumption period.
        calculation_snapshot_id: The market-based result this supports.
        emissions_log_id: The emissions row this supports.
        claim_reference: Claim/record reference.
    """

    organization_id: str
    instrument_id: str
    allocated_quantity: Decimal
    allocated_unit: str
    allocation_period_start: date
    allocation_period_end: date
    calculation_snapshot_id: Optional[str] = None
    emissions_log_id: Optional[str] = None
    claim_reference: Optional[str] = None

    def __post_init__(self) -> None:
        if self.allocated_quantity <= 0:
            raise AccountingDimensionError(
                "an allocated quantity must be greater than zero",
                details={"field": "allocated_quantity",
                         "received": str(self.allocated_quantity)},
            )
        if self.allocation_period_end < self.allocation_period_start:
            raise AccountingDimensionError(
                "an allocation period must not end before it starts",
                details={"field": "allocation_period"},
            )


def remaining_quantity(
    instrument: ContractualInstrument, existing: Sequence[InstrumentAllocation]
) -> Decimal:
    """Return how much of this instrument is still unallocated.

    Never negative: the DC-09 guard refuses an over-allocation, so a negative
    remainder would mean the invariant is already broken. Clamping keeps the
    function safe to call during validation without masking the breach, which
    :func:`assert_allocation_within_quantity` reports.
    """
    allocated = sum((a.allocated_quantity for a in existing), Decimal("0"))
    remainder = instrument.quantity - allocated
    return remainder if remainder > 0 else Decimal("0")


def assert_allocation_within_quantity(
    *,
    instrument: ContractualInstrument,
    existing: Sequence[InstrumentAllocation],
    new_quantity: Decimal,
    unit: Optional[str] = None,
) -> Decimal:
    """DC-09 — refuse an allocation that would exceed the instrument quantity.

    Returns the remaining quantity AFTER the new allocation on success.

    The unit is checked when supplied: allocating 500 kWh against a 500 MWh
    instrument is a silent understatement of a claim, not a rounding difference,
    and would slip past a bare quantity comparison.
    """
    if unit is not None and unit != instrument.unit:
        raise AccountingDimensionError(
            f"allocation unit {unit!r} does not match instrument unit "
            f"{instrument.unit!r}; quantities in different units must not be summed",
            details={"field": "allocated_unit", "instrument_unit": instrument.unit,
                     "received": unit},
        )

    allocated = sum((a.allocated_quantity for a in existing), Decimal("0"))
    total = allocated + new_quantity
    if total > instrument.quantity:
        raise InstrumentOverAllocatedError(
            f"DC-09: allocating {new_quantity} would bring the allocated total to "
            f"{total} against an instrument quantity of {instrument.quantity}; a "
            "quantity cannot be claimed more than once",
            details={
                "instrument_id": instrument.identifier,
                "instrument_quantity": str(instrument.quantity),
                "already_allocated": str(allocated),
                "requested": str(new_quantity),
                "total": str(total),
            },
        )
    return instrument.quantity - total
