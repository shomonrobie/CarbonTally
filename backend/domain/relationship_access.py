"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — client access profile + relationship
access state (F-3, F-4, PO-9).

Source of truth: ``docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md``

* §8.1  the five client-side states: OFF / READ_ONLY / COLLABORATIVE / MANAGED /
        POST-RELATIONSHIP (READ-ONLY RETAINED);
* §8.2  the client capability matrix (post-PO amendments, incl. PO-9);
* §8.3  the profile rules P-1..P-9 (CEILING not grant; server-side; PO-9 is ✗
        in EVERY profile);
* §15   the post-relationship access contract (PA-1..PA-7).
* §4.11 PO-9 — a client user NEVER maps factors, edits mappings or triggers
        recalculation, in ANY profile, including a client-Organisation Owner.

This module is PURE: it holds no I/O and grants nothing. It answers the
questions the authorization layer asks:

    resolve_relationship_state(status, retained_read_only) -> state
    profile_allows(operation, profile, state)              -> bool

The PROFILE is the CEILING (§6.1). Effective permission is
``CAPABILITY ∩ PROFILE ∩ ENTITLEMENT``; a profile can only ever REDUCE what is
permitted, never confer consultant capability onto a client user (§8.3 P-1).
"""
from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Client access profiles — the persisted ceiling
# (``consultant_clients.client_access_profile``).
# ---------------------------------------------------------------------------
PROFILE_OFF = "off"
PROFILE_READ_ONLY = "read_only"
PROFILE_COLLABORATIVE = "collaborative"
PROFILE_MANAGED = "managed"

ACCESS_PROFILES: tuple[str, ...] = (
    PROFILE_OFF,
    PROFILE_READ_ONLY,
    PROFILE_COLLABORATIVE,
    PROFILE_MANAGED,
)

#: IMPL-1 — S1's ``NONE`` and S2's ``OFF`` are ONE concept. We persist ``off``.
_ALIASES: dict[str, str] = {
    "none": PROFILE_OFF,
    "off": PROFILE_OFF,
    "": PROFILE_OFF,
    "read_only": PROFILE_READ_ONLY,
    "readonly": PROFILE_READ_ONLY,
    "collaborative": PROFILE_COLLABORATIVE,
    "managed": PROFILE_MANAGED,
}


def normalise_profile(value: Optional[str]) -> str:
    """Coerce a stored profile to a known value — FAIL CLOSED to OFF.

    An unknown or absent profile resolves to ``off`` (no client access), never
    to the most permissive profile (§6.5 FM-1: never assume enabled).
    """
    key = (value or "").strip().lower()
    return _ALIASES.get(key, PROFILE_OFF)


# ---------------------------------------------------------------------------
# Relationship access state — DERIVED, never a duplicate persisted column.
# ---------------------------------------------------------------------------
STATE_ACTIVE = "active"
STATE_RETAINED_READ_ONLY = "retained_read_only"
STATE_OFF = "off"

#: Relationship statuses (``consultant_clients.status``) that grant the CLIENT
#: nothing at all.
_NO_CLIENT_ACCESS_STATUSES: frozenset[str] = frozenset(
    {"pending", "rejected", "suspended", "inactive", "onboarding"}
)

#: Statuses that mean "the relationship has ended". A retained (PO-10) grant is
#: an ended relationship PLUS the explicit retained-read-only flag.
_ENDED_STATUSES: frozenset[str] = frozenset({"ended", "terminated"})


def resolve_relationship_state(
    status: Optional[str], retained_read_only: bool = False
) -> str:
    """Derive the client-plane access state from authoritative relationship data.

    ``active``            -> ACTIVE (client plane usable, profile ceiling applies)
    ``ended`` + retained  -> RETAINED_READ_ONLY (PO-10; read-only history)
    anything else         -> OFF (no client access)

    The retained flag can NEVER lift a non-ended relationship into RETAINED, and
    an ended relationship is OFF unless retention was explicitly applied.
    """
    value = (status or "").strip().lower()
    if value == "active":
        return STATE_ACTIVE
    if value in _ENDED_STATUSES and bool(retained_read_only):
        return STATE_RETAINED_READ_ONLY
    return STATE_OFF


# ---------------------------------------------------------------------------
# Operations and the matrix
# ---------------------------------------------------------------------------
OP_READ_DATA = "read_data"
OP_READ_REPORTS = "read_reports"
OP_READ_EVIDENCE = "read_evidence"
OP_COMMENT = "comment"
OP_UPLOAD_DOCUMENT = "upload_document"
OP_EDIT_MASTER_DATA = "edit_master_data"
OP_CORRECT_SUBMITTED_DATA = "correct_submitted_data"
OP_APPROVE_FINAL = "approve_final"

#: PO-9 (§4.11) — forbidden to a client user in EVERY profile and state,
#: including a client-Organisation Owner. Server-side denial is mandatory
#: (MUST-3); UI absence is never sufficient.
CLIENT_FORBIDDEN_OPERATIONS: frozenset[str] = frozenset(
    {"map_factors", "edit_mappings", "recalculate"}
)

#: Every operation this module knows how to judge. An operation outside this
#: set is DENIED (fail closed) — a new client operation must be classified
#: deliberately, never admitted by omission.
KNOWN_OPERATIONS: frozenset[str] = frozenset(
    {
        OP_READ_DATA,
        OP_READ_REPORTS,
        OP_READ_EVIDENCE,
        OP_COMMENT,
        OP_UPLOAD_DOCUMENT,
        OP_EDIT_MASTER_DATA,
        OP_CORRECT_SUBMITTED_DATA,
        OP_APPROVE_FINAL,
    }
)

_READ_OPS: frozenset[str] = frozenset(
    {OP_READ_DATA, OP_READ_REPORTS, OP_READ_EVIDENCE}
)

#: §8.2 — writes permitted once the link is ACTIVE, per profile. ``approve_final``
#: is additionally gated by the client ROLE (§13.1) — this module only expresses
#: the PROFILE ceiling for it.
_WRITE_OPS_BY_PROFILE: dict[str, frozenset[str]] = {
    PROFILE_OFF: frozenset(),
    PROFILE_READ_ONLY: frozenset({OP_COMMENT}),
    PROFILE_COLLABORATIVE: frozenset(
        {
            OP_COMMENT,
            OP_UPLOAD_DOCUMENT,
            OP_EDIT_MASTER_DATA,
            OP_CORRECT_SUBMITTED_DATA,
            OP_APPROVE_FINAL,
        }
    ),
    PROFILE_MANAGED: frozenset({OP_COMMENT}),
}


def profile_allows(operation: str, profile: str, state: str) -> bool:
    """The CEILING decision: may a client user perform ``operation``?

    Both the profile AND the state must admit, and PO-9 is enforced first so no
    profile/state combination can ever permit a forbidden operation.
    """
    if operation in CLIENT_FORBIDDEN_OPERATIONS:
        return False
    if operation not in KNOWN_OPERATIONS:
        return False

    profile = normalise_profile(profile)

    if state == STATE_RETAINED_READ_ONLY:
        # PA-2/PA-3: no WRITE of any kind, and no messaging-send; history (and
        # therefore READ) remains available.
        return operation in _READ_OPS

    if state != STATE_ACTIVE:
        return False

    if operation in _READ_OPS:
        return profile != PROFILE_OFF
    if profile == PROFILE_OFF:
        return False
    return operation in _WRITE_OPS_BY_PROFILE.get(profile, frozenset())


def has_client_login(profile: str) -> bool:
    """Whether a profile has any client login at all (§8.1)."""
    return normalise_profile(profile) != PROFILE_OFF


def state_has_client_plane(state: str) -> bool:
    """INV-E / AC-S-4 — the client plane is usable only for ACTIVE or RETAINED."""
    return state in (STATE_ACTIVE, STATE_RETAINED_READ_ONLY)
