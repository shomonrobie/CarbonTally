"""P17-IMPLEMENT-05 — Scope 2 calculation vertical slice.

Exercises the REAL path: ``Scope2CalculationService.calculate()`` →
``CalculationRequest.from_match_result`` → ``CalculationEngine.calculate()`` →
``sink.save_snapshot`` / ``create`` / ``save``.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.exceptions import (
    AccountingDimensionError,
    InstrumentEligibilityError,
    InstrumentOverAllocatedError,
    Scope2MethodRequiredError,
)
from domain.calculation import CalculationSnapshot, EmissionLog
from domain.contractual_instruments import (
    INSTRUMENT_TYPES,
    ContractualInstrument,
    InstrumentAllocation,
    RetirementStatus,
)
from domain.factor import EmissionFactor
from domain.matching import MatchResult
from engines.calculation import CalculationEngine
from services.scope2_calculation import Scope2CalculationService, Scope2Input

_ORG = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_FIRM = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_OTHER = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
_ELECTRICITY = "Electricity > Grid > UK grid electricity (kg CO2e) [kWh]"


def make_factor(**kwargs: Any) -> EmissionFactor:
    """A Scope 2 electricity factor by default."""
    return EmissionFactor(
        id=str(kwargs.get("id") or f"f-{uuid.uuid4().hex[:12]}"),
        reporting_year=int(kwargs.get("year", 2025)),
        activity_type=str(kwargs.get("activity_type") or _ELECTRICITY),
        co2e_multiplier=Decimal(str(kwargs.get("multiplier") or "0.20700")),
        unit=str(kwargs.get("unit") or "kWh"),
        scope=str(kwargs.get("scope") or "Scope 2"),
        factor_source=str(kwargs.get("factor_source") or "DEFRA-DESNZ"),
        factor_set=str(kwargs.get("factor_set") or "DEFRA-2025"),
        country=str(kwargs.get("country") or "GB"),
        provider_key="defra",
        import_batch_id=None,
        natural_key=("2025", _ELECTRICITY, "GB", "kWh", "Scope 2"),
    )


def make_match(factor: Optional[EmissionFactor] = None, **kwargs: Any) -> MatchResult:
    return MatchResult(
        status=str(kwargs.get("status") or "matched"),
        factor=factor if factor is not None else make_factor(),
        confidence=1.0,
        methodology="direct_multiply",
        request_id=str(kwargs.get("request_id") or "req-scope2-1"),
        factor_kind=str(kwargs.get("factor_kind") or "emission_factor"),
    )


def make_instrument(**kwargs: Any) -> ContractualInstrument:
    return ContractualInstrument(
        organization_id=str(kwargs.get("organization_id") or _ORG),
        instrument_type=str(kwargs.get("instrument_type") or INSTRUMENT_TYPES[0]),
        identifier=str(kwargs.get("identifier") or "GO-2025-0001"),
        geography=str(kwargs.get("geography") or "GB"),
        quantity=Decimal(str(kwargs.get("quantity") or "1000")),
        unit=str(kwargs.get("unit") or "kWh"),
        vintage_year=kwargs.get("vintage_year", 2025),
        retirement_status=str(
            kwargs.get("retirement_status") or RetirementStatus.ACTIVE.value
        ),
    )


class _RecordingSink:
    """In-memory ``CalculationSink`` retaining the objects it was handed."""

    def __init__(self) -> None:
        self.snapshots: list[CalculationSnapshot] = []
        self.created: list[EmissionLog] = []
        self.saved: list[EmissionLog] = []

    async def save_snapshot(self, snapshot: CalculationSnapshot, **kwargs: Any):
        self.snapshots.append(snapshot)
        return snapshot

    async def create(
        self,
        org_id: str,
        factor_id: Optional[str],
        quantity: Decimal,
        unit: str,
        scope: Optional[str],
        date: Any,
        asset_id: Optional[str],
        facility_id: Optional[str],
        snapshot_id: str,
        supplier_id: Optional[str] = None,
        accounting_dimensions: Optional[AccountingDimensions] = None,
    ) -> EmissionLog:
        log = EmissionLog(
            id=f"log-{len(self.created)}",
            organization_id=org_id,
            factor_id=factor_id,
            quantity=quantity,
            date=date,
            unit=unit,
            scope=scope,
            asset_id=asset_id,
            facility_id=facility_id,
            snapshot_id=snapshot_id,
        )
        self.created.append(log)
        return log

    async def save(self, entity: EmissionLog) -> EmissionLog:
        self.saved.append(entity)
        return entity


def make_input(**kwargs: Any) -> Scope2Input:
    def take(name: str, default: Any) -> Any:
        return kwargs.pop(name, default)

    method = take("method", "LOCATION_BASED")
    return Scope2Input(
        organization_id=str(take("organization_id", _ORG)),
        quantity=Decimal(str(take("quantity", "100"))),
        quantity_unit=str(take("quantity_unit", "kWh")),
        date=take("date", date(2025, 6, 1)),
        reporting_year=int(take("reporting_year", 2025)),
        activity=str(take("activity", "Grid electricity")),
        activity_type=str(take("activity_type", _ELECTRICITY)),
        method=method,
        energy_type=str(take("energy_type", "electricity")),
        match=take("match", make_match()),
        geography=take("geography", None),
        data_quality=take("data_quality", "primary_supplier"),
        facility_id=take("facility_id", None),
        performed_by=take("performed_by", "user-1"),
        performed_by_organization_id=take("performed_by_organization_id", _FIRM),
        acting_for_organization_id=take("acting_for_organization_id", _ORG),
        instrument=take("instrument", None),
        allocated_quantity=take("allocated_quantity", None),
        existing_allocations=take("existing_allocations", ()),
    )


def service(sink: _RecordingSink) -> Scope2CalculationService:
    return Scope2CalculationService(CalculationEngine(sink))  # type: ignore[arg-type]


# ===========================================================================
# Validation
# ===========================================================================
async def test_missing_method_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(Scope2MethodRequiredError):
        await service(sink).calculate(make_input(method=None))
    assert sink.snapshots == [] and sink.saved == []


async def test_invalid_method_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(make_input(method="GUESSED"))
    assert excinfo.value.code == "ACCOUNTING_DIMENSION_INVALID"
    assert sink.snapshots == []


async def test_invalid_energy_type_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(make_input(energy_type="biomass"))
    assert excinfo.value.code == "ACCOUNTING_DIMENSION_INVALID"
    assert sink.snapshots == []


async def test_fuel_is_rejected_with_a_deterministic_reason() -> None:
    """``fuel`` is a Scope 1/3 activity, never a Scope 2 energy type."""
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(make_input(energy_type="fuel"))
    assert "fuel is not a Scope 2 energy type" in excinfo.value.message
    assert sink.snapshots == []


async def test_scope1_factor_is_rejected_for_a_scope2_calculation() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(
            make_input(match=make_match(factor=make_factor(scope="Scope 1")))
        )
    assert "must not use a factor from another scope" in excinfo.value.message
    assert sink.snapshots == []


async def test_factor_from_another_year_is_never_silently_substituted() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(
            make_input(match=make_match(factor=make_factor(year=2024)))
        )
    assert "never silently substituted" in excinfo.value.message
    assert sink.snapshots == []


async def test_factor_from_another_geography_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(
            make_input(match=make_match(factor=make_factor(country="FR")), geography="GB")
        )
    assert "consumption geography" in excinfo.value.message
    assert sink.snapshots == []


async def test_unmatched_factor_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError):
        await service(sink).calculate(make_input(match=make_match(status="no_match")))
    assert sink.snapshots == []


# ===========================================================================
# Location-based
# ===========================================================================
@pytest.mark.parametrize("energy_type", ["electricity", "heat", "steam", "cooling"])
async def test_location_based_energy_types_calculate_and_persist(
    energy_type: str,
) -> None:
    sink = _RecordingSink()
    factor = make_factor(multiplier="0.20700")
    result = await service(sink).calculate(
        make_input(
            energy_type=energy_type, quantity="100", match=make_match(factor=factor)
        )
    )
    # Correct numerical result: 100 kWh x 0.20700 kg CO2e/kWh.
    assert result.co2e_kg == Decimal("20.700000")
    # Persisted through the canonical pipeline, on BOTH records.
    assert len(sink.snapshots) == 1 and len(sink.saved) == 1
    snapshot, log = sink.snapshots[0], sink.saved[0]
    assert snapshot.accounting_dimensions.scope2_method == "LOCATION_BASED"
    assert snapshot.accounting_dimensions.energy_type == energy_type
    assert log.accounting_dimensions.as_columns() == (
        snapshot.accounting_dimensions.as_columns()
    )
    # Provenance: the exact factor used is retained.
    assert snapshot.factor_id == factor.id
    assert snapshot.scope == "Scope 2"
    assert snapshot.content_hash
    # Log is linked to the authoritative snapshot and agrees on owner.
    assert log.snapshot_id == snapshot.id
    assert log.organization_id == snapshot.organization_id == _ORG


async def test_location_based_records_acting_for_separately_from_the_owner() -> None:
    """A consultant firm acting for a client: owner and acting-for differ."""
    sink = _RecordingSink()
    await service(sink).calculate(
        make_input(
            organization_id=_ORG,
            performed_by_organization_id=_FIRM,
            acting_for_organization_id=_ORG,
        )
    )
    dims = sink.snapshots[0].accounting_dimensions
    assert sink.snapshots[0].organization_id == _ORG  # owner
    assert dims.performed_by_organization_id == _FIRM
    assert dims.acting_for_organization_id == _ORG
    # The owner is never derived from the attribution pair.
    assert sink.saved[0].organization_id == _ORG


async def test_location_based_with_an_instrument_is_refused() -> None:
    """An instrument cannot support a location-based claim."""
    sink = _RecordingSink()
    with pytest.raises(InstrumentEligibilityError):
        await service(sink).calculate(
            make_input(method="LOCATION_BASED", instrument=make_instrument())
        )
    assert sink.snapshots == []


async def test_location_based_requires_no_instrument() -> None:
    sink = _RecordingSink()
    await service(sink).calculate(make_input(method="LOCATION_BASED"))
    assert sink.snapshots[0].accounting_dimensions.scope2_method == "LOCATION_BASED"


# ===========================================================================
# Market-based
# ===========================================================================
def _market_input(**kwargs: Any) -> Scope2Input:
    kwargs.setdefault("method", "MARKET_BASED")
    kwargs.setdefault("instrument", make_instrument())
    kwargs.setdefault(
        "allocated_quantity", Decimal(str(kwargs.get("quantity", "100")))
    )
    return make_input(**kwargs)


async def test_market_based_with_a_valid_instrument_and_allocation_succeeds() -> None:
    sink = _RecordingSink()
    result = await service(sink).calculate(_market_input(quantity="100"))
    assert result.co2e_kg == Decimal("20.700000")
    dims = sink.snapshots[0].accounting_dimensions
    assert dims.scope2_method == "MARKET_BASED"
    assert dims.energy_type == "electricity"
    assert sink.saved[0].accounting_dimensions.scope2_method == "MARKET_BASED"


async def test_market_based_without_an_instrument_is_refused_not_downgraded() -> None:
    """The grid-average figure is a DIFFERENT claim; it is never substituted."""
    sink = _RecordingSink()
    with pytest.raises(InstrumentEligibilityError) as excinfo:
        await service(sink).calculate(
            make_input(method="MARKET_BASED", allocated_quantity=Decimal("100"))
        )
    assert "never substituted automatically" in excinfo.value.message
    assert sink.snapshots == []


async def test_inactive_instrument_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(InstrumentEligibilityError):
        await service(sink).calculate(
            _market_input(
                instrument=make_instrument(
                    retirement_status=RetirementStatus.RETIRED.value
                )
            )
        )
    assert sink.snapshots == []


async def test_instrument_with_wrong_geography_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(InstrumentEligibilityError):
        await service(sink).calculate(
            _market_input(instrument=make_instrument(geography="FR"), geography="GB")
        )
    assert sink.snapshots == []


async def test_instrument_with_wrong_vintage_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(InstrumentEligibilityError):
        await service(sink).calculate(
            _market_input(instrument=make_instrument(vintage_year=2023))
        )
    assert sink.snapshots == []


async def test_instrument_from_another_tenant_is_rejected() -> None:
    """Cross-tenant instrument: it belongs to a different owner."""
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(
            _market_input(instrument=make_instrument(organization_id=_OTHER))
        )
    assert "different organization" in excinfo.value.message
    assert sink.snapshots == []


async def test_insufficient_allocation_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(InstrumentEligibilityError):
        await service(sink).calculate(
            _market_input(quantity="100", allocated_quantity=Decimal("10"))
        )
    assert sink.snapshots == []


async def test_duplicate_allocation_beyond_the_instrument_quantity_is_rejected() -> None:
    """DC-09 — the same instrument quantity cannot be claimed twice."""
    sink = _RecordingSink()
    existing = [
        InstrumentAllocation(
            organization_id=_ORG,
            instrument_id="GO-2025-0001",
            allocated_quantity=Decimal("950"),
            allocated_unit="kWh",
            allocation_period_start=date(2025, 1, 1),
            allocation_period_end=date(2025, 12, 31),
        )
    ]
    with pytest.raises(InstrumentOverAllocatedError):
        await service(sink).calculate(
            _market_input(
                quantity="100",
                instrument=make_instrument(quantity="1000"),
                existing_allocations=existing,
            )
        )
    assert sink.snapshots == []


async def test_allocation_in_an_incompatible_unit_is_rejected() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError):
        await service(sink).calculate(
            _market_input(
                quantity="100",
                quantity_unit="MWh",
                instrument=make_instrument(unit="kWh"),
            )
        )
    assert sink.snapshots == []



# ===========================================================================
# P16 regression / double-counting controls
# ===========================================================================
async def test_location_based_and_market_based_results_are_distinguishable() -> None:
    """The method is persisted with the calculation, not inferred later."""
    location = _RecordingSink()
    market = _RecordingSink()
    await service(location).calculate(make_input())
    await service(market).calculate(_market_input())
    assert (
        location.saved[0].accounting_dimensions.scope2_method == "LOCATION_BASED"
    )
    assert market.saved[0].accounting_dimensions.scope2_method == "MARKET_BASED"


async def test_repeated_identical_requests_share_the_request_identity() -> None:
    """P16 idempotency: identical inputs derive the same request identity."""
    sink = _RecordingSink()
    svc = service(sink)
    request = make_input(match=make_match(request_id="req-identical"))
    first = await svc.calculate(request)
    second = await svc.calculate(request)
    assert first.snapshot.match_request_id == second.snapshot.match_request_id
    assert first.snapshot.content_hash == second.snapshot.content_hash


async def test_scope1_calculation_is_unaffected_by_the_scope2_slice() -> None:
    """P16 Scope 1 regression: still calculates, with no Scope 2 dimensions."""
    from engines.calculation import CalculationRequest

    sink = _RecordingSink()
    engine = CalculationEngine(sink)  # type: ignore[arg-type]
    request = CalculationRequest.from_match_result(
        make_match(factor=make_factor(scope="Scope 1", activity_type="Fuels > Gas")),
        organization_id=_ORG,
        quantity=Decimal("100"),
        quantity_unit="kWh",
        date=date(2025, 6, 1),
        reporting_year=2025,
        activity="Natural gas",
        activity_type="Fuels > Gas",
        scope="Scope 1",
    )
    result = await engine.calculate(request)
    assert result.snapshot.accounting_dimensions is None
    assert result.snapshot.scope == "Scope 1"
    assert result.co2e_kg == Decimal("20.700000")


async def test_scope2_dimensions_do_not_change_the_content_hash() -> None:
    """P16 hash preservation, re-asserted through the new bridge parameter."""
    from domain.accounting_dimensions import AccountingDimensions
    from engines.calculation import CalculationRequest

    factor = make_factor(scope="Scope 1", activity_type="Fuels > Gas")
    base = dict(
        organization_id=_ORG,
        quantity=Decimal("100"),
        quantity_unit="kWh",
        date=date(2025, 6, 1),
        reporting_year=2025,
        activity="Natural gas",
        activity_type="Fuels > Gas",
        scope="Scope 1",
    )
    plain_sink = _RecordingSink()
    dims_sink = _RecordingSink()
    plain = CalculationRequest.from_match_result(make_match(factor=factor), **base)
    with_dims = CalculationRequest.from_match_result(
        make_match(factor=factor),
        accounting_dimensions=AccountingDimensions(data_quality="modelled"),
        **base,
    )
    plain_result = await CalculationEngine(plain_sink).calculate(plain)  # type: ignore[arg-type]
    dims_result = await CalculationEngine(dims_sink).calculate(with_dims)  # type: ignore[arg-type]
    assert plain_result.snapshot.content_hash == dims_result.snapshot.content_hash
