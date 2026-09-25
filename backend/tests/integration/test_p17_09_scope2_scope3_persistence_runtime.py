"""P17-IMPLEMENT-09 — real-PostgreSQL round-trip for Scope 2 and all 15 Scope 3 categories.

Why this file exists
--------------------
P17-IMPLEMENT-08 closed with verdict ``P17_IMPLEMENTATION_PARTIAL`` for exactly one
reason: the Scope 2/Scope 3 persistence path had never been exercised against a
real PostgreSQL instance. Every claim in this file is therefore a claim about a
**stored row**, not about an in-memory double:

* the real ``Scope2CalculationService`` / ``Scope3CalculationService``;
* the real ``CalculationEngine``;
* the real ``EmissionsLogsRepository``, ``EstimationRecordsRepository``,
  ``EmissionFactorsRepository``, ``SuppliersRepository`` and
  ``ContractualInstrumentsRepository``;
* the real P17 schema, including its ``CHECK`` guards, partial unique indexes and
  foreign keys.

What it proves
--------------
1. A calculation persists an immutable snapshot *and* its paired emissions log.
2. Category, methodology, factor, factor year, data quality, boundary
   declarations and the acting-for/performed-by attribution pair are all stored.
3. Supplier attribution survives to ``emissions_logs.supplier_id``.
4. An estimated value carries a persisted estimation record, idempotently.
5. All fifteen categories persist their distinct identity.
6. The database itself enforces the boundary and idempotency invariants.
7. Two organisations cannot see each other's results.
8. Scope 2 location-based and market-based both persist, with the instrument
   allocation recorded against the result.

Safety (F-046-1 restated)
-------------------------
This module uses the shared ``pool`` fixture, which performs **destructive**
setup (``TRUNCATE … RESTART IDENTITY CASCADE``). It therefore inherits that
fixture's guard: a target whose name matches ``qa`` / ``demo`` / ``investor`` /
``prod`` / ``live`` is refused before any statement runs, and the main
application databases are refused outright. Point ``INTEGRATION_DATABASE_URL``
at a disposable ``ct_*`` clone or at ``carbontally_test``. No production, demo,
investor or QA environment is contacted, and no migration is applied here.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from typing import Any

import asyncpg
import pytest

from core.exceptions import (
    AccountingDimensionError,
    BoundaryAmbiguityError,
    EstimationRecordRequiredError,
    InstrumentEligibilityError,
    InstrumentOverAllocatedError,
)
from core.types import DateRange
from data.contractual_instruments import ContractualInstrumentsRepository
from data.emission_factors import EmissionFactorsRepository
from data.emissions_logs import EmissionsLogsRepository
from data.estimation_records import EstimationRecordsRepository
from data.suppliers import SuppliersRepository
from domain.contractual_instruments import (
    ContractualInstrument,
    InstrumentAllocation,
    assert_allocation_within_quantity,
)
from domain.estimation import EstimationRecord
from domain.factor import EmissionFactor
from domain.matching import MatchResult
from domain.scope3_contracts import contract_for
from engines.calculation import CalculationEngine
from services.scope2_calculation import Scope2CalculationService, Scope2Input
from services.scope3_calculation import Scope3CalculationService, Scope3Input
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio

#: Deterministic canonical fixture inputs. Synthetic by construction and labelled
#: as such: no figure here is presented as collected customer data.
_REPORTING_YEAR = 2025
_CALC_DATE = date(2025, 6, 1)
_QUANTITY = Decimal("100")
_UNIT = "kg"
_MULTIPLIER = Decimal("2.500000")
_S3_ACTIVITY = "Scope 3 > Purchased goods > Paper (kg CO2e) [kg]"
_S2_ACTIVITY = "Electricity > UK grid average (kg CO2e) [kWh]"
_S2_UNIT = "kWh"
_GEOGRAPHY = "GB"

CATEGORIES = tuple(range(1, 16))


async def _require_p17_schema(pool: asyncpg.Pool) -> None:
    """Skip (never fail) when the P17 schema is not provisioned in this database.

    A skipped suite is NOT a PASS, so the implementation report states the
    environment explicitly rather than inferring it from a green tick.
    """
    present = await pool.fetchval(
        "SELECT to_regclass('public.scope3_categories') IS NOT NULL"
    )
    if not present:
        pytest.skip(
            "the P17 schema is not provisioned in this integration database; "
            "apply supabase/migrations/2026101{0,1,2,3}000000_p17*.sql to a "
            "disposable clone (see the F-046-1 recipe) before claiming a "
            "real-PostgreSQL round-trip"
        )


@dataclass(frozen=True, slots=True)
class _World:
    """One isolated tenant world: two organisations, a firm and their factories."""

    data_owner: str
    firm: str
    other_org: str
    s3_factor: EmissionFactor
    s2_factor: EmissionFactor
    supplier_id: str


async def _seed_factor(
    pool: asyncpg.Pool, *, activity: str, scope: str, unit: str
) -> EmissionFactor:
    """Insert one real ``emission_factors`` row and return the stored factor."""
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
    """Insert a real organisation-scoped supplier row and return its id."""
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
    """Build one isolated tenant world with real parent rows."""
    data_owner = await make_org(pool, "P17-09 Data Owner")
    firm = await make_org(pool, "P17-09 Consultant Firm")
    other = await make_org(pool, "P17-09 Other Tenant")
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
        supplier_id=await _seed_supplier(pool, data_owner, "P17-09 Waste Co"),
    )


#: Namespace for the deterministic request identity. The real routes derive their
#: request id with ``uuid5`` because ``calculation_snapshots.request_id`` is a
#: UUID column — the integration fixture must satisfy the same storage contract,
#: not a laxer one.
_REQUEST_NAMESPACE = uuid.UUID("9f2c1b7a-4d3e-4c5f-8a90-1b2c3d4e5f60")


def _request_id(*parts: str) -> str:
    """Return the deterministic UUID5 request identity for the given parts."""
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


def _estimation(
    category: int, owner: str, method: str = "average_data"
) -> EstimationRecord:
    return EstimationRecord(
        organization_id=owner,
        estimation_method=method,
        inputs={"basis": f"{_REPORTING_YEAR} industry average"},
        assumptions={"per_unit_factor": str(_MULTIPLIER)},
        scope3_category=category,
    )


#: The minimal *truthful* input for each category: exactly what the contract
#: requires, including boundary declarations and — for the estimation-based
#: categories — an explicitly-labelled estimate. Mirrors the IMPLEMENT-07 unit
#: fixtures so the real-database run proves the same contract, not a laxer one.
_FIXTURES: dict[int, dict[str, Any]] = {
    1: {"inputs": {}, "quality": "primary_supplier", "source": True},
    2: {"inputs": {"capitalisation_declared": True}, "quality": "primary_supplier"},
    3: {"inputs": {}, "quality": "primary_supplier", "source_snapshot": True},
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


def _scope3_input(world: _World, category: int, **over: Any) -> Scope3Input:
    """Build the minimal truthful ``Scope3Input`` for ``category``.

    ``source_snapshot_id`` for category 3 defaults to a random UUID: the column
    carries no foreign key (it is a lineage reference to a Scope 1/2 snapshot),
    and the dedicated category-3 test supplies a *real* source snapshot instead.
    """
    fixture = dict(_FIXTURES[category])
    params: dict[str, Any] = {
        "organization_id": world.data_owner,
        "category": category,
        "quantity": _QUANTITY,
        "quantity_unit": _UNIT,
        "date": _CALC_DATE,
        "reporting_year": _REPORTING_YEAR,
        "activity": "P17-09 canonical fixture activity",
        "activity_type": _S3_ACTIVITY,
        "match": _match(
            world.s3_factor, _request_id("s3", str(category), world.data_owner)
        ),
        "data_quality": fixture["quality"],
        "inputs": fixture.get("inputs", {}),
        "performed_by": new_id(),
        "performed_by_organization_id": world.firm,
        "acting_for_organization_id": world.data_owner,
        "supplier_id": world.supplier_id,
    }
    for key in ("transport_boundary", "waste_origin", "consolidation_approach"):
        if key in fixture:
            params[key] = fixture[key]
    if fixture.get("source") or fixture.get("source_snapshot"):
        params["source_snapshot_id"] = str(uuid.uuid4())
    if fixture.get("estimate"):
        params["estimation"] = _estimation(category, world.data_owner)
    params.update(over)
    return Scope3Input(**params)


def _scope3_service(pool: asyncpg.Pool) -> Scope3CalculationService:
    return Scope3CalculationService(CalculationEngine(EmissionsLogsRepository(pool)))


def _scope2_service(pool: asyncpg.Pool) -> Scope2CalculationService:
    return Scope2CalculationService(CalculationEngine(EmissionsLogsRepository(pool)))


def _scope2_input(
    world: _World, *, method: str = "LOCATION_BASED", **over: Any
) -> Scope2Input:
    params: dict[str, Any] = {
        "organization_id": world.data_owner,
        "quantity": Decimal("12500"),
        "quantity_unit": _S2_UNIT,
        "date": _CALC_DATE,
        "reporting_year": _REPORTING_YEAR,
        "activity": "P17-09 Scope 2 fixture activity",
        "activity_type": _S2_ACTIVITY,
        "method": method,
        "energy_type": "electricity",
        "match": _match(
            world.s2_factor, _request_id("s2", method, world.data_owner)
        ),
        "geography": _GEOGRAPHY,
        "data_quality": "primary_measured",
        "performed_by": new_id(),
        "performed_by_organization_id": world.firm,
        "acting_for_organization_id": world.data_owner,
        "supplier_id": world.supplier_id,
    }
    params.update(over)
    return Scope2Input(**params)


def _norm(row: asyncpg.Record) -> dict[str, Any]:
    """Return the row as a dict with UUID values rendered as strings.

    asyncpg hands UUID columns back as :class:`uuid.UUID` objects; every
    repository in this codebase exposes them as strings, so the assertions here
    compare against the same representation the application uses.
    """
    return {
        key: (str(value) if isinstance(value, uuid.UUID) else value)
        for key, value in dict(row).items()
    }


async def _snapshot_row(pool: asyncpg.Pool, snapshot_id: str) -> dict[str, Any]:
    row = await pool.fetchrow(
        "SELECT id, organization_id, scope, scope2_method, scope3_category, "
        "energy_type, data_quality, facility_id, transport_boundary, waste_origin, "
        "source_snapshot_id, performed_by_organization_id, "
        "acting_for_organization_id, factor_id, factor_kind, reporting_year, "
        "methodology, co2e_kg, request_id, content_hash, source_item_id, "
        "source_line_item_id "
        "FROM public.calculation_snapshots WHERE id = $1",
        snapshot_id,
    )
    return _norm(row) if row is not None else {}


async def _log_row(pool: asyncpg.Pool, snapshot_id: str) -> dict[str, Any]:
    row = await pool.fetchrow(
        "SELECT id, organization_id, snapshot_id, scope, scope2_method, "
        "scope3_category, energy_type, data_quality, facility_id, "
        "transport_boundary, waste_origin, source_snapshot_id, "
        "performed_by_organization_id, acting_for_organization_id, supplier_id, "
        "calculated_kg_co2e, raw_quantity, unit, emission_factor_id "
        "FROM public.emissions_logs WHERE snapshot_id = $1",
        snapshot_id,
    )
    return _norm(row) if row is not None else {}


# ===========================================================================
# A. The canonical activity/factor path persists a snapshot AND its log
# ===========================================================================
async def test_scope3_activity_factor_result_is_persisted_end_to_end(
    pool: asyncpg.Pool,
) -> None:
    """Category 1: one calculation → one immutable snapshot + one emissions log."""
    await _require_p17_schema(pool)
    world = await _world(pool)

    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 1))
    assert outcome.calculated is True

    snapshot = await _snapshot_row(pool, outcome.result.snapshot.id)
    log = await _log_row(pool, outcome.result.snapshot.id)

    assert snapshot is not None, "the calculation snapshot was not persisted"
    assert log is not None, "the emissions log was not persisted"

    # --- accounting identity -------------------------------------------------
    assert snapshot["scope"] == "Scope 3"
    assert snapshot["scope3_category"] == 1
    assert snapshot["scope2_method"] is None
    assert snapshot["energy_type"] is None
    assert snapshot["data_quality"] == "primary_supplier"
    assert snapshot["methodology"] == "direct_multiply"
    assert snapshot["reporting_year"] == _REPORTING_YEAR

    # --- factor provenance (governed: right factor, right scope, right year) --
    assert snapshot["factor_id"] == world.s3_factor.id
    assert snapshot["factor_kind"] == "emission_factor"

    # --- evidence / source lineage ------------------------------------------
    assert snapshot["source_snapshot_id"] is not None

    # --- attribution (acting-for is never the owner by accident) -------------
    assert snapshot["organization_id"] == world.data_owner
    assert snapshot["performed_by_organization_id"] == world.firm
    assert snapshot["acting_for_organization_id"] == world.data_owner
    assert snapshot["performed_by_organization_id"] != snapshot["organization_id"]

    # --- arithmetic and request identity ------------------------------------
    assert snapshot["co2e_kg"] == _QUANTITY * _MULTIPLIER
    assert snapshot["content_hash"]
    assert snapshot["request_id"] == _request_id("s3", "1", world.data_owner)

    # --- the operational log agrees with the immutable snapshot -------------
    assert log["snapshot_id"] == snapshot["id"]
    assert log["organization_id"] == world.data_owner
    assert log["scope"] == "Scope 3"
    assert log["scope3_category"] == 1
    assert log["data_quality"] == "primary_supplier"
    assert log["calculated_kg_co2e"] == _QUANTITY * _MULTIPLIER
    assert log["emission_factor_id"] == world.s3_factor.id
    assert log["acting_for_organization_id"] == world.data_owner


async def test_snapshot_and_log_carry_identical_p17_dimensions(
    pool: asyncpg.Pool,
) -> None:
    """The pair is written from ONE dimensions object, so it cannot disagree."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 5))

    snapshot = await _snapshot_row(pool, outcome.result.snapshot.id)
    log = await _log_row(pool, outcome.result.snapshot.id)

    for column in (
        "scope3_category",
        "data_quality",
        "transport_boundary",
        "waste_origin",
        "source_snapshot_id",
        "performed_by_organization_id",
        "acting_for_organization_id",
    ):
        assert snapshot[column] == log[column], f"{column} disagrees across the pair"


