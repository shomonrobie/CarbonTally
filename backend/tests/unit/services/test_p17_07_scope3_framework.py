"""P17-IMPLEMENT-07 — the unified Scope 3 framework, all fifteen categories.

Exercises the REAL path: ``Scope3CalculationService.calculate()`` →
``CalculationRequest.from_match_result`` → ``CalculationEngine.calculate()`` →
``sink.save_snapshot`` / ``create`` / ``save``.

Every one of the fifteen categories is driven through the same pathway here; the
sink is an in-memory stand-in for the repository, but the service, the engine,
the contracts, the taxonomy and the boundary guards are the real ones.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any, Optional

import pytest

from core.exceptions import (
    AccountingDimensionError,
    BoundaryAmbiguityError,
    EstimationRecordRequiredError,
)
from domain.calculation import CalculationSnapshot, EmissionLog
from domain.data_quality import ESTIMATED_DATA_QUALITY
from domain.estimation import EstimationRecord
from domain.factor import EmissionFactor
from domain.matching import MatchResult
from domain.scope3_contracts import CONTRACTS, CategoryPathway, contract_for
from engines.calculation import CalculationEngine
from services.scope3_calculation import (
    CALCULATED,
    CLARIFICATION_REQUIRED,
    Scope3CalculationService,
    Scope3Input,
)

_ORG = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_FIRM = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_ACTIVITY = "Scope 3 > Purchased goods > Paper (kg CO2e) [kg]"


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
        country=str(over.get("country", "GB")),
        provider_key="defra",
        import_batch_id=None,
        natural_key=("2025", _ACTIVITY, "GB", "kg", "Scope 3"),
    )


def make_match(factor: Optional[EmissionFactor] = None, **kw: Any) -> MatchResult:
    return MatchResult(
        status=str(kw.get("status") or "matched"),
        factor=factor if factor is not None else make_factor(),
        confidence=1.0,
        methodology="direct_multiply",
        request_id=str(kw.get("request_id") or "req-s3-1"),
        factor_kind="emission_factor",
    )


class _RecordingSink:
    """In-memory ``CalculationSink`` retaining what the engine wrote."""

    def __init__(self) -> None:
        self.snapshots: list[CalculationSnapshot] = []
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
    ) -> EmissionLog:
        return EmissionLog(
            id=f"log-{len(self.saved)}",
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

    async def save(self, entity: EmissionLog) -> EmissionLog:
        self.saved.append(entity)
        return entity


def service(sink: _RecordingSink) -> Scope3CalculationService:
    return Scope3CalculationService(CalculationEngine(sink))  # type: ignore[arg-type]


def estimation(**over: Any) -> EstimationRecord:
    base: dict[str, Any] = dict(
        organization_id=_ORG,
        estimation_method=str(over.get("method", "average_data")),
        inputs={"basis": "2025 DEFRA average"},
        assumptions={"per_employee_km": 3000},
        scope3_category=over.get("category"),
    )
    return EstimationRecord(**base)


#: The minimal truthful input for each category. Every entry states exactly what
#: the contract requires, including the boundary declarations and — for the
#: estimation-based categories — an explicitly-labelled estimate.
_FIXTURES: dict[int, dict[str, Any]] = {
    1: {"inputs": {}, "quality": "primary_supplier"},
    2: {"inputs": {"capitalisation_declared": True}, "quality": "primary_supplier"},
    3: {
        "inputs": {},
        "quality": "primary_supplier",
        "source_snapshot_id": "11111111-1111-4111-8111-111111111111",
        "source_item_id": "22222222-2222-4222-8222-222222222222",
    },
    4: {
        "inputs": {},
        "quality": "primary_supplier",
        "transport_boundary": "upstream",
    },
    5: {
        "inputs": {"material": "paper", "treatment_route": "recycling"},
        "quality": "primary_supplier",
        "waste_origin": "operations",
    },
    6: {"inputs": {"trip_purpose": "client_meeting"}, "quality": "primary_measured"},
    7: {"inputs": {}, "quality": "secondary_estimated", "estimate": True},
    8: {
        "inputs": {},
        "quality": "primary_supplier",
        "consolidation_approach": "operational_control",
    },
    9: {
        "inputs": {},
        "quality": "primary_supplier",
        "transport_boundary": "downstream",
    },
    10: {"inputs": {}, "quality": "secondary_estimated", "estimate": True},
    11: {
        "inputs": {"use_phase_assumption": "10 years at 100 kWh/yr"},
        "quality": "modelled",
        "estimate": True,
    },
    12: {
        "inputs": {"material": "steel", "treatment_route": "recycling"},
        "quality": "primary_supplier",
        "waste_origin": "sold_product_eol",
        "estimate": True,
    },
    13: {
        "inputs": {},
        "quality": "primary_supplier",
        "consolidation_approach": "operational_control",
    },
    14: {
        "inputs": {"allocation_basis": "floor_area_share"},
        "quality": "secondary_estimated",
        "estimate": True,
    },
    15: {
        "inputs": {"attribution_basis": "equity_share"},
        "quality": "modelled",
        "estimate": True,
    },
}

ALL_CATEGORIES = tuple(range(1, 16))


def valid_input(category: int, **over: Any) -> Scope3Input:
    """Build the minimal truthful request for ``category``."""
    fixture = dict(_FIXTURES[category])
    params: dict[str, Any] = {
        "organization_id": _ORG,
        "category": category,
        "quantity": Decimal("100"),
        "quantity_unit": "kg",
        "date": date(2025, 6, 1),
        "reporting_year": 2025,
        "activity": "Paper purchased",
        "activity_type": _ACTIVITY,
        "match": make_match(),
        "data_quality": fixture["quality"],
        "inputs": fixture.get("inputs", {}),
        "performed_by": "user-1",
        "performed_by_organization_id": _FIRM,
        "acting_for_organization_id": _ORG,
    }
    for key in ("transport_boundary", "waste_origin", "consolidation_approach",
                "source_snapshot_id", "source_item_id", "source_line_item_id"):
        if key in fixture:
            params[key] = fixture[key]
    if fixture.get("estimate"):
        params["estimation"] = estimation(category=category)
    params.update(over)
    return Scope3Input(**params)


# ===========================================================================
# A. Category coverage — all 15 recognized, all 15 contracts load
# ===========================================================================
def test_all_fifteen_categories_have_a_contract() -> None:
    assert sorted(CONTRACTS) == list(ALL_CATEGORIES), "a category has no contract"


@pytest.mark.parametrize("category", ALL_CATEGORIES)
def test_every_contract_is_complete(category: int) -> None:
    contract = contract_for(category)
    assert contract.category == category
    assert contract.name and contract.slug
    assert contract.architecture_status in {
        "SUPPORTED", "PARTIAL", "DEFERRED", "NOT_IMPLEMENTED"
    }
    assert contract.methodologies, "no methodology declared"
    assert contract.required_inputs, "no required input declared"
    assert contract.pathway in contract.allowed_pathways
    assert contract.discriminator, "no boundary discriminator declared"
    assert contract.refusal_reason, "no refusal reason declared"
    assert contract.automation, "no automation statement declared"


def test_invalid_category_is_rejected() -> None:
    from core.exceptions import Scope3CategoryRequiredError

    with pytest.raises(Scope3CategoryRequiredError):
        contract_for(0)


@pytest.mark.parametrize("category", ALL_CATEGORIES)
def test_architecture_status_is_never_upgraded(category: int) -> None:
    """The contract reports the taxonomy status verbatim — no silent promotion."""
    from domain.scope3 import status_of

    assert contract_for(category).architecture_status == status_of(category).value


# ===========================================================================
# B. Calculation — at least one valid pathway for EVERY category
# ===========================================================================
@pytest.mark.parametrize("category", ALL_CATEGORIES)
async def test_every_category_calculates_and_persists_its_identity(
    category: int,
) -> None:
    """All fifteen categories reach a persisted, category-attributed result."""
    sink = _RecordingSink()
    outcome = await service(sink).calculate(valid_input(category))

    assert outcome.calculated, (
        f"category {category} did not calculate: "
        f"{outcome.clarification and outcome.clarification.missing_fields}"
    )
    # Canonical persistence: snapshot + emissions log, on the one shared path.
    assert len(sink.snapshots) == 1, "no canonical snapshot created"
    assert len(sink.saved) == 1, "no emissions log created"
    snapshot = sink.snapshots[0]
    log = sink.saved[0]

    # CATEGORY IDENTITY IS PERSISTED — not inferred later.
    dims = snapshot.accounting_dimensions
    assert dims is not None
    assert dims.scope3_category == category
    assert log.accounting_dimensions.scope3_category == category
    assert log.accounting_dimensions.as_columns() == dims.as_columns()
    assert snapshot.scope == "Scope 3"
    # Data quality is recorded and distinguishable.
    assert dims.data_quality == _FIXTURES[category]["quality"]
    # The result is numerically correct: 100 kg x 2.50000.
    assert outcome.result is not None
    assert outcome.result.co2e_kg == Decimal("250.000000")
    # Owner and acting-for remain distinct.
    assert snapshot.organization_id == _ORG
    assert dims.performed_by_organization_id == _FIRM
    assert dims.acting_for_organization_id == _ORG
    assert log.organization_id == _ORG


@pytest.mark.parametrize("category", ALL_CATEGORIES)
async def test_every_category_contract_matches_its_persisted_dimensions(
    category: int,
) -> None:
    """The boundary declarations the contract demands are the ones persisted.

    ``consolidation_approach`` (DC-07) is deliberately excluded: it is an
    ORGANIZATION-level property, not a per-result column on
    ``calculation_snapshots``, so DC-07 validates it but does not persist it on
    the snapshot. Its enforcement is covered by the fail-closed test below.
    """
    sink = _RecordingSink()
    await service(sink).calculate(valid_input(category))
    dims = sink.snapshots[0].accounting_dimensions
    contract = contract_for(category)
    for field in contract.required_boundary_inputs:
        if field == "consolidation_approach":
            continue
        assert getattr(dims, field) == _FIXTURES[category].get(field), (
            f"category {category} did not persist {field}"
        )



def test_estimated_categories_are_marked_estimated() -> None:
    """No estimation-pathway category may claim a measured classification."""
    for category in ALL_CATEGORIES:
        contract = contract_for(category)
        if contract.pathway is CategoryPathway.ESTIMATION:
            assert set(contract.allowed_data_quality) <= set(ESTIMATED_DATA_QUALITY), (
                f"category {category} is estimation-based but permits "
                "non-estimated quality"
            )


@pytest.mark.parametrize("category", [7, 10, 11, 14, 15])
async def test_estimation_pathway_refuses_a_measured_classification(
    category: int,
) -> None:
    """An estimate must never be presented as measured data."""
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(
            valid_input(category, data_quality="primary_measured")
        )
    assert "estimation pathway" in excinfo.value.message
    assert sink.snapshots == []


@pytest.mark.parametrize("category", [7, 11, 12, 14])
async def test_estimated_category_without_an_estimation_record_is_refused(
    category: int,
) -> None:
    """T-INV-12 — no silent estimation."""
    sink = _RecordingSink()
    with pytest.raises(EstimationRecordRequiredError):
        await service(sink).calculate(valid_input(category, estimation=None))
    assert sink.snapshots == []


# ===========================================================================
# C. Validation — missing input is a controlled clarification, not a number
# ===========================================================================
async def test_missing_required_input_returns_clarification_not_a_value() -> None:
    """Category 5 without a treatment route must clarify, never invent one."""
    sink = _RecordingSink()
    outcome = await service(sink).calculate(
        valid_input(5, inputs={"material": "paper"})
    )
    assert outcome.status == CLARIFICATION_REQUIRED
    assert "treatment_route" in outcome.clarification.missing_fields
    assert outcome.clarification.reason
    assert outcome.clarification.guidance
    assert outcome.result is None
    assert sink.snapshots == []


async def test_clarification_names_every_missing_field() -> None:
    sink = _RecordingSink()
    outcome = await service(sink).calculate(valid_input(5, inputs={}))
    assert set(outcome.clarification.missing_fields) >= {"material", "treatment_route"}
    payload = outcome.clarification.as_payload()
    assert payload["status"] == "CLARIFICATION_REQUIRED"
    assert payload["category"] == 5


async def test_missing_boundary_declaration_returns_clarification() -> None:
    """DC-04 — a transport result with no stated boundary cannot be accounted."""
    sink = _RecordingSink()
    outcome = await service(sink).calculate(valid_input(4, transport_boundary=None))
    assert outcome.status == CLARIFICATION_REQUIRED
    assert "transport_boundary" in outcome.clarification.missing_fields
    assert sink.snapshots == []


async def test_missing_data_quality_is_refused() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(valid_input(6, data_quality=None))
    assert "data_quality" in excinfo.value.message
    assert sink.snapshots == []


async def test_invalid_methodology_is_refused() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(valid_input(6, methodology="invented_method"))
    assert "not supported" in excinfo.value.message
    assert sink.snapshots == []


async def test_supported_methodology_is_accepted() -> None:
    sink = _RecordingSink()
    outcome = await service(sink).calculate(valid_input(6, methodology="distance_based"))
    assert outcome.calculated
    assert outcome.result.snapshot.methodology == "distance_based"


async def test_invalid_pathway_is_refused() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError):
        await service(sink).calculate(valid_input(1, pathway="invented_pathway"))
    assert sink.snapshots == []


async def test_unavailable_pathway_for_a_category_is_refused() -> None:
    """Category 3 supports only the activity/factor pathway."""
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(valid_input(3, pathway="estimation"))
    assert "does not accept" in excinfo.value.message

# ===========================================================================
# E. Boundaries — the hard double-counting requirement
# ===========================================================================
async def test_category_4_cannot_be_declared_downstream() -> None:
    """DC-04 — upstream transport cannot silently become downstream."""
    sink = _RecordingSink()
    with pytest.raises(BoundaryAmbiguityError) as excinfo:
        await service(sink).calculate(valid_input(4, transport_boundary="downstream"))
    assert excinfo.value.code == "BOUNDARY_AMBIGUITY"
    assert sink.snapshots == []


async def test_category_9_cannot_be_declared_upstream() -> None:
    sink = _RecordingSink()
    with pytest.raises(BoundaryAmbiguityError):
        await service(sink).calculate(valid_input(9, transport_boundary="upstream"))
    assert sink.snapshots == []


async def test_category_5_cannot_be_declared_sold_product_eol() -> None:
    """DC-05 — operational waste cannot silently become end-of-life treatment."""
    sink = _RecordingSink()
    with pytest.raises(BoundaryAmbiguityError):
        await service(sink).calculate(valid_input(5, waste_origin="sold_product_eol"))
    assert sink.snapshots == []


async def test_category_12_cannot_be_declared_operations_waste() -> None:
    sink = _RecordingSink()
    with pytest.raises(BoundaryAmbiguityError):
        await service(sink).calculate(valid_input(12, waste_origin="operations"))
    assert sink.snapshots == []


async def test_categories_4_and_9_persist_distinguishable_boundaries() -> None:
    up, down = _RecordingSink(), _RecordingSink()
    await service(up).calculate(valid_input(4))
    await service(down).calculate(valid_input(9))
    assert up.snapshots[0].accounting_dimensions.transport_boundary == "upstream"
    assert down.snapshots[0].accounting_dimensions.transport_boundary == "downstream"
    assert up.snapshots[0].accounting_dimensions.scope3_category == 4
    assert down.snapshots[0].accounting_dimensions.scope3_category == 9


async def test_categories_5_and_12_persist_distinguishable_origins() -> None:
    ops, eol = _RecordingSink(), _RecordingSink()
    await service(ops).calculate(valid_input(5))
    await service(eol).calculate(valid_input(12))
    assert ops.snapshots[0].accounting_dimensions.waste_origin == "operations"
    assert eol.snapshots[0].accounting_dimensions.waste_origin == "sold_product_eol"


@pytest.mark.parametrize("category", [8, 13])
async def test_leased_asset_categories_fail_closed_without_consolidation(
    category: int,
) -> None:
    """DC-07 — upstream (8) and downstream (13) both need the consolidation basis."""
    sink = _RecordingSink()
    outcome = await service(sink).calculate(
        valid_input(category, consolidation_approach=None)
    )
    assert outcome.status == CLARIFICATION_REQUIRED
    assert "consolidation_approach" in outcome.clarification.missing_fields
    assert sink.snapshots == []


async def test_categories_8_and_13_are_distinguishable_by_category() -> None:
    up, down = _RecordingSink(), _RecordingSink()
    await service(up).calculate(valid_input(8))
    await service(down).calculate(valid_input(13))
    assert up.snapshots[0].accounting_dimensions.scope3_category == 8
    assert down.snapshots[0].accounting_dimensions.scope3_category == 13

# ===========================================================================
# D / H. Data quality, estimation metadata, provenance
# ===========================================================================
async def test_estimated_and_measured_results_are_distinguishable() -> None:
    measured, estimated = _RecordingSink(), _RecordingSink()
    await service(measured).calculate(valid_input(6))
    await service(estimated).calculate(valid_input(7))
    m = measured.snapshots[0].accounting_dimensions
    e = estimated.snapshots[0].accounting_dimensions
    assert m.data_quality == "primary_measured"
    assert e.data_quality == "secondary_estimated"


async def test_estimation_metadata_is_preserved_on_the_record() -> None:
    record = estimation(category=7, method="average_data")
    assert record.estimation_method == "average_data"
    assert record.inputs and record.assumptions
    assert record.as_row()["scope3_category"] == 7


def test_an_estimation_record_with_no_substance_is_refused() -> None:
    with pytest.raises(EstimationRecordRequiredError):
        EstimationRecord(
            organization_id=_ORG,
            estimation_method="average_data",
            inputs={},
            assumptions={},
        )


async def test_source_lineage_is_preserved_on_the_snapshot() -> None:
    sink = _RecordingSink()
    await service(sink).calculate(
        valid_input(1, source_item_id="22222222-2222-4222-8222-222222222222")
    )
    assert sink.snapshots[0].source_item_id == "22222222-2222-4222-8222-222222222222"


# ===========================================================================
# J. Idempotency — the P16 request identity is preserved
# ===========================================================================
async def test_repeated_identical_requests_share_the_request_identity() -> None:
    sink = _RecordingSink()
    svc = service(sink)
    request = valid_input(1, match=make_match(request_id="req-identical"))
    first = await svc.calculate(request)
    second = await svc.calculate(request)
    assert (
        first.result.snapshot.match_request_id
        == second.result.snapshot.match_request_id
    )
    assert first.result.snapshot.content_hash == second.result.snapshot.content_hash


async def test_scope3_dimensions_do_not_change_the_content_hash() -> None:
    """P16 hash preservation holds across the Scope 3 pathway too."""
    one, two = _RecordingSink(), _RecordingSink()
    factor = make_factor()
    await service(one).calculate(
        valid_input(1, match=make_match(factor=factor, request_id="req-h"))
    )
    await service(two).calculate(
        valid_input(1, match=make_match(factor=factor, request_id="req-h"))
    )
    assert one.snapshots[0].content_hash == two.snapshots[0].content_hash



def test_scope1_and_scope2_never_become_category_3_automatically() -> None:
    """DC-02 — category 3 is a derivation, never an automatic reclassification."""
    from domain.scope3 import derives_from_source_snapshot

    assert derives_from_source_snapshot(3) is True
    for other in (1, 2, 4, 5, 6):
        assert derives_from_source_snapshot(other) is False



async def test_unmatched_factor_is_refused_on_the_activity_pathway() -> None:
    sink = _RecordingSink()
    with pytest.raises(AccountingDimensionError) as excinfo:
        await service(sink).calculate(valid_input(1, match=make_match(status="no_match")))
    assert "requires a matched factor" in excinfo.value.message
    assert sink.snapshots == []


async def test_category_3_requires_its_source_snapshot() -> None:
    """DC-02 — a Scope 3 cat 3 result must link to the Scope 1/2 it derives from."""
    sink = _RecordingSink()
    outcome = await service(sink).calculate(
        valid_input(3, source_snapshot_id=None, source_item_id=None)
    )
    assert outcome.status == CLARIFICATION_REQUIRED
    assert "source_snapshot_id" in outcome.clarification.missing_fields
    assert sink.snapshots == []

