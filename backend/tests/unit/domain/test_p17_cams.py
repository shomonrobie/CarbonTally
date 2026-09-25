"""P17 unified CAMS engine tests (implementation tests).

Pure, no DB. Asserts that ONE engine serves every persona: a direct customer, a
consultant, a consultant client and a delegated user all reach the same verdict
on what makes a defensible number, because they all pass through
``resolve_accounting_dimensions``.

Also covers the rules that make an estimate audit-able (T-INV-12) and the DC-09
instrument-allocation guard.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import (
    AccountingDimensionError,
    EstimationRecordRequiredError,
    InstrumentOverAllocatedError,
    Scope2MethodRequiredError,
    Scope3CategoryNotSupportedError,
    Scope3CategoryRequiredError,
)
from domain.cams import (
    AccountingDimensions,
    CamsContext,
    CamsPersona,
    describe_dimensions,
    resolve_accounting_dimensions,
)
from domain.contractual_instruments import (
    ContractualInstrument,
    InstrumentAllocation,
    assert_allocation_within_quantity,
    remaining_quantity,
)
from domain.data_quality import (
    DATA_QUALITY_VALUES,
    ESTIMATED_DATA_QUALITY,
    PRODUCT_DATA_QUALITY_BUCKETS,
    describe_data_quality,
    is_estimated,
    quality_mix,
    reporting_bucket,
    validate_data_quality,
)
from domain.estimation import (
    ESTIMATION_METHODS,
    EstimationMethod,
    EstimationRecord,
    requires_estimation_record,
)

ORG = "org-1"

ALL_PERSONAS = (
    CamsPersona.STAFF,
    CamsPersona.DIRECT_CUSTOMER,
    CamsPersona.CONSULTANT,
    CamsPersona.CONSULTANT_CLIENT,
    CamsPersona.DELEGATED_USER,
)


# ---------------------------------------------------------------------------
# One engine, every persona
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("persona", ALL_PERSONAS)
def test_every_persona_gets_the_same_scope2_verdict(persona: str) -> None:
    """A persona changes what you may ask for, not what counts as valid."""
    dimensions = resolve_accounting_dimensions(
        scope="Scope 2",
        scope2_method="LOCATION_BASED",
        energy_type="electricity",
        data_quality="primary_measured",
    )
    assert dimensions.scope2_method == "LOCATION_BASED"
    # The same rule refuses every persona identically when the method is missing.
    with pytest.raises(Scope2MethodRequiredError):
        resolve_accounting_dimensions(scope="Scope 2", energy_type="electricity")


def test_every_persona_gets_the_same_scope3_refusal() -> None:
    for _persona in ALL_PERSONAS:
        with pytest.raises(Scope3CategoryNotSupportedError):
            resolve_accounting_dimensions(scope="Scope 3", scope3_category=2)


# ---------------------------------------------------------------------------
# Dimension resolution
# ---------------------------------------------------------------------------
def test_scope1_result_needs_no_scope2_or_scope3_dimension() -> None:
    dimensions = resolve_accounting_dimensions(scope="Scope 1")
    assert dimensions.scope == "Scope 1"
    assert dimensions.as_columns()["scope2_method"] is None


def test_scope2_market_based_resolves_with_its_dimensions() -> None:
    dimensions = resolve_accounting_dimensions(
        scope="Scope 2",
        scope2_method="MARKET_BASED",
        energy_type="cooling",
        data_quality="primary_supplier",
        facility_id="fac-1",
    )
    columns = dimensions.as_columns()
    assert columns["scope2_method"] == "MARKET_BASED"
    assert columns["energy_type"] == "cooling"
    assert columns["facility_id"] == "fac-1"


def test_scope3_category_4_resolves_once_its_boundary_is_supplied() -> None:
    dimensions = resolve_accounting_dimensions(
        scope="Scope 3", scope3_category=4, transport_boundary="upstream"
    )
    assert dimensions.scope3_category == 4
    assert dimensions.transport_boundary == "upstream"


def test_scope3_result_without_a_category_is_refused() -> None:
    with pytest.raises(Scope3CategoryRequiredError):
        resolve_accounting_dimensions(scope="Scope 3")


def test_scope3_not_implemented_category_is_refused_by_the_engine() -> None:
    with pytest.raises(Scope3CategoryNotSupportedError):
        resolve_accounting_dimensions(scope="Scope 3", scope3_category=10)


def test_cross_scope_dimensions_are_refused() -> None:
    """A dimension attached to the wrong scope is a data defect."""
    with pytest.raises(AccountingDimensionError):
        resolve_accounting_dimensions(scope="Scope 1", scope2_method="LOCATION_BASED")
    with pytest.raises(AccountingDimensionError):
        resolve_accounting_dimensions(scope="Scope 1", scope3_category=1)


def test_energy_type_is_refused_off_scope2() -> None:
    with pytest.raises(AccountingDimensionError):
        resolve_accounting_dimensions(
            scope="Scope 3", scope3_category=6, energy_type="heat"
        )


# ---------------------------------------------------------------------------
# Business-first description (UI principle)
# ---------------------------------------------------------------------------
def test_description_names_the_category_rather_than_printing_its_number() -> None:
    dimensions = resolve_accounting_dimensions(
        scope="Scope 3", scope3_category=5, waste_origin="operations"
    )
    described = describe_dimensions(dimensions)
    assert described["scope3_category_name"] == "Waste generated in operations"
    assert "Waste generated in operations" in described["label"]
    assert described["scope3_status"] == "SUPPORTED"


def test_description_flags_estimation_requirement() -> None:
    dimensions = resolve_accounting_dimensions(
        scope="Scope 3", scope3_category=7, data_quality="secondary_estimated"
    )
    described = describe_dimensions(dimensions)
    assert described["is_estimated"] is True
    assert described["requires_estimation_record"] is True


def test_unrecorded_dimensions_produce_an_honest_label() -> None:
    described = describe_dimensions(AccountingDimensions(scope="Scope 1"))
    assert described["label"] == "Scope 1"


# ---------------------------------------------------------------------------
# Data quality
#
# P17-IMPLEMENT-10 widened the vocabulary from five values to nine, reconciling
# it with the authoritative product contract (P17-PRODUCT-01 §7 lists
# PRIMARY/SUPPLIER_SPECIFIC/ACTIVITY_BASED/AVERAGE_DATA/SPEND_BASED/ESTIMATED/
# MANUAL/UNRESOLVED, and §29/§30 require the reporting layer to distinguish
# "activity based", "estimated", "manual review" and "unresolved"). Four of those
# had no member. These assertions are as strict as before — exact tuple/set
# equality — against the corrected vocabulary, and the migration test proves the
# database CHECK was WIDENED rather than narrowed.
# ---------------------------------------------------------------------------
def test_data_quality_vocabulary_is_exactly_nine_values() -> None:
    assert DATA_QUALITY_VALUES == (
        "primary_measured",
        "primary_supplier",
        "secondary_estimated",
        "spend_based_estimated",
        "modelled",
        "activity_based",
        "estimated",
        "manual",
        "unresolved",
    )


def test_exactly_four_classifications_are_estimates() -> None:
    assert ESTIMATED_DATA_QUALITY == frozenset(
        {"secondary_estimated", "spend_based_estimated", "modelled", "estimated"}
    )


def test_activity_based_manual_and_unresolved_are_not_estimates() -> None:
    """Only a value obtained *by estimating* owes an estimation record.

    ``activity_based`` is activity data; ``manual`` says who established the
    value; ``unresolved`` says no value was established. Treating any of them as
    an estimate would impose a T-INV-12 obligation the product contract does not.
    """
    assert is_estimated("activity_based") is False
    assert is_estimated("manual") is False
    assert is_estimated("unresolved") is False


def test_every_classification_maps_to_exactly_one_reporting_bucket() -> None:
    """The §29/§30 projection is total and deterministic."""
    assert set(reporting_bucket(q) for q in DATA_QUALITY_VALUES) <= set(
        PRODUCT_DATA_QUALITY_BUCKETS
    )
    assert reporting_bucket(None) == "UNCLASSIFIED"
    # An unrecognised value is surfaced, never silently dropped from a report.
    assert reporting_bucket("not_a_real_value") == "UNCLASSIFIED"


def test_quality_mix_reproduces_the_product_reporting_buckets() -> None:
    """§30's dashboard mix, derived from authoritative counts only."""
    mix = quality_mix(
        {
            "primary_measured": 31,
            "activity_based": 42,
            "secondary_estimated": 18,
            "spend_based_estimated": 7,
            "estimated": 2,
        }
    )
    assert mix["total"] == 100
    assert mix["buckets"]["PRIMARY_DATA"]["count"] == 31
    assert mix["buckets"]["ACTIVITY_BASED"]["count"] == 42
    assert mix["buckets"]["PRIMARY_DATA"]["label"] == "Primary data"
    assert mix["percentages"]["PRIMARY_DATA"] == "31.00"


