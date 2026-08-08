"""Integration tests for the Phase 8 Workflow Orchestrator (real Supabase DB).

Runs the full document pipeline end to end over real data: a real local HTTP
server serves the OpenAI-compatible LLM response, the real search index +
matching pipeline resolve the extracted activity to a seeded factor, and the
real calculation engine persists a snapshot and emissions log. Every stage is
also persisted to the real ``domain_events`` / ``audit_trail`` tables.
"""
from __future__ import annotations

import json
import threading
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import asyncpg
import pytest

from core.exceptions import WorkflowMaxRetriesError
from data.audit import AuditRepository
from data.documents import DocumentsRepository
from data.emission_factors import EmissionFactorsRepository
from data.emissions_logs import EmissionsLogsRepository
from data.events import EventsRepository
from domain.factor import EmissionFactor
from domain.matching import MatchingPipelineConfig
from domain.workflow import DomainEvent
from engines.ai_extraction import AIExtractionEngine
from engines.calculation import CalculationEngine
from engines.extraction import DocumentExtractionEngine
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from engines.workflow import WorkflowOrchestrator
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus
from infra.llm_client import LLMClient
from infra.search_index import FactorSearchIndex
from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio

#: Unique marker so seeded rows never collide with other test files.
_MARKER = f"p8-{new_id()[:6]}"
ACTIVITY = f"Natural gas {_MARKER} (kg CO2e) [kWh]"
_MULTIPLIER = Decimal("0.18400")

#: Field vocabulary the workflow AI stage is wired with (the Phase 10
#: composition root will supply the same set).
_AI_FIELDS = ("activity", "quantity", "unit", "country", "date")

_EXPECTED_STATES = [
    ("pending", "uploaded"),
    ("uploaded", "classifying"),
    ("classifying", "extracting"),
    ("extracting", "ai_matching"),
    ("ai_matching", "matched"),
    ("matched", "customer_review"),
    ("customer_review", "reviewed"),
    ("reviewed", "calculating"),
    ("calculating", "completed"),
]


class _LlmHandler(BaseHTTPRequestHandler):
    """Serves a configurable OpenAI-compatible extraction response."""

    fields: dict[str, dict[str, Any]] = {}

    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = json.dumps(
            {"choices": [{"message": {"content": json.dumps(self.fields)}}]}
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


def _llm_fields(*, confidence: float = 0.99) -> dict[str, dict[str, Any]]:
    return {
        "activity": {"value": ACTIVITY, "confidence": confidence},
        "quantity": {"value": "100", "confidence": confidence},
        "unit": {"value": "kWh", "confidence": confidence},
        "country": {"value": "GB", "confidence": confidence},
        "date": {"value": "2025-06-01", "confidence": confidence},
    }


async def _seed_factor(
    pool: asyncpg.Pool, *, activity: str = ACTIVITY
) -> EmissionFactor:
    repo = EmissionFactorsRepository(pool)
    factor = EmissionFactor(
        id=new_id(),
        reporting_year=2025,
        activity_type=activity,
        co2e_multiplier=_MULTIPLIER,
        unit="kWh",
        scope="Scope 1",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
        natural_key=("2025", activity, "GB", "kWh", "Scope 1"),
    )
    return await repo.save(factor)


def _matching_engine(
    index: FactorSearchIndex,
    *,
    event_bus: EventBus,
    audit_logger: AuditLogger,
) -> FactorMatchingEngine:
    config = MatchingPipelineConfig(stages=("exact_match",))
    return FactorMatchingEngine(
        index,
        build_matching_pipeline(config),
        event_bus=event_bus,
        audit_logger=audit_logger,
    )


async def _cleanup(
    pool: asyncpg.Pool,
    document_id: str,
    snapshot_id: str,
    factor_id: str,
) -> None:
    """Delete every row this test created, child-first.

    The factor is also referenced by ``emissions_logs``/``calculation_snapshots``
    (``emissions_logs_emission_factor_id_fkey``), so both are removed before the
    factor itself. Deleting by ``factor_id`` also clears rows a previously failed
    test in the same session may have left referencing the same factor.
    """
    if factor_id:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM public.emissions_logs WHERE emission_factor_id = $1",
                factor_id,
            )
            await conn.execute(
                "DELETE FROM public.calculation_snapshots WHERE factor_id = $1",
                factor_id,
            )
    if snapshot_id:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM public.emissions_logs WHERE snapshot_id = $1",
                snapshot_id,
            )
            await conn.execute(
                "DELETE FROM public.calculation_snapshots WHERE id = $1",
                snapshot_id,
            )
    if document_id:
        await DocumentsRepository(pool).delete(document_id)
    if factor_id:
        await EmissionFactorsRepository(pool).delete(factor_id)

