"""P17 Scope 2 accounting dimensions (ARCH-01 Scope 2, P17-A/P17-C).

Pure Python. No framework, database or infrastructure imports.

Scope 2 has TWO accounting methods and they are not interchangeable:

* ``LOCATION_BASED`` — grid-average emission factors for the geography the
  consumption occurred in.
* ``MARKET_BASED`` — contractual instruments (guarantees of origin, RECs, PPAs,
  supplier-specific contracts, green tariffs) claimed by the organization.

The method is STORED on the result (``calculation_snapshots.scope2_method``),
never inferred at reporting time. A Scope 2 result without a recorded method is
not reportable, because a location-based and a market-based figure are different
accounting claims — not two views of one number.

Energy types are exactly ``electricity``, ``heat``, ``steam`` and ``cooling``.
``fuel`` is deliberately NOT a member: fuel-borne energy is a Scope 1 or Scope 3
activity (ARCH-04, reconciling ARCH-03 LOW-02), identified by the activity and
factor rather than by ``energy_type``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from core.exceptions import (
    AccountingDimensionError,
    InstrumentEligibilityError,
    Scope2MethodRequiredError,
)

__all__ = [
    "Scope2Method",
    "EnergyType",
    "SCOPE2_METHODS",
    "ENERGY_TYPES",
    "InstrumentEligibility",
    "validate_scope2_method",
    "validate_energy_type",
    "requires_instrument",
    "instrument_is_eligible",
    "assert_instrument_eligible",
    "assert_scope2_dimensions",
]


class Scope2Method(StrEnum):
    """The two GHG Protocol Scope 2 accounting methods."""

    LOCATION_BASED = "LOCATION_BASED"
    MARKET_BASED = "MARKET_BASED"


class EnergyType(StrEnum):
    """Purchased-energy types in Scope 2. ``fuel`` is NOT a member."""

    ELECTRICITY = "electricity"
    HEAT = "heat"
    STEAM = "steam"
    COOLING = "cooling"


#: Frozen vocabulary, reused verbatim from the B1 disclosure model.
SCOPE2_METHODS: tuple[str, ...] = tuple(m.value for m in Scope2Method)

#: The authoritative four-value Scope 2 energy-type vocabulary.
ENERGY_TYPES: tuple[str, ...] = tuple(e.value for e in EnergyType)


def validate_scope2_method(value: Optional[str]) -> Optional[str]:
    """Return ``value`` when it is a valid Scope 2 method, else raise.

    ``None`` is permitted and means "not recorded". A Scope 2 result carrying
    ``None`` is treated as not reportable rather than defaulted to a method,
    because defaulting would silently invent an accounting claim.
    """
    if value is None:
        return None
    if value not in SCOPE2_METHODS:
        raise AccountingDimensionError(
            f"invalid Scope 2 method {value!r}; expected one of {SCOPE2_METHODS}",
            details={"field": "scope2_method", "received": value,
                     "allowed": list(SCOPE2_METHODS)},
        )
    return value


def validate_energy_type(value: Optional[str]) -> Optional[str]:
    """Return ``value`` when it is a valid Scope 2 energy type, else raise.

    ``fuel`` is rejected with its own explicit message rather than a bare
    "invalid" so the caller learns *why*: fuel is a Scope 1/3 activity, not a
    Scope 2 energy type.
    """
    if value is None:
        return None
    if value == "fuel":
        raise AccountingDimensionError(
            "fuel is not a Scope 2 energy type; fuel-borne energy is a Scope 1 "
            "or Scope 3 activity and is identified by its activity/factor "
            "(ARCH-04 // ARCH-03 LOW-02)",
            details={"field": "energy_type", "received": "fuel",
                     "allowed": list(ENERGY_TYPES)},
        )
    if value not in ENERGY_TYPES:
        raise AccountingDimensionError(
            f"invalid Scope 2 energy type {value!r}; expected one of {ENERGY_TYPES}",
            details={"field": "energy_type", "received": value,
                     "allowed": list(ENERGY_TYPES)},
        )
    return value


def requires_instrument(method: Optional[str]) -> bool:
    """True when this method's accounting claim must be backed by an instrument.

    Market-based Scope 2 is a claim about contractual instruments; location-based
    Scope 2 is a claim about the grid and needs none. This drives the DC-09
    check: a market-based result with no allocation is *unsupported*, which is
    not the same thing as zero.
    """
    return validate_scope2_method(method) == Scope2Method.MARKET_BASED.value


def assert_scope2_dimensions(
    *, scope: Optional[str], scope2_method: Optional[str], energy_type: Optional[str]
) -> None:
    """Fail closed when a NEW Scope 2 claim lacks its required dimensions.

    Applies only to new writes: historical P16 rows carry no method and are
    exempt at the database level (``NOT VALID``), and this guard is not run
    against them.
    """
    if scope != "Scope 2":
        return
    if scope2_method is None:
        raise Scope2MethodRequiredError(
            "a Scope 2 result must record its accounting method "
            "(LOCATION_BASED or MARKET_BASED); the method is never inferred",
            details={"field": "scope2_method"},
        )
    validate_scope2_method(scope2_method)


@dataclass(frozen=True, slots=True)
class InstrumentEligibility:
    """The outcome of asking whether an instrument may support a consumption row."""

    eligible: bool
    reason: Optional[str] = None

    def __bool__(self) -> bool:  # pragma: no cover - convenience only
        return self.eligible


def instrument_is_eligible(
    *,
    method: Optional[str],
    instrument_method: Optional[str] = None,
    instrument_retirement_status: str = "active",
    instrument_geography: Optional[str] = None,
    consumption_geography: Optional[str] = None,
    instrument_vintage_year: Optional[int] = None,
    consumption_vintage_year: Optional[int] = None,
) -> InstrumentEligibility:
    """Decide whether a contractual instrument can back a market-based result.

    Rules, in the architecture's order of strictness:

    1. The result must be market-based. A location-based result can never be
       supported by an instrument; the two are different claims.
    2. The instrument must be ``active``. A retired or cancelled certificate has
       already been claimed, so claiming it again is double counting.
    3. Geography must match when both sides state one. A mismatch is refused
       rather than silently substituted.
    4. Vintage must match when both sides state one. This is the factor-year
       guard applied to instruments: a vintage mismatch must never silently
       substitute another year's instrument.

    ``None`` on a comparison field means "not stated" and the check is skipped
    rather than guessed, so an incomplete record is refused only where the rule
    can actually be evaluated. That is deliberate: refusing on absent data would
    conflate "not recorded" with "known to be wrong".
    """
    if validate_scope2_method(method) != Scope2Method.MARKET_BASED.value:
        return InstrumentEligibility(
            False, "instrument support requires a MARKET_BASED Scope 2 result"
        )
    if instrument_method is not None and instrument_method not in SCOPE2_METHODS:
        return InstrumentEligibility(
            False, f"instrument declares an unknown Scope 2 method {instrument_method!r}"
        )
    if instrument_retirement_status != "active":
        return InstrumentEligibility(
            False,
            f"instrument is {instrument_retirement_status!r}; a non-active "
            "instrument has already been claimed and must not be claimed again",
        )
    if (
        instrument_geography is not None
        and consumption_geography is not None
        and instrument_geography != consumption_geography
    ):
        return InstrumentEligibility(
            False,
            f"instrument geography {instrument_geography!r} does not match "
            f"consumption geography {consumption_geography!r}",
        )
    if (
        instrument_vintage_year is not None
        and consumption_vintage_year is not None
        and instrument_vintage_year != consumption_vintage_year
    ):
        return InstrumentEligibility(
            False,
            f"instrument vintage {instrument_vintage_year} does not match "
            f"consumption vintage {consumption_vintage_year}; another year is "
            "never silently substituted",
        )
    return InstrumentEligibility(True, None)


def assert_instrument_eligible(**kwargs: object) -> InstrumentEligibility:
    """Raise :class:`InstrumentEligibilityError` unless the instrument is eligible."""
    result = instrument_is_eligible(**kwargs)  # type: ignore[arg-type]
    if not result.eligible:
        raise InstrumentEligibilityError(
            f"contractual instrument cannot support this result: {result.reason}",
            details={"reason": result.reason},
        )
    return result