def test_quality_mix_reports_no_percentage_when_there_is_no_data() -> None:
    """No data must not be reported as 0% of the data."""
    mix = quality_mix({})
    assert mix["total"] == 0
    assert mix["percentages"]["PRIMARY_DATA"] is None
    assert mix["buckets"]["MANUAL_REVIEW"]["count"] == 0


def test_is_estimated_recognises_estimates_and_rejects_primary_data() -> None:
    assert is_estimated("secondary_estimated") is True
    assert is_estimated("spend_based_estimated") is True
    assert is_estimated("modelled") is True
    assert is_estimated("estimated") is True
    assert is_estimated("primary_measured") is False
    assert is_estimated("primary_supplier") is False
    assert is_estimated(None) is False


def test_unknown_data_quality_is_refused() -> None:
    with pytest.raises(AccountingDimensionError):
        validate_data_quality("high_confidence")


def test_unclassified_data_quality_is_visible_not_assumed_primary() -> None:
    """An unclassified value must read as a gap, never as implicit assurance."""
    assert validate_data_quality(None) is None
    assert "not classified" in describe_data_quality(None).lower()


def test_description_carries_no_numeric_uncertainty() -> None:
    """The platform does not measure an uncertainty band, so it must not claim one."""
    for value in DATA_QUALITY_VALUES:
        text = describe_data_quality(value)
        assert "%" not in text
        assert "+/-" not in text