async def _wire(
    pool: asyncpg.Pool,
    port: int,
    *,
    bus: EventBus,
    audit_logger: AuditLogger,
    index: FactorSearchIndex,
) -> WorkflowOrchestrator:
    """Build every engine + the orchestrator over the real repositories."""
    docs_repo = DocumentsRepository(pool)
    events_repo = EventsRepository(pool)
    logs_repo = EmissionsLogsRepository(pool)

    #: Orchestrator-owned events are persisted directly by the orchestrator's
    #: ``_emit`` (DocumentUploaded / ExtractionRequested in the stage methods,
    #: WorkflowStateChanged in ``_transition``); the bus persist subscriber must
    #: only persist engine-published events, otherwise every state transition is
    #: stored twice.
    _ORCHESTRATOR_PERSISTED = frozenset(
        {"DocumentUploaded", "ExtractionRequested", "WorkflowStateChanged"}
    )

    async def persist(event: DomainEvent) -> None:
        if type(event).__name__ in _ORCHESTRATOR_PERSISTED:
            return
        await events_repo.store(event)

    bus.subscribe(None, persist)
    llm = LLMClient(
        base_url=f"http://127.0.0.1:{port}/v1",
        api_key="test-key",
        model="gpt-test",
        timeout_seconds=5.0,
    )
    return WorkflowOrchestrator(
        docs_repo,
        events_repo,
        extraction_engine=DocumentExtractionEngine(
            docs_repo, event_bus=bus, audit_logger=audit_logger
        ),
        ai_extraction_engine=AIExtractionEngine(
            docs_repo,
            llm,
            event_bus=bus,
            audit_logger=audit_logger,
            fields=_AI_FIELDS,
        ),
        matching_engine=_matching_engine(
            index, event_bus=bus, audit_logger=audit_logger
        ),
        calculation_engine=CalculationEngine(
            logs_repo, event_bus=bus, audit_logger=audit_logger
        ),
        event_bus=bus,
        audit_logger=audit_logger,
    )


