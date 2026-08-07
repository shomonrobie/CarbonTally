"""Integration tests for infra.audit_logger + AuditRepository.

Verifies the logger records actions, the audit decorator captures success and
failure entries against the real append-only audit trail, and querying round-
trips the stored fields.
"""
from __future__ import annotations

import asyncpg
import pytest

from data.audit import AuditRepository
from domain.audit import AuditQuery
from infra.audit_logger import AuditLogger
from tests.integration.conftest import new_id

pytestmark = pytest.mark.asyncio


def _make_logger(pool: asyncpg.Pool) -> AuditLogger:
    return AuditLogger(AuditRepository(pool), default_actor="system")


async def test_log_action_and_query_round_trip(pool: asyncpg.Pool) -> None:
    logger = _make_logger(pool)
    correlation = new_id()
    entity_id = new_id()
    entry = await logger.log_action(
        action="activated",
        entity_type="import_batch",
        entity_id=entity_id,
        correlation_id=correlation,
        actor="import-svc",
        reason="published",
        after={"is_active": True},
    )
    assert entry.id

    found = await logger.query(AuditQuery(correlation_id=correlation))
    assert len(found) == 1
    assert found[0].action == "activated"
    assert found[0].entity_type == "import_batch"
    assert found[0].entity_id == entity_id
    assert found[0].actor == "import-svc"
    assert found[0].reason == "published"
    assert found[0].after == {"is_active": True}


async def test_audit_decorator_records_success(pool: asyncpg.Pool) -> None:
    logger = _make_logger(pool)
    correlation = new_id()
    document_id = new_id()

    @logger.audit(
        action="document.processed",
        entity_type="document",
        entity_id_arg="document_id",
        correlation_id_arg="correlation_id",
        record_result=True,
    )
    async def process(document_id: str, correlation_id: str) -> dict[str, str]:
        return {"document_id": document_id, "status": "done"}

    result = await process(document_id, correlation)
    assert result == {"document_id": document_id, "status": "done"}

    found = await logger.query(AuditQuery(correlation_id=correlation))
    assert len(found) == 1
    assert found[0].action == "document.processed"
    assert found[0].entity_id == document_id
    assert found[0].after == {"document_id": document_id, "status": "done"}


async def test_audit_decorator_records_failure_and_reraises(
    pool: asyncpg.Pool,
) -> None:
    logger = _make_logger(pool)
    correlation = new_id()
    batch_id = new_id()

    @logger.audit(
        action="import.run",
        entity_type="import_batch",
        entity_id_arg="batch_id",
        correlation_id_arg="correlation_id",
    )
    async def run_import(batch_id: str, correlation_id: str) -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await run_import(batch_id, correlation)

    found = await logger.query(AuditQuery(correlation_id=correlation))
    assert len(found) == 1
    assert found[0].action == "import.run"
    assert found[0].entity_id == batch_id
    assert found[0].reason is not None
    assert "boom" in found[0].reason
