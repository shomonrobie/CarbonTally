"""P17-IMPLEMENT-10 — Scope 3 category methodology persistence (real path).

Why this file exists
--------------------
P17-IMPLEMENT-10 forensics proved that a **contract-valid** category methodology
could not be persisted at all. ``Scope3CalculationService`` validated the
requested method against the category contract and then handed that same string
to ``CalculationRequest.methodology``, which the engine only accepts when it is a
``CalculationMethodology`` value (``direct_multiply`` / ``distance_based`` /
``spend_based`` / ``area_based`` / ``mass_balance``). Eight of the ten methods the
fifteen contracts actually permit — ``supplier_specific``, ``average_data``,
``extrapolated``, ``survey_based``, ``asset_specific``, ``industry_average``,
``modelled``, ``proxy_data`` — were therefore refused as an "unknown calculation
methodology", so a category could not record which method it had used.

That directly contradicts P17-PRODUCT-01 §29 (the reporting layer must expose the
methodology) and §34 ("category-specific methodology" is a must-have).

What the fix is, and what these tests pin
-----------------------------------------
The product method and the engine arithmetic label are **two different facts** and
are now persisted separately:

* the product method goes to the ``scope3_method`` dimension, validated against
  the *category's own* contract vocabulary; and
* ``calculation_snapshots.methodology`` keeps the engine arithmetic label,
  derived deterministically by ``engine_methodology_for``.

The Scope 2 path already worked exactly this way (``scope2_method`` carries
LOCATION_BASED/MARKET_BASED while ``methodology`` stays ``direct_multiply``), so
this removes an inconsistency rather than adding a concept.

Every test drives the REAL service, the REAL engine, the REAL contracts and the
REAL domain validators; only the persistence sink is in memory.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.exceptions import CarbonTallyError, Scope3MethodNotSupportedError
from domain.accounting_dimensions import AccountingDimensions
from domain.calculation import CalculationSnapshot, EmissionLog
from domain.factor import EmissionFactor
from domain.estimation import EstimationRecord
from domain.matching import MatchResult
from domain.scope3_contracts import CONTRACTS, SCOPE3_METHODS, contract_for
from engines.calculation import CalculationEngine, CalculationMethodology
from services.scope3_calculation import Scope3CalculationService, Scope3Input

_ORG = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_FIRM = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_ACTIVITY = "Scope 3 > Test activity (kg CO2e) [kg]"


def make_factor(**over: Any) -> EmissionFactor:
    return EmissionFactor(
        id=over.get("id", f"f-{uuid.uuid4().hex[:8]}"),
        reporting_year=int(over.get("year", 2025)),
        activity_type=_ACTIVITY,
        co2e_multiplier=Decimal(str(over.get("multiplier", "2.50000"))),
        unit=str(over.get("unit", "kg")),
        scope=str(over.get("scope", "Scope 3")),
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
        import_batch_id=None,
        natural_key=("2025", _ACTIVITY, "GB", "kg", "Scope 3"),
    )


def make_match(factor: Optional[EmissionFactor] = None) -> MatchResult:
    return MatchResult(
        status="matched",
        factor=factor if factor is not None else make_factor(),
        confidence=1.0,
        methodology="direct_multiply",
        request_id="req-p17-10",
        factor_kind="emission_factor",
    )


class _RecordingSink:
    """In-memory ``CalculationSink`` retaining what the engine wrote."""

    def __init__(self) -> None:
        self.snapshots: list[CalculationSnapshot] = []
        self.logs: list[EmissionLog] = []
        #: What the engine handed to ``create`` — the only place the P12 supplier
        #: attribution reaches persistence (the domain models carry dimensions,
        #: not the supplier).
        self.create_calls: list[dict[str, Any]] = []

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
        self.create_calls.append(
            {
                "organization_id": org_id,
                "supplier_id": supplier_id,
                "accounting_dimensions": accounting_dimensions,
            }
        )
        return EmissionLog(
            id=f"log-{len(self.logs)}",
            organization_id=org_id,
            factor_id=factor_id,
            quantity=quantity,
            date=date,
            unit=unit,
            scope=scope,
            asset_id=asset_id,
            facility_id=facility_id,
            snapshot_id=snapshot_id,
            accounting_dimensions=accounting_dimensions,
        )

    async def save(self, entity: EmissionLog) -> EmissionLog:
        self.logs.append(entity)
        return entity


def _service(sink: _RecordingSink) -> Scope3CalculationService:
    return Scope3CalculationService(CalculationEngine(sink))  # type: ignore[arg-type]


def _derive_boundary_inputs(category: int) -> dict[str, Any]:
    """Supply the boundary/discriminator inputs the category's contract requires."""
    inputs: dict[str, Any] = {}
    for name in contract_for(category).required_inputs:
        if name in ("activity", "quantity", "unit"):
            continue
        inputs[name] = "declared-for-test"
    boundary: dict[str, Any] = {}
    for name in contract_for(category).required_boundary_inputs:
        if name == "transport_boundary":
            boundary[name] = "upstream" if category == 4 else "downstream"
        elif name == "waste_origin":
            boundary[name] = "operations" if category == 5 else "sold_product_eol"
        elif name == "consolidation_approach":
            boundary[name] = "OPERATIONAL_CONTROL"
        elif name == "source_snapshot_id":
            boundary[name] = uuid.uuid4().hex
    return {"inputs": inputs, **boundary}


