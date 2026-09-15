"""Unit tests for the B3 disclosure projection domain model (pure, no I/O)."""
from __future__ import annotations

from decimal import Decimal

import pytest

from domain.disclosure import SOURCE_KINDS, VALUE_STATUSES, DisclosureViolation
from domain.disclosure_projection import (
    PRODUCER_REGISTRY,
    aggregate,
    assert_no_legal_determination,
    assert_producer_registry_complete,
    compute_intensity_ratio,
    decide_projection,
    derive_effective_class,
    permitted_aggregations,
    registry_entry,
    validate_applicability_basis,
)


# --- registry ---------------------------------------------------------------
def test_registry_covers_exactly_the_ratified_source_kinds() -> None:
    assert_producer_registry_complete()
    assert set(PRODUCER_REGISTRY) == set(SOURCE_KINDS)
    assert len(SOURCE_KINDS) == 9


def test_unknown_source_kind_is_rejected() -> None:
    with pytest.raises(DisclosureViolation):
        registry_entry("NOT_A_PRODUCER")


def test_permitted_aggregations_are_source_specific() -> None:
    calc = permitted_aggregations("CALCULATION_AGGREGATE")
    assert "SUM_KG_CO2E" in calc
    prov = permitted_aggregations("FACTOR_PROVENANCE")
    assert "SUM_KG_CO2E" not in prov and "PASSTHROUGH" in prov


# --- aggregation ------------------------------------------------------------
def test_sum_kg_co2e_sums_authoritative_rows() -> None:
    rows = [{"co2e_kg": "10.5"}, {"co2e_kg": "2.25"}, {"co2e_kg": 7}]
    result = aggregate("SUM_KG_CO2E", rows)
    assert result.numeric_value == Decimal("19.75")
    assert result.value_unit == "kgCO2e"
    assert result.row_count == 3


def test_sum_kg_co2e_requires_the_field() -> None:
    with pytest.raises(DisclosureViolation):
        aggregate("SUM_KG_CO2E", [{"quantity": 1}])


def test_sum_requires_a_single_normalised_unit() -> None:
    ok = aggregate("SUM", [{"quantity": "1", "unit": "kWh"}, {"quantity": "2", "unit": "kWh"}])
    assert ok.numeric_value == Decimal("3") and ok.value_unit == "kWh"
    with pytest.raises(DisclosureViolation):
        aggregate("SUM", [{"quantity": 1, "unit": "kWh"}, {"quantity": 1, "unit": "m3"}])


def test_distinct_count_uses_natural_key() -> None:
    result = aggregate("DISTINCT_COUNT", [{"natural_key": "a"}, {"natural_key": "a"}, {"natural_key": "b"}])
    assert result.numeric_value == Decimal("2")
    with pytest.raises(DisclosureViolation):
        aggregate("DISTINCT_COUNT", [{"nothing": 1}])


def test_ratio_with_zero_denominator_yields_no_value() -> None:
    result = aggregate("RATIO", [{"numerator": "10", "denominator": "0"}])
    assert result.numeric_value is None and result.reason == "ratio denominator is zero"
    good = aggregate("RATIO", [{"numerator": "10", "denominator": "4"}])
    assert good.numeric_value == Decimal("2.5")


def test_passthrough_requires_exactly_one_row() -> None:
    assert aggregate("PASSTHROUGH", [{"value": "5", "unit": "GBP"}]).numeric_value == Decimal("5")
    with pytest.raises(DisclosureViolation):
        aggregate("PASSTHROUGH", [{"value": 1}, {"value": 2}])


def test_empty_rows_is_not_a_value() -> None:
    result = aggregate("SUM_KG_CO2E", [])
    assert result.numeric_value is None
    assert result.reason == "no authoritative rows for the period"


# --- effective class / projection decisions ---------------------------------
def test_effective_class_precedence() -> None:
    assert derive_effective_class(requirement_class="REQUIRED", applicability_status="DOES_NOT_APPLY", carbontally_capability="SUPPORTED") == "NOT_APPLICABLE"
    assert derive_effective_class(requirement_class="REQUIRED", applicability_status="UNDETERMINED", carbontally_capability="SUPPORTED") == "UNDETERMINED"
    assert derive_effective_class(requirement_class="REQUIRED", applicability_status="APPLIES", carbontally_capability="MISSING_CAPABILITY") == "NOT_SUPPORTED"
    assert derive_effective_class(requirement_class="FUTURE", applicability_status="APPLIES", carbontally_capability="SUPPORTED") == "FUTURE"
    assert derive_effective_class(requirement_class="REQUIRED", applicability_status="APPLIES", carbontally_capability="SUPPORTED") == "REQUIRED"


def test_undetermined_is_never_coerced_to_not_applicable() -> None:
    decision = decide_projection(requirement_class="REQUIRED", carbontally_capability="SUPPORTED", applicability_status="UNDETERMINED")
    assert decision.effective_class == "UNDETERMINED"
    assert decision.value_status == "UNRESOLVED"
    assert "undetermined" in (decision.reason or "")


