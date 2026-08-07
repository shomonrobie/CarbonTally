"""Integration tests for AuditRepository."""
from __future__ import annotations

from datetime import datetime, timedelta

import asyncpg
import pytest

from data.audit import AuditRepository
from domain.audit import AuditEntry, AuditQuery
from tests.integration.conftest import new_id

pytestmark = pytest.mark.asyncio


def _entry(**kwargs: object) -> AuditEntry:
    correlation_id = str(kwargs.get("correlation_id") or new_id())
    return AuditEntry(
        id=str(kwargs.get("id") or new_id()),
        correlation_id=correlation_id,
        entity_type=str(kwargs.get("entity_type") or "document"),
        entity_id=str(kwargs.get("entity_id") or new_id()),
        action=str(kwargs.get("action") or "created"),
        actor=str(kwargs.get("actor") or new_id()),
        occurred_at=datetime.now(),
        changed_fields={"status": "pending"},
        reason="test entry",
        ip_address="192.168.0.10",
        before=None,
        after={"status": "pending"},
    )


async def test_record_and_get_round_trip(pool: asyncpg.Pool) -> None:
    repo = AuditRepository(pool)
    entry = _entry(actor="system")
    stored = await repo.record(entry)
    assert stored.id
    fetched = await repo.get(stored.id)
    assert fetched is not None
    assert fetched.correlation_id == entry.correlation_id
    assert fetched.entity_type == "document"
    assert fetched.action == "created"
    assert fetched.actor == "system"
    assert fetched.reason == "test entry"
    assert fetched.ip_address == "192.168.0.10"
    assert fetched.changed_fields == {"status": "pending"}


async def test_query_filters(pool: asyncpg.Pool) -> None:
    repo = AuditRepository(pool)
    correlation = new_id()
    entity_id = new_id()
    actor = new_id()
    action = f"created-{new_id()}"
    await repo.record(_entry(action=action, correlation_id=correlation, entity_id=entity_id, actor=actor))
    await repo.record(_entry(action=action, entity_id=entity_id, actor=actor))
    await repo.record(_entry(action=action, actor=actor))

    by_correlation = await repo.query(AuditQuery(correlation_id=correlation))
    assert len(by_correlation) == 1

    by_entity = await repo.query(AuditQuery(entity_id=entity_id))
    assert len(by_entity) == 2

    by_action = await repo.query(AuditQuery(action=action))
    assert len(by_action) == 3

    by_actor = await repo.query(AuditQuery(actor=actor))
    assert len(by_actor) == 3

    empty = await repo.query(AuditQuery(action="nonexistent"))
    assert empty == []


async def test_get_by_correlation(pool: asyncpg.Pool) -> None:
    repo = AuditRepository(pool)
    correlation = new_id()
    first = await repo.record(_entry(correlation_id=correlation))
    second = await repo.record(_entry(correlation_id=correlation))
    entries = await repo.get_by_correlation(correlation)
    assert {e.id for e in entries} == {first.id, second.id}


async def test_export_csv(pool: asyncpg.Pool) -> None:
    repo = AuditRepository(pool)
    correlation = new_id()
    await repo.record(_entry(correlation_id=correlation, action="exported"))
    csv_text = await repo.export_csv(AuditQuery(correlation_id=correlation))
    assert csv_text.startswith("id,correlation_id")
    assert "exported" in csv_text
    assert correlation in csv_text


async def test_save_and_delete(pool: asyncpg.Pool) -> None:
    repo = AuditRepository(pool)
    entry = _entry()
    stored = await repo.save(entry)
    assert stored.id == entry.id
    assert (await repo.get(entry.id)) is not None
    await repo.delete(entry.id)
    assert await repo.get(entry.id) is None
