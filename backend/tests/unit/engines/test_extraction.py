"""Unit tests for engines.extraction."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import pytest

from core.exceptions import ExtractionFailedError
from domain.audit import AuditEntry
from domain.document import Document
from domain.workflow import (
    DomainEvent,
    ExtractionCompleted,
    ExtractionRequested,
    FieldsExtracted,
)
from engines.extraction import DocumentExtractionEngine
from infra.event_bus import EventBus


def make_document(**kwargs: Any) -> Document:
    return Document(
        id=str(kwargs.get("id") or f"doc-{uuid.uuid4().hex[:12]}"),
        organization_id=str(kwargs.get("organization_id") or "org-1"),
        filename=str(kwargs.get("filename") or "invoice.pdf"),
        storage_path=str(kwargs.get("storage_path") or "uploads/invoice.pdf"),
        file_type=str(kwargs.get("file_type") or "pdf"),
        status=str(kwargs.get("status") or "pending"),
        uploaded_at=datetime.now(timezone.utc),
        uploaded_by=str(kwargs.get("uploaded_by") or "user-1"),
    )


class _MemoryDocSink:
    def __init__(self) -> None:
        self.updates: list[tuple[str, str]] = []

    async def update_status(self, doc_id: str, status: str) -> Document:
        self.updates.append((doc_id, status))
        return make_document(id=doc_id, status=status)


class _AuditSink:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def log_action(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        correlation_id: str,
        actor: Optional[str] = None,
        changed_fields: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        before: Any = None,
        after: Any = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor or "system",
            occurred_at=datetime.now(timezone.utc),
            changed_fields=dict(changed_fields or {}),
            reason=reason,
            ip_address=ip_address,
            before=before,
            after=after,
        )
        self.entries.append(entry)
        return entry


def make_engine(**kwargs: Any) -> tuple[DocumentExtractionEngine, _MemoryDocSink]:
    sink = _MemoryDocSink()
    engine = DocumentExtractionEngine(sink, **kwargs)
    return engine, sink


class TestExtract:
    async def test_splits_pages(self) -> None:
        engine, _sink = make_engine()
        document = make_document()
        text = "Page one content\fPage two content"
        result = await engine.extract(document, text)
        assert len(result.pages) == 2
        assert result.pages[0].page_number == 1
        assert result.pages[0].text == "Page one content"
        assert result.pages[1].page_number == 2
        assert result.pages[1].text == "Page two content"
        assert result.raw_text == text
        assert result.confidence == 1.0

    async def test_single_page_without_separator(self) -> None:
        engine, _sink = make_engine()
        result = await engine.extract(make_document(), "Just one page")
        assert len(result.pages) == 1
        assert result.metadata["page_count"] == 1

    async def test_extracts_fields(self) -> None:
        engine, _sink = make_engine()
        text = "Supplier: Acme Corp\nInvoice Number: INV-42\nDate: 2025-06-01"
        result = await engine.extract(make_document(), text)
        fields = result.metadata["fields"]
        assert fields["supplier"] == "Acme Corp"
        assert fields["invoice_number"] == "INV-42"
        assert fields["date"] == "2025-06-01"

    async def test_extracts_tables(self) -> None:
        engine, _sink = make_engine()
        text = "Header\tValue\nAlpha\t1\nBeta\t2"
        result = await engine.extract(make_document(), text)
        assert len(result.tables) == 1
        table = result.tables[0]
        assert table.headers == ("Header", "Value")
        assert table.rows == (("Alpha", "1"), ("Beta", "2"))

    async def test_empty_text_raises_and_marks_failed(self) -> None:
        engine, sink = make_engine()
        document = make_document()
        with pytest.raises(ExtractionFailedError, match="no usable content"):
            await engine.extract(document, "   ")
        assert sink.updates[-1] == (document.id, "failed")

    async def test_status_transitions_on_success(self) -> None:
        engine, sink = make_engine()
        document = make_document()
        await engine.extract(document, "content")
        assert sink.updates == [
            (document.id, "processing"),
            (document.id, "processed"),
        ]

    async def test_custom_field_patterns_override_generic(self) -> None:
        engine, _sink = make_engine(
            field_patterns={
                "invoice_number": re.compile(
                    r"(?im)^\s*ref\s*[:：]\s*(.+?)\s*$"
                )
            }
        )
        result = await engine.extract(
            make_document(), "Ref: ABC-123\nInvoice Number: INV-42"
        )
        fields = result.metadata["fields"]
        assert fields["invoice_number"] == "ABC-123"

    async def test_constructor_validation(self) -> None:
        with pytest.raises(ValueError, match="documents_repo"):
            DocumentExtractionEngine(None)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="page_separator"):
            DocumentExtractionEngine(_MemoryDocSink(), page_separator="")
        with pytest.raises(ValueError, match="table_delimiter"):
            DocumentExtractionEngine(_MemoryDocSink(), table_delimiter="")


class TestSideEffects:
    async def test_publishes_extraction_events(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        async def capture(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(None, capture)
        engine, _sink = make_engine(event_bus=bus)
        document = make_document()
        await engine.extract(document, "Supplier: Acme Corp")
        await bus.drain()

        names = [type(e).__name__ for e in received]
        assert "ExtractionRequested" in names
        assert "ExtractionCompleted" in names
        assert "FieldsExtracted" in names
        completed = next(
            e for e in received if isinstance(e, ExtractionCompleted)
        )
        assert completed.document_id == document.id
        assert completed.page_count == 1
        assert completed.confidence == 1.0
        fields_event = next(
            e for e in received if isinstance(e, FieldsExtracted)
        )
        assert fields_event.fields == {"supplier": "Acme Corp"}

    async def test_audits_extraction(self) -> None:
        audit = _AuditSink()
        engine, _sink = make_engine(audit_logger=audit)
        document = make_document()
        await engine.extract(document, "content")
        assert len(audit.entries) == 1
        entry = audit.entries[0]
        assert entry.action == "document_extraction:completed"
        assert entry.entity_type == "document"
        assert entry.entity_id == document.id

    async def test_failing_event_bus_does_not_break_extraction(self) -> None:
        class _BrokenBus:
            async def publish(self, event: DomainEvent) -> int:
                raise RuntimeError("bus down")

        engine, _sink = make_engine(event_bus=_BrokenBus())
        result = await engine.extract(make_document(), "content")
        assert len(result.pages) == 1