# ===========================================================================
# B. Supplier attribution reaches the operational record (IMPLEMENT-09)
# ===========================================================================
async def test_supplier_attribution_is_persisted_on_the_emissions_log(
    pool: asyncpg.Pool,
) -> None:
    """A resolved supplier must survive to ``emissions_logs.supplier_id``.

    Before P17-IMPLEMENT-09 the Scope 3 route accepted ``supplier_id`` and
    dropped it: the claim was silently discarded. This asserts the stored row.
    """
    await _require_p17_schema(pool)
    world = await _world(pool)

    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 5))
    log = await _log_row(pool, outcome.result.snapshot.id)

    assert log["supplier_id"] is not None, "supplier attribution was dropped"
    assert log["supplier_id"] == world.supplier_id

    supplier_org = await pool.fetchval(
        "SELECT organization_id FROM public.suppliers WHERE id = $1",
        world.supplier_id,
    )
    assert str(supplier_org) == world.data_owner


async def test_a_calculation_without_a_supplier_stores_null_never_a_guess(
    pool: asyncpg.Pool,
) -> None:
    """No supplier claimed → NULL. An unresolved supplier is never invented."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    outcome = await _scope3_service(pool).calculate(
        _scope3_input(world, 5, supplier_id=None)
    )
    log = await _log_row(pool, outcome.result.snapshot.id)
    assert log["supplier_id"] is None


# ===========================================================================
# C. All fifteen categories persist their distinct identity
# ===========================================================================
@pytest.mark.parametrize("category", CATEGORIES)
async def test_every_category_persists_its_identity(
    pool: asyncpg.Pool, category: int
) -> None:
    """Every one of the fifteen categories reaches a stored, identified row."""
    await _require_p17_schema(pool)
    world = await _world(pool)

    outcome = await _scope3_service(pool).calculate(_scope3_input(world, category))
    assert outcome.calculated is True, f"category {category} produced no result"

    snapshot = await _snapshot_row(pool, outcome.result.snapshot.id)
    log = await _log_row(pool, outcome.result.snapshot.id)

    assert snapshot["scope3_category"] == category
    assert log["scope3_category"] == category
    assert snapshot["scope"] == "Scope 3"
    assert log["scope"] == "Scope 3"
    assert snapshot["methodology"], "a stored result must name its methodology"
    assert snapshot["data_quality"], "a stored result must carry its data quality"
    assert snapshot["reporting_year"] == _REPORTING_YEAR
    assert snapshot["factor_id"] == world.s3_factor.id

    # Boundary declarations survive to both rows (DC-04 / DC-05 / DC-07).
    fixture = _FIXTURES[category]
    for column in ("transport_boundary", "waste_origin"):
        expected = fixture.get(column)
        assert snapshot[column] == expected, f"{column} not persisted for {category}"
        assert log[column] == expected, f"{column} not persisted on the log {category}"

    # The architecture status is reported verbatim: this file upgrades nothing.
    assert contract_for(category).architecture_status in {
        "SUPPORTED",
        "PARTIAL",
        "DEFERRED",
        "NOT_IMPLEMENTED",
    }


# ===========================================================================
# D. Estimation — an estimate carries a persisted, idempotent record
# ===========================================================================
async def test_estimated_category_persists_an_estimation_record(
    pool: asyncpg.Pool,
) -> None:
    """T-INV-12 against a real database: the estimate's basis is stored, once."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    records = EstimationRecordsRepository(pool)

    outcome = await _scope3_service(pool).calculate(_scope3_input(world, 7))
    assert outcome.calculated is True
    snapshot_id = outcome.result.snapshot.id

    record = replace(
        _estimation(7, world.data_owner),
        calculation_snapshot_id=snapshot_id,
        emissions_log_id=None,
        actor_user_id=new_id(),
        actor_organization_id=world.firm,
        acting_for_organization_id=world.data_owner,
    )
    first = await records.record(record)
    assert first is not None, "the estimation record was not persisted"

    row = await pool.fetchrow(
        "SELECT organization_id, calculation_snapshot_id, estimation_method, "
        "inputs, assumptions, scope3_category, actor_organization_id, "
        "acting_for_organization_id "
        "FROM public.estimation_records WHERE calculation_snapshot_id = $1",
        snapshot_id,
    )
    assert row is not None
    row = _norm(row)
    assert row["organization_id"] == world.data_owner
    assert row["estimation_method"] == "average_data"
    assert row["scope3_category"] == 7
    assert row["inputs"], "an estimation record must record its inputs"
    assert row["assumptions"], "an estimation record must record its assumptions"
    assert row["actor_organization_id"] == world.firm
    assert row["acting_for_organization_id"] == world.data_owner

    # Idempotent: the database allows ONE substantiating record per calculation
    # (``uq_estimation_records_snapshot``), so a retry cannot double the evidence.
    second = await records.record(record)
    assert second is None, "a second estimation record was written for one result"
    count = await pool.fetchval(
        "SELECT count(*) FROM public.estimation_records WHERE calculation_snapshot_id = $1",
        snapshot_id,
    )
    assert count == 1
    assert len(await records.list_for_snapshot(snapshot_id)) == 1


