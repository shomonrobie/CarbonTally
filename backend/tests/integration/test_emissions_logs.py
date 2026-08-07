"""Integration tests for EmissionsLogsRepository."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import asyncpg
import pytest

from core.types import DateRange
from data.emission_factors import EmissionFactorsRepository
from data.emissions_logs import EmissionsLogsRepository
from domain.factor import EmissionFactor
from tests.integration.conftest import make_org, make_snapshot, new_id

pytestmark = pytest.mark.asyncio


async def _seed_factor(pool: asyncpg.Pool, activity: str | None = None) -> EmissionFactor:
    """Save one factor with a unique natural key so concurrent tests never
    upsert over each other's row (the RC2 natural-key unique index treats
    ``(year, activity_type, country, unit, scope)`` as the identity)."""
    factor = EmissionFactor(
        id=new_id(),
        reporting_year=2025,
        activity_type=activity or f"Logs > Electricity {new_id()[:8]}",
        co2e_multiplier=Decimal("0.20000"),
        unit="kWh",
        scope="Scope 2",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
    )
    await EmissionFactorsRepository(pool).save(factor)
    return factor


async def test_create_and_get_round_trip(pool: asyncpg.Pool) -> None:
    repo = EmissionsLogsRepository(pool)
    org_id = await make_org(pool)
    factor = await _seed_factor(pool)
    snapshot_id = await make_snapshot(pool, org_id, factor.id)
    log = await repo.create(
        org_id=org_id,
        factor_id=factor.id,
        quantity=Decimal("100.00"),
        unit="kWh",
        scope="Scope 2",
        date=date(2025, 6, 1),
        asset_id=None,
        facility_id="facility-abc",
        snapshot_id=snapshot_id,
    )
    assert log.id
    assert log.quantity == Decimal("100.00")
    assert log.date == date(2025, 6, 1)
    assert log.facility_id == "facility-abc"
    assert log.calculated_kg_co2e == Decimal("0")

    fetched = await repo.get(log.id)
    assert fetched is not None
    assert fetched.factor_id == factor.id
    assert fetched.snapshot_id == snapshot_id
    assert fetched.facility_id == "facility-abc"


async def test_save_updates_calculated_value(pool: asyncpg.Pool) -> None:
    repo = EmissionsLogsRepository(pool)
    org_id = await make_org(pool)
    factor = await _seed_factor(pool)
    snapshot_id = await make_snapshot(pool, org_id, factor.id)
    log = await repo.create(
        org_id=org_id,
        factor_id=factor.id,
        quantity=Decimal("10.00"),
        unit="kWh",
        scope="Scope 2",
        date=date(2025, 6, 1),
        asset_id=None,
        facility_id=None,
        snapshot_id=snapshot_id,
    )
    from dataclasses import replace

    computed = replace(log, calculated_kg_co2e=Decimal("2.000000"))
    saved = await repo.save(computed)
    assert saved.calculated_kg_co2e == Decimal("2.000000")


async def test_find_by_org_period_filter(pool: asyncpg.Pool) -> None:
    repo = EmissionsLogsRepository(pool)
    org_id = await make_org(pool)
    factor = await _seed_factor(pool)
    snapshot_id = await make_snapshot(pool, org_id, factor.id)
    await repo.create(
        org_id=org_id, factor_id=factor.id, quantity=Decimal("1"),
        unit="kWh", scope="Scope 2", date=date(2025, 1, 15),
        asset_id=None, facility_id=None, snapshot_id=snapshot_id,
    )
    await repo.create(
        org_id=org_id, factor_id=factor.id, quantity=Decimal("2"),
        unit="kWh", scope="Scope 2", date=date(2025, 12, 15),
        asset_id=None, facility_id=None, snapshot_id=snapshot_id,
    )
    in_range = await repo.find_by_org(
        org_id, DateRange(date(2025, 6, 1), date(2025, 12, 31))
    )
    assert len(in_range) == 1
    assert in_range[0].date == date(2025, 12, 15)


async def test_aggregate_and_count_by_scope(pool: asyncpg.Pool) -> None:
    repo = EmissionsLogsRepository(pool)
    org_id = await make_org(pool)
    factor = await _seed_factor(pool)
    snapshot_id = await make_snapshot(pool, org_id, factor.id)
    for day, qty, scope in (
        (1, "10.00", "Scope 2"),
        (2, "20.00", "Scope 2"),
        (3, "30.00", "Scope 1"),
    ):
        await repo.create(
            org_id=org_id, factor_id=factor.id, quantity=Decimal(qty),
            unit="kWh", scope=scope, date=date(2025, 2, day),
            asset_id=None, facility_id=None, snapshot_id=snapshot_id,
        )
        # set calculated values via save so aggregation sees non-zero sums
    logs = await repo.find_by_org(
        org_id, DateRange(date(2025, 1, 1), date(2025, 12, 31))
    )
    from dataclasses import replace

    for idx, log in enumerate(logs):
        await repo.save(replace(log, calculated_kg_co2e=Decimal(f"{idx + 1}.000000")))

    agg = await repo.aggregate(
        org_id, DateRange(date(2025, 1, 1), date(2025, 12, 31)), "scope"
    )
    assert agg.total_rows == 3
    assert agg.total_co2e_kg == Decimal("6.000000")
    assert agg.by_scope["Scope 1"] == Decimal("3.000000")
    assert agg.by_scope["Scope 2"] == Decimal("3.000000")
    assert agg.group_by == "scope"

    counts = await repo.count_by_scope(org_id, 2025)
    assert counts["Scope 1"] == 1
    assert counts["Scope 2"] == 2
