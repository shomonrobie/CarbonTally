"""Report version lifecycle state machine (Phase 8 Reporting S3).

Pure, dependency-free domain model of the **ratified report-version lifecycle**
(Phase 8 Reporting Lifecycle Specification §12–§14, ratified §10.2). This module
holds the state vocabulary, the guarded transition table, the audit-event names
(§21.2) and the declared authority level per action. It performs no I/O — the
repository persists, the API authorizes/audits.

Ratified stored states (exactly six — no assurance/verification state exists):

    DRAFT ──submit──► REVIEWED ──approve──► APPROVED ──finalize──► FINAL
                        │
                        ├──request_changes──► CHANGES_REQUESTED
                        └──reject───────────► REJECTED

``FINAL`` is terminal for a version; ``SUPERSEDED`` and "current version" are
**derived** (an approved/final version with a higher ``version_number``), never
stored. A post-approval/post-final change creates a **new** ``DRAFT`` version
rather than mutating the approved/final one.

CarbonTally's approval is the **customer's own assertion** — it is never
independent GHG assurance, verification, certification or audit opinion.
"""

from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Stored version states (ratified — exactly six)
# ---------------------------------------------------------------------------
DRAFT = "DRAFT"
REVIEWED = "REVIEWED"
CHANGES_REQUESTED = "CHANGES_REQUESTED"
REJECTED = "REJECTED"
APPROVED = "APPROVED"
FINAL = "FINAL"

#: Every persisted ``report_versions.status`` value, in lifecycle order.
VERSION_STATUSES: tuple[str, ...] = (
    DRAFT,
    REVIEWED,
    CHANGES_REQUESTED,
    REJECTED,
    APPROVED,
    FINAL,
)

#: The state a freshly generated version starts in (§12.3).
DEFAULT_STATUS = DRAFT

#: ``FINAL`` is terminal for a version — it can only be superseded by a new one.
TERMINAL_STATUSES: tuple[str, ...] = (FINAL,)

#: Approved/final version content is immutable (§10.2 invariants 1–2, §18).
IMMUTABLE_STATUSES: tuple[str, ...] = (APPROVED, FINAL)

# ---------------------------------------------------------------------------
# Lifecycle actions
# ---------------------------------------------------------------------------
SUBMIT = "submit_review"              # T3  DRAFT     → REVIEWED
REQUEST_CHANGES = "request_changes"   # T7  REVIEWED  → CHANGES_REQUESTED
REJECT = "reject"                     # T8  REVIEWED  → REJECTED
APPROVE = "approve"                   # T11 REVIEWED  → APPROVED
FINALIZE = "finalize"                 # T12 APPROVED  → FINAL
NEW_VERSION = "new_version"           # T9/T10/T17 — supersede by a NEW draft version

#: Status-changing transitions, keyed by ``(action, from_state)``.
TRANSITIONS: dict[tuple[str, str], str] = {
    (SUBMIT, DRAFT): REVIEWED,
    (REQUEST_CHANGES, REVIEWED): CHANGES_REQUESTED,
    (REJECT, REVIEWED): REJECTED,
    (APPROVE, REVIEWED): APPROVED,
    (FINALIZE, APPROVED): FINAL,
}

#: Source states that may be superseded by a new draft version (§23.2 T9/T10/T17,
#: plus the ratified post-approval change rule §10.2 invariant 2 / §18 Option A).
NEW_VERSION_SOURCES: tuple[str, ...] = (
    CHANGES_REQUESTED,
    REJECTED,
    APPROVED,
    FINAL,
)

#: Append-only audit event names (§21.2). All classify to ``CAT_REPORT`` via the
#: existing ``report`` action prefix — no taxonomy change is introduced.
AUDIT_EVENTS: dict[str, str] = {
    SUBMIT: "report.review_submitted",
    REQUEST_CHANGES: "report.changes_requested",
    REJECT: "report.rejected",
    APPROVE: "report.approved",
    FINALIZE: "report.finalized",
    NEW_VERSION: "report.version_created",
}

# ---------------------------------------------------------------------------
# Declared authority per action (Phase 8 S3 PO-ratified boundary)
# ---------------------------------------------------------------------------
#: Any organisation member (owner/admin/member) — the acting-org author.
AUTHORITY_MEMBER = "org_member"
#: Organisation authority only (owner/admin). Member and Viewer are excluded,
#: and Consultants / Internal staff / Processing Entities are never granted
#: report-lifecycle authority in S3 (future PO-gated decisions).
AUTHORITY_ADMIN = "org_admin"

ACTION_AUTHORITY: dict[str, str] = {
    SUBMIT: AUTHORITY_MEMBER,
    REQUEST_CHANGES: AUTHORITY_ADMIN,
    REJECT: AUTHORITY_ADMIN,
    APPROVE: AUTHORITY_ADMIN,
    FINALIZE: AUTHORITY_ADMIN,
    NEW_VERSION: AUTHORITY_MEMBER,
}


class TransitionNotAllowed(ValueError):
    """Raised when an action is not valid from the version's current state."""

    def __init__(
        self,
        action: str,
        from_state: str,
        allowed_from: tuple[str, ...] = (),
    ) -> None:
        self.action = action
        self.from_state = from_state
        self.allowed_from = allowed_from
        detail = f"action {action!r} is not valid from state {from_state!r}"
        if allowed_from:
            detail += f" (valid from: {', '.join(sorted(allowed_from))})"
        super().__init__(detail)


def is_valid_status(status: object) -> bool:
    """Return whether ``status`` is one of the six ratified stored states."""
    return isinstance(status, str) and status in VERSION_STATUSES


def validate_status(status: str) -> str:
    """Return ``status`` when valid, else raise :class:`ValueError`."""
    if not is_valid_status(status):
        raise ValueError(
            f"invalid report version status {status!r}; "
            f"expected one of {list(VERSION_STATUSES)}"
        )
    return status


def resolve_transition(action: str, from_state: str) -> str:
    """Return the resulting state for ``action`` from ``from_state``.

    Raises :class:`TransitionNotAllowed` when the transition is not permitted
    (the server-side guard that rejects invalid transitions such as
    ``DRAFT → APPROVED`` or ``APPROVED → FINAL`` without approval).
    """
    if action == NEW_VERSION:
        if from_state in NEW_VERSION_SOURCES:
            return DEFAULT_STATUS
        raise TransitionNotAllowed(action, from_state, NEW_VERSION_SOURCES)
    try:
        return TRANSITIONS[(action, from_state)]
    except KeyError:
        allowed = tuple(state for (act, state) in TRANSITIONS if act == action)
        raise TransitionNotAllowed(action, from_state, allowed) from None


def allowed_actions(state: str) -> tuple[str, ...]:
    """Return the actions permitted from ``state`` (empty for unknown states)."""
    actions = [action for (action, source) in TRANSITIONS if source == state]
    if state in NEW_VERSION_SOURCES:
        actions.append(NEW_VERSION)
    return tuple(actions)


def can_create_new_version(state: str) -> bool:
    """Return whether a new version may be created from ``state``."""
    return state in NEW_VERSION_SOURCES


def is_immutable(state: str) -> bool:
    """Return whether ``state`` marks content that must never be mutated."""
    return state in IMMUTABLE_STATUSES


def is_terminal(state: str) -> bool:
    """Return whether ``state`` is terminal for a version (``FINAL``)."""
    return state in TERMINAL_STATUSES


def required_authority(action: str) -> Optional[str]:
    """Return the declared authority level for ``action`` (``None`` if unknown)."""
    return ACTION_AUTHORITY.get(action)