async def test_an_estimated_result_without_an_estimation_record_is_refused(
    pool: asyncpg.Pool,
) -> None:
    """No fabricated estimate: a missing basis is refused, not written."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    before = await pool.fetchval("SELECT count(*) FROM public.calculation_snapshots")

    with pytest.raises(EstimationRecordRequiredError):
        await _scope3_service(pool).calculate(
            _scope3_input(world, 11, estimation=None)
        )

    after = await pool.fetchval("SELECT count(*) FROM public.calculation_snapshots")
    assert after == before, "a refused estimate left a row behind"


# ===========================================================================
# E. Boundary / double-counting controls
# ===========================================================================
async def test_a_missing_boundary_declaration_yields_a_clarification(
    pool: asyncpg.Pool,
) -> None:
    """DC-04 / DC-05 / DC-07 / DC-02: an unstated boundary is never assumed."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    service = _scope3_service(pool)
    before = await pool.fetchval("SELECT count(*) FROM public.calculation_snapshots")

    cases = (
        (4, {"transport_boundary": None}, "transport_boundary"),
        (5, {"waste_origin": None}, "waste_origin"),
        (8, {"consolidation_approach": None}, "consolidation_approach"),
        (3, {"source_snapshot_id": None}, "source_snapshot_id"),
        (13, {"consolidation_approach": None}, "consolidation_approach"),
    )
    for category, overrides, field in cases:
        outcome = await service.calculate(_scope3_input(world, category, **overrides))
        assert outcome.calculated is False, f"category {category} was calculated"
        assert outcome.clarification is not None
        assert field in outcome.clarification.missing_fields
        assert outcome.clarification.missing_fields

    after = await pool.fetchval("SELECT count(*) FROM public.calculation_snapshots")
    assert after == before, "a clarified (refused) request persisted a result"


