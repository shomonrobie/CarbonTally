"""Integration tests for DocumentExtractionEngine (real Supabase DB).

Seeds a real document row, runs extraction, and verifies the document status
transition and the persisted workflow events through the real repositories.
"""
from __future__ import annotations

import asyncpg
import pytest

from core.exceptions import ExtractionFailedError
from data.documents import DocumentsRepository
from data.events import EventsRepository
from domain.workflow import DomainEvent, ExtractionCompleted, FieldsExtracted
from engines.extraction import DocumentExtractionEngine
from infra.event_bus import EventBus
from tests.integration.conftest import make_org

pytestmark = pytest.mark.asyncio


async def test_extraction_updates_document_and_persists_events(
    pool: asyncpg.Pool,
) -> None:
    org_id = await make_org(pool)
    docs_repo = DocumentsRepository(pool)
    events_repo = EventsRepository(pool)
    bus = EventBus()

    async def persist(event: DomainEvent) -> None:
        await events_repo.store(event)

    bus.subscribe(None, persist)
    engine = DocumentExtractionEngine(docs_repo, event_bus=bus)
    document = await docs_repo.create_from_upload(
        org_id=org_id,
        storage_path="uploads/invoice.pdf",
        filename="invoice.pdf",
        file_type="pdf",
    )
    text = (
        "Supplier: Acme Corp\nInvoice Number: INV-42\n"
        "\fItem\tQuantity\nWidget\t2\nGadget\t5"
    )
    result = await engine.extract(document, text)
    await bus.drain()

    assert len(result.pages) == 2
    assert result.metadata["field_count"] >= 2
    assert len(result.tables) == 1

    stored = await docs_repo.get(document.id)
    assert stored is not None
    assert stored.status == "processed"

    events = await events_repo.get_by_correlation(document.id)
    assert any(isinstance(e, ExtractionCompleted) for e in events)
    assert any(isinstance(e, FieldsExtracted) for e in events)

    await docs_repo.delete(document.id)


async def test_failed_extraction_marks_document_failed(pool: asyncpg.Pool) -> None:
    org_id = await make_org(pool)
    docs_repo = DocumentsRepository(pool)
    engine = DocumentExtractionEngine(docs_repo)
    document = await docs_repo.create_from_upload(
        org_id=org_id,
        storage_path="uploads/blank.pdf",
        filename="blank.pdf",
        file_type="pdf",
    )
    with pytest.raises(ExtractionFailedError, match="no usable content"):
        await engine.extract(document, "   ")

    stored = await docs_repo.get(document.id)
    assert stored is not None
    assert stored.status == "failed"

    await docs_repo.delete(document.id)
