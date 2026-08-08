"""Unit tests for engines.ai_extraction."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import pytest

from core.exceptions import AIExtractionFailedError, ExtractionFailedError
from domain.audit import AuditEntry
from domain.document import Document
from domain.workflow import DomainEvent, FieldsExtracted
from engines.ai_extraction import AIExtractionEngine
from engines.extraction import DocumentSink
from infra.event_bus import EventBus
from infra.llm_client import ChatCompletionResponse, LLMClient


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


def _llm(response_text: str) -> LLMClient:
    def transport(payload: dict[str, object]) -> ChatCompletionResponse:
        return ChatCompletionResponse(text=response_text)

    return LLMClient(
        base_url="https://llm.test/v1",
        api_key="key",
        model="gpt-test",
        transport=transport,
    )


def make_engine(
    doc_sink: DocumentSink,
    llm_client: LLMClient,
    **kwargs: Any,
) -> AIExtractionEngine:
    return AIExtractionEngine(doc_sink, llm_client, **kwargs)


class TestExtractFields:
    async def test_parses_fields_from_llm_json(self) -> None:
        payload = {
            "supplier": {"value": "Acme Corp", "confidence": 0.99},
            "invoice_number": {"value": "INV-42", "confidence": 0.95},
        }
        llm = _llm(json.dumps(payload))
        engine = make_engine(_MemoryDocSink(), llm)
        fields = await engine.extract_fields(make_document(), "invoice text")
        by_name = {f.field_name: f for f in fields}
        assert set(by_name) == {"supplier", "invoice_number"}
        assert by_name["supplier"].value == "Acme Corp"
        assert by_name["supplier"].confidence == 0.99
        assert by_name["supplier"].source == "ai"

    async def test_strips_code_fence(self) -> None:
        payload = {
            "supplier": {"value": "Acme Corp", "confidence": 1.0},
        }
        response = "```json\n" + json.dumps(payload) + "\n```"
        llm = _llm(response)
        engine = make_engine(_MemoryDocSink(), llm)
        fields = await engine.extract_fields(make_document(), "text")
        assert fields[0].field_name == "supplier"

    async def test_missing_fields_are_omitted(self) -> None:
        llm = _llm(json.dumps({"supplier": {"value": "Acme", "confidence": 0.9}}))
        engine = make_engine(_MemoryDocSink(), llm)
        fields = await engine.extract_fields(make_document(), "text")
        assert [f.field_name for f in fields] == ["supplier"]

    async def test_custom_fields_subset(self) -> None:
        llm = _llm(json.dumps({"currency": {"value": "GBP", "confidence": 0.8}}))
        engine = make_engine(
            _MemoryDocSink(), llm, fields=("currency", "supplier")
        )
        fields = await engine.extract_fields(make_document(), "text")
        assert [f.field_name for f in fields] == ["currency"]

    async def test_empty_text_raises_and_marks_failed(self) -> None:
        llm = _llm("{}")
        sink = _MemoryDocSink()
        engine = make_engine(sink, llm)
        document = make_document()
        with pytest.raises(ExtractionFailedError, match="no document text"):
            await engine.extract_fields(document, "  ")
        assert sink.updates[-1] == (document.id, "failed")

    async def test_status_transitions_on_success(self) -> None:
        llm = _llm("{}")
        sink = _MemoryDocSink()
        engine = make_engine(sink, llm)
        document = make_document()
        await engine.extract_fields(document, "text")
        assert sink.updates == [
            (document.id, "processing"),
            (document.id, "processed"),
        ]


class TestErrors:
    async def test_invalid_json_raises_and_marks_failed(self) -> None:
        llm = _llm("not json at all")
        sink = _MemoryDocSink()
        engine = make_engine(sink, llm)
        document = make_document()
        with pytest.raises(AIExtractionFailedError, match="invalid JSON"):
            await engine.extract_fields(document, "text")
        assert sink.updates[-1] == (document.id, "failed")

    async def test_non_object_response_raises(self) -> None:
        llm = _llm("[1, 2, 3]")
        engine = make_engine(_MemoryDocSink(), llm)
        with pytest.raises(AIExtractionFailedError, match="JSON object"):
            await engine.extract_fields(make_document(), "text")

    async def test_malformed_field_raises(self) -> None:
        llm = _llm(json.dumps({"supplier": "Acme"}))
        engine = make_engine(_MemoryDocSink(), llm)
        with pytest.raises(AIExtractionFailedError, match="malformed"):
            await engine.extract_fields(make_document(), "text")

    async def test_confidence_out_of_range_raises(self) -> None:
        llm = _llm(
            json.dumps({"supplier": {"value": "Acme", "confidence": 1.5}})
        )
        engine = make_engine(_MemoryDocSink(), llm)
        with pytest.raises(AIExtractionFailedError, match="out of range"):
            await engine.extract_fields(make_document(), "text")

    async def test_confidence_not_a_number_raises(self) -> None:
        llm = _llm(
            json.dumps({"supplier": {"value": "Acme", "confidence": "high"}})
        )
        engine = make_engine(_MemoryDocSink(), llm)
        with pytest.raises(AIExtractionFailedError, match="not a number"):
            await engine.extract_fields(make_document(), "text")


class TestSideEffects:
    async def test_publishes_fields_extracted_event(self) -> None:
        bus = EventBus()
        received: list[DomainEvent] = []

        async def capture(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(None, capture)
        llm = _llm(json.dumps({"supplier": {"value": "Acme", "confidence": 0.9}}))
        engine = make_engine(_MemoryDocSink(), llm, event_bus=bus)
        document = make_document()
        await engine.extract_fields(document, "text")
        await bus.drain()
        assert len(received) == 1
        event = received[0]
        assert isinstance(event, FieldsExtracted)
        assert event.document_id == document.id
        assert event.fields == {"supplier": "Acme"}
        assert event.confidence == 0.9

    async def test_audits_extraction(self) -> None:
        audit = _AuditSink()
        llm = _llm(json.dumps({"supplier": {"value": "Acme", "confidence": 0.9}}))
        engine = make_engine(
            _MemoryDocSink(), llm, audit_logger=audit
        )
        document = make_document()
        await engine.extract_fields(document, "text")
        assert len(audit.entries) == 1
        entry = audit.entries[0]
        assert entry.action == "ai_extraction:completed"
        assert entry.entity_id == document.id

    async def test_failing_event_bus_does_not_break_extraction(self) -> None:
        class _BrokenBus:
            async def publish(self, event: DomainEvent) -> int:
                raise RuntimeError("bus down")

        llm = _llm("{}")
        engine = make_engine(
            _MemoryDocSink(), llm, event_bus=_BrokenBus()
        )
        fields = await engine.extract_fields(make_document(), "text")
        assert fields == ()

