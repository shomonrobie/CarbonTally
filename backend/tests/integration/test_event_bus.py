"""Integration tests for infra.event_bus + EventsRepository.

Publishes real domain events through the bus and verifies a handler that
persists to ``EventsRepository`` stores them so they can be replayed.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg
import pytest

from data.events import EventsRepository
from domain.workflow import DocumentUploaded, DomainEvent, ImportStarted
from infra.event_bus import EventBus
from tests.integration.conftest import new_id

pytestmark = pytest.mark.asyncio


def _document_event(**kwargs: Any) -> DocumentUploaded:
    return DocumentUploaded(
        event_id=new_id(),
        occurred_at=datetime.now(),
        correlation_id=str(kwargs.get("correlation_id") or new_id()),
        document_id=str(kwargs.get("document_id") or new_id()),
        organization_id=str(kwargs.get("organization_id") or new_id()),
        storage_path=str(kwargs.get("storage_path") or "uploads/invoice.pdf"),
    )


async def test_bus_persists_events_via_handler(pool: asyncpg.Pool) -> None:
    bus = EventBus()
    repo = EventsRepository(pool)
    correlation = new_id()
    document_id = new_id()

    async def persist(event: DomainEvent) -> None:
        await repo.store(event)

    bus.subscribe(DocumentUploaded, persist)
    event = _document_event(
        correlation_id=correlation, document_id=document_id
    )
    dispatched = await bus.publish_and_wait(event)
    assert dispatched == 1

    stored = await repo.get_by_correlation(correlation)
    assert len(stored) == 1
    fetched = stored[0]
    assert isinstance(fetched, DocumentUploaded)
    assert fetched.document_id == document_id
    assert fetched.aggregate_type == "document"


async def test_bus_background_publish_then_drain(pool: asyncpg.Pool) -> None:
    bus = EventBus()
    repo = EventsRepository(pool)
    correlation = new_id()

    async def persist(event: DomainEvent) -> None:
        await repo.store(event)

    bus.subscribe(ImportStarted, persist)
    event = ImportStarted(
        event_id=new_id(),
        occurred_at=datetime.now(),
        correlation_id=correlation,
        batch_id=new_id(),
        provider_key="defra",
    )
    dispatched = await bus.publish(event)
    assert dispatched == 1
    await bus.drain()

    stored = await repo.get_by_correlation(correlation)
    assert len(stored) == 1
    assert isinstance(stored[0], ImportStarted)
    assert stored[0].provider_key == "defra"


async def test_bus_wildcard_handler_and_failing_handler_isolated(
    pool: asyncpg.Pool,
) -> None:
    bus = EventBus()
    repo = EventsRepository(pool)
    correlation = new_id()

    async def failing(event: DomainEvent) -> None:
        raise RuntimeError("handler boom")

    async def persist(event: DomainEvent) -> None:
        await repo.store(event)

    bus.subscribe(None, failing)
    bus.subscribe(DocumentUploaded, persist)
    event = _document_event(correlation_id=correlation)
    dispatched = await bus.publish_and_wait(event)
    assert dispatched == 2

    stored = await repo.get_by_correlation(correlation)
    assert len(stored) == 1
