"""First-class Issue domain objects (V3, ADR-V3-009 — DECIDED, Option B).

Pure Python, immutable frozen dataclasses mirroring the V3M-5 ``issues`` table.

An Issue is distinct from a Conversation, from ``user_feedback`` and from
``qc_checks``/``qc_errors``. It may carry any of the optional context FKs
(organisation, processing entity, work item, document, batch, conversation).

Lifecycle (spec §14.2): creation → assignment → priority/severity → SLA →
escalation → resolution → reopening → closure. The DB enforces the vocabulary;
the service enforces who may transition (transition authority is an API/backend
concern per V3M-5).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

#: Issue-type vocabulary (V3M-5 CHECK).
ISSUE_TYPES = ("defect", "exception", "escalation")

#: Severity vocabulary (V3M-5 CHECK).
ISSUE_SEVERITIES = ("low", "medium", "high", "critical")

#: Status vocabulary (V3M-5 CHECK).
ISSUE_STATUSES = ("open", "in_progress", "on_hold", "escalated", "resolved", "closed")

#: Status transition table (spec §14.2). Reopening returns to ``open`` and is
#: recorded via ``reopened_at`` (V3M-5 test invariant).
_ISSUE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "open": ("in_progress", "on_hold", "escalated", "resolved", "closed"),
    "in_progress": ("on_hold", "escalated", "resolved", "closed"),
    "on_hold": ("in_progress", "escalated", "resolved", "closed"),
    "escalated": ("in_progress", "resolved", "closed"),
    "resolved": ("closed", "open"),
    "closed": ("open",),
}


@dataclass(frozen=True, slots=True)
class Issue:
    """A first-class Issue (V3M-5 row).

    Attributes:
        id: Primary key (UUID string).
        issue_type: ``defect`` / ``exception`` / ``escalation``.
        severity: ``low`` / ``medium`` / ``high`` / ``critical``.
        priority: Non-negative integer (higher = more urgent).
        status: Lifecycle status (see :data:`ISSUE_STATUSES`).
        title: Short subject.
        description: Optional detail.
        organization_id: Optional org context (FK, ON DELETE CASCADE).
        entity_id: Optional processing-entity context (FK, ON DELETE RESTRICT).
        work_item_id: Optional work-item context (FK, ON DELETE RESTRICT).
        document_id: Optional document context (FK, ON DELETE RESTRICT).
        batch_id: Optional batch context (FK, ON DELETE RESTRICT).
        conversation_id: Optional linked conversation (FK, ON DELETE SET NULL).
        assignee_id: Optional assignee (staff/user).
        escalation_level: Non-negative escalation counter.
        sla_deadline: SLA deadline (passthrough mirror of the V3M-5 column).
        sla_breached: SLA breach flag (mirrors ``manual_review_queue.sla_breached``).
        reopened_at: Set on reopen transitions.
        created_at / updated_at: Row timestamps.
        created_by / updated_by: Actors.
    """

    id: str
    title: str
    issue_type: str = "exception"
    severity: str = "medium"
    priority: int = 0
    status: str = "open"
    description: Optional[str] = None
    organization_id: Optional[str] = None
    entity_id: Optional[str] = None
    work_item_id: Optional[str] = None
    document_id: Optional[str] = None
    batch_id: Optional[str] = None
    conversation_id: Optional[str] = None
    assignee_id: Optional[str] = None
    escalation_level: int = 0
    sla_deadline: Optional[datetime] = None
    sla_breached: Optional[bool] = None
    reopened_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id must not be empty")
        if not self.title:
            raise ValueError("title must not be empty")
        if self.issue_type not in ISSUE_TYPES:
            raise ValueError(f"issue_type {self.issue_type!r} not in {ISSUE_TYPES}")
        if self.severity not in ISSUE_SEVERITIES:
            raise ValueError(
                f"severity {self.severity!r} not in {ISSUE_SEVERITIES}"
            )
        if self.priority < 0:
            raise ValueError("priority must be >= 0")
        if self.status not in ISSUE_STATUSES:
            raise ValueError(f"status {self.status!r} not in {ISSUE_STATUSES}")
        if self.escalation_level < 0:
            raise ValueError("escalation_level must be >= 0")

    def can_transition_to(self, new_status: str) -> bool:
        """Return ``True`` when ``new_status`` is a permitted lifecycle step."""
        if new_status == self.status:
            return True
        return new_status in _ISSUE_TRANSITIONS.get(self.status, ())
