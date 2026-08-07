"""Integration tests for EventsRepository."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import asyncpg
import pytest

from data.events import EventsRepository
from domain.workflow import (
    CalculationCompleted,
    DocumentUploaded,
    ImportStarted,
    ValidationFailed,
)
from tests.integration.conftest import new_id

pytestmark = pytest.mark.asyncio


async def test_store_and_reconstruct_typed_event(pool: asyncpg.Pool) -> None:
    repo = EventsRepository(pool)
    document_id = new_id()
    correlation = new_id()
    event = DocumentUploaded(
        event_id=new_id(),
        occurred_at=datetime.now(),
        correlation_id=correlation,
        document_id=document_id,
        organization_id=new_id(),
        storage_path="uploads/invoice.pdf",
    )
    stored = await repo.store(event)
    assert stored.event_id
    fetched = await repo.get(stored.event_id)
    assert isinstance(fetched, DocumentUploaded)
    assert fetched.document_id == document_id
    assert fetched.storage_path == "uploads/invoice.pdf"
    assert fetched.aggregate_id == document_id
    assert fetched.aggregate_type == "document"


async def test_decimal_event_round_trip(pool: asyncpg.Pool) -> None:
    repo = EventsRepository(pool)
    snapshot_id = new_id()
    event = CalculationCompleted(
        event_id=new_id(),
        occurred_at=datetime.now(),
        correlation_id=new_id(),
        snapshot_id=snapshot_id,
        co2e_kg=Decimal("12.340000"),
    )
    stored = await repo.store(event)
    fetched = await repo.get(stored.event_id)
    assert isinstance(fetched, CalculationCompleted)
    assert fetched.co2e_kg == Decimal("12.340000")


async def test_tuple_field_event_round_trip(pool: asyncpg.Pool) -> None:
    repo = EventsRepository(pool)
    event = ValidationFailed(
        event_id=new_id(),
        occurred_at=datetime.now(),
        correlation_id=new_id(),
        entity_type="document",
        entity_id=new_id(),
        errors=("bad", "worse"),
    )
    stored = await repo.store(event)
    fetched = await repo.get(stored.event_id)
    assert isinstance(fetched, ValidationFailed)
    assert fetched.errors == ("bad", "worse")


async def test_get_by_correlation_and_replay(pool: asyncpg.Pool) -> None:
    repo = EventsRepository(pool)
    correlation = new_id()
    batch_id = new_id()
    e1 = await repo.store(
        ImportStarted(
            event_id=new_id(), occurred_at=datetime.now(),
            correlation_id=correlation, batch_id=batch_id, provider_key="defra",
        )
    )
    e2 = await repo.store(
        ImportStarted(
            event_id=new_id(), occurred_at=datetime.now(),
            correlation_id=new_id(), batch_id=batch_id, provider_key="defra",
        )
    )

    by_correlation = await repo.get_by_correlation(correlation)
    assert {ev.event_id for ev in by_correlation} == {e1.event_id}

    replay = await repo.replay(batch_id)
    assert {ev.event_id for ev in replay} == {e1.event_id, e2.event_id}


async def test_delete(pool: asyncpg.Pool) -> None:
    repo = EventsRepository(pool)
    event = await repo.store(
        DocumentUploaded(
            event_id=new_id(), occurred_at=datetime.now(),
            correlation_id=new_id(), document_id=new_id(),
            organization_id=new_id(), storage_path="s/a.pdf",
        )
    )
    await repo.delete(event.event_id)
    assert await repo.get(event.event_id) is None