# ---------------------------------------------------------------------------
# The defect: every contract method must be persistable
# ---------------------------------------------------------------------------
def test_every_contract_method_in_the_union_is_still_advertised() -> None:
    """The frozen union is derived from the contracts, not restated."""
    derived = {m for c in CONTRACTS.values() for m in c.methodologies}
    assert set(SCOPE3_METHODS) == derived
    # The eight that the engine previously refused are all still in the contract.
    assert {
        "supplier_specific",
        "average_data",
        "extrapolated",
        "survey_based",
        "asset_specific",
        "industry_average",
        "modelled",
        "proxy_data",
    } <= set(SCOPE3_METHODS)


@pytest.mark.parametrize("category", sorted(CONTRACTS))
@pytest.mark.asyncio
async def test_each_category_persists_a_method_its_contract_permits(
    category: int,
) -> None:
    """REGRESSION: a contract-valid method reaches ``scope3_method``.

    Before the fix this raised ``ValidationFailedError: unknown calculation
    methodology ...`` for every method except ``distance_based``/``spend_based``,
    so most of the fifteen categories could not record a method at all.
    """
    contract = contract_for(category)
    method = contract.methodologies[0]
    # An estimation-pathway category (7, 10, 11, 12, 14, 15) may only be
    # classified as an estimate and must carry a persisted estimation record
    # (T-INV-12) — that rule is untouched by this task and is respected here.
    if contract.requires_estimation_record:
        quality = "secondary_estimated"
        estimation = EstimationRecord(
            organization_id=_ORG,
            estimation_method="average_data",
            inputs={"basis": "industry average"},
            assumptions={},
            scope3_category=category,
        )
    else:
        quality = "primary_measured"
        estimation = None
    sink = _RecordingSink()
    outcome = await _service(sink).calculate(
        Scope3Input(
            organization_id=_ORG,
            category=category,
            quantity=Decimal("10"),
            quantity_unit="kg",
            date=date(2025, 6, 1),
            reporting_year=2025,
            activity="Test activity",
            activity_type="Test activity",
            match=make_match(),
            methodology=method,
            data_quality=quality,
            performed_by_organization_id=_FIRM,
            estimation=estimation,
            **_derive_boundary_inputs(category),
        )
    )
    assert outcome.calculated, outcome.clarification
    dimensions = sink.snapshots[-1].accounting_dimensions
    assert dimensions is not None
    assert dimensions.scope3_method == method
    assert dimensions.scope3_category == category


@pytest.mark.asyncio
async def test_product_method_and_engine_methodology_are_persisted_separately() -> None:
    """The accounting method and the arithmetic label are distinct facts."""
    sink = _RecordingSink()
    outcome = await _service(sink).calculate(
        Scope3Input(
            organization_id=_ORG,
            category=1,
            quantity=Decimal("10"),
            quantity_unit="kg",
            date=date(2025, 6, 1),
            reporting_year=2025,
            activity="Purchased goods",
            activity_type="Paper",
            match=make_match(),
            methodology="supplier_specific",
            data_quality="primary_supplier",
        )
    )
    assert outcome.calculated
    snapshot = sink.snapshots[-1]
    # The accounting claim is recorded in full ...
    assert snapshot.accounting_dimensions.scope3_method == "supplier_specific"
    # ... and the engine still records how the number was multiplied.
    assert snapshot.methodology == CalculationMethodology.DIRECT_MULTIPLY.value


@pytest.mark.asyncio
async def test_arithmetic_changing_methods_keep_their_engine_label() -> None:
    """``spend_based``/``distance_based`` genuinely change the arithmetic."""
    for method, expected in (
        ("spend_based", CalculationMethodology.SPEND_BASED.value),
        ("distance_based", CalculationMethodology.DISTANCE_BASED.value),
    ):
        sink = _RecordingSink()
        outcome = await _service(sink).calculate(
            Scope3Input(
                organization_id=_ORG,
                category=6,
                quantity=Decimal("100"),
                quantity_unit="km",
                date=date(2025, 6, 1),
                reporting_year=2025,
                activity="Rail",
                activity_type="Rail",
                match=make_match(factor=make_factor(unit="km")),
                methodology=method,
                data_quality="primary_measured",
                inputs={"trip_purpose": "client meeting"},
            )
        )
        assert outcome.calculated, outcome.clarification
        assert sink.snapshots[-1].methodology == expected
        assert sink.snapshots[-1].accounting_dimensions.scope3_method == method


