"""Durable automatic document-processing pipeline (V3 Phase A / CL-56).

Pure Python state machine + constants for the automatic pipeline:

    UPLOAD → INGEST → EXTRACTION → MAPPING → VALIDATION → CALCULATION
    → EVIDENCE → REVIEW/APPROVAL → REPORTING

The durable job is a ``document_processing_queue`` row; ``status`` keeps the
RC2 vocabulary (so legacy consumers and the existing CHECK constraint remain
valid) while ``stage`` records the exact pipeline step. This module owns the
stage vocabulary and the transition table only — persistence lives in
:mod:`data.document_processing`, execution in :mod:`services.automatic_processing`
and the background claim loop in :mod:`workers.automatic_processing`.

Pipeline stages
---------------
* ``enqueued`` — the upload has been recorded and the job is runnable.
* ``ingesting`` — the source object is being read from private storage.
* ``extracting`` — text/OCR/CSV/XLSX → structured ``extracted_data``.
* ``mapping`` — activity/unit → emission factor (approved customer factor
  precedence, D-cf-5).
* ``validating`` — item-level data-quality validation (findings persisted).
* ``calculating`` — authoritative CO2e calculation → immutable snapshot +
  emissions log + evidence chain.
* ``review`` — waiting on the distinct customer/owner verification (D5).
* ``completed`` — the job is finished end-to-end.
* ``failed`` — a terminal error; retryable via re-enqueue.
* ``blocked`` — the manual-review gate: a human must confirm or correct the
  extraction/mapping/validation before the job resumes.

Idempotency: a stage's persisted output is its resume marker. Re-running the
pipeline on a job that already has ``extracted_data`` (etc.) skips that stage.
``failed``/``blocked`` jobs re-enter the pipeline through ``enqueued`` and the
stage re-run is bounded by ``max_attempts``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from domain.workflow import WorkflowDefinition

#: Pipeline version stamped into every job created by this implementation.
PIPELINE_VERSION = "v3-auto-1.1"  # P1-D1: P1 extraction-shape generation

#: Default retry cap per job (dead-letter after this many attempts).
DEFAULT_MAX_ATTEMPTS = 3

#: Stage confidence gate — extraction completeness below this (fraction of the
#: target fields resolved) routes the job to the manual-review gate.
AUTO_EXTRACT_CONFIDENCE_MIN = 0.5

#: Mapping confidence gate — an automatic factor match below this routes the
#: job to the manual-review gate.
AUTO_MAPPING_CONFIDENCE_MIN = 0.6

#: Fields the automatic extractor must resolve for the job to continue without
#: human review (calculation needs quantity × unit and mapping needs activity).
REQUIRED_EXTRACT_FIELDS: tuple[str, ...] = ("activity", "quantity", "unit")

#: The full automatic pipeline state machine (fine-grained ``stage`` column).
AUTOMATIC_PIPELINE: WorkflowDefinition = WorkflowDefinition(
    name="automatic_document_pipeline",
    states=(
        "enqueued",
        "ingesting",
        "extracting",
        "mapping",
        "validating",
        "calculating",
        "review",
        "completed",
        "failed",
        "blocked",
    ),
    transitions=(
        ("enqueued", "ingesting"),
        ("ingesting", "extracting"),
        ("extracting", "mapping"),
        ("extracting", "blocked"),      # extraction failed / low completeness
        ("mapping", "validating"),
        ("mapping", "blocked"),         # no factor matched / low confidence
        ("validating", "calculating"),
        ("validating", "blocked"),      # blocking findings → human rework
        ("calculating", "review"),      # awaiting customer/owner verification
        ("review", "completed"),        # customer approved
        ("review", "blocked"),          # customer rejected → human rework
        ("blocked", "enqueued"),        # human confirmed/corrected → resume
        ("failed", "enqueued"),         # explicit retry → re-enqueue
        ("*", "failed"),                # any stage may fail terminally
    ),
)

#: Stages that must be claimed by the worker (runnable + recoverable in-flight).
#: ``validating``/``calculating`` are included so jobs that crash mid-pipeline
#: are resumed by the next tick (stage outputs are the resume markers).
RUNNABLE_STAGES: tuple[str, ...] = (
    "enqueued",
    "ingesting",
    "extracting",
    "mapping",
    "validating",
    "calculating",
)
#: Stages that only a human may advance (the manual-review / approval gates).
HUMAN_GATE_STAGES: tuple[str, ...] = ("blocked", "review")

#: Terminal stages.
TERMINAL_STAGES: tuple[str, ...] = ("completed", "failed")

#: Maps the fine-grained stage to the RC2 ``status`` vocabulary persisted on
#: the same row (keeps the existing CHECK constraint and legacy consumers valid).
STAGE_TO_STATUS: dict[str, str] = {
    "enqueued": "pending",
    "ingesting": "processing",
    "extracting": "processing",
    "mapping": "processing",
    "validating": "processing",
    "calculating": "processing",
    "review": "customer_review",
    "completed": "completed",
    "failed": "failed",
    "blocked": "manual_review",
}

#: Human-readable stage labels (API/UX surface; never sent to the DB).
STAGE_LABELS: dict[str, str] = {
    "enqueued": "Enqueued",
    "ingesting": "Ingesting",
    "extracting": "Extracting",
    "mapping": "Mapping",
    "validating": "Validating",
    "calculating": "Calculating",
    "review": "Awaiting review",
    "completed": "Completed",
    "failed": "Failed",
    "blocked": "Manual review",
}

@dataclass(frozen=True, slots=True)
class AutomaticProcessingJob:
    """The durable job record for one document through the automatic pipeline.

    Mirrors the ``document_processing_queue`` columns (RC2 + V3M-9 additions).
    ``status`` is the RC2 vocabulary; ``stage`` the fine-grained pipeline step.
    """

    id: str
    organization_id: str
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    processing_type: str = "utility"
    status: str = "pending"
    stage: Optional[str] = None
    attempt_count: int = 0
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    last_error: Optional[str] = None
    extracted_data: Optional[dict] = None
    mapped_data: Optional[dict] = None
    validation_result: Optional[dict] = None
    calculation_snapshot_id: Optional[str] = None
    manual_review_reason: Optional[str] = None
    source_item_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    # WS4 Gate 5 (task T3) — write-once automated-execution attribution block.
    # NULL = deterministic-only result / no AI contributed / legacy row.
    automation_provider: Optional[str] = None
    automation_model: Optional[str] = None
    automation_model_version: Optional[str] = None
    # WS4 Gate 6 (workstream W1 / gap G6-A) — the original automated extraction
    # output, preserved independently of later human edits. Populated ONCE by
    # the automatic-processing worker at the extraction → mapping advance that
    # first persists `extracted_data` — for BOTH deterministic-only and
    # AI-contributing runs (the automatic pipeline produced this output either
    # way; the automation_* block above remains AI-contribution-specific and
    # NULL for deterministic-only runs). NULL = no automated extraction output
    # was ever durably produced (failed/blocked attempt) or a legacy row that
    # predates this column (never fabricated/backfilled). Human saves never
    # write this column, so a later human correction of the working
    # `extracted_data` can neither replace nor delete the original output.
    automation_extracted_data: Optional[dict] = None
    pipeline_version: Optional[str] = None
    # WS4 Gate 6 (workstream W3 / gap G6-C) — authoritative human-after
    # automation attribution fields on the canonical job record. These are the
    # existing DB actor columns that human gates already persist (server-side
    # only): ``created_by`` = authenticated user who uploaded/enqueued the job;
    # ``updated_by`` = authenticated user of the last confirm/retry
    # re-enqueue; ``customer_reviewed_by/at`` + ``customer_approved`` +
    # notes/reason = the owner/admin review decision. Read-only exposure; never
    # taken from client input and never an authorization signal. A human action
    # is distinct from the machine ``automation_*`` block / ``automatic_pipeline``.
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    customer_reviewed_by: Optional[str] = None
    customer_reviewed_at: Optional[datetime] = None
    customer_approved: Optional[bool] = None
    customer_notes: Optional[str] = None
    customer_rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    lock_token: Optional[str] = None
    ingested_at: Optional[datetime] = None
    extracted_at: Optional[datetime] = None
    mapped_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    calculated_at: Optional[datetime] = None
    review_ready_at: Optional[datetime] = None
    notified_at: Optional[datetime] = None
    reprocess_count: int = 0

    @property
    def runnable(self) -> bool:
        """Whether a worker may claim this job."""
        return self.stage in RUNNABLE_STAGES or (
            self.status in ("pending", "processing") and self.stage is None
        )

    @property
    def blocked(self) -> bool:
        return self.stage == "blocked"

    @property
    def awaiting_review(self) -> bool:
        return self.stage == "review"

    @property
    def terminal(self) -> bool:
        return self.stage in TERMINAL_STAGES

    @property
    def completeness(self) -> float:
        """Fraction of the required extraction fields resolved (0..1).

        For tabular documents (``line_items``) the fraction is computed over
        every line; for single-line documents over the top-level fields.
        """
        data = self.extracted_data or {}
        if not data:
            return 0.0
        line_items = data.get("line_items") or []
        if line_items:
            resolved = 0
            total = 0
            for line in line_items:
                if not isinstance(line, dict):
                    continue
                for field in REQUIRED_EXTRACT_FIELDS:
                    total += 1
                    if str(line.get(field) or "").strip():
                        resolved += 1
            return round(resolved / total, 4) if total else 0.0
        resolved = sum(
            1
            for f in REQUIRED_EXTRACT_FIELDS
            if str(data.get(f) or "").strip()
        )
        return round(resolved / len(REQUIRED_EXTRACT_FIELDS), 4)

    def can_transition_to(self, target: str) -> bool:
        """Return ``True`` when the state machine permits ``stage -> target``."""
        current = self.stage or "enqueued"
        if current == target:
            return True
        return AUTOMATIC_PIPELINE.can_transition(current, target)


def validate_stage(value: Optional[str]) -> bool:
    """Return ``True`` when ``value`` is a known pipeline stage (or ``None``)."""
    if value is None:
        return True
    return AUTOMATIC_PIPELINE.validate_state(value)

