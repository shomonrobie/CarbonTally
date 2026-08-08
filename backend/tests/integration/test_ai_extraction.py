"""Integration tests for AIExtractionEngine (real Supabase DB + real HTTP LLM).

Runs the AI extraction end to end: a real local HTTP server serves the
OpenAI-compatible response, the real ``LLMClient`` transports it, and the engine
persists the document status + ``FieldsExtracted`` event through the real
repositories.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import asyncpg
import pytest

from data.documents import DocumentsRepository
from data.events import EventsRepository
from domain.workflow import DomainEvent, FieldsExtracted
from engines.ai_extraction import AIExtractionEngine
from infra.event_bus import EventBus
from infra.llm_client import LLMClient
from tests.integration.conftest import make_org

pytestmark = pytest.mark.asyncio

_LLM_FIELDS = {
    "supplier": {"value": "Acme Corp", "confidence": 0.99},
    "date": {"value": "2025-06-01", "confidence": 0.95},
    "net_amount": {"value": "120.00", "confidence": 0.9},
}


class _LlmHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = json.dumps(
            {"choices": [{"message": {"content": json.dumps(_LLM_FIELDS)}}]}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


def _serve(
    handler_type: type[BaseHTTPRequestHandler],
) -> tuple[ThreadingHTTPServer, int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_type)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, int(server.server_address[1])


async def test_ai_extraction_end_to_end(pool: asyncpg.Pool) -> None:
    server, port = _serve(_LlmHandler)
    try:
        org_id = await make_org(pool)
        docs_repo = DocumentsRepository(pool)
        events_repo = EventsRepository(pool)
        bus = EventBus()

        async def persist(event: DomainEvent) -> None:
            await events_repo.store(event)

        bus.subscribe(None, persist)
        llm = LLMClient(
            base_url=f"http://127.0.0.1:{port}/v1",
            api_key="test-key",
            model="gpt-test",
            timeout_seconds=5.0,
        )
        engine = AIExtractionEngine(docs_repo, llm, event_bus=bus)
        document = await docs_repo.create_from_upload(
            org_id=org_id,
            storage_path="uploads/invoice.pdf",
            filename="invoice.pdf",
            file_type="pdf",
        )

        fields = await engine.extract_fields(
            document, "Supplier: Acme Corp\nDate: 2025-06-01"
        )
        await bus.drain()

        by_name = {f.field_name: f for f in fields}
        assert set(by_name) >= {"supplier", "date"}
        assert by_name["supplier"].value == "Acme Corp"
        assert by_name["supplier"].source == "ai"

        stored = await docs_repo.get(document.id)
        assert stored is not None
        assert stored.status == "processed"

        events = await events_repo.get_by_correlation(document.id)
        assert any(isinstance(e, FieldsExtracted) for e in events)

        await docs_repo.delete(document.id)
    finally:
        server.shutdown()
