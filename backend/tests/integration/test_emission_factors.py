"""Integration tests for EmissionFactorsRepository."""
from __future__ import annotations

from decimal import Decimal

import asyncpg
import pytest

from data.emission_factors import EmissionFactorsRepository
from data.imports import ImportsRepository
from domain.factor import EmissionFactor
from tests.integration.conftest import new_id

pytestmark = pytest.mark.asyncio


def _factor(
    activity_type: str = "Fuels > Liquid fuels > Diesel (net CV)",
    multiplier: str = "2.52000",
    unit: str | None = "litres",
    scope: str | None = "Scope 1",
    batch_id: str | None = None,
    **kwargs: object,
) -> EmissionFactor:
    year = kwargs.get("reporting_year", 2025)
    return EmissionFactor(
        id=str(kwargs.get("id") or new_id()),
        reporting_year=int(year) if isinstance(year, int) else int(str(year)),
        activity_type=activity_type,
        co2e_multiplier=Decimal(multiplier),
        unit=unit,
        scope=scope,
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
        import_batch_id=batch_id,
    )


async def _repo(pool: asyncpg.Pool) -> EmissionFactorsRepository:
    return EmissionFactorsRepository(pool)


async def test_save_and_get_round_trip(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    factor = _factor()
    saved = await repo.save(factor)
    assert saved.id == factor.id
    fetched = await repo.get(factor.id)
    assert fetched is not None
    assert fetched.activity_type == factor.activity_type
    assert fetched.co2e_multiplier == factor.co2e_multiplier
    assert fetched.unit == "litres"
    assert fetched.scope == "Scope 1"
    assert fetched.country == "GB"
    assert fetched.natural_key == (
        "2025",
        factor.activity_type,
        "GB",
        "litres",
        "Scope 1",
    )


async def test_get_missing_returns_none(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    assert await repo.get(new_id()) is None


async def test_save_updates_existing_by_natural_key(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    activity = f"Fuels > Upsert {new_id()[:8]}"
    factor = _factor(activity_type=activity)
    await repo.save(factor)
    updated = _factor(
        activity_type=activity,
        multiplier="3.00000",
        batch_id=factor.import_batch_id,
    )
    await repo.save(updated)
    fetched = await repo.get(factor.id)
    assert fetched is not None
    assert fetched.co2e_multiplier == Decimal("3.00000")


async def test_find_by_natural_key_exact(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    factor = _factor(
        activity_type="Fuels > Diesel (exact lookup)", unit="litres", scope="Scope 1"
    )
    await repo.save(factor)
    found = await repo.find_by_natural_key(
        2025, factor.activity_type, "GB", "litres", "Scope 1"
    )
    assert found is not None
    assert found.id == factor.id


async def test_find_by_natural_key_null_unit_scope(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    factor = _factor(unit=None, scope=None)
    await repo.save(factor)
    found = await repo.find_by_natural_key(
        2025, factor.activity_type, "GB", None, None
    )
    assert found is not None
    assert found.unit is None
    assert found.scope is None


async def test_find_by_activity_keyword_and_filters(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    diesel = _factor(activity_type="Fuels > Diesel engine > Diesel", unit="litres")
    petrol = _factor(activity_type="Fuels > Petrol engine > Petrol", unit="litres")
    await repo.save(diesel)
    await repo.save(petrol)

    results = await repo.find_by_activity("diesel")
    ids = {r.id for r in results}
    assert diesel.id in ids
    assert petrol.id not in ids

    narrowed = await repo.find_by_activity("fuel", year=2025, country="GB")
    assert {r.id for r in narrowed} >= {diesel.id, petrol.id}

    none = await repo.find_by_activity("diesel", unit="m3")
    assert none == []


async def test_bulk_upsert_counts_and_idempotency(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    factors = [_factor(activity_type=f"Bulk > Item {i}") for i in range(3)]
    inserted = await repo.bulk_upsert(factors)
    assert inserted == 3

    # Re-upserting the same natural keys updates but inserts nothing.
    changed = [
        EmissionFactor(
            id=f.id,
            reporting_year=f.reporting_year,
            activity_type=f.activity_type,
            co2e_multiplier=Decimal("9.99999"),
            unit=f.unit,
            scope=f.scope,
            factor_source=f.factor_source,
            factor_set=f.factor_set,
            country=f.country,
            provider_key=f.provider_key,
            import_batch_id=f.import_batch_id,
        )
        for f in factors
    ]
    inserted_again = await repo.bulk_upsert(changed)
    assert inserted_again == 0
    fetched = await repo.get(factors[0].id)
    assert fetched is not None
    assert fetched.co2e_multiplier == Decimal("9.99999")


async def test_get_active_set_and_deactivate_by_batch(pool: asyncpg.Pool) -> None:
    factors_repo = await _repo(pool)
    batches_repo = ImportsRepository(pool)

    created_by = new_id()
    batch = await batches_repo.create_batch(
        provider="defra", version="2025.1", year=2025,
        source="defra-2025.xlsx", checksum="a" * 64, created_by=created_by,
    )
    await batches_repo.activate_batch(batch.id)

    active = _factor(
        activity_type="Active > Electricity", batch_id=batch.id, scope="Scope 2"
    )
    await factors_repo.save(active)

    stale_batch = await batches_repo.create_batch(
        provider="defra", version="2024.1", year=2024,
        source="defra-2024.xlsx", checksum="b" * 64, created_by=created_by,
    )
    stale = _factor(
        activity_type="Stale > Gas", batch_id=stale_batch.id, scope="Scope 1"
    )
    await factors_repo.save(stale)

    active_set = await factors_repo.get_active_set("defra", 2025)
    assert {f.id for f in active_set} == {active.id}

    detached = await factors_repo.deactivate_by_batch(batch.id)
    assert detached == 1
    assert await factors_repo.get_active_set("defra", 2025) == []


async def test_count_by_provider(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    batches = ImportsRepository(pool)
    created_by = new_id()
    batch = await batches.create_batch(
        provider="seai", version="2024", year=2024,
        source="seai.xlsx", checksum="c" * 64, created_by=created_by,
    )
    for i in range(2):
        await repo.save(
            _factor(
                activity_type=f"SEAI > Item {i}", batch_id=batch.id,
                country="IE",
            )
        )
    count = await repo.count_by_provider("seai")
    assert count == 2


async def test_load_all_for_index(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    f1 = _factor(activity_type="Index > One")
    f2 = _factor(activity_type="Index > Two")
    await repo.save(f1)
    await repo.save(f2)
    all_factors = await repo.load_all_for_index()
    ids = {f.id for f in all_factors}
    assert f1.id in ids and f2.id in ids


async def test_delete(pool: asyncpg.Pool) -> None:
    repo = await _repo(pool)
    factor = _factor(activity_type="Delete > Me")
    await repo.save(factor)
    await repo.delete(factor.id)
    assert await repo.get(factor.id) is None
