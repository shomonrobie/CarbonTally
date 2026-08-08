"""Workflow orchestration engine (Backend v2.1 §7, §14; prep-pack Phase 8).

The :class:`WorkflowOrchestrator` sits *above* the engines and coordinates the
document-processing pipeline described by :data:`domain.workflow.DOCUMENT_PIPELINE`
(§14.4). It never re-implements extraction, matching or calculation logic — those
stay in the Phase 4/6/7 engines — but drives them in the state-machine order,
guarding every stage with the workflow definition and per-run latches so that
duplicate or replayed events can never run a stage twice.

Stage model
-----------
* Abstract workflow states (``pending`` → ``uploaded`` → ``classifying`` →
  ``extracting`` → ``ai_matching`` → ``matched`` → ``customer_review`` →
  ``reviewed`` → ``calculating`` → ``completed`` | ``manual_review`` | ``failed``)
  are tracked per run and persisted as ``WorkflowStateChanged`` events through
  the events repository.
* The ``customer_documents.status`` column only accepts the RC2 vocabulary
  (``uploaded``/``pending``/``processing``/``processed``/``manual_review``/``failed``),
  so the orchestrator maps abstract states through :data:`DOCUMENT_STATUS_MAP`:
  every in-flight state persists as ``processing`` and success as ``processed``.

Event handlers (§8.2)
---------------------
:meth:`WorkflowOrchestrator.register_handlers` subscribes typed handlers for
``DocumentUploaded``, ``FieldsExtracted`` and ``FactorMatched``. Each handler is
small and orchestration-focused: it delegates the actual work to the matching
engine via the same guarded stage methods and is a no-op for every event that
does not apply to the run's current stage (idempotent re-entry). The
``EventBus`` isolates any handler failure from the publisher and other handlers.

Dependency rules: this module imports only from ``core``, ``domain``, ``infra``
and sibling ``engines`` modules — never ``data`` and never the API layer.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Mapping, Optional, Protocol, cast

from core.exceptions import (
    CarbonTallyError,
    WorkflowInvalidTransitionError,
    WorkflowMaxRetriesError,
)
from core.logging import get_logger
from domain.document import Document, ExtractionField, ExtractionResult
from domain.matching import MatchRequest, MatchResult
from domain.workflow import (
    DOCUMENT_PIPELINE,
    DocumentUploaded,
    DomainEvent,
    ExtractionRequested,
    FactorMatched,
    FieldsExtracted,
    WorkflowDefinition,
    WorkflowStateChanged,
)
from engines.ai_extraction import AIExtractionEngine
from engines.calculation import CalculationEngine, CalculationRequest
from engines.extraction import DocumentExtractionEngine
from engines.factor_matching import FactorMatchingEngine
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus, EventHandler

logger = get_logger(__name__)

#: Maps the abstract document-pipeline states (Backend v2.1 §14.4) to the
#: status vocabulary permitted by the ``customer_documents_status_in_list``
#: CHECK constraint (``uploaded/pending/processing/processed/manual_review/failed``).
#: All in-flight pipeline stages persist as ``processing``; a completed pipeline
#: persists as ``processed``.
DOCUMENT_STATUS_MAP: Mapping[str, str] = {
    "pending": "pending",
    "uploaded": "uploaded",
    "classifying": "processing",
    "extracting": "processing",
    "ai_matching": "processing",
    "matched": "processing",
    "customer_review": "processing",
    "reviewed": "processing",
    "calculating": "processing",
    "completed": "processed",
    "manual_review": "manual_review",
    "failed": "failed",
}

#: Field names the default resolver reads out of the AI-extracted fields.
_ACTIVITY_FIELDS = ("activity", "activity_type")


class WorkflowDocumentSink(Protocol):
    """The document-repository surface used for workflow persistence.

    Satisfied structurally by :class:`data.documents.DocumentsRepository`.
    """

    async def get(self, id: str) -> Optional[Document]: ...

    async def update_status(self, doc_id: str, status: str) -> Document: ...


class WorkflowEventSink(Protocol):
    """The append-only event-repository surface used by the orchestrator.

    Satisfied structurally by :class:`data.events.EventsRepository`.
    """

    async def store(self, event: DomainEvent) -> DomainEvent: ...


@dataclass(frozen=True, slots=True)
class MatchInput:
    """Consumption facts the workflow derives from extraction for matching.

    The ``ai_matching`` stage turns the extracted fields into this value; the
    orchestrator turns it into a :class:`MatchRequest` and (after a successful
    match) a :class:`CalculationRequest`.
    """

    activity: str
    country: str = "GB"
    reporting_year: int = 0
    unit: Optional[str] = None
    scope: Optional[str] = None
    quantity: Optional[Decimal] = None
    quantity_unit: Optional[str] = None
    date: Optional[date] = None


class ActivityResolver(Protocol):
    """Derives the consumption facts for matching from the extracted fields.

    Returns ``None`` when the fields do not describe a matchable activity
    (the orchestrator then routes the run to ``manual_review``).
    """

    def resolve(
        self, document: Document, fields: Mapping[str, str]
    ) -> Optional[MatchInput]: ...


class InvoiceActivityResolver:
    """Deterministic default field → :class:`MatchInput` mapping.

    Reads ``activity`` (or ``activity_type``), ``country`` (default ``GB``),
    ``reporting_year`` (or the year of the ``date`` field, or the upload year),
    ``unit``/``quantity_unit``, ``scope`` and ``quantity`` from the extracted
    fields. Returns ``None`` when no activity is present.
    """

    def __init__(self, default_country: str = "GB") -> None:
        if not default_country.strip():
            raise ValueError("default_country must not be empty")
        self._default_country = default_country.strip()

    def resolve(
        self, document: Document, fields: Mapping[str, str]
    ) -> Optional[MatchInput]:
        activity = ""
        for name in _ACTIVITY_FIELDS:
            candidate = fields.get(name)
            if candidate and candidate.strip():
                activity = candidate.strip()
                break
        if not activity:
            return None
        return MatchInput(
            activity=activity,
            country=_clean(fields.get("country")) or self._default_country,
            reporting_year=_parse_year(fields.get("reporting_year"))
            or _year_from_date(fields.get("date"))
            or document.uploaded_at.year,
            unit=_clean(fields.get("unit")),
            scope=_clean(fields.get("scope")),
            quantity=_parse_decimal(fields.get("quantity")),
            quantity_unit=_clean(fields.get("quantity_unit") or fields.get("unit")),
            date=_parse_date(fields.get("date")),
        )


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """The outcome of a workflow run for one document."""

    run_id: str
    document_id: str
    status: str
    stage: str
    snapshot_id: str = ""
    co2e_kg: Decimal = Decimal("0")
    confidence: float = 0.0
    match_status: str = ""
    error: str = ""


@dataclass(slots=True)
class _WorkflowRun:
    """Mutable per-document pipeline state (in-memory; never persisted as-is)."""

    document: Document
    document_id: str
    correlation_id: str
    applied_by: str
    stage: str = "extracting"
    status: str = "running"
    retries: int = 0
    error: str = ""
    extraction: Optional[ExtractionResult] = None
    ai_fields: tuple[ExtractionField, ...] = ()
    ai_confidence: float = 0.0
    match_request: Optional[MatchRequest] = None
    match_result: Optional[MatchResult] = None
    match_input: Optional[MatchInput] = None
    snapshot_id: str = ""
    co2e_kg: Decimal = Decimal("0")
    extraction_started: bool = False
    ai_started: bool = False
    ai_completed: bool = False
    matching_started: bool = False
    calculating_started: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class WorkflowOrchestrator:
    """Coordinates the document pipeline across the processing engines.

    Args:
        documents_repo: Repository used for document status transitions.
        events_repo: Repository used to persist workflow/domain events.
        extraction_engine: Phase 7 regex document-extraction engine.
        ai_extraction_engine: Phase 7 AI field-extraction engine.
        matching_engine: Phase 4 factor-matching engine.
        calculation_engine: Phase 6 calculation engine.
        event_bus: Optional bus receiving the workflow's domain events.
        audit_logger: Optional logger that records every transition and failure.
        state_machine: The workflow definition to enforce (defaults to
            :data:`DOCUMENT_PIPELINE`).
        max_retries: Bounded retry allowance for a failing stage before the run
            is failed (default 3).
        ai_confidence_threshold: Below this aggregate AI confidence the run is
            routed to ``manual_review`` instead of matching (default 0.5).
        auto_review: When ``True`` (Phase 8 default) the orchestrator advances
            ``customer_review`` → ``reviewed`` automatically; when ``False`` it
            stops at ``customer_review`` for a future review API to drive.
        activity_resolver: Field → :class:`MatchInput` mapping used by the
            ``ai_matching`` stage (defaults to :class:`InvoiceActivityResolver`).
    """

    def __init__(
        self,
        documents_repo: WorkflowDocumentSink,
        events_repo: WorkflowEventSink,
        *,
        extraction_engine: DocumentExtractionEngine,
        ai_extraction_engine: AIExtractionEngine,
        matching_engine: FactorMatchingEngine,
        calculation_engine: CalculationEngine,
        event_bus: Optional[EventBus] = None,
        audit_logger: Optional[AuditLogger] = None,
        state_machine: WorkflowDefinition = DOCUMENT_PIPELINE,
        max_retries: int = 3,
        ai_confidence_threshold: float = 0.5,
        auto_review: bool = True,
        activity_resolver: Optional[ActivityResolver] = None,
    ) -> None:
        if documents_repo is None:
            raise ValueError("documents_repo must not be None")
        if events_repo is None:
            raise ValueError("events_repo must not be None")
        if extraction_engine is None:
            raise ValueError("extraction_engine must not be None")
        if ai_extraction_engine is None:
            raise ValueError("ai_extraction_engine must not be None")
        if matching_engine is None:
            raise ValueError("matching_engine must not be None")
        if calculation_engine is None:
            raise ValueError("calculation_engine must not be None")
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if not 0.0 <= ai_confidence_threshold <= 1.0:
            raise ValueError("ai_confidence_threshold must be in [0, 1]")
        self._documents_repo = documents_repo
        self._events_repo = events_repo
        self._extraction_engine = extraction_engine
        self._ai_extraction_engine = ai_extraction_engine
        self._matching_engine = matching_engine
        self._calculation_engine = calculation_engine
        self._event_bus = event_bus
        self._audit_logger = audit_logger
        self._state_machine = state_machine
        self._max_retries = max_retries
        self._ai_confidence_threshold = ai_confidence_threshold
        self._auto_review = auto_review
        self._activity_resolver = activity_resolver or InvoiceActivityResolver()
        self._runs: dict[str, _WorkflowRun] = {}
        self._texts: dict[str, str] = {}
        self._handlers_registered = False


    @property
    def state_machine(self) -> WorkflowDefinition:
        """The workflow definition enforced by this orchestrator."""
        return self._state_machine

    @property
    def max_retries(self) -> int:
        """The per-stage retry allowance before a run is failed."""
        return self._max_retries

    @property
    def ai_confidence_threshold(self) -> float:
        """The confidence below which a run routes to ``manual_review``."""
        return self._ai_confidence_threshold

    @property
    def auto_review(self) -> bool:
        """Whether ``customer_review`` is auto-approved by the orchestrator."""
        return self._auto_review

    @property
    def handlers_registered(self) -> bool:
        """Whether :meth:`register_handlers` has been called."""
        return self._handlers_registered

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register_handlers(self) -> None:
        """Subscribe the workflow's typed event handlers on the event bus.

        Idempotent: calling twice does not duplicate subscriptions. Requires
        the orchestrator to have been constructed with an ``event_bus``.
        """
        if self._event_bus is None:
            raise ValueError("an event_bus is required to register workflow handlers")
        if self._handlers_registered:
            return
        self._event_bus.subscribe(
            DocumentUploaded, cast(EventHandler, self._on_document_uploaded)
        )
        self._event_bus.subscribe(
            FieldsExtracted, cast(EventHandler, self._on_fields_extracted)
        )
        self._event_bus.subscribe(
            FactorMatched, cast(EventHandler, self._on_factor_matched)
        )
        self._handlers_registered = True

    async def submit_document(
        self,
        document: Document,
        text: str,
        *,
        correlation_id: Optional[str] = None,
        applied_by: str = "workflow_orchestrator",
    ) -> WorkflowResult:
        """Start the pipeline for ``document`` and return immediately.

        The document is transitioned through ``pending → uploaded →
        classifying → extracting`` and a ``DocumentUploaded`` event is
        published. Registered handlers (see :meth:`register_handlers`) drive
        the remaining stages asynchronously. Resubmitting a document whose run
        already reached a terminal state returns that run's result unchanged
        (idempotent); resubmitting while a run is active raises
        :class:`WorkflowInvalidTransitionError`.
        """
        run = await self._start_run(document, text, correlation_id, applied_by)
        return self._result(run)

    async def process_document(
        self,
        document: Document,
        text: str,
        *,
        correlation_id: Optional[str] = None,
        applied_by: str = "workflow_orchestrator",
    ) -> WorkflowResult:
        """Run the full pipeline for ``document`` to completion.

        The deterministic, request-scoped path: every stage runs in order and
        every emitted event is awaited before returning the final
        :class:`WorkflowResult`. Genuine business failures (exhausted retries,
        engine errors) propagate to the caller; the document is marked
        ``failed`` and a ``WorkflowStateChanged`` event is persisted first.
        """
        run = await self._start_run(document, text, correlation_id, applied_by)
        if run.status == "running":
            await self._drive(run)
            if self._event_bus is not None:
                await self._event_bus.drain()
        return self._result(run)

    # ------------------------------------------------------------------
    # Pipeline start
    # ------------------------------------------------------------------

    async def _start_run(
        self,
        document: Document,
        text: str,
        correlation_id: Optional[str],
        applied_by: str,
    ) -> _WorkflowRun:
        if document is None or not document.id:
            raise ValueError("document and document.id are required")
        existing = self._runs.get(document.id)
        if existing is not None:
            if existing.status == "running":
                raise WorkflowInvalidTransitionError(
                    f"document {document.id!r} already has an active workflow run"
                )
            return existing
        stored = await self._documents_repo.get(document.id)
        start_status = stored.status if stored is not None else document.status
        if start_status not in ("pending", "uploaded"):
            raise WorkflowInvalidTransitionError(
                f"document {document.id!r} cannot start the pipeline "
                f"from status {start_status!r}"
            )
        run = _WorkflowRun(
            document=document,
            document_id=document.id,
            correlation_id=correlation_id or str(uuid.uuid4()),
            applied_by=applied_by,
        )
        self._runs[document.id] = run
        self._texts[document.id] = text
        try:
            if start_status == "pending":
                await self._transition(run, "pending", "uploaded")
            await self._transition(run, "uploaded", "classifying")
            await self._transition(run, "classifying", "extracting")
        except Exception:
            self._runs.pop(document.id, None)
            self._texts.pop(document.id, None)
            raise
        await self._emit(
            DocumentUploaded(
                event_id=str(uuid.uuid4()),
                occurred_at=datetime.now(timezone.utc),
                correlation_id=run.correlation_id,
                document_id=document.id,
                organization_id=document.organization_id,
                storage_path=document.storage_path,
            ),
            run,
        )
        return run


    # ------------------------------------------------------------------
    # Stage driving
    # ------------------------------------------------------------------

    async def _drive(self, run: _WorkflowRun) -> None:
        """Advance ``run`` through every pending stage, in state-machine order.

        Serialised per run by ``run.lock``; every stage is further guarded by a
        latch so concurrent or duplicate drives can never run a stage twice.
        """
        async with run.lock:
            while (
                run.status == "running"
                and run.stage in ("extracting", "ai_matching", "calculating")
            ):
                stage = run.stage
                try:
                    if stage == "extracting" and not run.extraction_started:
                        await self._run_extraction(run)
                    elif stage == "ai_matching" and not run.ai_started:
                        await self._run_ai(run)
                    elif (
                        stage == "ai_matching"
                        and run.ai_completed
                        and not run.matching_started
                    ):
                        await self._run_matching(run)
                    elif stage == "calculating" and not run.calculating_started:
                        await self._run_calculation(run)
                    else:
                        break
                except WorkflowInvalidTransitionError:
                    raise
                except CarbonTallyError as exc:
                    run.retries += 1
                    if run.retries > self._max_retries:
                        await self._fail(
                            run,
                            f"{stage} stage failed after "
                            f"{self._max_retries} retries: {exc}",
                        )
                        raise WorkflowMaxRetriesError(
                            f"workflow for document {run.document_id!r} exhausted "
                            f"retries at {stage!r}: {exc}"
                        ) from exc
                    logger.warning(
                        "workflow stage %s failed for document %s "
                        "(attempt %d/%d): %s",
                        stage,
                        run.document_id,
                        run.retries,
                        self._max_retries,
                        exc,
                    )
                    self._reset_stage_latches(run, stage)
                    try:
                        await self._documents_repo.update_status(
                            run.document_id, DOCUMENT_STATUS_MAP[stage]
                        )
                    except Exception:  # noqa: BLE001 - best effort before retry
                        logger.exception(
                            "failed to restore document status before workflow retry"
                        )
                except Exception as exc:
                    await self._fail(run, f"{stage} stage failed: {exc}")
                    raise

    def _reset_stage_latches(self, run: _WorkflowRun, stage: str) -> None:
        """Clear the guard latches so a failed stage can be retried."""
        if stage == "extracting":
            run.extraction_started = False
        elif stage == "ai_matching":
            run.ai_started = False
            run.ai_completed = False
            run.matching_started = False
        elif stage == "calculating":
            run.calculating_started = False

    async def _run_extraction(self, run: _WorkflowRun) -> None:
        document = await self._documents_repo.get(run.document_id)
        if document is None:
            raise RuntimeError(f"document {run.document_id!r} does not exist")
        run.document = document
        run.extraction_started = True
        text = self._texts.get(run.document_id, "")
        await self._emit(
            ExtractionRequested(
                event_id=str(uuid.uuid4()),
                occurred_at=datetime.now(timezone.utc),
                correlation_id=run.correlation_id,
                document_id=run.document_id,
            ),
            run,
        )
        result = await self._extraction_engine.extract(document, text)
        run.extraction = result
        await self._transition(run, "extracting", "ai_matching")

    async def _run_ai(self, run: _WorkflowRun) -> None:
        document = await self._documents_repo.get(run.document_id)
        if document is None:
            raise RuntimeError(f"document {run.document_id!r} does not exist")
        run.document = document
        run.ai_started = True
        text = self._texts.get(run.document_id, "")
        fields = await self._ai_extraction_engine.extract_fields(document, text)
        run.ai_fields = fields
        run.ai_confidence = (
            sum(field.confidence for field in fields) / len(fields) if fields else 0.0
        )
        run.ai_completed = True


    async def _run_matching(self, run: _WorkflowRun) -> None:
        run.matching_started = True
        if run.ai_confidence < self._ai_confidence_threshold:
            await self._transition(run, "ai_matching", "manual_review")
            run.status = "needs_review"
            return
        fields_map = {field.field_name: field.value for field in run.ai_fields}
        match_input = self._activity_resolver.resolve(run.document, fields_map)
        if match_input is None or not match_input.activity.strip():
            await self._transition(run, "ai_matching", "manual_review")
            run.status = "needs_review"
            return
        request = MatchRequest(
            id=str(uuid.uuid4()),
            activity=match_input.activity,
            country=match_input.country,
            reporting_year=match_input.reporting_year,
            unit=match_input.unit,
            scope=match_input.scope,
            organization_id=run.document.organization_id,
        )
        run.match_request = request
        result = await self._matching_engine.match(request)
        run.match_result = result
        if result.status != "matched" or result.factor is None:
            await self._transition(run, "ai_matching", "manual_review")
            run.status = "needs_review"
            return
        run.match_input = match_input
        await self._transition(run, "ai_matching", "matched")
        await self._transition(run, "matched", "customer_review")
        if not self._auto_review:
            run.status = "needs_review"
            return
        await self._transition(run, "customer_review", "reviewed")
        await self._transition(run, "reviewed", "calculating")

    async def _run_calculation(self, run: _WorkflowRun) -> None:
        run.calculating_started = True
        match_input = run.match_input
        factor = run.match_result.factor if run.match_result is not None else None
        match_request = run.match_request
        if match_input is None or factor is None or match_request is None:
            raise WorkflowInvalidTransitionError(
                f"document {run.document_id!r} reached calculation "
                "without a matched factor"
            )
        if match_input.quantity is None or match_input.quantity_unit is None:
            raise WorkflowInvalidTransitionError(
                f"document {run.document_id!r} reached calculation "
                "without a quantity"
            )
        request = CalculationRequest(
            match_request_id=match_request.id,
            organization_id=run.document.organization_id,
            factor=factor,
            quantity=match_input.quantity,
            quantity_unit=match_input.quantity_unit,
            date=match_input.date or run.document.uploaded_at.date(),
            reporting_year=match_input.reporting_year,
            activity=match_input.activity,
            activity_type=factor.activity_type,
            scope=match_input.scope or factor.scope,
            source_file=run.document.filename,
        )
        result = await self._calculation_engine.calculate(request)
        run.snapshot_id = result.snapshot.id
        run.co2e_kg = result.co2e_kg
        await self._transition(run, "calculating", "completed")
        run.status = "completed"


    # ------------------------------------------------------------------
    # State, events, audit
    # ------------------------------------------------------------------

    async def _transition(
        self, run: _WorkflowRun, from_state: str, to_state: str
    ) -> None:
        """Apply one state-machine transition, persisting the event + audit."""
        if not self._state_machine.can_transition(from_state, to_state):
            raise WorkflowInvalidTransitionError(
                f"workflow cannot transition {from_state!r} -> {to_state!r} "
                f"for document {run.document_id!r}"
            )
        persisted = DOCUMENT_STATUS_MAP.get(to_state)
        if persisted is None:
            raise WorkflowInvalidTransitionError(
                f"no customer_documents status mapped for workflow state {to_state!r}"
            )
        await self._documents_repo.update_status(run.document_id, persisted)
        run.stage = to_state
        await self._emit(
            WorkflowStateChanged(
                event_id=str(uuid.uuid4()),
                occurred_at=datetime.now(timezone.utc),
                correlation_id=run.correlation_id,
                entity_type="document",
                entity_id=run.document_id,
                from_state=from_state,
                to_state=to_state,
            ),
            run,
        )
        await self._audit(
            action="workflow:state_changed",
            entity_type="document",
            entity_id=run.document_id,
            correlation_id=run.correlation_id,
            actor=run.applied_by,
            after={"from_state": from_state, "to_state": to_state},
        )

    async def _fail(self, run: _WorkflowRun, message: str) -> None:
        """Mark the run failed and persist the transition to ``failed``."""
        run.status = "failed"
        run.error = message
        try:
            await self._transition(run, run.stage, "failed")
        except WorkflowInvalidTransitionError:
            await self._documents_repo.update_status(run.document_id, "failed")
            run.stage = "failed"
        await self._audit(
            action="workflow:failed",
            entity_type="document",
            entity_id=run.document_id,
            correlation_id=run.correlation_id,
            actor=run.applied_by,
            after={"error": message},
        )

    async def _emit(self, event: DomainEvent, run: _WorkflowRun) -> None:
        """Persist ``event`` through the events repo and publish it on the bus."""
        await self._store_event(event)
        await self._publish(event)

    async def _store_event(self, event: DomainEvent) -> None:
        try:
            await self._events_repo.store(event)
        except Exception:  # noqa: BLE001 - persistence must not break the pipeline
            logger.exception(
                "failed to persist %s for correlation %s",
                type(event).__name__,
                event.correlation_id,
            )

    async def _publish(self, event: DomainEvent) -> None:
        if self._event_bus is None:
            return
        try:
            await self._event_bus.publish(event)
        except Exception:  # noqa: BLE001 - side effects must not break the pipeline
            logger.exception(
                "failed to publish %s for correlation %s",
                type(event).__name__,
                event.correlation_id,
            )

    async def _audit(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        correlation_id: str,
        actor: str,
        before: object = None,
        after: object = None,
    ) -> None:
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                correlation_id=correlation_id,
                actor=actor,
                before=before,
                after=after,
            )
        except Exception:  # noqa: BLE001 - audit must not break the pipeline
            logger.exception(
                "failed to audit %s for %s %s", action, entity_type, entity_id
            )


    # ------------------------------------------------------------------
    # Event handlers (registered by :meth:`register_handlers`)
    # ------------------------------------------------------------------

    async def _on_document_uploaded(self, event: DocumentUploaded) -> None:
        """Drive the pipeline from ``extracting`` when a document is uploaded."""
        run = self._runs.get(event.document_id)
        if run is None or run.status != "running":
            return
        await self._drive(run)

    async def _on_fields_extracted(self, event: FieldsExtracted) -> None:
        """Resume the pipeline when a fields event arrives for an active run."""
        run = self._runs.get(event.document_id)
        if run is None or run.status != "running":
            return
        await self._drive(run)

    async def _on_factor_matched(self, event: FactorMatched) -> None:
        """Advance a matched run toward calculation (reactive path)."""
        run = self._find_run_by_match_request(event.request_id)
        if run is None or run.status != "running":
            return
        await self._drive(run)

    def _find_run_by_match_request(self, request_id: str) -> Optional[_WorkflowRun]:
        for run in self._runs.values():
            if run.match_request is not None and run.match_request.id == request_id:
                return run
        return None

    # ------------------------------------------------------------------
    # Result shaping
    # ------------------------------------------------------------------

    def _result(self, run: _WorkflowRun) -> WorkflowResult:
        match_status = run.match_result.status if run.match_result is not None else ""
        return WorkflowResult(
            run_id=run.correlation_id,
            document_id=run.document_id,
            status=run.status,
            stage=run.stage,
            snapshot_id=run.snapshot_id,
            co2e_kg=run.co2e_kg,
            confidence=run.ai_confidence,
            match_status=match_status,
            error=run.error,
        )


# ---------------------------------------------------------------------------
# Small deterministic helpers (field parsing for the default activity resolver)
# ---------------------------------------------------------------------------


def _clean(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    if not value:
        return None
    try:
        return Decimal(value.strip())
    except (InvalidOperation, ValueError):
        return None


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_year(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        year = int(value.strip())
    except ValueError:
        return None
    return year if 1990 <= year <= 2100 else None


def _year_from_date(value: Optional[str]) -> Optional[int]:
    parsed = _parse_date(value)
    return parsed.year if parsed is not None else None

