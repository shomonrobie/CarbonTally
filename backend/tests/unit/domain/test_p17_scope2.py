"""P17 Scope 2 accounting-dimension tests (implementation tests).

Pure, no DB. Covers the P17-A/ARCH-04 Scope 2 vocabulary contract:

* the authoritative energy-type vocabulary is exactly four values and ``fuel``
  is explicitly NOT one of them (ARCH-04, reconciling ARCH-03 LOW-02);
* the accounting method is a required, stored dimension and is never inferred;
* contractual-instrument eligibility refuses retired instruments, geography
  mismatches and vintage mismatches rather than silently substituting.
"""
from __future__ import annotations

import pytest

from core.exceptions import (
    AccountingDimensionError,
    InstrumentEligibilityError,
    Scope2MethodRequiredError,
)
from domain.scope2 import (
    ENERGY_TYPES,
    SCOPE2_METHODS,
    EnergyType,
    Scope2Method,
    assert_instrument_eligible,
    assert_scope2_dimensions,
    instrument_is_eligible,
    requires_instrument,
    validate_energy_type,
    validate_scope2_method,
)


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------
def test_scope2_methods_is_exactly_the_two_ghg_protocol_methods() -> None:
    assert SCOPE2_METHODS == ("LOCATION_BASED", "MARKET_BASED")
    assert tuple(m.value for m in Scope2Method) == SCOPE2_METHODS


def test_energy_types_is_exactly_four_purchased_energy_types() -> None:
    assert ENERGY_TYPES == ("electricity", "heat", "steam", "cooling")
    assert tuple(e.value for e in EnergyType) == ENERGY_TYPES


def test_fuel_is_not_a_scope2_energy_type() -> None:
    """ARCH-03 LOW-02 / ARCH-04: fuel is Scope 1/3, never a Scope 2 energy type."""
    assert "fuel" not in ENERGY_TYPES
    with pytest.raises(AccountingDimensionError) as exc:
        validate_energy_type("fuel")
    # The refusal must explain WHY, not just reject the token.
    assert "Scope 1" in str(exc.value) and "Scope 3" in str(exc.value)


@pytest.mark.parametrize("value", ENERGY_TYPES)
def test_each_energy_type_validates(value: str) -> None:
    assert validate_energy_type(value) == value


def test_none_energy_type_is_permitted_and_means_not_recorded() -> None:
    assert validate_energy_type(None) is None


def test_unknown_energy_type_is_refused() -> None:
    with pytest.raises(AccountingDimensionError):
        validate_energy_type("biomass")


def test_none_scope2_method_is_permitted_but_unknown_is_not() -> None:
    assert validate_scope2_method(None) is None
    with pytest.raises(AccountingDimensionError):
        validate_scope2_method("HYBRID")


# ---------------------------------------------------------------------------
# Method is required for Scope 2 and never inferred
# ---------------------------------------------------------------------------
def test_scope2_result_without_a_method_is_refused() -> None:
    with pytest.raises(Scope2MethodRequiredError):
        assert_scope2_dimensions(scope="Scope 2", scope2_method=None, energy_type=None)


def test_scope2_result_with_a_method_is_accepted() -> None:
    assert_scope2_dimensions(
        scope="Scope 2",
        scope2_method=Scope2Method.LOCATION_BASED.value,
        energy_type="electricity",
    )


def test_non_scope2_result_is_unaffected_by_the_scope2_rule() -> None:
    assert_scope2_dimensions(scope="Scope 1", scope2_method=None, energy_type=None)
    assert_scope2_dimensions(scope="Scope 3", scope2_method=None, energy_type=None)


def test_only_market_based_requires_an_instrument() -> None:
    assert requires_instrument(Scope2Method.MARKET_BASED.value) is True
    assert requires_instrument(Scope2Method.LOCATION_BASED.value) is False
    assert requires_instrument(None) is False


# ---------------------------------------------------------------------------
# Instrument eligibility
# ---------------------------------------------------------------------------
def test_active_matching_instrument_is_eligible() -> None:
    result = instrument_is_eligible(
        method=Scope2Method.MARKET_BASED.value,
        instrument_geography="GB",
        consumption_geography="GB",
        instrument_vintage_year=2025,
        consumption_vintage_year=2025,
    )
    assert result.eligible is True
    assert result.reason is None


def test_location_based_result_can_never_be_supported_by_an_instrument() -> None:
    result = instrument_is_eligible(method=Scope2Method.LOCATION_BASED.value)
    assert result.eligible is False
    assert "MARKET_BASED" in (result.reason or "")


@pytest.mark.parametrize("status", ["retired", "cancelled"])
def test_non_active_instruments_are_ineligible(status: str) -> None:
    """A claimed certificate must not be claimed a second time."""
    result = instrument_is_eligible(
        method=Scope2Method.MARKET_BASED.value,
        instrument_retirement_status=status,
    )
    assert result.eligible is False


def test_geography_mismatch_is_refused_when_both_sides_state_one() -> None:
    result = instrument_is_eligible(
        method=Scope2Method.MARKET_BASED.value,
        instrument_geography="GB",
        consumption_geography="IE",
    )
    assert result.eligible is False
    assert "geography" in (result.reason or "")


def test_vintage_mismatch_is_refused_never_silently_substituted() -> None:
    result = instrument_is_eligible(
        method=Scope2Method.MARKET_BASED.value,
        instrument_vintage_year=2024,
        consumption_vintage_year=2025,
    )
    assert result.eligible is False
    assert "vintage" in (result.reason or "")


def test_absent_comparison_values_are_skipped_not_guessed() -> None:
    """An unstated geography/vintage must not be treated as a mismatch."""
    assert instrument_is_eligible(
        method=Scope2Method.MARKET_BASED.value,
        instrument_geography=None,
        consumption_geography="GB",
    ).eligible is True
    assert instrument_is_eligible(
        method=Scope2Method.MARKET_BASED.value,
        instrument_vintage_year=None,
        consumption_vintage_year=2025,
    ).eligible is True


def test_assert_instrument_eligible_raises_on_ineligibility() -> None:
    with pytest.raises(InstrumentEligibilityError):
        assert_instrument_eligible(
            method=Scope2Method.MARKET_BASED.value,
            instrument_retirement_status="retired",
        )


def test_assert_instrument_eligible_returns_the_result_when_eligible() -> None:
    result = assert_instrument_eligible(method=Scope2Method.MARKET_BASED.value)
    assert result.eligible is True
