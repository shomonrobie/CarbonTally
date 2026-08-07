"""Integration tests for ImportsRepository."""
from __future__ import annotations

import asyncpg
import pytest

from data.imports import ImportsRepository
from domain.provider import ImportError
from tests.integration.conftest import new_id

pytestmark = pytest.mark.asyncio


async def test_create_batch_round_trip(pool: asyncpg.Pool) -> None:
    repo = ImportsRepository(pool)
    created_by = new_id()
    batch = await repo.create_batch(
        provider="defra",
        version="2025.1",
        year=2025,
        source="defra-2025.xlsx",
        checksum="a" * 64,
        created_by=created_by,
    )
    assert batch.status == "pending"
    assert batch.provider_key == "defra"
    assert batch.reporting_year == 2025
    assert not batch.is_active
    fetched = await repo.get(batch.id)
    assert fetched is not None
    assert fetched.id == batch.id
    assert fetched.source_checksum == "a" * 64


async def test_complete_and_fail_batch(pool: asyncpg.Pool) -> None:
    repo = ImportsRepository(pool)
    batch = await repo.create_batch(
        provider="defra", version="2025.1", year=2025,
        source="x.xlsx", checksum="b" * 64, created_by=new_id(),
    )
    completed = await repo.complete_batch(
        batch.id, total=10, imported=8, skipped=1, duplicates=1,
        errors=[ImportError(row_number=3, field="unit", message="missing", severity="error")],
    )
    assert completed.status == "completed"
    assert completed.rows_imported == 8
    assert completed.rows_total == 10
    assert len(completed.errors) == 1
    assert completed.errors[0].field == "unit"

    failed = await repo.fail_batch(
        batch.id, errors=[ImportError(row_number=1, field="sheet", message="bad", severity="error")]
    )
    assert failed.status == "failed"
    assert failed.is_active is False


async def test_activation_single_active_invariant(pool: asyncpg.Pool) -> None:
    repo = ImportsRepository(pool)
    created_by = new_id()
    first = await repo.create_batch(
        provider="defra", version="2024.1", year=2024,
        source="a.xlsx", checksum="c" * 64, created_by=created_by,
    )
    second = await repo.create_batch(
        provider="defra", version="2024.2", year=2024,
        source="b.xlsx", checksum="d" * 64, created_by=created_by,
    )
    await repo.activate_batch(first.id)
    await repo.activate_batch(second.id)

    active = await repo.get_active("defra", 2024)
    assert active is not None
    assert active.id == second.id
    # the first batch is no longer active
    first_after = await repo.get(first.id)
    assert first_after is not None
    assert not first_after.is_active


async def test_rollback_and_history(pool: asyncpg.Pool) -> None:
    repo = ImportsRepository(pool)
    created_by = new_id()
    first = await repo.create_batch(
        provider="epa", version="2023", year=2023,
        source="a.xlsx", checksum="e" * 64, created_by=created_by,
    )
    replacement = await repo.create_batch(
        provider="epa", version="2023.1", year=2023,
        source="b.xlsx", checksum="f" * 64, created_by=created_by,
    )
    rolled = await repo.rollback_batch(first.id, replacement.id)
    assert rolled.status == "rolled_back"
    assert not rolled.is_active
    assert rolled.rolled_back_from == replacement.id

    history = await repo.get_history("epa")
    ids = [b.id for b in history]
    assert first.id in ids and replacement.id in ids


async def test_deactivate_batch(pool: asyncpg.Pool) -> None:
    repo = ImportsRepository(pool)
    batch = await repo.create_batch(
        provider="ipcc", version="2022", year=2022,
        source="a.xlsx", checksum="g" * 64, created_by=new_id(),
    )
    await repo.activate_batch(batch.id)
    deactivated = await repo.deactivate_batch(batch.id)
    assert not deactivated.is_active
    assert await repo.get_active("ipcc", 2022) is None


async def test_save_updates_batch_fields(pool: asyncpg.Pool) -> None:
    repo = ImportsRepository(pool)
    batch = await repo.create_batch(
        provider="ademe", version="2022", year=2022,
        source="a.xlsx", checksum="h" * 64, created_by=new_id(),
    )
    changed = batch  # immutable; construct the updated state explicitly
    from dataclasses import replace

    updated = replace(changed, status="importing")
    saved = await repo.save(updated)
    assert saved.status == "importing"
    fetched = await repo.get(batch.id)
    assert fetched is not None
    assert fetched.status == "importing"