def test_not_supported_and_customer_input_reasons_are_never_conflated() -> None:
    unsupported = decide_projection(requirement_class="REQUIRED", carbontally_capability="MISSING_CAPABILITY", applicability_status="APPLIES")
    needs_input = decide_projection(requirement_class="CUSTOMER_INPUT_REQUIRED", carbontally_capability="STRUCTURED_INPUT_REQUIRED", applicability_status="APPLIES")
    assert unsupported.effective_class == "NOT_SUPPORTED"
    assert needs_input.effective_class == "CUSTOMER_INPUT_REQUIRED"
    assert unsupported.reason != needs_input.reason
    assert unsupported.reason == "not supported by CarbonTally"
    assert needs_input.reason == "customer input required"


def test_customer_input_materialises_when_supplied() -> None:
    decision = decide_projection(
        requirement_class="CUSTOMER_INPUT_REQUIRED",
        carbontally_capability="STRUCTURED_INPUT_REQUIRED",
        applicability_status="APPLIES",
        customer_input={"value": "123.5", "unit": "GBP"},
    )
    assert decision.value_status == "RESOLVED"
    assert decision.numeric_value == Decimal("123.5")
    assert decision.source_kind == "CUSTOMER_INPUT"


def test_happy_path_materialises_from_snapshots() -> None:
    decision = decide_projection(
        requirement_class="REQUIRED",
        carbontally_capability="SUPPORTED",
        applicability_status="APPLIES",
        source_kind="CALCULATION_AGGREGATE",
        rows=[{"co2e_kg": "100.0"}, {"co2e_kg": "23.5"}],
    )
    assert decision.value_status == "RESOLVED"
    assert decision.numeric_value == Decimal("123.5")
    assert decision.value_unit == "kgCO2e"


def test_no_authoritative_rows_is_unresolved_not_zero() -> None:
    decision = decide_projection(
        requirement_class="REQUIRED",
        carbontally_capability="SUPPORTED",
        applicability_status="APPLIES",
        source_kind="EMISSIONS_LOG_AGGREGATE",
        rows=[],
    )
    assert decision.value_status == "UNRESOLVED"
    assert decision.numeric_value is None
    assert decision.reason == "no authoritative rows for the period"


def test_source_kind_is_required_to_materialise() -> None:
    with pytest.raises(DisclosureViolation):
        decide_projection(requirement_class="REQUIRED", carbontally_capability="SUPPORTED", applicability_status="APPLIES")


def test_aggregation_must_be_permitted_for_the_source_kind() -> None:
    with pytest.raises(DisclosureViolation):
        decide_projection(
            requirement_class="REQUIRED",
            carbontally_capability="SUPPORTED",
            applicability_status="APPLIES",
            source_kind="FACTOR_PROVENANCE",
            aggregation="SUM_KG_CO2E",
            rows=[{"co2e_kg": 1}],
        )


def test_every_decision_uses_the_ratified_value_status_vocabulary() -> None:
    cases = [
        decide_projection(requirement_class="REQUIRED", carbontally_capability="SUPPORTED", applicability_status="APPLIES", source_kind="CALCULATION_AGGREGATE", rows=[{"co2e_kg": 1}]),
        decide_projection(requirement_class="REQUIRED", carbontally_capability="SUPPORTED", applicability_status="DOES_NOT_APPLY"),
        decide_projection(requirement_class="REQUIRED", carbontally_capability="SUPPORTED", applicability_status="APPLIES", source_kind="CALCULATION_AGGREGATE", rows=[]),
    ]
    for decision in cases:
        assert decision.value_status in VALUE_STATUSES


# --- intensity + applicability guards ---------------------------------------
def test_intensity_ratio_arithmetic() -> None:
    assert compute_intensity_ratio("100", "4") == Decimal("25")
    assert compute_intensity_ratio("1", "0") is None
    assert compute_intensity_ratio(None, "4") is None
    with pytest.raises(DisclosureViolation):
        compute_intensity_ratio("1", "-2")


def test_legal_determination_phrases_are_rejected() -> None:
    assert_no_legal_determination("Turnover exceeds the threshold; CarbonTally records this as applicable.")
    with pytest.raises(DisclosureViolation):
        assert_no_legal_determination("The organisation is legally required to report.")


def test_applicability_basis_must_be_real_and_non_legal() -> None:
    assert validate_applicability_basis("  Turnover above threshold per filed accounts  ", "APPLIES") == "Turnover above threshold per filed accounts"
    with pytest.raises(DisclosureViolation):
        validate_applicability_basis("   ", "APPLIES")
    with pytest.raises(DisclosureViolation):
        validate_applicability_basis("This is legal advice", "APPLIES")
    with pytest.raises(DisclosureViolation):
        validate_applicability_basis("ok", "NOT_A_STATUS")


def test_unmapped_customer_input_requirement_keeps_its_own_reason() -> None:
    """A CUSTOMER_INPUT_REQUIRED requirement is never reported as merely unmapped."""
    from domain.disclosure_projection import unmapped_decision

    decision = unmapped_decision(
        requirement_class="CUSTOMER_INPUT_REQUIRED",
        carbontally_capability="STRUCTURED_INPUT_REQUIRED",
        applicability_status="APPLIES",
    )
    assert decision.value_status == "UNRESOLVED"
    assert decision.effective_class == "CUSTOMER_INPUT_REQUIRED"
    assert decision.reason == "customer input required"

    plain = unmapped_decision(
        requirement_class="REQUIRED",
        carbontally_capability="SUPPORTED",
        applicability_status="APPLIES",
    )
    assert plain.reason == "no producer mapping recorded for this requirement"
    assert plain.reason != decision.reason