# ---------------------------------------------------------------------------
# Estimation records (T-INV-12)
# ---------------------------------------------------------------------------
def test_estimation_vocabulary_matches_the_database_constraint() -> None:
    assert "average_data" in ESTIMATION_METHODS
    assert "spend_based" in ESTIMATION_METHODS
    assert "modelled" in ESTIMATION_METHODS


def test_a_substantiated_estimation_record_is_accepted() -> None:
    record = EstimationRecord(
        organization_id=ORG,
        estimation_method=EstimationMethod.AVERAGE_DATA,
        assumptions={"basis": "national average commute distance"},
    )
    assert record.estimation_method == "average_data"
    assert record.as_row()["assumptions"]["basis"].startswith("national average")


def test_an_estimate_with_no_method_is_refused() -> None:
    with pytest.raises(EstimationRecordRequiredError):
        EstimationRecord(organization_id=ORG, estimation_method="")


def test_an_estimate_with_no_inputs_and_no_assumptions_is_refused() -> None:
    with pytest.raises(EstimationRecordRequiredError):
        EstimationRecord(
            organization_id=ORG, estimation_method=EstimationMethod.MODELLED
        )


def test_inputs_alone_substantiate_an_estimate() -> None:
    record = EstimationRecord(
        organization_id=ORG,
        estimation_method=EstimationMethod.EXTRAPOLATED,
        inputs={"survey_responses": 42, "headcount": 200},
    )
    assert record.inputs["headcount"] == 200


def test_requires_estimation_record_covers_quality_and_explicit_flag() -> None:
    assert requires_estimation_record(data_quality="modelled") is True
    assert requires_estimation_record(data_quality=None, declared_estimated=True) is True
    assert requires_estimation_record(data_quality="primary_measured") is False


def test_estimation_row_carries_acting_for_provenance() -> None:
    record = EstimationRecord(
        organization_id=ORG,
        estimation_method=EstimationMethod.INDUSTRY_AVERAGE,
        assumptions={"source": "industry median"},
        actor_user_id="u-1",
        actor_organization_id="firm-1",
        acting_for_organization_id=ORG,
    )
    row = record.as_row()
    assert row["acting_for_organization_id"] == ORG
    assert row["actor_organization_id"] == "firm-1"


# ---------------------------------------------------------------------------
# Contractual instruments and DC-09
# ---------------------------------------------------------------------------
def _instrument(quantity: str = "1000") -> ContractualInstrument:
    return ContractualInstrument(
        organization_id=ORG,
        instrument_type="guarantee_of_origin",
        identifier="GO-1",
        geography="GB",
        quantity=Decimal(quantity),
        unit="kWh",
        vintage_year=2025,
    )


