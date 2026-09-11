"""Audit trail domain objects (Backend v2.1 §9, ADR-10).

Pure Python, immutable frozen dataclasses. ``AuditTrail`` aggregates the
``AuditEntry`` records belonging to one correlation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Phase 7 — canonical audit taxonomy (additive; no schema change)
# ---------------------------------------------------------------------------
#
# These vocabularies are stored in the existing ``audit_trail.metadata`` JSONB
# (the table already uses ``metadata`` for flexible extra data). They make the
# audit ledger investigable by category/origin/outcome without a new table and
# without copying sensitive payloads.

#: Actor classes recorded on an audit entry (the provenance model).
ACTOR_HUMAN = "human"
ACTOR_INTERNAL_STAFF = "internal_staff"
ACTOR_ORG_USER = "org_user"
ACTOR_CONSULTANT = "consultant"
ACTOR_PE_STAFF = "pe_staff"
ACTOR_SYSTEM = "system"
ACTOR_TYPES: tuple[str, ...] = (
    ACTOR_HUMAN,
    ACTOR_INTERNAL_STAFF,
    ACTOR_ORG_USER,
    ACTOR_CONSULTANT,
    ACTOR_PE_STAFF,
    ACTOR_SYSTEM,
)

#: Whether an action was performed by a human or by the automated pipeline.
ORIGIN_HUMAN = "human"
ORIGIN_SYSTEM = "system"
ORIGINS: tuple[str, ...] = (ORIGIN_HUMAN, ORIGIN_SYSTEM)

#: Outcome of the audited action (success/failure only — never a fabricated
#: third state).
OUTCOME_SUCCESS = "success"
OUTCOME_FAILURE = "failure"
OUTCOMES: tuple[str, ...] = (OUTCOME_SUCCESS, OUTCOME_FAILURE)

#: Canonical audit categories covering the CarbonTally lifecycle.
CAT_AUTH = "authentication"
CAT_SECURITY = "authorization"
CAT_DOCUMENT = "document"
CAT_EXTRACTION = "extraction"
CAT_MAPPING = "mapping"
CAT_VALIDATION = "validation"
CAT_CALCULATION = "calculation"
CAT_EVIDENCE = "evidence"
CAT_WORKFLOW = "workflow"
CAT_REPORT = "report"
CAT_ADMIN = "administration"
CAT_SYSTEM = "system"
CATEGORIES: tuple[str, ...] = (
    CAT_AUTH,
    CAT_SECURITY,
    CAT_DOCUMENT,
    CAT_EXTRACTION,
    CAT_MAPPING,
    CAT_VALIDATION,
    CAT_CALCULATION,
    CAT_EVIDENCE,
    CAT_WORKFLOW,
    CAT_REPORT,
    CAT_ADMIN,
    CAT_SYSTEM,
)

#: Machine/automation actor labels (mirrors ``services.automatic_processing``
#: ``_SYSTEM_ACTOR`` and the audit helper's machine zero-UUID marker).
SYSTEM_ACTOR_LABELS: frozenset[str] = frozenset(
    {
        "system",
        "automatic_pipeline",
        "automation",
        "00000000-0000-0000-0000-000000000000",
    }
)

#: Action head -> category. Ordered longest-prefix-first at lookup time.
_ACTION_PREFIX_CATEGORY: dict[str, str] = {
    "session": CAT_AUTH,
    "auth": CAT_AUTH,
    "login": CAT_AUTH,
    "logout": CAT_AUTH,
    "access": CAT_SECURITY,
    "security": CAT_SECURITY,
    "permission": CAT_SECURITY,
    "role": CAT_ADMIN,
    "document": CAT_DOCUMENT,
    "file": CAT_DOCUMENT,
    "upload": CAT_DOCUMENT,
    "extract": CAT_EXTRACTION,
    "extraction": CAT_EXTRACTION,
    "manual_extraction": CAT_EXTRACTION,
    "map": CAT_MAPPING,
    "mapping": CAT_MAPPING,
    "validate": CAT_VALIDATION,
    "validation": CAT_VALIDATION,
    "calculate": CAT_CALCULATION,
    "calculation": CAT_CALCULATION,
    "verify": CAT_CALCULATION,
    "evidence": CAT_EVIDENCE,
    "review": CAT_WORKFLOW,
    "qc": CAT_WORKFLOW,
    "approve": CAT_WORKFLOW,
    "approval": CAT_WORKFLOW,
    "reject": CAT_WORKFLOW,
    "assign": CAT_WORKFLOW,
    "reassign": CAT_WORKFLOW,
    "workflow": CAT_WORKFLOW,
    "item": CAT_WORKFLOW,
    "batch": CAT_WORKFLOW,
    "report": CAT_REPORT,
    "organization": CAT_ADMIN,
    "member": CAT_ADMIN,
    "staff": CAT_ADMIN,
    "subscription": CAT_ADMIN,
    "billing": CAT_ADMIN,
    "settings": CAT_ADMIN,
    "commercial": CAT_ADMIN,
    "consultant": CAT_ADMIN,
    "entity": CAT_ADMIN,
    "system": CAT_SYSTEM,
    "automation": CAT_SYSTEM,
    "job": CAT_SYSTEM,
    "worker": CAT_SYSTEM,
    # Observed V3 action heads (see backend/api/*.py record() calls).
    "whitelabel": CAT_ADMIN,
    "plan": CAT_ADMIN,
    "processing_entity": CAT_ADMIN,
    "factor_alias": CAT_MAPPING,
    "discovery": CAT_DOCUMENT,
    "item_extraction": CAT_EXTRACTION,
    "customer": CAT_WORKFLOW,
    "emissions": CAT_CALCULATION,
    "msg": CAT_SYSTEM,
    "message": CAT_SYSTEM,
    "notification": CAT_SYSTEM,
    "retention": CAT_ADMIN,
}

#: Surface/domain prefixes stripped before classification (``pe_calculate`` ->
#: ``calculate``, ``ops_validate`` -> ``validate``).
_DOMAIN_PREFIXES: tuple[str, ...] = (
    "pe_",
    "ops_",
    "org_",
    "consultant_",
    "staff_",
    "customer_",
)


def classify_action(action: str) -> str:
    """Map an audit ``action_type`` to a canonical :data:`CATEGORIES` value.

    Deterministic and prefix-based (pure). Handles the real V3 action shapes
    (``head:verb`` and ``domain.verb``) and strips a leading surface prefix
    (``pe_calculate`` -> ``calculate``). An unknown action is classified as
    ``system`` rather than guessed; this is used both for investigation
    filtering and to derive the category of entries written before Phase 7.
    """
    if not action:
        return CAT_SYSTEM
    normalized = action.strip().lower().replace("-", "_")
    head = normalized.replace(".", ":").split(":", 1)[0]
    candidates = [head]
    for prefix in _DOMAIN_PREFIXES:
        if head.startswith(prefix) and len(head) > len(prefix):
            candidates.insert(0, head[len(prefix):])
    for candidate in candidates:
        if candidate in _ACTION_PREFIX_CATEGORY:
            return _ACTION_PREFIX_CATEGORY[candidate]
    for prefix in sorted(_ACTION_PREFIX_CATEGORY, key=len, reverse=True):
        for candidate in candidates:
            if candidate.startswith(prefix):
                return _ACTION_PREFIX_CATEGORY[prefix]
    return CAT_SYSTEM


def classify_origin(actor: Optional[str], actor_type: Optional[str] = None) -> str:
    """Return ``system`` for machine actors, else ``human`` (provenance).

    Prefers an explicit ``actor_type``; otherwise treats the known automation
    labels (and the machine zero-UUID marker) as system-origin.
    """
    if actor_type == ACTOR_SYSTEM:
        return ORIGIN_SYSTEM
    if actor is not None and actor.strip() in SYSTEM_ACTOR_LABELS:
        return ORIGIN_SYSTEM
    if not actor:
        return ORIGIN_SYSTEM
    return ORIGIN_HUMAN


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
    # --- Phase 7 additive provenance/classification (stored in metadata) ---
    #: Actor class from :data:`ACTOR_TYPES` (optional; derived when unset).
    actor_type: Optional[str] = None
    #: ``human`` / ``system`` origin (optional; derived from ``actor``).
    origin: Optional[str] = None
    #: ``success`` / ``failure`` outcome (optional).
    outcome: Optional[str] = None
    #: Owning organisation id when the event is tenant-scoped (optional).
    organization_id: Optional[str] = None
    #: Canonical category from :data:`CATEGORIES` (optional; derived from action).
    category: Optional[str] = None


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
    ``offset`` page the result set. ``q`` is a free-text search across the
    action, resource, actor, entity id and stored reason; ``sort``/``order``
    select the server-side ordering (BL-4) so the audit console can page over
    a full trail without loading it all.
    """

    correlation_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action: Optional[str] = None
    actor: Optional[str] = None
    occurred_after: Optional[datetime] = None
    occurred_before: Optional[datetime] = None
    q: Optional[str] = None
    sort: Optional[str] = None
    order: str = "desc"
    limit: int = 100
    offset: int = 0
    # --- Phase 7 additive investigation filters ---
    #: Canonical category (see :data:`CATEGORIES`).
    category: Optional[str] = None
    #: ``human`` / ``system`` origin.
    origin: Optional[str] = None
    #: ``success`` / ``failure`` outcome.
    outcome: Optional[str] = None
    #: Tenant scope: only entries tagged with this organisation id.
    organization_id: Optional[str] = None

    SORTABLE = ("occurred_at", "action", "actor", "entity_type")

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.offset < 0:
            raise ValueError("offset must be >= 0")
        if self.category is not None and self.category not in CATEGORIES:
            raise ValueError(f"category must be one of {list(CATEGORIES)}")
        if self.origin is not None and self.origin not in ORIGINS:
            raise ValueError(f"origin must be one of {list(ORIGINS)}")
        if self.outcome is not None and self.outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {list(OUTCOMES)}")
        if (
            self.occurred_after is not None
            and self.occurred_before is not None
            and self.occurred_before < self.occurred_after
        ):
            raise ValueError("occurred_before is before occurred_after")
        if self.sort is not None and self.sort not in self.SORTABLE:
            raise ValueError(f"sort must be one of {sorted(self.SORTABLE)}")
        if self.order not in ("asc", "desc"):
            raise ValueError("order must be 'asc' or 'desc'")
        if self.q is not None and not self.q.strip():
            object.__setattr__(self, "q", None)
