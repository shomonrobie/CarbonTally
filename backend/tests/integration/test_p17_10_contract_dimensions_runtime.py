"""P17-IMPLEMENT-10 — product-contract dimensions, verified on real PostgreSQL.

What this proves
----------------
The three product-contract facts this task added survive the full canonical path
against a real database, not an in-memory double:

1. **Scope 3 category methodology** (P17-PRODUCT-01 §29/§34). Every method in the
   frozen contract union is written to ``emissions_logs.scope3_method`` and
   ``calculation_snapshots.scope3_method`` on a genuinely stored row. This is the
   regression proof for the defect P17-IMPLEMENT-10 forensics found: eight of the
   ten contract methods could not be persisted at all.
2. **transaction provider vs underlying supplier** (P17-PRODUCT-01 §5). The
   purchase channel and the emissions-generating supplier are stored as two
   independent facts; an unresolved supplier stays NULL while the provider is
   still recorded, and the provider is never copied into the supplier column.
3. **The widened data-quality vocabulary** (P17-PRODUCT-01 §7/§29/§30). The four
   product classifications (``activity_based``, ``estimated``, ``manual``,
   ``unresolved``) persist, and the category-level reporting projection can group
   by the new dimensions.

At least one test proves the information survives
``input -> calculation -> canonical persistence -> read/reporting projection``.

Safety (F-046-1 restated)
-------------------------
This module uses the shared ``pool`` fixture, which performs **destructive** setup
(``TRUNCATE … RESTART IDENTITY CASCADE``). It therefore inherits that fixture's
guard: a target whose name matches ``qa`` / ``demo`` / ``investor`` / ``prod`` /
``live`` is refused before any statement runs, and the main application databases
are refused outright. Point ``INTEGRATION_DATABASE_URL`` at a disposable ``ct_*``
clone or at ``carbontally_test``. No production, demo, investor or QA environment
is contacted, and no migration is applied here.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import asyncpg
import pytest

from core.types import DateRange
from data.emission_factors import EmissionFactorsRepository
from data.emissions_logs import EmissionsLogsRepository
from data.suppliers import SuppliersRepository
from domain.estimation import EstimationRecord
from domain.factor import EmissionFactor
from domain.matching import MatchResult
from domain.scope3_contracts import SCOPE3_METHODS, contract_for
from engines.calculation import CalculationEngine
from services.scope2_calculation import Scope2CalculationService, Scope2Input
from services.scope3_calculation import Scope3CalculationService, Scope3Input
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio

_REPORTING_YEAR = 2025
_CALC_DATE = date(2025, 6, 1)
_QUANTITY = Decimal("100")
_UNIT = "kg"
_MULTIPLIER = Decimal("2.500000")
_S3_ACTIVITY = "Scope 3 > Purchased goods > Paper (kg CO2e) [kg]"
_S2_ACTIVITY = "Electricity > UK grid average (kg CO2e) [kWh]"
_S2_UNIT = "kWh"
_GEOGRAPHY = "GB"

#: A category whose contract permits each method — so the method test can drive a
#: method the CATEGORY agrees with, not merely one in the union.
_METHOD_CATEGORY: dict[str, int] = {
    method: next(
        c
        for c in range(1, 16)
        if method in contract_for(c).methodologies
    )
    for method in SCOPE3_METHODS
}


async def _require_p17_10_schema(pool: asyncpg.Pool) -> None:
    """Skip (never fail) when the P17-10 columns are absent from this database.

    A skipped suite is NOT a PASS, so the implementation report states the
    environment explicitly rather than inferring it from a green tick.
    """
    present = await pool.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='emissions_logs' "
        "AND column_name='scope3_method')"
    )
    if not present:
        pytest.skip(
            "the P17-IMPLEMENT-10 columns are not provisioned in this integration "
            "database; apply "
            "supabase/migrations/20261014000000_p17_10_product_contract_"
            "reporting_dimensions.sql to a disposable ct_* clone (F-046-1) before "
            "claiming a real-PostgreSQL round-trip"
        )



@dataclass(frozen=True, slots=True)
class _World:
    """One isolated tenant world: a data owner, a consultant firm, another tenant."""

    data_owner: str
    firm: str
    other_org: str
    s3_factor: EmissionFactor
    s2_factor: EmissionFactor
    supplier_id: str


async def _seed_factor(
    pool: asyncpg.Pool, *, activity: str, scope: str, unit: str
) -> EmissionFactor:
    factor = EmissionFactor(
        id=new_id(),
        reporting_year=_REPORTING_YEAR,
        activity_type=activity,
        co2e_multiplier=_MULTIPLIER,
        unit=unit,
        scope=scope,
        factor_source="DEFRA-DESNZ",
        factor_set=f"DEFRA-{_REPORTING_YEAR}",
        country=_GEOGRAPHY,
        provider_key="defra",
        import_batch_id=None,
        natural_key=(str(_REPORTING_YEAR), activity, _GEOGRAPHY, unit, scope),
    )
    return await EmissionFactorsRepository(pool).save(factor)


async def _seed_supplier(pool: asyncpg.Pool, org_id: str, name: str) -> str:
    supplier = await SuppliersRepository(pool).create(
        org_id=org_id,
        name=name,
        type_="waste",
        supplier_type=None,
        contact_name=None,
        contact_email=None,
        contact_phone=None,
        country=_GEOGRAPHY,
        vat_number=None,
        metadata={},
        created_by=None,
        provenance={
            "actor_organization_id": org_id,
            "acting_for_organization_id": org_id,
        },
    )
    return supplier.id


async def _world(pool: asyncpg.Pool) -> _World:
    data_owner = await make_org(pool, "P17-10 Data Owner")
    firm = await make_org(pool, "P17-10 Consultant Firm")
    other = await make_org(pool, "P17-10 Other Tenant")
    return _World(
        data_owner=data_owner,
        firm=firm,
        other_org=other,
        s3_factor=await _seed_factor(
            pool, activity=_S3_ACTIVITY, scope="Scope 3", unit=_UNIT
        ),
        s2_factor=await _seed_factor(
            pool, activity=_S2_ACTIVITY, scope="Scope 2", unit=_S2_UNIT
        ),
        supplier_id=await _seed_supplier(pool, data_owner, "P17-10 Hotel Co"),
    )


_REQUEST_NAMESPACE = uuid.UUID("c4d5e6f7-8a9b-4c1d-9e2f-3a4b5c6d7e80")


def _request_id(*parts: str) -> str:
    return str(uuid.uuid5(_REQUEST_NAMESPACE, "|".join(parts)))


def _match(factor: EmissionFactor, request_id: str) -> MatchResult:
    return MatchResult(
        status="matched",
        factor=factor,
        confidence=1.0,
        methodology="direct_multiply",
        request_id=request_id,
        factor_kind="emission_factor",
    )


def _boundary_inputs(category: int) -> dict[str, Any]:
    """Exactly the required/boundary inputs the category contract demands."""
    inputs: dict[str, Any] = {
        name: "declared-for-test"
        for name in contract_for(category).required_inputs
        if name not in ("activity", "quantity", "unit")
    }
    extra: dict[str, Any] = {}
    for name in contract_for(category).required_boundary_inputs:
        if name == "transport_boundary":
            extra[name] = "upstream" if category == 4 else "downstream"
        elif name == "waste_origin":
            extra[name] = "operations" if category == 5 else "sold_product_eol"
        elif name == "consolidation_approach":
            extra[name] = "OPERATIONAL_CONTROL"
        elif name == "source_snapshot_id":
            extra[name] = str(uuid.uuid4())
    return {"inputs": inputs, **extra}


def _scope3_input(world: _World, category: int, **over: Any) -> Scope3Input:
    contract = contract_for(category)
    params: dict[str, Any] = {
        "organization_id": world.data_owner,
        "category": category,
        "quantity": _QUANTITY,
        "quantity_unit": _UNIT,
        "date": _CALC_DATE,
        "reporting_year": _REPORTING_YEAR,
        "activity": "P17-10 canonical fixture activity",
        "activity_type": _S3_ACTIVITY,
        "match": _match(
            world.s3_factor, _request_id("s3", str(category), world.data_owner)
        ),
        "performed_by": new_id(),
        "performed_by_organization_id": world.firm,
        "acting_for_organization_id": world.data_owner,
        "supplier_id": world.supplier_id,
        **_boundary_inputs(category),
    }
    if contract.requires_estimation_record:
        params["data_quality"] = "secondary_estimated"
        params["estimation"] = EstimationRecord(
            organization_id=world.data_owner,
            estimation_method="average_data",
            inputs={"basis": f"{_REPORTING_YEAR} industry average"},
            assumptions={"per_unit_factor": str(_MULTIPLIER)},
            scope3_category=category,
        )
    else:
        params["data_quality"] = "primary_supplier"
    params.update(over)
    return Scope3Input(**params)


def _scope3_service(pool: asyncpg.Pool) -> Scope3CalculationService:
    return Scope3CalculationService(CalculationEngine(EmissionsLogsRepository(pool)))


def _scope2_service(pool: asyncpg.Pool) -> Scope2CalculationService:
    return Scope2CalculationService(CalculationEngine(EmissionsLogsRepository(pool)))



# ---------------------------------------------------------------------------
# 1. Schema and RLS
# ---------------------------------------------------------------------------
async def test_p17_10_columns_exist_nullable_and_without_default(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    rows = await pool.fetch(
        "SELECT table_name, column_name, is_nullable, column_default, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema='public' AND column_name IN "
        "('scope3_method','transaction_provider')"
    )
    found = {(r["table_name"], r["column_name"]) for r in rows}
    assert found == {
        ("calculation_snapshots", "scope3_method"),
        ("calculation_snapshots", "transaction_provider"),
        ("emissions_logs", "scope3_method"),
        ("emissions_logs", "transaction_provider"),
    }
    for r in rows:
        assert r["is_nullable"] == "YES", r
        assert r["column_default"] is None, r
        assert r["data_type"] == "text", r


async def test_rls_remains_enabled_on_both_tables(pool: asyncpg.Pool) -> None:
    await _require_p17_10_schema(pool)
    rows = await pool.fetch(
        "SELECT relname, relrowsecurity FROM pg_class "
        "WHERE relname IN ('calculation_snapshots','emissions_logs') "
        "AND relnamespace = 'public'::regnamespace"
    )
    assert {r["relname"] for r in rows} == {
        "calculation_snapshots",
        "emissions_logs",
    }
    assert all(r["relrowsecurity"] for r in rows), rows


# ---------------------------------------------------------------------------
# 2. The defect: every contract method persists on a real stored row
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method", sorted(SCOPE3_METHODS))
async def test_every_contract_method_is_stored_on_real_rows(
    pool: asyncpg.Pool, method: str
) -> None:
    """REGRESSION — before the fix eight of these raised before persisting."""
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    category = _METHOD_CATEGORY[method]
    outcome = await _scope3_service(pool).calculate(
        _scope3_input(world, category, methodology=method)
    )
    assert outcome.calculated, outcome.clarification
    snapshot_id = outcome.result.snapshot.id
    stored_snapshot = await pool.fetchrow(
        "SELECT scope3_method, methodology, scope3_category, scope "
        "FROM public.calculation_snapshots WHERE id = $1",
        uuid.UUID(snapshot_id),
    )
    stored_log = await pool.fetchrow(
        "SELECT scope3_method, scope3_category, scope "
        "FROM public.emissions_logs WHERE snapshot_id = $1",
        uuid.UUID(snapshot_id),
    )
    assert stored_snapshot is not None and stored_log is not None
    for row in (stored_snapshot, stored_log):
        assert row["scope3_method"] == method
        assert row["scope3_category"] == category
        assert row["scope"] == "Scope 3"
    # The arithmetic label is a DIFFERENT fact and is recorded on the snapshot
    # (emissions_logs carries no methodology column — the snapshot is authoritative).
    expected_engine = (
        "spend_based" if method == "spend_based"
        else "distance_based" if method == "distance_based"
        else "direct_multiply"
    )
    assert stored_snapshot["methodology"] == expected_engine


async def test_absent_method_is_stored_as_null_not_defaulted(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 1))
    assert outcome.calculated
    stored = await pool.fetchval(
        "SELECT scope3_method FROM public.emissions_logs WHERE snapshot_id = $1",
        uuid.UUID(outcome.result.snapshot.id),
    )
    assert stored is None


# ---------------------------------------------------------------------------
# 3. transaction provider vs underlying supplier (P17-PRODUCT-01 §5)
# ---------------------------------------------------------------------------
async def test_provider_and_supplier_are_stored_as_separate_columns(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(
        _scope3_input(
            world,
            6,
            methodology="distance_based",
            quantity_unit=_UNIT,
            transaction_provider="Booking.com",
        )
    )
    assert outcome.calculated, outcome.clarification
    row = await pool.fetchrow(
        "SELECT supplier_id, transaction_provider FROM public.emissions_logs "
        "WHERE snapshot_id = $1",
        uuid.UUID(outcome.result.snapshot.id),
    )
    assert str(row["supplier_id"]) == world.supplier_id
    assert row["transaction_provider"] == "Booking.com"
    # Two independent facts, not one copied into the other.
    assert row["transaction_provider"] != str(row["supplier_id"])
    snap = await pool.fetchval(
        "SELECT transaction_provider FROM public.calculation_snapshots WHERE id = $1",
        uuid.UUID(outcome.result.snapshot.id),
    )
    assert snap == "Booking.com"


async def test_unresolved_supplier_stays_null_while_the_provider_is_recorded(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(
        _scope3_input(
            world, 6, methodology="distance_based", supplier_id=None,
            transaction_provider="Agoda",
        )
    )
    assert outcome.calculated
    row = await pool.fetchrow(
        "SELECT supplier_id, transaction_provider FROM public.emissions_logs "
        "WHERE snapshot_id = $1",
        uuid.UUID(outcome.result.snapshot.id),
    )
    assert row["supplier_id"] is None
    assert row["transaction_provider"] == "Agoda"


async def test_known_supplier_does_not_populate_the_provider(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 1))
    assert outcome.calculated
    assert (
        await pool.fetchval(
            "SELECT transaction_provider FROM public.emissions_logs "
            "WHERE snapshot_id = $1",
            uuid.UUID(outcome.result.snapshot.id),
        )
        is None
    )


async def test_consultant_acting_for_client_records_both_facts(
    pool: asyncpg.Pool,
) -> None:
    """A delegated consultant write keeps owner, attribution and provider apart."""
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(
        _scope3_input(world, 6, methodology="distance_based",
                      transaction_provider="Trainline")
    )
    assert outcome.calculated
    row = await pool.fetchrow(
        "SELECT organization_id, performed_by_organization_id, "
        "acting_for_organization_id, transaction_provider "
        "FROM public.emissions_logs WHERE snapshot_id = $1",
        uuid.UUID(outcome.result.snapshot.id),
    )
    assert str(row["organization_id"]) == world.data_owner
    assert str(row["performed_by_organization_id"]) == world.firm
    assert str(row["acting_for_organization_id"]) == world.data_owner
    assert row["transaction_provider"] == "Trainline"


# ---------------------------------------------------------------------------
# 4. Widened data-quality vocabulary on real rows
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quality", ["activity_based", "estimated", "manual", "unresolved"]
)
async def test_product_data_quality_classifications_persist(
    pool: asyncpg.Pool, quality: str
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    # Category 1's activity/factor pathway permits any classification. ``estimated``
    # is an estimate by definition, so T-INV-12 still requires a persisted basis —
    # that rule is deliberately untouched by this task.
    over: dict[str, Any] = {"data_quality": quality}
    if quality == "estimated":
        over["estimation"] = EstimationRecord(
            organization_id=world.data_owner,
            estimation_method="average_data",
            inputs={"basis": f"{_REPORTING_YEAR} industry average"},
            assumptions={},
            scope3_category=1,
        )
    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 1, **over))
    assert outcome.calculated, outcome.clarification
    stored = await pool.fetchval(
        "SELECT data_quality FROM public.emissions_logs WHERE snapshot_id = $1",
        uuid.UUID(outcome.result.snapshot.id),
    )
    assert stored == quality


# ---------------------------------------------------------------------------
# 5. input -> calculation -> persistence -> READ / REPORTING PROJECTION
# ---------------------------------------------------------------------------
async def test_category_reporting_projection_reads_the_new_dimensions(
    pool: asyncpg.Pool,
) -> None:
    """P17-PRODUCT-01 §29: the read layer can group by the new dimensions.

    This is the end-to-end claim: the same stored row is grouped by category,
    category method and data quality through the existing organization-scoped
    analytics projection — no second result table and no duplicated snapshot.
    """
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    service = _scope3_service(pool)
    repo = EmissionsLogsRepository(pool)
    # Two categories with distinct methods, both on the SAME period.
    for category, method in ((1, "supplier_specific"), (4, "distance_based")):
        outcome = await service.calculate(
            _scope3_input(world, category, methodology=method)
        )
        assert outcome.calculated, outcome.clarification

    period = DateRange(start_date=_CALC_DATE, end_date=_CALC_DATE)
    by_category = await repo.aggregate_groups(
        world.data_owner, period, "scope3_category", 50
    )
    keys = {str(r["group_key"]): Decimal(str(r["co2e_kg"])) for r in by_category}
    assert set(keys) == {"1", "4"}
    # 100 kg x 2.5 = 250 kg CO2e each.
    assert keys["1"] == Decimal("250.000000")
    assert keys["4"] == Decimal("250.000000")

    by_method = {
        str(r["group_key"])
        for r in await repo.aggregate_groups(
            world.data_owner, period, "scope3_method", 50
        )
    }
    assert by_method == {"supplier_specific", "distance_based"}

    by_quality = {
        str(r["group_key"])
        for r in await repo.aggregate_groups(
            world.data_owner, period, "data_quality", 50
        )
    }
    assert by_quality == {"primary_supplier"}


async def test_transaction_provider_is_a_read_dimension(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(
        _scope3_input(
            world, 6, methodology="distance_based",
            transaction_provider="Booking.com",
        )
    )
    assert outcome.calculated
    repo = EmissionsLogsRepository(pool)
    period = DateRange(start_date=_CALC_DATE, end_date=_CALC_DATE)
    groups = await repo.aggregate_groups(
        world.data_owner, period, "transaction_provider", 50
    )
    assert {str(r["group_key"]) for r in groups} == {"Booking.com"}


async def test_scope2_read_projection_exposes_method_and_energy_type(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    result = await _scope2_service(pool).calculate(
        Scope2Input(
            organization_id=world.data_owner,
            quantity=Decimal("12500"),
            quantity_unit=_S2_UNIT,
            date=_CALC_DATE,
            reporting_year=_REPORTING_YEAR,
            activity="P17-10 electricity",
            activity_type=_S2_ACTIVITY,
            method="LOCATION_BASED",
            energy_type="electricity",
            match=_match(
                world.s2_factor,
                _request_id("s2", world.data_owner, "loc"),
            ),
            data_quality="primary_measured",
            performed_by=new_id(),
            performed_by_organization_id=world.firm,
            acting_for_organization_id=world.data_owner,
            supplier_id=world.supplier_id,
            transaction_provider="British Gas Business",
        )
    )
    repo = EmissionsLogsRepository(pool)
    period = DateRange(start_date=_CALC_DATE, end_date=_CALC_DATE)
    methods = {
        str(r["group_key"])
        for r in await repo.aggregate_groups(
            world.data_owner, period, "scope2_method", 50
        )
    }
    energies = {
        str(r["group_key"])
        for r in await repo.aggregate_groups(
            world.data_owner, period, "energy_type", 50
        )
    }
    assert methods == {"LOCATION_BASED"}
    assert energies == {"electricity"}
    stored = await pool.fetchrow(
        "SELECT supplier_id, transaction_provider FROM public.emissions_logs "
        "WHERE snapshot_id = $1",
        uuid.UUID(result.snapshot.id),
    )
    assert str(stored["supplier_id"]) == world.supplier_id
    assert stored["transaction_provider"] == "British Gas Business"



# ---------------------------------------------------------------------------
# 6. Security: tenant isolation, database vocabulary guards, idempotency
# ---------------------------------------------------------------------------
async def test_cross_tenant_read_projection_cannot_leak_and_stays_isolated(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(
        _scope3_input(world, 1, methodology="supplier_specific")
    )
    assert outcome.calculated
    repo = EmissionsLogsRepository(pool)
    period = DateRange(start_date=_CALC_DATE, end_date=_CALC_DATE)
    # The other tenant sees NOTHING, for every new dimension.
    for dimension in (
        "scope3_category",
        "scope3_method",
        "data_quality",
        "transaction_provider",
    ):
        assert await repo.aggregate_groups(
            world.other_org, period, dimension, 50
        ) == [], dimension
    assert await repo.count_snapshots(world.other_org, period) == 0
    # And the owner does see it (the isolation is not a blanket empty result).
    assert await repo.count_snapshots(world.data_owner, period) == 1


async def test_database_refuses_a_method_outside_the_vocabulary(
    pool: asyncpg.Pool,
) -> None:
    """The vocabulary is enforced by the database, not only by the domain."""
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 1))
    assert outcome.calculated
    snapshot_id = uuid.UUID(outcome.result.snapshot.id)
    with pytest.raises(asyncpg.exceptions.CheckViolationError):
        await pool.execute(
            "UPDATE public.emissions_logs SET scope3_method = $2 "
            "WHERE snapshot_id = $1",
            snapshot_id,
            "invented_method",
        )
    with pytest.raises(asyncpg.exceptions.CheckViolationError):
        await pool.execute(
            "UPDATE public.calculation_snapshots SET scope3_method = $2 "
            "WHERE id = $1",
            snapshot_id,
            "invented_method",
        )


async def test_database_refuses_a_blank_transaction_provider(
    pool: asyncpg.Pool,
) -> None:
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 1))
    assert outcome.calculated
    with pytest.raises(asyncpg.exceptions.CheckViolationError):
        await pool.execute(
            "UPDATE public.emissions_logs SET transaction_provider = '   ' "
            "WHERE snapshot_id = $1",
            uuid.UUID(outcome.result.snapshot.id),
        )


async def test_database_refuses_scope3_method_on_a_scope2_row(
    pool: asyncpg.Pool,
) -> None:
    """The Scope-3-only guard is enforced on new writes (NOT VALID: history exempt)."""
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    result = await _scope2_service(pool).calculate(
        Scope2Input(
            organization_id=world.data_owner,
            quantity=Decimal("100"),
            quantity_unit=_S2_UNIT,
            date=_CALC_DATE,
            reporting_year=_REPORTING_YEAR,
            activity="P17-10 electricity",
            activity_type=_S2_ACTIVITY,
            method="LOCATION_BASED",
            energy_type="electricity",
            match=_match(world.s2_factor, _request_id("s2", world.data_owner, "guard")),
            data_quality="primary_measured",
        )
    )
    with pytest.raises(asyncpg.exceptions.CheckViolationError):
        await pool.execute(
            "UPDATE public.emissions_logs SET scope3_method = 'average_data' "
            "WHERE snapshot_id = $1",
            uuid.UUID(result.snapshot.id),
        )


async def test_repeating_the_calculation_persists_exactly_one_row(
    pool: asyncpg.Pool,
) -> None:
    """P16 idempotency is untouched: one result per request identity.

    The ``uq_calc_snapshots_request_id`` index refuses a second write of the same
    identity outright rather than duplicating the accounting result — the caller
    resolves the existing result by looking the request id up first (the P16
    property, unchanged by these dimensions). The assertion that matters is that
    the duplicate cannot double the data.
    """
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    service = _scope3_service(pool)
    first = await service.calculate(
        _scope3_input(world, 1, methodology="supplier_specific")
    )
    assert first.calculated
    with pytest.raises(asyncpg.exceptions.UniqueViolationError):
        await service.calculate(
            _scope3_input(world, 1, methodology="supplier_specific")
        )
    repo = EmissionsLogsRepository(pool)
    period = DateRange(start_date=_CALC_DATE, end_date=_CALC_DATE)
    assert await repo.count_snapshots(world.data_owner, period) == 1
    assert (
        await pool.fetchval(
            "SELECT count(*) FROM public.emissions_logs WHERE organization_id = $1",
            uuid.UUID(world.data_owner),
        )
        == 1
    )


async def test_lifecycle_reportability_columns_are_untouched(
    pool: asyncpg.Pool,
) -> None:
    """P16-R5 reportability protection still applies to a new result."""
    await _require_p17_10_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 1))
    assert outcome.calculated
    row = await pool.fetchrow(
        "SELECT reportability_status, invalidated_reason, "
        "superseded_by_snapshot_id FROM public.calculation_snapshots "
        "WHERE id = $1",
        uuid.UUID(outcome.result.snapshot.id),
    )
    # A fresh calculation is NOT reportable merely because it was created.
    assert row["reportability_status"] not in ("REPORTABLE", "APPROVED")
    assert row["invalidated_reason"] is None
    assert row["superseded_by_snapshot_id"] is None