def _allocation(quantity: str) -> InstrumentAllocation:
    return InstrumentAllocation(
        organization_id=ORG,
        instrument_id="i-1",
        allocated_quantity=Decimal(quantity),
        allocated_unit="kWh",
        allocation_period_start=date(2025, 1, 1),
        allocation_period_end=date(2025, 12, 31),
    )


def test_an_active_instrument_is_claimable() -> None:
    assert _instrument().is_claimable is True


@pytest.mark.parametrize("status", ["retired", "cancelled"])
def test_a_retired_or_cancelled_instrument_is_not_claimable(status: str) -> None:
    instrument = ContractualInstrument(
        organization_id=ORG,
        instrument_type="ppa",
        identifier="PPA-1",
        geography="GB",
        quantity=Decimal("10"),
        unit="MWh",
        retirement_status=status,
    )
    assert instrument.is_claimable is False


def test_a_zero_instrument_quantity_is_refused() -> None:
    with pytest.raises(AccountingDimensionError):
        ContractualInstrument(
            organization_id=ORG,
            instrument_type="other",
            identifier="X",
            geography="GB",
            quantity=Decimal("0"),
            unit="kWh",
        )


def test_an_unknown_instrument_type_is_refused() -> None:
    with pytest.raises(AccountingDimensionError):
        ContractualInstrument(
            organization_id=ORG,
            instrument_type="carbon_credit",
            identifier="X",
            geography="GB",
            quantity=Decimal("1"),
            unit="kWh",
        )


def test_remaining_quantity_is_the_unallocated_balance() -> None:
    assert remaining_quantity(_instrument(), [_allocation("600")]) == Decimal("400")


def test_dc09_refuses_an_allocation_that_exceeds_the_instrument() -> None:
    with pytest.raises(InstrumentOverAllocatedError) as exc:
        assert_allocation_within_quantity(
            instrument=_instrument(),
            existing=[_allocation("600")],
            new_quantity=Decimal("600"),
            unit="kWh",
        )
    assert exc.value.details["already_allocated"] == "600"


def test_dc09_allows_an_allocation_that_exactly_exhausts_the_instrument() -> None:
    remaining = assert_allocation_within_quantity(
        instrument=_instrument(),
        existing=[_allocation("600")],
        new_quantity=Decimal("400"),
        unit="kWh",
    )
    assert remaining == Decimal("0")


def test_dc09_refuses_a_unit_mismatch_rather_than_summing_them() -> None:
    with pytest.raises(AccountingDimensionError):
        assert_allocation_within_quantity(
            instrument=_instrument(),
            existing=[],
            new_quantity=Decimal("10"),
            unit="MWh",
        )


def test_an_allocation_with_a_reversed_period_is_refused() -> None:
    with pytest.raises(AccountingDimensionError):
        InstrumentAllocation(
            organization_id=ORG,
            instrument_id="i-1",
            allocated_quantity=Decimal("1"),
            allocated_unit="kWh",
            allocation_period_start=date(2025, 12, 31),
            allocation_period_end=date(2025, 1, 1),
        )


# ---------------------------------------------------------------------------
# CamsContext — provenance without authorization substitution
# ---------------------------------------------------------------------------
def test_a_non_delegated_context_reports_no_acting_for() -> None:
    context = CamsContext(actor_user_id="u-1", data_owning_organization_id=ORG)
    assert context.acting_for_organization_id is None
    assert context.is_delegated is False
    assert context.provenance_columns() == {
        "actor_organization_id": None,
        "acting_for_organization_id": None,
    }


def test_a_delegated_context_carries_the_acting_for_organization() -> None:
    from domain.acting_for import (
        ActingForKind,
        Entitlement,
        EntitlementBasis,
        resolve_acting_for,
    )

    acting_for = resolve_acting_for(
        actor_user_id="u-1",
        target_organization_id=ORG,
        entitlements=[
            Entitlement(
                organization_id=ORG,
                basis=EntitlementBasis.ACTIVE_CONSULTANT_DELEGATION,
                actor_organization_id="firm-1",
            )
        ],
        kind=ActingForKind.CONSULTANT_FOR_CLIENT,
    )
    context = CamsContext(
        actor_user_id="u-1",
        data_owning_organization_id=ORG,
        acting_for=acting_for,
        persona=CamsPersona.CONSULTANT,
    )
    assert context.acting_for_organization_id == ORG
    assert context.is_delegated is True
    assert context.provenance_columns()["actor_organization_id"] == "firm-1"
    # Ownership is unchanged: the data-owning organization is the authorization key.
    assert context.data_owning_organization_id == ORG
