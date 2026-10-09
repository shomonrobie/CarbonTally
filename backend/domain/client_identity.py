"""Client-identity lifecycle policy — PD-1A (invitation) and PD-2A (role authority).

Pure policy module. It performs NO I/O and grants NO authority by itself; it is
the single, testable place where the *business rules* for the client-user
identity lifecycle live, so both the organisation plane and the consultant
plane apply identical rules rather than re-implementing them.

Ratified source of truth:

* ``docs/architecture/CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02.md`` §2
    - **PD-1A** ``A`` — invitation is CarbonTally-controlled, secure and
      single-use. Neither a consultant nor the client may bypass the
      invitation step and self-insert a client Workspace user.
    - **PD-2A** ``C`` — Dual authority with explicit boundaries. WHILE the
      relationship is ACTIVE and access is permitted, the client Organisation
      owner/admin may manage their own Organisation's users; the consultant
      firm MAY create/manage those users on the client's behalf WITHIN the
      permitted role boundary. This does NOT grant the consultant access to
      client DATA. Neither side may grant itself access beyond what the client
      access profile permits; consultant-managed users are confined to the
      CLIENT Organisation (the consultant does not become a member of it and
      receives no client-plane data access by creating a user).

The client role vocabulary is deliberately NOT redefined here: it is the
``organization_members.role`` CHECK model (owner/admin/member/viewer).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

__all__ = [
    "CLIENT_ROLES",
    "ASSIGNABLE_CLIENT_ROLES",
    "INVITATION_PENDING",
    "INVITATION_ACCEPTED",
    "INVITATION_REVOKED",
    "INVITATION_EXPIRED",
    "INVITATION_EXPIRY_DAYS",
    "ClientIdentityError",
    "validate_client_role",
    "normalise_email",
    "expiry_from_now",
    "resolve_invitation_state",
    "invitation_is_consumable",
    "may_manage_client_users",
    "permitted_assignable_roles",
]

#: The authoritative client role set — mirrors ``organization_members.role``
#: (CHECK role IN ('owner','admin','member','viewer')). Do not add a second
#: role vocabulary.
CLIENT_ROLES: tuple[str, ...] = ("owner", "admin", "member", "viewer")

#: PD-2A: the roles an ACTING client owner/admin — or a consultant managing the
#: client's users on the client's behalf — is permitted to ASSIGN. The decision
#: register bounds this by the *client-role boundary* (the four roles above); it
#: does not introduce a narrower owner restriction, so we deliberately do not
#: invent one here. Keeping it as an explicit named set makes the boundary a
#: single, changeable, testable policy point should a PO decision ever tighten
#: it.
ASSIGNABLE_CLIENT_ROLES: tuple[str, ...] = CLIENT_ROLES

# -- invitation lifecycle ----------------------------------------------------
INVITATION_PENDING = "pending"
INVITATION_ACCEPTED = "accepted"
INVITATION_REVOKED = "revoked"
#: ``expired`` is a DERIVED state (status='pending' AND expires_at <= now). It is
#: never written to the database — the durable column only ever holds
#: pending / accepted / revoked, so expiry needs no background job to be true.
INVITATION_EXPIRED = "expired"

#: Default validity window for a single-use client invitation.
INVITATION_EXPIRY_DAYS = 7


class ClientIdentityError(ValueError):
    """Raised when a client-identity request violates PD-1A / PD-2A policy."""


def validate_client_role(role: str) -> str:
    """Return ``role`` if it is a valid client role, else raise.

    Keeps the PD-2A role boundary enforced *before* any persistence occurs.
    """
    normalised = (role or "").strip().lower()
    if normalised not in CLIENT_ROLES:
        raise ClientIdentityError(
            f"invalid client role {role!r}; expected one of {', '.join(CLIENT_ROLES)}"
        )
    return normalised


def normalise_email(email: str) -> str:
    """Canonical invitation email form (trimmed, lower-cased)."""
    return (email or "").strip().lower()


def expiry_from_now(
    *, days: int = INVITATION_EXPIRY_DAYS, now: Optional[datetime] = None
) -> datetime:
    """The ``expires_at`` for a newly created invitation."""
    base = now or datetime.now(timezone.utc)
    return base + timedelta(days=days)


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def resolve_invitation_state(
    status: Optional[str],
    expires_at: Optional[datetime],
    *,
    now: Optional[datetime] = None,
) -> str:
    """Resolve the *effective* state of an invitation record.

    A ``pending`` row whose ``expires_at`` has passed is reported as
    ``expired`` without any stored mutation — an invitation that is too old can
    therefore never be consumed, and no scheduled job is required for the
    expiry to be authoritative.
    """
    current = (status or INVITATION_PENDING).strip().lower()
    if current != INVITATION_PENDING:
        # accepted / revoked (or any terminal state) is reported verbatim.
        return current
    expiry = _as_utc(expires_at)
    if expiry is not None:
        moment = now or datetime.now(timezone.utc)
        if moment >= expiry:
            return INVITATION_EXPIRED
    return INVITATION_PENDING


def invitation_is_consumable(
    status: Optional[str],
    expires_at: Optional[datetime],
    *,
    now: Optional[datetime] = None,
) -> bool:
    """True only for a still-pending, unexpired invitation (PD-1A single-use)."""
    return resolve_invitation_state(status, expires_at, now=now) == INVITATION_PENDING


def may_manage_client_users(role: Optional[str]) -> bool:
    """PD-2A: who may administer a client Organisation's users.

    The client Organisation ``owner`` and ``admin`` hold this authority for their
    OWN organisation. ``member`` and ``viewer`` never do.
    """
    return (role or "").strip().lower() in ("owner", "admin")


def permitted_assignable_roles(actor_role: Optional[str]) -> tuple[str, ...]:
    """PD-2A: the role set ``actor_role`` is authorised to assign.

    Returns the empty tuple when the actor holds no client-user administration
    authority at all, so callers can distinguish "not permitted" from
    "permitted but restricted".
    """
    if not may_manage_client_users(actor_role):
        return ()
    return ASSIGNABLE_CLIENT_ROLES