async def test_a_contradictory_boundary_is_refused_by_the_domain_guard(
    pool: asyncpg.Pool,
) -> None:
    """A downstream boundary cannot be attached to category 4."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    with pytest.raises(BoundaryAmbiguityError):
        await _scope3_service(pool).calculate(
            _scope3_input(world, 4, transport_boundary="downstream")
        )


async def test_the_database_itself_refuses_a_boundary_on_the_wrong_category(
    pool: asyncpg.Pool,
) -> None:
    """The P17 CHECK guard holds even for a write that bypasses the service.

    ``calc_snapshots_transport_boundary_scope_check`` is NOT VALID (historical rows
    are exempt) but every NEW row is enforced — proven here by writing directly.
    """
    await _require_p17_schema(pool)
    world = await _world(pool)
    with pytest.raises(asyncpg.exceptions.CheckViolationError):
        await pool.execute(
            """
            INSERT INTO public.calculation_snapshots (
                organization_id, activity, activity_type, quantity, quantity_unit,
                co2e_multiplier, co2e_kg, date, reporting_year, methodology,
                algorithm_version, content_hash, scope3_category, transport_boundary
            ) VALUES ($1, 'raw', 'raw', 1, 'kg', 1, 1, $2, $3,
                      'direct_multiply', 'v1', 'raw-hash', 5, 'upstream')
            """,
            world.data_owner,
            _CALC_DATE,
            _REPORTING_YEAR,
        )


async def test_category_3_derivation_is_unique_per_source_snapshot(
    pool: asyncpg.Pool,
) -> None:
    """DC-02: one Scope 1/2 source can be derived into category 3 exactly once.

    ``uq_calc_snapshots_cat3_source`` is a partial unique index, so a second
    derivation from the same source snapshot is refused by PostgreSQL itself —
    the double-counting control is structural, not a UI warning.
    """
    await _require_p17_schema(pool)
    world = await _world(pool)

    source = await _scope2_service(pool).calculate(_scope2_input(world))
    source_id = source.snapshot.id

    first = await _scope3_service(pool).calculate(
        _scope3_input(world, 3, source_snapshot_id=source_id)
    )
    assert first.calculated is True
    snapshot = await _snapshot_row(pool, first.result.snapshot.id)
    assert snapshot["source_snapshot_id"] == source_id
    assert snapshot["scope3_category"] == 3

    with pytest.raises(asyncpg.exceptions.UniqueViolationError):
        await _scope3_service(pool).calculate(
            _scope3_input(
                world,
                3,
                source_snapshot_id=source_id,
                match=_match(
                    world.s3_factor, _request_id("s3", "3-second", world.data_owner)
                ),
            )
        )

    derived = await pool.fetchval(
        "SELECT count(*) FROM public.calculation_snapshots "
        "WHERE scope3_category = 3 AND source_snapshot_id = $1",
        source_id,
    )
    assert derived == 1


# ===========================================================================
# F. Idempotency — the request id is the idempotency key
# ===========================================================================
async def test_a_repeated_request_cannot_create_a_second_result(
    pool: asyncpg.Pool,
) -> None:
    """The unique request-id index refuses a duplicate; nothing is doubled."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    service = _scope3_service(pool)
    request = _scope3_input(world, 2)

    first = await service.calculate(request)
    assert first.calculated is True
    request_id = _request_id("s3", "2", world.data_owner)

    # The canonical lookup resolves the already-persisted result.
    found = await EmissionsLogsRepository(pool).find_snapshot_by_request_id(request_id)
    assert found is not None
    assert str(found["id"]) == first.result.snapshot.id

    with pytest.raises(asyncpg.exceptions.UniqueViolationError):
        await service.calculate(request)

    rows = await pool.fetchval(
        "SELECT count(*) FROM public.calculation_snapshots WHERE request_id = $1",
        request_id,
    )
    assert rows == 1, "the idempotency key no longer prevents a duplicate result"
    logs = await pool.fetchval(
        "SELECT count(*) FROM public.emissions_logs WHERE snapshot_id = $1",
        first.result.snapshot.id,
    )
    assert logs == 1


