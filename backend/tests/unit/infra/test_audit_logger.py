"""Unit tests for infra.audit_logger."""
from __future__ import annotations

import pytest

from domain.audit import AuditEntry, AuditQuery
from infra.audit_logger import (
    AuditLogger,
    init_audit_logger,
    reset_audit_logger,
)


class _MemorySink:
    """In-memory AuditSink for unit tests."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []
        self.fail_on_record = False

    async def record(self, entry: AuditEntry) -> AuditEntry:
        if self.fail_on_record:
            raise RuntimeError("sink down")
        stored = AuditEntry(
            id=entry.id or "stored-id",
            correlation_id=entry.correlation_id,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            action=entry.action,
            actor=entry.actor,
            occurred_at=entry.occurred_at,
            changed_fields=entry.changed_fields,
            reason=entry.reason,
            ip_address=entry.ip_address,
            before=entry.before,
            after=entry.after,
        )
        self.entries.append(stored)
        return stored

    async def query(self, filters: AuditQuery) -> list[AuditEntry]:
        result = self.entries
        if filters.correlation_id is not None:
            result = [e for e in result if e.correlation_id == filters.correlation_id]
        if filters.action is not None:
            result = [e for e in result if e.action == filters.action]
        return result[: filters.limit]


def _logger(sink: _MemorySink | None = None) -> tuple[AuditLogger, _MemorySink]:
    memory = sink or _MemorySink()
    return AuditLogger(memory, default_actor="system"), memory


class TestLogAction:
    async def test_log_action_uses_default_actor(self) -> None:
        logger, memory = _logger()
        entry = await logger.log_action(
            action="activated",
            entity_type="import_batch",
            entity_id="batch-1",
            correlation_id="corr-1",
        )
        assert entry.action == "activated"
        assert entry.actor == "system"
        assert entry.correlation_id == "corr-1"
        assert len(memory.entries) == 1

    async def test_log_action_explicit_actor_and_reason(self) -> None:
        logger, memory = _logger()
        entry = await logger.log_action(
            action="created",
            entity_type="document",
            entity_id="doc-1",
            correlation_id="corr-1",
            actor="admin@carbon.tally",
            reason="manual import",
            changed_fields={"status": "pending"},
            before={"status": None},
            after={"status": "pending"},
        )
        assert entry.actor == "admin@carbon.tally"
        assert entry.reason == "manual import"
        assert entry.changed_fields == {"status": "pending"}
        assert entry.before == {"status": None}
        assert entry.after == {"status": "pending"}

    async def test_query_delegates_to_sink(self) -> None:
        logger, _memory = _logger()
        await logger.log_action(
            action="created", entity_type="document", entity_id="doc-1",
            correlation_id="corr-1",
        )
        await logger.log_action(
            action="deleted", entity_type="document", entity_id="doc-1",
            correlation_id="corr-2",
        )
        created = await logger.query(AuditQuery(correlation_id="corr-1"))
        assert [e.action for e in created] == ["created"]


class TestAuditDecoratorSuccess:
    async def test_records_success_with_arg_resolution(self) -> None:
        logger, memory = _logger()

        @logger.audit(
            action="document.processed",
            entity_type="document",
            entity_id_arg="document_id",
            correlation_id_arg="correlation_id",
        )
        async def process(document_id: str, correlation_id: str) -> str:
            return document_id

        result = await process("doc-1", "corr-1")
        assert result == "doc-1"
        assert len(memory.entries) == 1
        entry = memory.entries[0]
        assert entry.action == "document.processed"
        assert entry.entity_type == "document"
        assert entry.entity_id == "doc-1"
        assert entry.correlation_id == "corr-1"
        assert entry.actor == "system"

    async def test_action_defaults_to_function_name(self) -> None:
        logger, memory = _logger()

        @logger.audit(
            entity_type="document",
            entity_id_arg="document_id",
            correlation_id="corr-fixed",
        )
        async def process_document(document_id: str) -> str:
            return document_id

        await process_document("doc-1")
        assert memory.entries[0].action == "process_document"
        assert memory.entries[0].correlation_id == "corr-fixed"

    async def test_record_result_captures_after(self) -> None:
        logger, memory = _logger()

        @logger.audit(
            action="calculate",
            entity_type="document",
            entity_id_arg="document_id",
            correlation_id="corr-1",
            record_result=True,
        )
        async def calculate(document_id: str) -> dict[str, str]:
            return {"id": document_id, "status": "done"}

        await calculate("doc-1")
        assert memory.entries[0].after == {"id": "doc-1", "status": "done"}

    async def test_before_snapshot_from_callable(self) -> None:
        logger, memory = _logger()

        def snapshot(document_id: str) -> dict[str, str]:
            return {"document_id": document_id, "state": "pending"}

        @logger.audit(
            action="archive",
            entity_type="document",
            entity_id_arg="document_id",
            correlation_id="corr-1",
            before=snapshot,
        )
        async def archive(document_id: str) -> None:
            return None

        await archive("doc-1")
        assert memory.entries[0].before == {
            "document_id": "doc-1",
            "state": "pending",
        }

    async def test_static_before_snapshot(self) -> None:
        logger, memory = _logger()

        @logger.audit(
            action="archive",
            entity_type="document",
            entity_id_arg="document_id",
            correlation_id="corr-1",
            before={"state": "active"},
        )
        async def archive(document_id: str) -> None:
            return None

        await archive("doc-1")
        assert memory.entries[0].before == {"state": "active"}


class TestAuditDecoratorFailure:
    async def test_failure_records_reason_and_reraises(self) -> None:
        logger, memory = _logger()

        @logger.audit(
            action="import.run",
            entity_type="import_batch",
            entity_id_arg="batch_id",
            correlation_id="corr-1",
        )
        async def run_import(batch_id: str) -> str:
            raise ValueError("bad workbook")

        with pytest.raises(ValueError, match="bad workbook"):
            await run_import("batch-1")
        assert len(memory.entries) == 1
        entry = memory.entries[0]
        assert entry.action == "import.run"
        assert entry.entity_id == "batch-1"
        assert entry.reason is not None
        assert "bad workbook" in entry.reason

    async def test_record_failures_disabled(self) -> None:
        logger, memory = _logger()

        @logger.audit(
            action="import.run",
            entity_type="import_batch",
            entity_id_arg="batch_id",
            correlation_id="corr-1",
            record_failures=False,
        )
        async def run_import(batch_id: str) -> str:
            raise ValueError("bad workbook")

        with pytest.raises(ValueError):
            await run_import("batch-1")
        assert memory.entries == []

    async def test_missing_entity_context_is_skipped(self) -> None:
        logger, memory = _logger()

        @logger.audit(
            entity_type_arg="entity_type",
            entity_id_arg="entity_id",
        )
        async def op_without_context() -> str:
            return "ok"

        result = await op_without_context()
        assert result == "ok"
        assert memory.entries == []

    async def test_sink_failure_never_breaks_operation(self) -> None:
        memory = _MemorySink()
        memory.fail_on_record = True
        logger = AuditLogger(memory, default_actor="system")

        @logger.audit(
            entity_type="document",
            entity_id_arg="document_id",
            correlation_id="corr-1",
        )
        async def process(document_id: str) -> str:
            return document_id

        assert await process("doc-1") == "doc-1"


class TestSingleton:
    def test_init_and_reset_audit_logger(self) -> None:
        reset_audit_logger()
        try:
            logger, memory = _logger()
            installed = init_audit_logger(memory, default_actor="svc")
            assert installed.default_actor == "svc"
            reset_audit_logger()
        finally:
            reset_audit_logger()


