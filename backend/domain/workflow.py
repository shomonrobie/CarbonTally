"""Workflow and domain-event objects (Backend v2.1 §9, ADR-10, §14).

Pure Python, immutable frozen dataclasses. Events are keyword-only dataclasses
that extend :class:`DomainEvent`; ``aggregate_id``/``aggregate_type`` are
derived automatically from the event's domain fields.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, Protocol, Sequence


# ---------------------------------------------------------------------------
# Workflow definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """A named state machine: states plus allowed transitions.

    A transition tuple ``("*", state)`` is a wildcard meaning *any* state may
    transition to ``state``.
    """

    name: str
    states: tuple[str, ...]
    transitions: tuple[tuple[str, str], ...]

    def can_transition(self, from_state: str, to_state: str) -> bool:
        """Return ``True`` when the transition is allowed by the definition."""
        return (from_state, to_state) in self.transitions or ("*", to_state) in self.transitions

    def validate_state(self, state: str) -> bool:
        """Return ``True`` when ``state`` is one of the defined states."""
        return state in self.states


#: The document processing pipeline state machine (Backend v2.1 §14.4).
DOCUMENT_PIPELINE: WorkflowDefinition = WorkflowDefinition(
    name="document_pipeline",
    states=(
        "pending",
        "uploaded",
        "classifying",
        "extracting",
        "ai_matching",
        "matched",
        "customer_review",
        "reviewed",
        "calculating",
        "completed",
        "failed",
        "manual_review",
    ),
    transitions=(
        ("pending", "uploaded"),
        ("uploaded", "classifying"),
        ("classifying", "extracting"),
        ("extracting", "ai_matching"),
        ("ai_matching", "matched"),
        ("ai_matching", "manual_review"),
        ("matched", "customer_review"),
        ("customer_review", "reviewed"),
        ("customer_review", "manual_review"),
        ("reviewed", "calculating"),
        ("calculating", "completed"),
        ("*", "failed"),
    ),
)


@dataclass(frozen=True, slots=True)
class Transition:
    """A record of one applied workflow transition."""

    workflow_id: str
    from_state: str
    to_state: str
    applied_at: datetime
    applied_by: str


# ---------------------------------------------------------------------------
# Domain events
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent(ABC):
    """Abstract base class for all domain events (Backend v2.1 §14.1).

    Attributes:
        event_id: Unique event id (UUID string).
        occurred_at: When the event happened.
        correlation_id: Id correlating all events of one request/pipeline run.
        aggregate_id: Id of the aggregate the event concerns (derived).
        aggregate_type: Kind of aggregate (``document``, ``import_batch``, ...)
            (derived).
    """

    event_id: str
    occurred_at: datetime
    correlation_id: str
    aggregate_id: str = ""
    aggregate_type: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentUploaded(DomainEvent):
    """Published when a customer document is uploaded to storage."""

    document_id: str
    organization_id: str
    storage_path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.document_id)
        object.__setattr__(self, "aggregate_type", "document")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractionRequested(DomainEvent):
    """Published when a document is queued for extraction."""

    document_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.document_id)
        object.__setattr__(self, "aggregate_type", "document")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractionCompleted(DomainEvent):
    """Published when a document's extraction pipeline finishes."""

    document_id: str
    page_count: int
    confidence: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.document_id)
        object.__setattr__(self, "aggregate_type", "document")
        if self.page_count < 0:
            raise ValueError("page_count must be >= 0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True, kw_only=True)
class FieldsExtracted(DomainEvent):
    """Published when key/value fields are extracted from a document."""

    document_id: str
    fields: dict[str, Any]
    confidence: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.document_id)
        object.__setattr__(self, "aggregate_type", "document")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True, kw_only=True)
class CalculationRequested(DomainEvent):
    """Published when a match request is queued for calculation."""

    match_request_id: str
    organization_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.match_request_id)
        object.__setattr__(self, "aggregate_type", "calculation")


@dataclass(frozen=True, slots=True, kw_only=True)
class CalculationCompleted(DomainEvent):
    """Published when a calculation completes and a snapshot is stored."""

    snapshot_id: str
    co2e_kg: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.snapshot_id)
        object.__setattr__(self, "aggregate_type", "calculation")
        if self.co2e_kg < 0:
            raise ValueError("co2e_kg must be >= 0")


@dataclass(frozen=True, slots=True, kw_only=True)
class ReportGenerated(DomainEvent):
    """Published when a report is generated and stored."""

    report_id: str
    organization_id: str
    storage_url: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.report_id)
        object.__setattr__(self, "aggregate_type", "report")


@dataclass(frozen=True, slots=True, kw_only=True)
class ImportStarted(DomainEvent):
    """Published when an import batch begins processing."""

    batch_id: str
    provider_key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.batch_id)
        object.__setattr__(self, "aggregate_type", "import_batch")


@dataclass(frozen=True, slots=True, kw_only=True)
class ImportCompleted(DomainEvent):
    """Published when an import batch finishes successfully."""

    batch_id: str
    rows_imported: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.batch_id)
        object.__setattr__(self, "aggregate_type", "import_batch")
        if self.rows_imported < 0:
            raise ValueError("rows_imported must be >= 0")


@dataclass(frozen=True, slots=True, kw_only=True)
class ImportRolledBack(DomainEvent):
    """Published when an import batch is rolled back."""

    batch_id: str
    replaced_by: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.batch_id)
        object.__setattr__(self, "aggregate_type", "import_batch")


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorMatched(DomainEvent):
    """Published when a match request is resolved to a factor."""

    request_id: str
    factor_id: str
    confidence: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.request_id)
        object.__setattr__(self, "aggregate_type", "factor_match")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True, kw_only=True)
class FactorNotFound(DomainEvent):
    """Published when a match request cannot be resolved to a factor."""

    request_id: str
    activity: str
    unit: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.request_id)
        object.__setattr__(self, "aggregate_type", "factor_match")


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationFailed(DomainEvent):
    """Published when data-quality checks reject an entity."""

    entity_type: str
    entity_id: str
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.entity_id)
        object.__setattr__(self, "aggregate_type", self.entity_type)


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowStateChanged(DomainEvent):
    """Published whenever a workflow entity changes state."""

    entity_type: str
    entity_id: str
    from_state: str
    to_state: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "aggregate_id", self.entity_id)
        object.__setattr__(self, "aggregate_type", self.entity_type)


# ---------------------------------------------------------------------------
# Sagas
# ---------------------------------------------------------------------------


class SagaStep(Protocol):
    """Contract for one step in a saga (execute + compensating action)."""

    async def execute(self) -> None: ...

    async def compensate(self) -> None: ...


class Saga(ABC):
    """A long-running transaction with compensating rollback (Backend v2.1 §14.3).

    Concrete sagas (Phase 8) implement :meth:`execute` and :meth:`compensate`
    by driving the steps in order and walking back the compensations in
    reverse on failure.
    """

    def __init__(
        self, steps: Sequence[SagaStep], compensations: Sequence[SagaStep]
    ) -> None:
        self.steps: list[SagaStep] = list(steps)
        self.compensations: list[SagaStep] = list(compensations)

    @abstractmethod
    async def execute(self) -> None:
        """Run every step in order; roll back via :meth:`compensate` on failure."""

    @abstractmethod
    async def compensate(self) -> None:
        """Undo every completed step, in reverse order."""

