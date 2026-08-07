"""Audit trail domain objects (Backend v2.1 §9, ADR-10).

Pure Python, immutable frozen dataclasses. ``AuditTrail`` aggregates the
``AuditEntry`` records belonging to one correlation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """An immutable record of one audited action.

    Attributes:
        id: Primary key (UUID string).
        correlation_id: Links entries produced by the same request/pipeline run.
        entity_type: Aggregate kind (``document``, ``import_batch``, ...).
        entity_id: Id of the entity the action was performed on.
        action: Verb describing the action (``created``, ``activated``, ...).
        actor: User or service that performed the action (``system`` for engine
            steps).
        occurred_at: When the action happened.
        changed_fields: The fields changed by the action.
        reason: Free-text explanation (nullable).
        ip_address: Actor IP address, when available.
        before: State of the entity before the action (nullable).
        after: State of the entity after the action (nullable).
    """

    id: str
    correlation_id: str
    entity_type: str
    entity_id: str
    action: str
    actor: str
    occurred_at: datetime
    changed_fields: dict[str, Any] = field(default_factory=dict)
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    before: Optional[dict[str, Any]] = None
    after: Optional[dict[str, Any]] = None


@dataclass(frozen=True, slots=True)
class AuditTrail:
    """An ordered collection of audit entries for one correlation."""

    correlation_id: str
    entries: tuple[AuditEntry, ...] = ()

    def __post_init__(self) -> None:
        for entry in self.entries:
            if entry.correlation_id != self.correlation_id:
                raise ValueError(
                    f"entry {entry.id!r} belongs to correlation "
                    f"{entry.correlation_id!r}, not {self.correlation_id!r}"
                )

    def by_action(self, action: str) -> list[AuditEntry]:
        """Return the entries whose action equals ``action``, in order."""
        return [e for e in self.entries if e.action == action]

    def by_entity(self, entity_type: str, entity_id: str) -> list[AuditEntry]:
        """Return the entries for one entity, in order."""
        return [
            e
            for e in self.entries
            if e.entity_type == entity_type and e.entity_id == entity_id
        ]


@dataclass(frozen=True, slots=True)
class AuditQuery:
    """Filters for querying and exporting the audit trail.

    Every filter is optional; unfiltered dimensions are ignored. ``limit`` and
    ``offset`` page the result set.
    """

    correlation_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action: Optional[str] = None
    actor: Optional[str] = None
    occurred_after: Optional[datetime] = None
    occurred_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.offset < 0:
            raise ValueError("offset must be >= 0")
        if (
            self.occurred_after is not None
            and self.occurred_before is not None
            and self.occurred_before < self.occurred_after
        ):
            raise ValueError("occurred_before is before occurred_after")