# ===========================================================================
# G. Tenant isolation — one organisation cannot see another's results
# ===========================================================================
async def test_two_organisations_do_not_see_each_others_results(
    pool: asyncpg.Pool,
) -> None:
    """The persisted owner is the calculation's own organisation, never a claim."""
    await _require_p17_schema(pool)
    first = await _world(pool)
    second = await _world(pool)
    service = _scope3_service(pool)

    a = await service.calculate(_scope3_input(first, 1))
    b = await service.calculate(_scope3_input(second, 6))

    a_snapshot = await _snapshot_row(pool, a.result.snapshot.id)
    b_snapshot = await _snapshot_row(pool, b.result.snapshot.id)
    assert a_snapshot["organization_id"] == first.data_owner
    assert b_snapshot["organization_id"] == second.data_owner
    assert a_snapshot["organization_id"] != b_snapshot["organization_id"]

    repository = EmissionsLogsRepository(pool)
    period = DateRange(date(2025, 1, 1), date(2025, 12, 31))
    a_logs = await repository.find_by_org(first.data_owner, period)
    b_logs = await repository.find_by_org(second.data_owner, period)

    a_ids = {log.id for log in a_logs}
    b_ids = {log.id for log in b_logs}
    assert a_ids and b_ids
    assert a_ids.isdisjoint(b_ids), "a log leaked across the tenant boundary"
    assert all(log.organization_id == first.data_owner for log in a_logs)
    assert all(log.organization_id == second.data_owner for log in b_logs)


