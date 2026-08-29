"""Unit tests for the durable automatic-processing pipeline domain (CL-56)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.automatic_processing import (
    AUTOMATIC_PIPELINE,
    RUNNABLE_STAGES,
    STAGE_LABELS,
    STAGE_TO_STATUS,
    TERMINAL_STAGES,
    AutomaticProcessingJob,
)


def _job(**overrides) -> AutomaticProcessingJob:
    base = {
        "id": "job-1",
        "organization_id": "org-1",
        "file_name": "invoice.pdf",
        "file_url": "uploads/org-1/invoice.pdf",
        "file_type": "PDF",
    }
    base.update(overrides)
    return AutomaticProcessingJob(**base)


class TestStateMachine:
    def test_pipeline_states_cover_the_end_to_end_flow(self) -> None:
        assert "enqueued" in AUTOMATIC_PIPELINE.states
        assert "ingesting" in AUTOMATIC_PIPELINE.states
        assert "extracting" in AUTOMATIC_PIPELINE.states
        assert "mapping" in AUTOMATIC_PIPELINE.states
        assert "validating" in AUTOMATIC_PIPELINE.states
        assert "calculating" in AUTOMATIC_PIPELINE.states
        assert "review" in AUTOMATIC_PIPELINE.states
        assert "completed" in AUTOMATIC_PIPELINE.states
        assert "failed" in AUTOMATIC_PIPELINE.states
        assert "blocked" in AUTOMATIC_PIPELINE.states

    def test_forward_transitions_are_permitted(self) -> None:
        assert AUTOMATIC_PIPELINE.can_transition("enqueued", "ingesting")
        assert AUTOMATIC_PIPELINE.can_transition("ingesting", "extracting")
        assert AUTOMATIC_PIPELINE.can_transition("extracting", "mapping")
        assert AUTOMATIC_PIPELINE.can_transition("mapping", "validating")
        assert AUTOMATIC_PIPELINE.can_transition("validating", "calculating")
        assert AUTOMATIC_PIPELINE.can_transition("calculating", "review")
        assert AUTOMATIC_PIPELINE.can_transition("review", "completed")

    def test_gate_and_retry_transitions(self) -> None:
        assert AUTOMATIC_PIPELINE.can_transition("extracting", "blocked")
        assert AUTOMATIC_PIPELINE.can_transition("mapping", "blocked")
        assert AUTOMATIC_PIPELINE.can_transition("validating", "blocked")
        assert AUTOMATIC_PIPELINE.can_transition("review", "blocked")
        assert AUTOMATIC_PIPELINE.can_transition("blocked", "enqueued")
        assert AUTOMATIC_PIPELINE.can_transition("failed", "enqueued")

    def test_illegal_transitions_are_rejected(self) -> None:
        assert not AUTOMATIC_PIPELINE.can_transition("enqueued", "completed")
        assert not AUTOMATIC_PIPELINE.can_transition("completed", "review")
        assert not AUTOMATIC_PIPELINE.can_transition("extracting", "calculating")

    def test_status_mapping_keeps_rc2_vocabulary(self) -> None:
        # The fine-grained stage persists an RC2-compatible status so the
        # existing CHECK constraint and legacy consumers stay valid.
        assert STAGE_TO_STATUS["enqueued"] == "pending"
        assert STAGE_TO_STATUS["extracting"] == "processing"
        assert STAGE_TO_STATUS["review"] == "customer_review"
        assert STAGE_TO_STATUS["blocked"] == "manual_review"
        assert STAGE_TO_STATUS["completed"] == "completed"
        assert STAGE_TO_STATUS["failed"] == "failed"


class TestJobModel:
    def test_runnable_stages(self) -> None:
        assert _job(stage="enqueued").runnable
        assert _job(stage="mapping").runnable
        assert _job(stage="calculating").runnable
        assert not _job(stage="blocked").runnable
        assert not _job(stage="review").runnable
        assert not _job(stage="completed").runnable

    def test_gate_and_terminal_properties(self) -> None:
        assert _job(stage="blocked").blocked
        assert _job(stage="review").awaiting_review
        assert _job(stage="completed").terminal
        assert _job(stage="failed").terminal

    def test_completeness_single_line(self) -> None:
        job = _job(
            stage="extracting",
            extracted_data={
                "activity": "Electricity",
                "quantity": 100,
                "unit": "kWh",
            },
        )
        assert job.completeness == 1.0

    def test_completeness_tabular(self) -> None:
        job = _job(
            stage="extracting",
            extracted_data={
                "line_items": [
                    {"activity": "Diesel", "quantity": 10, "unit": "litres"},
                    {"activity": "", "quantity": 5, "unit": "litres"},
                ]
            },
        )
        # 5 of 6 required fields resolved across the two lines.
        assert job.completeness == round(5 / 6, 4)

    def test_transition_helper(self) -> None:
        job = _job(stage="extracting")
        assert job.can_transition_to("mapping")
        assert job.can_transition_to("blocked")
        assert not job.can_transition_to("completed")
