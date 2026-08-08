"""Unit tests for engines.workflow (Phase 8 Workflow Orchestrator).

Uses in-memory fakes for the repository sinks and the four engines so every
pipeline branch is tested deterministically without a database.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

import pytest

from core.exceptions import (
    AIExtractionFailedError,
    ExtractionFailedError,
    WorkflowInvalidTransitionError,
    WorkflowMaxRetriesError,
)
from domain.calculation import CalculationMethodology, CalculationSnapshot
from domain.document import (
    Document,
    ExtractedPage,
    ExtractionField,
    ExtractionResult,
)
from domain.factor import EmissionFactor
from domain.matching import MatchRequest, MatchResult
from domain.workflow import DomainEvent, FieldsExtracted, WorkflowStateChanged
from engines.calculation import CalculationRequest
from engines.workflow import (
    DOCUMENT_STATUS_MAP,
    InvoiceActivityResolver,
    WorkflowOrchestrator,
    WorkflowResult,
)
from infra.event_bus import EventBus


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def make_document(**kwargs: object) -> Document:
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


def make_factor(*, activity: str = "Natural gas") -> EmissionFactor:
    return EmissionFactor(
        id="factor-1",
        reporting_year=2025,
        activity_type=activity,
        co2e_multiplier=Decimal("0.18400"),
        unit="kWh",
        scope="Scope 1",
        factor_source="DEFRA-DESNZ",
        factor_set="DEFRA-2025",
        country="GB",
        provider_key="defra",
    )


def ai_fields(*, confidence: float = 0.95) -> tuple[ExtractionField, ...]:
    return (
        ExtractionField(field_name="activity", value="Natural gas", confidence=confidence, source="ai"),
        ExtractionField(field_name="quantity", value="100", confidence=confidence, source="ai"),
        ExtractionField(field_name="unit", value="kWh", confidence=confidence, source="ai"),
        ExtractionField(field_name="country", value="GB", confidence=confidence, source="ai"),
        ExtractionField(field_name="date", value="2025-06-01", confidence=confidence, source="ai"),
    )


# ---------------------------------------------------------------------------
# In-memory fakes (structurally satisfy the engine protocols)
# ---------------------------------------------------------------------------


class FakeDocumentRepo:
    def __init__(self, document: Document) -> None:
        self._docs: dict[str, Document] = {document.id: document}
        self.updates: list[tuple[str, str]] = []

    async def get(self, id: str) -> Optional[Document]:
        return self._docs.get(id)

    async def update_status(self, doc_id: str, status: str) -> Document:
        current = self._docs[doc_id]
        updated = Document(
            id=current.id,
            organization_id=current.organization_id,
            filename=current.filename,
            storage_path=current.storage_path,
            file_type=current.file_type,
            status=status,
            uploaded_at=current.uploaded_at,
            uploaded_by=current.uploaded_by,
        )
        self._docs[doc_id] = updated
        self.updates.append((doc_id, status))
        return updated


class FakeEventRepo:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def store(self, event: DomainEvent) -> DomainEvent:
        self.events.append(event)
        return event


class FakeExtractionEngine:
    def __init__(self, *, fail_times: int = 0) -> None:
        self.calls = 0
        self.fail_times = fail_times

    async def extract(self, document: Document, text: str) -> ExtractionResult:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ExtractionFailedError("extraction failed")
        return ExtractionResult(
            raw_text=text,
            pages=(ExtractedPage(page_number=1, text=text, confidence=1.0),),
            tables=(),
            metadata={"field_count": 1, "fields": {"supplier": "Acme Corp"}},
            confidence=1.0,
        )


class FakeAIExtractionEngine:
    def __init__(
        self,
        *,
        fields: Optional[tuple[ExtractionField, ...]] = None,
        fail_times: int = 0,
    ) -> None:
        self.calls = 0
        self.fail_times = fail_times
        self.fields = fields if fields is not None else ai_fields()

    async def extract_fields(
        self, document: Document, text: str
    ) -> tuple[ExtractionField, ...]:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise AIExtractionFailedError("ai extraction failed")
        return self.fields


class FakeMatchingEngine:
    def __init__(self, *, status: str = "matched") -> None:
        self.calls = 0
        self.status = status
        self.requests: list[MatchRequest] = []

    async def match(self, request: MatchRequest) -> MatchResult:
        self.calls += 1
        self.requests.append(request)
        if self.status == "matched":
            return MatchResult(
                status="matched",
                factor=make_factor(),
                confidence=1.0,
                methodology="exact_match",
                provider="defra",
                stages_executed=("exact_match",),
                request_id=request.id,
            )
        if self.status == "no_match":
            return MatchResult.no_match(
                suggestions=[], stages_executed=[], request_id=request.id
            )
        return MatchResult(status="ambiguous", request_id=request.id)


class FakeCalculationEngine:
    def __init__(self) -> None:
        self.calls = 0
        self.requests: list[CalculationRequest] = []

    async def calculate(self, request: CalculationRequest) -> object:
        self.calls += 1
        self.requests.append(request)
        co2e_kg = request.quantity * request.factor.co2e_multiplier
        snapshot = CalculationSnapshot(
            id="snapshot-1",
            match_request_id=request.match_request_id,
            organization_id=request.organization_id,
            factor_id=request.factor.id,
            quantity=request.quantity,
            quantity_unit=request.quantity_unit,
            co2e_multiplier=request.factor.co2e_multiplier,
            co2e_kg=co2e_kg,
            scope=request.scope,
            date=request.date,
            reporting_year=request.reporting_year,
            methodology=request.methodology,
            algorithm_version="v1.0-test",
            created_at=date(2025, 6, 1),
        )
        from domain.calculation import CalculationResult

        return CalculationResult(
            co2e_kg=co2e_kg,
            co2e_tonnes=co2e_kg / Decimal("1000"),
            snapshot=snapshot,
            factor_used=request.factor,
            methodology=CalculationMethodology.DIRECT_MULTIPLY,
        )


class Harness:
    """Wires an orchestrator over the in-memory fakes."""

    def __init__(
        self,
        *,
        document: Optional[Document] = None,
        matching_status: str = "matched",
        ai_fields_override: Optional[tuple[ExtractionField, ...]] = None,
        extraction_fail_times: int = 0,
        ai_fail_times: int = 0,
        max_retries: int = 3,
        ai_confidence_threshold: float = 0.5,
        auto_review: bool = True,
        bus: Optional[EventBus] = None,
    ) -> None:
        self.document = document or make_document()
        self.docs = FakeDocumentRepo(self.document)
        self.events = FakeEventRepo()
        self.extraction = FakeExtractionEngine(fail_times=extraction_fail_times)
        self.ai = FakeAIExtractionEngine(
            fields=ai_fields_override, fail_times=ai_fail_times
        )
        self.matching = FakeMatchingEngine(status=matching_status)
        self.calculation = FakeCalculationEngine()
        self.bus = bus or EventBus()
        self.orchestrator = WorkflowOrchestrator(
            self.docs,
            self.events,
            extraction_engine=self.extraction,  # type: ignore[arg-type]
            ai_extraction_engine=self.ai,  # type: ignore[arg-type]
            matching_engine=self.matching,  # type: ignore[arg-type]
            calculation_engine=self.calculation,  # type: ignore[arg-type]
            event_bus=self.bus,
            max_retries=max_retries,
            ai_confidence_threshold=ai_confidence_threshold,
            auto_review=auto_review,
        )

    def state_sequence(self) -> list[tuple[str, str]]:
        return [
            (event.from_state, event.to_state)
            for event in self.events.events
            if isinstance(event, WorkflowStateChanged)
        ]
# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------


def test_constructor_requires_all_dependencies() -> None:
    doc = make_document()
    with pytest.raises(ValueError, match="documents_repo"):
        WorkflowOrchestrator(
            None,  # type: ignore[arg-type]
            FakeEventRepo(),
            extraction_engine=FakeExtractionEngine(),  # type: ignore[arg-type]
            ai_extraction_engine=FakeAIExtractionEngine(),  # type: ignore[arg-type]
            matching_engine=FakeMatchingEngine(),  # type: ignore[arg-type]
            calculation_engine=FakeCalculationEngine(),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="events_repo"):
        WorkflowOrchestrator(
            FakeDocumentRepo(doc),
            None,  # type: ignore[arg-type]
            extraction_engine=FakeExtractionEngine(),  # type: ignore[arg-type]
            ai_extraction_engine=FakeAIExtractionEngine(),  # type: ignore[arg-type]
            matching_engine=FakeMatchingEngine(),  # type: ignore[arg-type]
            calculation_engine=FakeCalculationEngine(),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="max_retries"):
        WorkflowOrchestrator(
            FakeDocumentRepo(doc),
            FakeEventRepo(),
            extraction_engine=FakeExtractionEngine(),  # type: ignore[arg-type]
            ai_extraction_engine=FakeAIExtractionEngine(),  # type: ignore[arg-type]
            matching_engine=FakeMatchingEngine(),  # type: ignore[arg-type]
            calculation_engine=FakeCalculationEngine(),  # type: ignore[arg-type]
            max_retries=0,
        )
    with pytest.raises(ValueError, match="ai_confidence_threshold"):
        WorkflowOrchestrator(
            FakeDocumentRepo(doc),
            FakeEventRepo(),
            extraction_engine=FakeExtractionEngine(),  # type: ignore[arg-type]
            ai_extraction_engine=FakeAIExtractionEngine(),  # type: ignore[arg-type]
            matching_engine=FakeMatchingEngine(),  # type: ignore[arg-type]
            calculation_engine=FakeCalculationEngine(),  # type: ignore[arg-type]
            ai_confidence_threshold=1.5,
        )


def test_register_handlers_requires_event_bus() -> None:
    doc = make_document()
    orchestrator = WorkflowOrchestrator(
        FakeDocumentRepo(doc),
        FakeEventRepo(),
        extraction_engine=FakeExtractionEngine(),  # type: ignore[arg-type]
        ai_extraction_engine=FakeAIExtractionEngine(),  # type: ignore[arg-type]
        matching_engine=FakeMatchingEngine(),  # type: ignore[arg-type]
        calculation_engine=FakeCalculationEngine(),  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="event_bus"):
        orchestrator.register_handlers()


# ---------------------------------------------------------------------------
# Default activity resolver
# ---------------------------------------------------------------------------


def test_invoice_activity_resolver_maps_fields() -> None:
    resolver = InvoiceActivityResolver()
    document = make_document()
    result = resolver.resolve(
        document,
        {
            "activity": "Natural gas",
            "quantity": "100.5",
            "unit": "kWh",
            "country": "IE",
            "scope": "Scope 1",
            "date": "2025-06-01",
        },
    )
    assert result is not None
    assert result.activity == "Natural gas"
    assert result.country == "IE"
    assert result.quantity == Decimal("100.5")
    assert result.quantity_unit == "kWh"
    assert result.scope == "Scope 1"
    assert result.reporting_year == 2025
    assert result.date == date(2025, 6, 1)


def test_invoice_activity_resolver_uses_fallbacks() -> None:
    resolver = InvoiceActivityResolver(default_country="IE")
    document = make_document()
    result = resolver.resolve(document, {"activity_type": "Diesel"})
    assert result is not None
    assert result.activity == "Diesel"
    assert result.country == "IE"
    assert result.quantity is None
    assert result.reporting_year == document.uploaded_at.year


def test_invoice_activity_resolver_rejects_missing_activity() -> None:
    resolver = InvoiceActivityResolver()
    document = make_document()
    assert resolver.resolve(document, {"supplier": "Acme Corp"}) is None
    assert resolver.resolve(document, {"activity": "   "}) is None


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_process_document_completes_full_pipeline() -> None:
    harness = Harness()
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()

    assert isinstance(result, WorkflowResult)
    assert result.status == "completed"
    assert result.stage == "completed"
    assert result.match_status == "matched"
    assert result.snapshot_id == "snapshot-1"
    assert result.co2e_kg == Decimal("18.40000")
    assert result.confidence == 0.95
    assert result.error == ""

    assert harness.extraction.calls == 1
    assert harness.ai.calls == 1
    assert harness.matching.calls == 1
    assert harness.calculation.calls == 1

    assert harness.docs.updates[-1] == (harness.document.id, "processed")
    assert DOCUMENT_STATUS_MAP["completed"] == "processed"


async def test_process_document_persists_ordered_state_sequence() -> None:
    harness = Harness()
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()
    assert result.status == "completed"

    assert harness.state_sequence() == [
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
    event_types = [type(event).__name__ for event in harness.events.events]
    assert event_types == [
        "WorkflowStateChanged",
        "WorkflowStateChanged",
        "WorkflowStateChanged",
        "DocumentUploaded",
        "ExtractionRequested",
        "WorkflowStateChanged",
        "WorkflowStateChanged",
        "WorkflowStateChanged",
        "WorkflowStateChanged",
        "WorkflowStateChanged",
        "WorkflowStateChanged",
    ]


async def test_submit_document_returns_early_when_unhandled() -> None:
    harness = Harness(bus=EventBus())
    result = await harness.orchestrator.submit_document(
        harness.document, "Supplier: Acme Corp"
    )
    assert result.status == "running"
    assert result.stage == "extracting"
    assert harness.extraction.calls == 0
    assert harness.ai.calls == 0
    assert harness.calculation.calls == 0
    # document is mid-flight: the abstract state persists as "processing"
    assert harness.docs.updates[-1] == (harness.document.id, "processing")

# ---------------------------------------------------------------------------
# Routing: manual_review / customer_review
# ---------------------------------------------------------------------------


async def test_low_ai_confidence_routes_to_manual_review() -> None:
    harness = Harness(ai_fields_override=ai_fields(confidence=0.3))
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()

    assert result.status == "needs_review"
    assert result.stage == "manual_review"
    assert harness.matching.calls == 0
    assert harness.calculation.calls == 0
    assert harness.docs.updates[-1] == (harness.document.id, "manual_review")
    assert ("ai_matching", "manual_review") in harness.state_sequence()


async def test_missing_activity_routes_to_manual_review() -> None:
    fields = (
        ExtractionField(
            field_name="supplier", value="Acme", confidence=0.9, source="ai"
        ),
    )
    harness = Harness(ai_fields_override=fields)
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()

    assert result.status == "needs_review"
    assert result.stage == "manual_review"
    assert harness.matching.calls == 0
    assert harness.calculation.calls == 0


async def test_no_match_routes_to_manual_review() -> None:
    harness = Harness(matching_status="no_match")
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()

    assert result.status == "needs_review"
    assert result.stage == "manual_review"
    assert result.match_status == "no_match"
    assert harness.matching.calls == 1
    assert harness.calculation.calls == 0


async def test_auto_review_false_stops_at_customer_review() -> None:
    harness = Harness(auto_review=False)
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()

    assert result.status == "needs_review"
    assert result.stage == "customer_review"
    assert result.match_status == "matched"
    assert harness.calculation.calls == 0


# ---------------------------------------------------------------------------
# Failures, retries, idempotency
# ---------------------------------------------------------------------------


async def test_extraction_failure_is_retried_then_completes() -> None:
    harness = Harness(extraction_fail_times=2)
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()

    assert harness.extraction.calls == 3
    assert result.status == "completed"


async def test_exhausted_retries_fail_document_and_raise() -> None:
    harness = Harness(extraction_fail_times=99, max_retries=2)
    with pytest.raises(WorkflowMaxRetriesError):
        await harness.orchestrator.process_document(
            harness.document, "Supplier: Acme Corp"
        )
    await harness.bus.drain()

    assert harness.extraction.calls == 3
    assert harness.calculation.calls == 0
    assert harness.docs.updates[-1] == (harness.document.id, "failed")
    assert ("extracting", "failed") in harness.state_sequence()


async def test_ai_failure_is_retried_then_completes() -> None:
    harness = Harness(ai_fail_times=1)
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()
    assert harness.ai.calls == 2
    assert result.status == "completed"


async def test_resubmit_after_completion_is_idempotent() -> None:
    harness = Harness()
    first = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()
    assert first.status == "completed"

    second = await harness.orchestrator.process_document(
        harness.document, "different text"
    )
    await harness.bus.drain()

    assert second == first
    assert harness.calculation.calls == 1
    assert harness.extraction.calls == 1


async def test_resubmit_while_active_raises() -> None:
    harness = Harness()
    submitted = await harness.orchestrator.submit_document(
        harness.document, "Supplier: Acme Corp"
    )
    assert submitted.status == "running"
    with pytest.raises(WorkflowInvalidTransitionError, match="active workflow"):
        await harness.orchestrator.process_document(
            harness.document, "Supplier: Acme Corp"
        )


async def test_document_already_processed_cannot_restart() -> None:
    document = make_document(status="processed")
    harness = Harness(document=document)
    with pytest.raises(WorkflowInvalidTransitionError, match="cannot start"):
        await harness.orchestrator.process_document(
            harness.document, "Supplier: Acme Corp"
        )


# ---------------------------------------------------------------------------
# Event handlers (§8.2)
# ---------------------------------------------------------------------------


async def test_registered_handlers_drive_submitted_pipeline() -> None:
    harness = Harness()
    harness.orchestrator.register_handlers()
    assert harness.orchestrator.handlers_registered is True

    result = await harness.orchestrator.submit_document(
        harness.document, "Supplier: Acme Corp"
    )
    assert result.status == "running"
    await harness.bus.drain()

    assert harness.extraction.calls == 1
    assert harness.ai.calls == 1
    assert harness.matching.calls == 1
    assert harness.calculation.calls == 1
    assert harness.docs.updates[-1] == (harness.document.id, "processed")


async def test_register_handlers_is_idempotent() -> None:
    harness = Harness()
    harness.orchestrator.register_handlers()
    harness.orchestrator.register_handlers()
    assert harness.bus.subscriber_count() == 3


async def test_duplicate_fields_event_does_not_duplicate_calculation() -> None:
    harness = Harness()
    result = await harness.orchestrator.process_document(
        harness.document, "Supplier: Acme Corp"
    )
    await harness.bus.drain()
    assert result.status == "completed"
    assert harness.calculation.calls == 1

    await harness.bus.publish_and_wait(
        FieldsExtracted(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(timezone.utc),
            correlation_id="dup-correlation",
            document_id=harness.document.id,
            fields={"activity": "Natural gas"},
            confidence=1.0,
        )
    )
    assert harness.calculation.calls == 1