# ===========================================================================
# H. Scope 2 — location-based, all four energy types
# ===========================================================================
@pytest.mark.parametrize("energy_type", ("electricity", "heat", "steam", "cooling"))
async def test_scope2_location_based_persists_method_and_energy_type(
    pool: asyncpg.Pool, energy_type: str
) -> None:
    """Scope 2 location-based: method and energy type are stored, not inferred."""
    await _require_p17_schema(pool)
    world = await _world(pool)

    result = await _scope2_service(pool).calculate(
        _scope2_input(world, method="LOCATION_BASED", energy_type=energy_type)
    )
    snapshot = await _snapshot_row(pool, result.snapshot.id)
    log = await _log_row(pool, result.snapshot.id)

    assert snapshot["scope"] == "Scope 2"
    assert snapshot["scope2_method"] == "LOCATION_BASED"
    assert snapshot["energy_type"] == energy_type
    assert snapshot["scope3_category"] is None
    assert snapshot["data_quality"] == "primary_measured"
    assert snapshot["reporting_year"] == _REPORTING_YEAR
    assert snapshot["factor_id"] == world.s2_factor.id
    assert snapshot["acting_for_organization_id"] == world.data_owner
    assert snapshot["performed_by_organization_id"] == world.firm
    # ``fuel`` is not a Scope 2 energy type; the stored value is one of the four.
    assert snapshot["energy_type"] in ("electricity", "heat", "steam", "cooling")

    assert log["scope2_method"] == "LOCATION_BASED"
    assert log["energy_type"] == energy_type
    assert log["supplier_id"] == world.supplier_id


