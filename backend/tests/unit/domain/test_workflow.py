"""Unit tests for domain.workflow."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal
from typing import TypeVar

import pytest

from domain.workflow import (
    DOCUMENT_PIPELINE,
    CalculationCompleted,
    CalculationRequested,
    DocumentUploaded,
    DomainEvent,
    ExtractionCompleted,
    ExtractionRequested,
    FactorMatched,
    FactorNotFound,
    FieldsExtracted,
    ImportCompleted,
    ImportRolledBack,
    ImportStarted,
    ReportGenerated,
    Saga,
    Transition,
    ValidationFailed,
    WorkflowDefinition,
    WorkflowStateChanged,
)

E = TypeVar("E", bound=DomainEvent)


def utc_now() -> datetime:
    return datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestWorkflowDefinition:
    def test_can_transition_allowed(self) -> None:
        wf = WorkflowDefinition(
            name="test",
            states=("a", "b", "failed"),
            transitions=(("a", "b"),),
        )
        assert wf.can_transition("a", "b") is True
        assert wf.can_transition("b", "a") is False

    def test_can_transition_wildcard(self) -> None:
        wf = WorkflowDefinition(
            name="test",
            states=("a", "b", "failed"),
            transitions=(("a", "b"), ("*", "failed")),
        )
        assert wf.can_transition("b", "failed") is True
        assert wf.can_transition("a", "failed") is True

    def test_validate_state(self) -> None:
        wf = WorkflowDefinition(name="test", states=("a", "b"), transitions=())
        assert wf.validate_state("a") is True
        assert wf.validate_state("z") is False

    def test_document_pipeline_is_well_formed(self) -> None:
        assert DOCUMENT_PIPELINE.name == "document_pipeline"
        assert DOCUMENT_PIPELINE.validate_state("pending") is True
        assert DOCUMENT_PIPELINE.validate_state("completed") is True
        # allowed transitions
        assert DOCUMENT_PIPELINE.can_transition("pending", "uploaded") is True
        assert DOCUMENT_PIPELINE.can_transition("reviewed", "calculating") is True
        # wildcard to failed
        assert DOCUMENT_PIPELINE.can_transition("matched", "failed") is True
        # disallowed
        assert DOCUMENT_PIPELINE.can_transition("completed", "uploaded") is False

    def test_transition_record(self) -> None:
        t = Transition(
            workflow_id="document_pipeline",
            from_state="pending",
            to_state="uploaded",
            applied_at=utc_now(),
            applied_by="system",
        )
        assert t.to_state == "uploaded"


def make_event(
    event_class: type[E],
    **fields: object,
) -> E:
    """Build a concrete DomainEvent with the shared fields plus event fields."""
    base: dict[str, object] = {
        "event_id": "evt-1",
        "occurred_at": utc_now(),
        "correlation_id": "corr-1",
    }
    base.update(fields)
    return event_class(**base)  # type: ignore[arg-type]


class TestDocumentEvents:
    def test_document_uploaded(self) -> None:
        event = make_event(
            DocumentUploaded,
            document_id="doc-1",
            organization_id="org-1",
            storage_path="org-1/invoice.pdf",
        )
        assert isinstance(event, DocumentUploaded)
        assert event.aggregate_id == "doc-1"
        assert event.aggregate_type == "document"

    def test_extraction_requested(self) -> None:
        event = make_event(ExtractionRequested, document_id="doc-1")
        assert event.aggregate_id == "doc-1"
        assert event.aggregate_type == "document"

    def test_extraction_completed(self) -> None:
        event = make_event(
            ExtractionCompleted, document_id="doc-1", page_count=3, confidence=0.92
        )
        assert event.page_count == 3
        with pytest.raises(ValueError):
            make_event(ExtractionCompleted, document_id="doc-1", page_count=-1, confidence=0.9)

    def test_fields_extracted(self) -> None:
        event = make_event(
            FieldsExtracted,
            document_id="doc-1",
            fields={"supplier": "ACME"},
            confidence=0.88,
        )
        assert event.fields["supplier"] == "ACME"
        assert event.aggregate_type == "document"


class TestCalculationEvents:
    def test_calculation_requested(self) -> None:
        event = make_event(
            CalculationRequested, match_request_id="mr-1", organization_id="org-1"
        )
        assert event.aggregate_id == "mr-1"
        assert event.aggregate_type == "calculation"

    def test_calculation_completed(self) -> None:
        event = make_event(
            CalculationCompleted, snapshot_id="snap-1", co2e_kg=Decimal("252.000000")
        )
        assert event.co2e_kg == Decimal("252.000000")
        assert event.aggregate_id == "snap-1"
        with pytest.raises(ValueError):
            make_event(CalculationCompleted, snapshot_id="s", co2e_kg=Decimal("-1"))


class TestReportEvent:
    def test_report_generated(self) -> None:
        event = make_event(
            ReportGenerated,
            report_id="r-1",
            organization_id="org-1",
            storage_url="s3://reports/r-1.pdf",
        )
        assert event.aggregate_id == "r-1"
        assert event.aggregate_type == "report"


class TestImportEvents:
    def test_import_started(self) -> None:
        event = make_event(ImportStarted, batch_id="b-1", provider_key="defra")
        assert event.aggregate_id == "b-1"
        assert event.aggregate_type == "import_batch"

    def test_import_completed(self) -> None:
        event = make_event(ImportCompleted, batch_id="b-1", rows_imported=98)
        assert event.rows_imported == 98
        with pytest.raises(ValueError):
            make_event(ImportCompleted, batch_id="b-1", rows_imported=-1)

    def test_import_rolled_back(self) -> None:
        event = make_event(ImportRolledBack, batch_id="b-1", replaced_by="b-2")
        assert event.replaced_by == "b-2"


class TestMatchEvents:
    def test_factor_matched(self) -> None:
        event = make_event(FactorMatched, request_id="mr-1", factor_id="f-1", confidence=0.98)
        assert event.aggregate_type == "factor_match"
        with pytest.raises(ValueError):
            make_event(FactorMatched, request_id="mr-1", factor_id="f-1", confidence=1.5)

    def test_factor_not_found(self) -> None:
        event = make_event(FactorNotFound, request_id="mr-1", activity="diesel", unit="litres")
        assert event.unit == "litres"


class TestStateChangeEvents:
    def test_validation_failed(self) -> None:
        event = make_event(
            ValidationFailed,
            entity_type="document",
            entity_id="doc-1",
            errors=("no pages",),
        )
        assert event.aggregate_id == "doc-1"
        assert event.aggregate_type == "document"

    def test_workflow_state_changed(self) -> None:
        event = make_event(
            WorkflowStateChanged,
            entity_type="document",
            entity_id="doc-1",
            from_state="extracting",
            to_state="ai_matching",
        )
        assert event.aggregate_type == "document"
        assert event.from_state == "extracting"
        assert event.to_state == "ai_matching"


class TestEventImmutability:
    def test_events_are_frozen(self) -> None:
        event = make_event(DocumentUploaded, document_id="doc-1", organization_id="o", storage_path="p")
        with pytest.raises(FrozenInstanceError):
            event.correlation_id = "other"  # type: ignore[misc]

    def test_events_are_keyword_only(self) -> None:
        with pytest.raises(TypeError):
            DocumentUploaded("evt-1", utc_now(), "corr-1", "doc-1", "o", "p")  # type: ignore[call-arg,misc]


class TestSaga:
    def test_saga_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            Saga(steps=[], compensations=[])  # type: ignore[abstract]