@pytest.mark.asyncio
async def test_absent_method_stays_absent_and_is_never_defaulted() -> None:
    """No stated method must not become the contract's first entry."""
    sink = _RecordingSink()
    outcome = await _service(sink).calculate(
        Scope3Input(
            organization_id=_ORG,
            category=1,
            quantity=Decimal("10"),
            quantity_unit="kg",
            date=date(2025, 6, 1),
            reporting_year=2025,
            activity="Purchased goods",
            activity_type="Paper",
            match=make_match(),
            data_quality="primary_measured",
        )
    )
    assert outcome.calculated
    assert sink.snapshots[-1].accounting_dimensions.scope3_method is None
    assert sink.snapshots[-1].methodology == CalculationMethodology.DIRECT_MULTIPLY.value


@pytest.mark.asyncio
async def test_a_method_the_category_does_not_permit_is_refused() -> None:
    """Category 6 does not permit ``supplier_specific``; nothing is persisted.

    The service's own contract guard fires first (it knows the category), so the
    raised error is its precise ``AccountingDimensionError``; the domain-level
    union check in ``AccountingDimensions`` is the second, independent guard.
    Either way the refusal is a 422-class ``CarbonTallyError`` and no row is
    written — which is the property that matters.
    """
    sink = _RecordingSink()
    with pytest.raises(CarbonTallyError) as excinfo:
        await _service(sink).calculate(
            Scope3Input(
                organization_id=_ORG,
                category=6,
                quantity=Decimal("100"),
                quantity_unit="km",
                date=date(2025, 6, 1),
                reporting_year=2025,
                activity="Rail",
                activity_type="Rail",
                match=make_match(factor=make_factor(unit="km")),
                methodology="supplier_specific",
                data_quality="primary_measured",
                inputs={"trip_purpose": "client meeting"},
            )
        )
    assert excinfo.value.http_status == 422
    assert sink.snapshots == [] and sink.logs == []


# ---------------------------------------------------------------------------
# P17-PRODUCT-01 §5 — transaction provider vs underlying supplier
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_provider_and_supplier_are_persisted_as_independent_facts() -> None:
    """Booking.com is the channel; Hotel ABC is the emissions-generating supplier."""
    sink = _RecordingSink()
    supplier = "11111111-1111-4111-8111-111111111111"
    outcome = await _service(sink).calculate(
        Scope3Input(
            organization_id=_ORG,
            category=6,
            quantity=Decimal("1"),
            quantity_unit="night",
            date=date(2025, 6, 1),
            reporting_year=2025,
            activity="Hotel",
            activity_type="Hotel accommodation",
            match=make_match(factor=make_factor(unit="night")),
            data_quality="primary_measured",
            supplier_id=supplier,
            transaction_provider="Booking.com",
            inputs={"trip_purpose": "client meeting"},
        )
    )
    assert outcome.calculated, outcome.clarification
    dimensions = sink.snapshots[-1].accounting_dimensions
    assert dimensions.transaction_provider == "Booking.com"
    assert sink.create_calls[-1]["supplier_id"] == supplier
    # The provider is NEVER written into the supplier column.
    assert dimensions.transaction_provider != sink.create_calls[-1]["supplier_id"]


@pytest.mark.asyncio
async def test_unresolved_supplier_leaves_supplier_null_with_a_known_provider() -> None:
    """An unknown underlying supplier stays NULL — it is never guessed."""
    sink = _RecordingSink()
    outcome = await _service(sink).calculate(
        Scope3Input(
            organization_id=_ORG,
            category=6,
            quantity=Decimal("1"),
            quantity_unit="night",
            date=date(2025, 6, 1),
            reporting_year=2025,
            activity="Hotel",
            activity_type="Hotel accommodation",
            match=make_match(factor=make_factor(unit="night")),
            data_quality="primary_measured",
            transaction_provider="Agoda",
            inputs={"trip_purpose": "client meeting"},
        )
    )
    assert outcome.calculated
    assert sink.create_calls[-1]["supplier_id"] is None
    assert sink.snapshots[-1].accounting_dimensions.transaction_provider == "Agoda"


@pytest.mark.asyncio
async def test_known_supplier_is_never_copied_into_the_provider_field() -> None:
    """The provider is not derived from the supplier (no silent equating)."""
    sink = _RecordingSink()
    outcome = await _service(sink).calculate(
        Scope3Input(
            organization_id=_ORG,
            category=1,
            quantity=Decimal("10"),
            quantity_unit="kg",
            date=date(2025, 6, 1),
            reporting_year=2025,
            activity="Purchased goods",
            activity_type="Paper",
            match=make_match(),
            data_quality="primary_measured",
            supplier_id="22222222-2222-4222-8222-222222222222",
        )
    )
    assert outcome.calculated
    assert sink.snapshots[-1].accounting_dimensions.transaction_provider is None

