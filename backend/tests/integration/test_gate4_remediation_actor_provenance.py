"""WS4 Gate 4 remediation F1/F2 — real-DB persistence regression.

Runs against the dedicated integration-test database (never the main app
database — see ``tests/integration/conftest.py``). Proves, at the repository/
engine layer over real PostgreSQL rows:

* ``calculation_snapshots.performed_by`` stores the actual human actor id (never
  the organisation id), which is the F1 calculation-evidence fix;
* ``calculation_snapshots.source_item_id`` persists the originating work item
  (F2) for both PE- and internal-style calculation requests;
* automatic runs (no actor supplied) keep ``performed_by = NULL`` — machine
  provenance remains out of scope and no snapshot semantics change.

The additive migration file is applied idempotently at module scope so this
suite is self-contained against a freshly restored test database.
"""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import asyncpg
import pytest

from data.emission_factors import EmissionFactorsRepository
from data.emissions_logs import EmissionsLogsRepository
from data.manual_extraction import ManualExtractionRepository
from domain.factor import EmissionFactor
from engines.calculation import CalculationEngine, CalculationRequest
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio

_MIGRATION_PATH = Path(__file__).resolve().parents[3] / "supabase" / "migrations" / (
    "20260905000000_gate4_actor_provenance.sql"
)
_ACTIVITY = "Fuels > Gas fuels > Natural gas G4R (kg CO2e) [kWh]"
_MULTIPLIER = Decimal("0.18400")


async def _seed_factor(pool: asyncpg.Pool) -> EmissionFactor:
    repo = EmissionFactorsRepository(pool)
    factor = EmissionFactor(
        id=new_id(),
        reporting_year=2025,
        activity_type=_ACTIVITY,
        co2e_multiplier=_MULTIPLIER,
        unit="kWh",
        scope="Scope 1",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
    )
    return await repo.save(factor)


@pytest.fixture(autouse=True, scope="module")
async def _ensure_migration(pool: asyncpg.Pool) -> None:
    """Apply the additive remediation migration to the test database once."""
    async with pool.acquire() as conn:
        await conn.execute(_MIGRATION_PATH.read_text())


async def _cleanup(pool, snapshot_ids, *, factor_id, org_id, item_id, batch_id):
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM public.emissions_logs WHERE snapshot_id = ANY($1::uuid[])",
            snapshot_ids,
        )
        await conn.execute(
            "DELETE FROM public.calculation_snapshots WHERE id = ANY($1::uuid[])",
            snapshot_ids,
        )
        await conn.execute(
            "DELETE FROM public.manual_extraction_items WHERE id = $1", item_id
        )
        await conn.execute(
            "DELETE FROM public.manual_extraction_batches WHERE id = $1", batch_id
        )
    await EmissionFactorsRepository(pool).delete(factor_id)
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM public.organizations WHERE id = $1", org_id)


async def test_engine_persists_actor_and_source_item_link(pool: asyncpg.Pool) -> None:
    org_id = await make_org(pool)
    factor = await _seed_factor(pool)

    manual = ManualExtractionRepository(pool)
    batch = await manual.create_batch(
        org_id, "G4R Batch", 1, 1, 0.0, "GBP", None, None, created_by=None
    )
    item = await manual.create_item(
        batch.id, "g4r-source.csv", "storage/docs/g4r-source.csv",
        1, "invoice", "pending",
    )

    actor_id = new_id()  # human/PE actor uuid (test DB has no auth.users FK)
    logs_repo = EmissionsLogsRepository(pool)
    engine = CalculationEngine(logs_repo)

    # --- human actor + source-item link (both origins share this contract) ---
    request = CalculationRequest(
        match_request_id=new_id(),
        organization_id=org_id,
        factor=factor,
        quantity=Decimal("100"),
        quantity_unit="kWh",
        date=date(2025, 6, 1),
        reporting_year=2025,
        activity="Natural gas",
        activity_type=_ACTIVITY,
        scope="Scope 1",
        source_item_id=item.id,
        performed_by=actor_id,
    )
    result = await engine.calculate(request)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT performed_by, calculated_by, source_item_id, co2e_kg "
            "FROM public.calculation_snapshots WHERE id = $1",
            result.snapshot.id,
        )
    assert row is not None
    assert str(row["performed_by"]) == actor_id  # F1: human actor, not the org
    assert row["performed_by"] is not None
    assert str(row["performed_by"]) != org_id
    assert str(row["source_item_id"]) == item.id  # F2: item -> snapshot link
    assert Decimal(str(row["co2e_kg"])) == Decimal("18.400000")

    # --- automatic run (no human actor) keeps performed_by NULL ---
    auto_request = CalculationRequest(
        match_request_id=new_id(),
        organization_id=org_id,
        factor=factor,
        quantity=Decimal("100"),
        quantity_unit="kWh",
        date=date(2025, 6, 1),
        reporting_year=2025,
        activity="Natural gas",
        activity_type=_ACTIVITY,
        scope="Scope 1",
        source_item_id=item.id,
    )
    auto_result = await engine.calculate(auto_request)
    async with pool.acquire() as conn:
        auto_row = await conn.fetchrow(
            "SELECT performed_by, source_item_id FROM public.calculation_snapshots WHERE id = $1",
            auto_result.snapshot.id,
        )
    assert auto_row["performed_by"] is None
    assert str(auto_row["source_item_id"]) == item.id

    await _cleanup(
        pool,
        [result.snapshot.id, auto_result.snapshot.id],
        factor_id=factor.id,
        org_id=org_id,
        item_id=item.id,
        batch_id=batch.id,
    )