async def test_scope2_refuses_fuel_and_a_scope3_factor(pool: asyncpg.Pool) -> None:
    """A wrong energy type and a wrong-scope factor both fail closed."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    service = _scope2_service(pool)
    before = await pool.fetchval("SELECT count(*) FROM public.calculation_snapshots")

    with pytest.raises(AccountingDimensionError):
        await service.calculate(_scope2_input(world, energy_type="fuel"))

    with pytest.raises(AccountingDimensionError):
        await service.calculate(
            _scope2_input(
                world,
                match=_match(
                    world.s3_factor, _request_id("s2-wrong-scope", world.data_owner)
                ),
            )
        )

    after = await pool.fetchval("SELECT count(*) FROM public.calculation_snapshots")
    assert after == before, "a refused Scope 2 claim persisted a result"


# ===========================================================================
# I. Scope 2 — market-based with a contractual instrument and its allocation
# ===========================================================================
async def test_scope2_market_based_persists_the_instrument_allocation(
    pool: asyncpg.Pool,
) -> None:
    """Consumption + eligible instrument + allocation = a stored market claim."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    instruments = ContractualInstrumentsRepository(pool)

    instrument = ContractualInstrument(
        id=new_id(),
        organization_id=world.data_owner,
        instrument_type="guarantee_of_origin",
        identifier=f"GO-{world.data_owner[:8]}",
        geography=_GEOGRAPHY,
        quantity=Decimal("12500"),
        unit=_S2_UNIT,
        vintage_year=_REPORTING_YEAR,
        retirement_status="active",
        issuer="P17-09 Test Registry",
        valid_from=date(2025, 1, 1),
        valid_to=date(2025, 12, 31),
    )
    stored = await instruments.save(instrument)
    assert stored.id == instrument.id

    result = await _scope2_service(pool).calculate(
        _scope2_input(
            world,
            method="MARKET_BASED",
            instrument=stored,
            allocated_quantity=Decimal("12500"),
        )
    )
    snapshot = await _snapshot_row(pool, result.snapshot.id)
    assert snapshot["scope2_method"] == "MARKET_BASED"
    assert snapshot["energy_type"] == "electricity"
    assert snapshot["scope3_category"] is None

    # Record the claim exactly as the route does: only after the snapshot exists.
    allocation_id = await instruments.record_allocation(
        InstrumentAllocation(
            organization_id=world.data_owner,
            instrument_id=stored.id,
            allocated_quantity=Decimal("12500"),
            allocated_unit=_S2_UNIT,
            allocation_period_start=_CALC_DATE,
            allocation_period_end=_CALC_DATE,
            calculation_snapshot_id=result.snapshot.id,
            claim_reference=f"p17-09:{result.snapshot.match_request_id}",
        )
    )
    assert allocation_id is not None

    row = await pool.fetchrow(
        "SELECT instrument_id, allocated_quantity, allocated_unit, "
        "calculation_snapshot_id FROM public.instrument_allocations WHERE id = $1",
        allocation_id,
    )
    assert str(row["instrument_id"]) == stored.id
    assert row["allocated_quantity"] == Decimal("12500")
    assert row["allocated_unit"] == _S2_UNIT
    assert str(row["calculation_snapshot_id"]) == result.snapshot.id

    # DC-09 — the instrument is fully allocated, and the detector agrees.
    over = await pool.fetchval(
        "SELECT public.p17_instrument_over_allocated($1)", stored.id
    )
    assert over is False, "a fully-allocated instrument was reported as over-allocated"

    existing = await instruments.list_allocations(stored.id, world.data_owner)
    assert len(existing) == 1
    with pytest.raises(InstrumentOverAllocatedError):
        assert_allocation_within_quantity(
            instrument=stored,
            existing=existing,
            new_quantity=Decimal("1"),
            unit=_S2_UNIT,
        )


async def test_scope2_market_based_refuses_an_ineligible_instrument(
    pool: asyncpg.Pool,
) -> None:
    """A retired instrument has already been claimed; it cannot back a new claim."""
    await _require_p17_schema(pool)
    world = await _world(pool)
    retired = ContractualInstrument(
        id=new_id(),
        organization_id=world.data_owner,
        instrument_type="guarantee_of_origin",
        identifier=f"GO-RETIRED-{world.data_owner[:8]}",
        geography=_GEOGRAPHY,
        quantity=Decimal("12500"),
        unit=_S2_UNIT,
        vintage_year=_REPORTING_YEAR,
        retirement_status="retired",
        issuer="P17-09 Test Registry",
    )
    before = await pool.fetchval("SELECT count(*) FROM public.calculation_snapshots")
    with pytest.raises(InstrumentEligibilityError):
        await _scope2_service(pool).calculate(
            _scope2_input(
                world,
                method="MARKET_BASED",
                instrument=retired,
                allocated_quantity=Decimal("12500"),
            )
        )
    after = await pool.fetchval("SELECT count(*) FROM public.calculation_snapshots")
    assert after == before
