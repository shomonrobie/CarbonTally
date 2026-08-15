"""Processing Entity domain objects (V3, ADR-V3-001 — DECIDED, Option B).

Pure Python, immutable frozen dataclasses mirroring the V3M-1
``processing_entities`` table. The ``NULL`` convention from the V3 architecture
is preserved at the domain level: a ``ProcessingEntity`` row is always a
concrete entity; CarbonTally-internal processing is represented by
``entity_id IS NULL`` on staff/work rows (never by a synthetic entity).

Lifecycle vocabulary mirrors the V3M-1 CHECK:
``active / remediation / suspended / terminated``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

#: Lifecycle statuses permitted by ``processing_entities.status`` (V3M-1 CHECK).
ENTITY_STATUSES = ("active", "remediation", "suspended", "terminated")

#: Transitions permitted by the lifecycle (ADR-V3-001 Q6 — CarbonTally-internal
#: authority; an entity can never self-activate).
_ENTITY_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "active": ("remediation", "suspended", "terminated"),
    "remediation": ("active", "suspended", "terminated"),
    "suspended": ("active", "terminated"),
    "terminated": (),
}


@dataclass(frozen=True, slots=True)
class ProcessingEntity:
    """A first-class Human Data Processing Entity (V3M-1 row).

    Attributes:
        id: Primary key (UUID string).
        name: Entity display name.
        description: Optional description.
        status: Lifecycle status (see :data:`ENTITY_STATUSES`).
        metadata: Contract/commercial metadata (V3M-1 Q1 — deferred exact fields).
        created_at: Row creation time.
        updated_at: Row last-update time.
        created_by: Actor that created the row.
        updated_by: Actor that last updated the row.
    """

    id: str
    name: str
    status: str = "active"
    description: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("id must not be empty")
        if not self.name:
            raise ValueError("name must not be empty")
        if self.status not in ENTITY_STATUSES:
            raise ValueError(
                f"status {self.status!r} not in {ENTITY_STATUSES}"
            )

    def can_transition_to(self, new_status: str) -> bool:
        """Return ``True`` when ``new_status`` is a permitted lifecycle step."""
        if new_status == self.status:
            return True
        return new_status in _ENTITY_TRANSITIONS.get(self.status, ())