async def _fetch_events(
    pool: asyncpg.Pool, document_id: str
) -> tuple[list[tuple[str, str]], set[str]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT event_type, payload FROM public.domain_events
            WHERE aggregate_id = $1::uuid
            ORDER BY occurred_at, id
            """,
            document_id,
        )
        all_rows = await conn.fetch(
            "SELECT DISTINCT event_type FROM public.domain_events"
        )
    states = [
        (
            str(json.loads(r["payload"]).get("from_state")),
            str(json.loads(r["payload"]).get("to_state")),
        )
        for r in rows
        if r["event_type"] == "WorkflowStateChanged"
    ]
    types = {str(r["event_type"]) for r in all_rows}
    return states, types


async def test_workflow_end_to_end_completes_with_persisted_state(
    pool: asyncpg.Pool,
) -> None:
    server, port = _serve(_LlmHandler)
    try:
        _LlmHandler.fields = _llm_fields()
        org_id = await make_org(pool)
        factor = await _seed_factor(pool)
        docs_repo = DocumentsRepository(pool)
        audit_repo = AuditRepository(pool)
        bus = EventBus()
        audit_logger = AuditLogger(audit_repo)
        index = FactorSearchIndex()
        index.load([factor])
        orchestrator = await _wire(pool, port, bus=bus, audit_logger=audit_logger, index=index)

        document = await docs_repo.create_from_upload(
            org_id=org_id,
            storage_path="uploads/invoice.pdf",
            filename="invoice.pdf",
            file_type="pdf",
        )
        result = await orchestrator.process_document(
            document, f"Supplier: Acme Corp\nActivity: {ACTIVITY}\nQuantity: 100 kWh"
        )
        await bus.drain()

        assert result.status == "completed"
        assert result.stage == "completed"
        assert result.match_status == "matched"
        assert result.co2e_kg == Decimal("18.4")
        assert result.snapshot_id

        stored = await docs_repo.get(document.id)
        assert stored is not None
        assert stored.status == "processed"

        states, event_types = await _fetch_events(pool, document.id)
        assert states == _EXPECTED_STATES
        for expected in (
            "DocumentUploaded",
            "ExtractionRequested",
            "ExtractionCompleted",
            "FieldsExtracted",
            "FactorMatched",
            "CalculationRequested",
            "CalculationCompleted",
        ):
            assert expected in event_types, f"missing persisted event {expected}"

        async with pool.acquire() as conn:
            snap_count = await conn.fetchval(
                "SELECT COUNT(*) FROM public.calculation_snapshots WHERE id = $1",
                result.snapshot_id,
            )
            assert int(snap_count or 0) == 1
            log_count = await conn.fetchval(
                "SELECT COUNT(*) FROM public.emissions_logs"
                " WHERE snapshot_id = $1",
                result.snapshot_id,
            )
            assert int(log_count or 0) == 1

        entries = await audit_repo.get_by_correlation(result.run_id)
        actions = {entry.action for entry in entries}
        assert "workflow:state_changed" in actions

        await _cleanup(pool, document.id, result.snapshot_id, factor.id)
    finally:
        server.shutdown()


async def test_low_ai_confidence_routes_to_manual_review(pool: asyncpg.Pool) -> None:
    server, port = _serve(_LlmHandler)
    try:
        _LlmHandler.fields = _llm_fields(confidence=0.2)
        org_id = await make_org(pool)
        factor = await _seed_factor(pool, activity=f"{ACTIVITY} (manual-review)")
        docs_repo = DocumentsRepository(pool)
        bus = EventBus()
        audit_logger = AuditLogger(AuditRepository(pool))
        index = FactorSearchIndex()
        index.load([factor])
        orchestrator = await _wire(pool, port, bus=bus, audit_logger=audit_logger, index=index)

        document = await docs_repo.create_from_upload(
            org_id=org_id,
            storage_path="uploads/invoice.pdf",
            filename="invoice.pdf",
            file_type="pdf",
        )
        result = await orchestrator.process_document(
            document, f"Supplier: Acme Corp\nActivity: {ACTIVITY}"
        )
        await bus.drain()

        assert result.status == "needs_review"
        assert result.stage == "manual_review"
        assert result.snapshot_id == ""
        assert result.co2e_kg == Decimal("0")

        stored = await docs_repo.get(document.id)
        assert stored is not None
        assert stored.status == "manual_review"

        async with pool.acquire() as conn:
            snap_count = await conn.fetchval(
                "SELECT COUNT(*) FROM public.calculation_snapshots"
                " WHERE organization_id = $1",
                org_id,
            )
        assert int(snap_count or 0) == 0

        await _cleanup(pool, document.id, "", factor.id)
    finally:
        server.shutdown()


async def test_workflow_failure_marks_document_failed_and_raises(
    pool: asyncpg.Pool,
) -> None:
    server, port = _serve(_LlmHandler)
    try:
        _LlmHandler.fields = _llm_fields()
        org_id = await make_org(pool)
        factor = await _seed_factor(pool, activity=f"{ACTIVITY} (failure)")
        docs_repo = DocumentsRepository(pool)
        bus = EventBus()
        audit_logger = AuditLogger(AuditRepository(pool))
        index = FactorSearchIndex()
        index.load([factor])
        orchestrator = await _wire(pool, port, bus=bus, audit_logger=audit_logger, index=index)

        document = await docs_repo.create_from_upload(
            org_id=org_id,
            storage_path="uploads/blank.pdf",
            filename="blank.pdf",
            file_type="pdf",
        )
        with pytest.raises(WorkflowMaxRetriesError):
            await orchestrator.process_document(document, "   ")
        await bus.drain()

        stored = await docs_repo.get(document.id)
        assert stored is not None
        assert stored.status == "failed"

        async with pool.acquire() as conn:
            snap_count = await conn.fetchval(
                "SELECT COUNT(*) FROM public.calculation_snapshots"
                " WHERE organization_id = $1",
                org_id,
            )
        assert int(snap_count or 0) == 0

        await _cleanup(pool, document.id, "", factor.id)
    finally:
        server.shutdown()


async def test_registered_handlers_drive_submitted_pipeline(
    pool: asyncpg.Pool,
) -> None:
    server, port = _serve(_LlmHandler)
    try:
        _LlmHandler.fields = _llm_fields()
        org_id = await make_org(pool)
        factor = await _seed_factor(pool)
        docs_repo = DocumentsRepository(pool)
        bus = EventBus()
        audit_logger = AuditLogger(AuditRepository(pool))
        index = FactorSearchIndex()
        index.load([factor])
        orchestrator = await _wire(pool, port, bus=bus, audit_logger=audit_logger, index=index)
        orchestrator.register_handlers()

        document = await docs_repo.create_from_upload(
            org_id=org_id,
            storage_path="uploads/invoice.pdf",
            filename="invoice.pdf",
            file_type="pdf",
        )
        submitted = await orchestrator.submit_document(
            document, f"Supplier: Acme Corp\nActivity: {ACTIVITY}\nQuantity: 100 kWh"
        )
        assert submitted.status == "running"
        await bus.drain()

        stored = await docs_repo.get(document.id)
        assert stored is not None
        assert stored.status == "processed"

        states, _event_types = await _fetch_events(pool, document.id)
        assert states == _EXPECTED_STATES

        async with pool.acquire() as conn:
            snapshot_id = await conn.fetchval(
                "SELECT id FROM public.calculation_snapshots"
                " WHERE organization_id = $1 ORDER BY calculated_at DESC LIMIT 1",
                org_id,
            )
        await _cleanup(pool, document.id, snapshot_id or "", factor.id)
    finally:
        server.shutdown()

