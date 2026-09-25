"""P17 acting-for / delegated-user context (ARCH-04 §10.3, P17-0 item 11).

Pure Python. No framework, database or infrastructure imports.

THE GOVERNING RULE, restated because everything here depends on it:

    ACTING FOR is operational CONTEXT, not an authorization boundary.
    (POST-ARCH §35; UIUX-01 §6, §44)

Ownership remains ``organization_id`` on every accounting object. An acting-for
record answers "which organization was this person operating *for* when they did
this?", and it is persisted so the question stays answerable after membership or
consultancy has changed. That is precisely why it cannot be derived at read time
from ``uploaded_by`` / ``created_by``: those columns record *who*, not *for whom*,
and the mapping from a user to an organization is mutable.

The consequence for security is deliberate and strict:

* an acting-for context NEVER grants access to an organization;
* the actor must ALREADY be entitled to the target organization, by membership or
  by an active consultant-client delegation;
* acting-for then attributes the operation; it never widens it.

An implementation that let acting-for stand in for authorization would be a
tenant-isolation bypass wearing a provenance label. This module makes that
distinction executable rather than aspirational.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Iterable, Optional

from core.exceptions import ActingForError

__all__ = [
    "ActingForKind",
    "EntitlementBasis",
    "ActingForContext",
    "Entitlement",
    "resolve_acting_for",
    "assert_acting_for_allowed",
]


class ActingForKind(StrEnum):
    """Which acting-for relationship is being recorded."""

    SELF = "SELF"
    CONSULTANT_FOR_CLIENT = "CONSULTANT_FOR_CLIENT"
    CONSULTANT_TEAM_FOR_FIRM = "CONSULTANT_TEAM_FOR_FIRM"
    PROCESSING_ENTITY_FOR_ASSIGNMENT = "PROCESSING_ENTITY_FOR_ASSIGNMENT"
    CARBONTALLY_STAFF = "CARBONTALLY_STAFF"
    DELEGATED_USER = "DELEGATED_USER"


class EntitlementBasis(StrEnum):
    """Why the actor is entitled to the target organization.

    There is deliberately no ``ACTING_FOR`` member: acting-for is never itself a
    basis of entitlement.
    """

    ORGANIZATION_MEMBERSHIP = "ORGANIZATION_MEMBERSHIP"
    ACTIVE_CONSULTANT_DELEGATION = "ACTIVE_CONSULTANT_DELEGATION"
    CARBONTALLY_INTERNAL_ROLE = "CARBONTALLY_INTERNAL_ROLE"
    PROCESSING_ENTITY_ASSIGNMENT = "PROCESSING_ENTITY_ASSIGNMENT"
    #: P17-IMPLEMENT-02 — the actor is a member of their OWN consultant firm,
    #: whose organization is linked via ``consultant_profiles.organization_id``.
    #: Distinct from ``ACTIVE_CONSULTANT_DELEGATION``, which is about a CLIENT.
    CONSULTANT_FIRM_MEMBERSHIP = "CONSULTANT_FIRM_MEMBERSHIP"


@dataclass(frozen=True, slots=True)
class Entitlement:
    """A verified basis on which the actor may operate on an organization.

    Attributes:
        organization_id: The organization the actor is entitled to.
        basis: Why the entitlement exists.
        actor_organization_id: The organization the actor belongs to (their own
            tenant), when meaningful. ``None`` for internal staff.
    """

    organization_id: str
    basis: EntitlementBasis
    actor_organization_id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ActingForContext:
    """The persisted context of one operation.

    Attributes:
        actor_user_id: Who performed the operation.
        actor_organization_id: The organization the actor belongs to.
        acting_for_organization_id: The organization the operation is attributed
            to — the data-owning organization. Always the entitled organization,
            never an arbitrary target.
        kind: Which acting-for relationship was recorded.
        basis: The verified entitlement that permitted the operation.
        is_delegated: True when the actor acted for an organization other than
            their own (a genuine delegation).
        recorded_at: When the context was resolved.
    """

    actor_user_id: str
    actor_organization_id: Optional[str]
    acting_for_organization_id: str
    kind: ActingForKind
    basis: EntitlementBasis
    is_delegated: bool
    recorded_at: Optional[datetime] = None

    def as_audit_columns(self) -> dict[str, Optional[str]]:
        """Return the column payload persisted on every acting-for-carrying path.

        Kept identical across the eight ARCH-04 §10.3 paths so one writer helper
        can serve documents, suppliers, review decisions, report artefacts,
        snapshots, emissions rows, evidence and the audit trail.
        """
        return {
            "actor_organization_id": self.actor_organization_id,
            "acting_for_organization_id": self.acting_for_organization_id,
        }


def assert_acting_for_allowed(
    *,
    actor_user_id: str,
    target_organization_id: str,
    entitlements: Iterable[Entitlement],
) -> Entitlement:
    """Return the matching entitlement, or raise :class:`ActingForError`.

    This is the enforcement point that keeps acting-for from becoming an
    authorization bypass. It is evaluated against verified entitlements supplied
    by the caller (membership rows, active delegations, internal roles, PE
    assignments) and never against the acting-for value the client asked for.
    """
    for entitlement in entitlements:
        if entitlement.organization_id == target_organization_id:
            return entitlement
    raise ActingForError(
        "acting for this organization is not permitted: the actor holds no "
        "membership, active delegation, internal role or assignment for it. "
        "Acting-for adds context to an existing entitlement; it never creates one.",
        details={
            "actor_user_id": actor_user_id,
            "target_organization_id": target_organization_id,
        },
    )


def resolve_acting_for(
    *,
    actor_user_id: str,
    target_organization_id: str,
    entitlements: Iterable[Entitlement],
    kind: ActingForKind = ActingForKind.SELF,
    actor_organization_id: Optional[str] = None,
    recorded_at: Optional[datetime] = None,
) -> ActingForContext:
    """Resolve and validate an acting-for context for one operation.

    Raises :class:`ActingForError` when the actor is not entitled. On success the
    returned context's ``acting_for_organization_id`` is always the *entitled*
    organization, so a caller cannot attribute an operation to a tenant the actor
    has no right to touch even if it passes an arbitrary target.
    """
    entitlement = assert_acting_for_allowed(
        actor_user_id=actor_user_id,
        target_organization_id=target_organization_id,
        entitlements=entitlements,
    )

    effective_actor_org = actor_organization_id or entitlement.actor_organization_id
    resolved_kind = kind
    if resolved_kind is ActingForKind.SELF and (
        effective_actor_org is not None
        and effective_actor_org != target_organization_id
    ):
        # The caller claimed "self" but the actor's own organization differs from
        # the target. That is a delegation being mislabelled, so record it
        # truthfully rather than trusting the label.
        resolved_kind = ActingForKind.DELEGATED_USER

    is_delegated = (
        effective_actor_org is not None
        and effective_actor_org != target_organization_id
    )

    return ActingForContext(
        actor_user_id=actor_user_id,
        actor_organization_id=effective_actor_org,
        acting_for_organization_id=entitlement.organization_id,
        kind=resolved_kind,
        basis=entitlement.basis,
        is_delegated=is_delegated,
        recorded_at=recorded_at,
    )
