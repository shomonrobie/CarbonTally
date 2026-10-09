"""CT-MP-SUB-004 NOTIFICATION-IMPLEMENT-04 — Manual Processing lifecycle
notifications (N1-N4).

Product-Owner authorised (2026-10-05, recorded immediately before this task).
This module is the **single producer** for all four events, so the recipient
rules, the deterministic event keys and the fail-safe behaviour are defined in
exactly one place.

    N1  MP work assigned/routed to a Processing Entity   -> active PE staff
    N2  MP item/batch assigned to an internal validator  -> that validator
    N3  a document/batch enters Manual Processing        -> responsible consultant
    N4  MP reaches its terminal validated state          -> original uploader

Ratified rules implemented here (no exceptions):

* **In-app only.** No email, no ``notification_delivery`` row, no mailer call.
  The X2 operational-alerting email path is untouched.
* **Server-derived recipients only.** No request payload, caller or client input
  can nominate a recipient or an event key.
* **Mandatory, not configurable.** No preference system, no opt-out, no Admin
  off-switch, no event-level toggle and no feature flag is introduced or read.
* **Idempotent.** Every event key is deterministic, namespaced and derived from
  the stable business identity of the event; the existing
  ``uq_notifications_event_key`` unique index on ``(recipient_id, event_key)``
  is the final boundary.
* **Best-effort, never fatal.** The business mutation (assignment, status
  transition, audit) is already committed before this module runs; a
  notification failure is logged and never rolls the workflow back.

Manual Processing **allocation/release remain audit-only** (PO decision P-2) and
are deliberately absent from this module.

The ``notifications`` table is reached only through the existing
``NotificationsRepository.create_idempotent``; the retrieval path is the
existing ``/api/v3/notifications`` API. Supabase Realtime is never a
dependency of this module.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

_log = logging.getLogger("carbon_tally.manual_processing_notifications")

# ---------------------------------------------------------------------------
# Vocabulary (``notification_type`` is a free-form column; one value per event)
# ---------------------------------------------------------------------------

NOTIFICATION_TYPE_PE_ASSIGNMENT = "manual_processing.pe_assigned"
NOTIFICATION_TYPE_VALIDATOR_ASSIGNMENT = "manual_processing.validator_assigned"
NOTIFICATION_TYPE_MP_ENTRY = "manual_processing.entered"
NOTIFICATION_TYPE_COMPLETION = "manual_processing.completed"

#: The per-recipient event-key namespaces (one per event class).
_KEY_PE_ASSIGNMENT = "manual_processing.pe_assigned"
_KEY_VALIDATOR_ASSIGNMENT = "manual_processing.validator_assigned"
_KEY_MP_ENTRY = "manual_processing.entered"
_KEY_COMPLETION = "manual_processing.completed"

#: ``actor_domain`` recorded on the row (informational; no CHECK constraint).
ACTOR_DOMAIN_INTERNAL_STAFF = "internal_staff"
ACTOR_DOMAIN_PROCESSING_ENTITY = "processing_entity"

#: The machine identity recorded as the actor of a platform decision. Mirrors
#: the automatic-processing worker / routing module system actor (nil UUID).
SYSTEM_ACTOR = "00000000-0000-0000-0000-000000000000"

#: Audit action recorded when an authorised event exists but the single
#: responsible consultant cannot be deterministically resolved. The event is
#: NOT guessed and NOT broadcast (PO recipient rule).
AUDIT_CONSULTANT_UNRESOLVED = "manual_processing:consultant_notification_unresolved"

# ---------------------------------------------------------------------------
# Deep links (existing, role-gated CarbonTally routes only)
# ---------------------------------------------------------------------------

LINK_PE_QUEUE = "/pe/assignments"
LINK_CONSULTANT_WORKSPACE = "/consultant"
LINK_NOTIFICATIONS = "/notifications"


def link_ops_item(item_id: str) -> str:
    """The existing internal operations item workspace (``can_process``)."""
    return f"/ops/items/{item_id}"


def link_processing_item(item_id: str) -> str:
    """The existing organisation processing-item page (``requireOrg``)."""
    return f"/processing/{item_id}"


# ---------------------------------------------------------------------------
# Deterministic event keys (server-generated; never caller-supplied)
# ---------------------------------------------------------------------------


def pe_assignment_event_key(
    *, item_id: str, assignment_id: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> str:
    """N1 key for one item-level Processing Entity assignment.

    The discriminator is the D38 ``work_item_assignments.id`` of the OPEN
    assignment row, so a re-route that creates no new ledger row (the router is
    idempotent by construction) can never produce a second notification, while
    a genuine reassignment can.
    """
    discriminator = str(assignment_id or f"entity:{entity_id}")
    return f"{_KEY_PE_ASSIGNMENT}:item:{item_id}:{discriminator}"


def pe_batch_assignment_event_key(*, batch_id: str, entity_id: str) -> str:
    """N1 key for one batch-level Processing Entity assignment (D22)."""
    return f"{_KEY_PE_ASSIGNMENT}:batch:{batch_id}:{entity_id}"


def validator_batch_assignment_event_key(*, batch_id: str, user_id: str) -> str:
    """N2 key for one batch-level internal validator assignment (D22)."""
    return f"{_KEY_VALIDATOR_ASSIGNMENT}:batch:{batch_id}:{user_id}"


def mp_entry_item_event_key(*, item_id: str) -> str:
    """N3 key for one item entering Manual Processing (item identity)."""
    return f"{_KEY_MP_ENTRY}:item:{item_id}"


def mp_entry_batch_event_key(*, batch_id: str) -> str:
    """N3 key for one batch entering Manual Processing (batch identity)."""
    return f"{_KEY_MP_ENTRY}:batch:{batch_id}"


def completion_event_key(*, item_id: str) -> str:
    """N4 key for the item's terminal validated state (at most one per item)."""
    return f"{_KEY_COMPLETION}:item:{item_id}"


# ---------------------------------------------------------------------------
# Recipient resolvers (server-derived; authoritative data only)
# ---------------------------------------------------------------------------


async def pe_staff_recipients(repos: Any, entity_id: Optional[str]) -> list[str]:
    """Active staff user ids of ONE Processing Entity.

    Authoritative source: ``staff_profiles.entity_id`` (the existing roster
    query ``StaffRepository.list_entity_staff``). Inactive profiles and
    profiles without a ``user_id`` are excluded. The notification is never the
    source of truth — the D38 assignment ledger remains authoritative.

    Only the ASSIGNED entity's staff are returned; every other entity's staff
    and every internal user is excluded by the query itself.
    """
    if not entity_id:
        return []
    getter = getattr(getattr(repos, "staff", None), "list_entity_staff", None)
    if getter is None:
        return []
    try:
        profiles = await getter(str(entity_id))
    except Exception:  # noqa: BLE001 — roster lookup must never break the workflow
        _log.warning("PE staff roster lookup failed for entity %s", entity_id)
        return []
    recipients = {
        str(getattr(p, "user_id", "") or "")
        for p in profiles or []
        if getattr(p, "is_active", True) and getattr(p, "user_id", None)
    }
    return sorted(r for r in recipients if r)


async def _active_client_grants(repos: Any, organization_id: str) -> list[Any]:
    """Active consultant-client grants for one organisation (authoritative)."""
    getter = getattr(getattr(repos, "consultants", None),
                     "list_active_client_grants", None)
    if getter is None:
        return []
    try:
        return list(await getter(str(organization_id)) or [])
    except Exception:  # noqa: BLE001
        _log.warning("consultant grant lookup failed for org %s", organization_id)
        return []


async def _item_consultant_firm_id(repos: Any, item: Any) -> Optional[str]:
    """The item's durable D7 consultant-firm provenance (or ``None``)."""
    item_id = getattr(item, "id", None)
    if not item_id:
        return None
    getter = getattr(getattr(repos, "manual_extraction", None),
                     "get_item_consultant_provenance", None)
    if getter is None:
        return None
    try:
        row = await getter(str(item_id))
    except Exception:  # noqa: BLE001
        return None
    firm_id = (row or {}).get("consultant_firm_id")
    return str(firm_id) if firm_id else None


async def _firm_responsible_user(
    repos: Any, firm_id: str, grants: list[Any]
) -> Optional[str]:
    """The ONE responsible consultant user for a firm (or ``None``).

    Deterministic order, never a broadcast group:

    1. the **active firm member recorded as the creator of the client
       relationship** (``consultant_clients.created_by`` — the
       server-authoritative actor who established the grant);
    2. otherwise the **firm's principal consultant**
       (``consultant_profiles.user_id``).

    A candidate is only accepted when it is an ACTIVE member of the firm. When
    neither rule yields a member of the firm, ``None`` is returned and the
    caller fails safe.
    """
    getter = getattr(getattr(repos, "consultants", None), "list_firm_members", None)
    if getter is None:
        return None
    try:
        members = await getter(str(firm_id)) or []
    except Exception:  # noqa: BLE001
        return None
    active = {
        str(getattr(m, "user_id", "") or "")
        for m in members
        if getattr(m, "is_active", True) and getattr(m, "user_id", None)
    }
    if not active:
        return None
    for grant in grants:
        if str(getattr(grant, "consultant_id", "") or "") != str(firm_id):
            continue
        created_by = str(getattr(grant, "created_by", "") or "")
        if created_by and created_by in active:
            return created_by
    profile_getter = getattr(
        getattr(repos, "consultants", None), "get_profile_by_id", None
    )
    if profile_getter is not None:
        try:
            profile = await profile_getter(str(firm_id))
        except Exception:  # noqa: BLE001
            profile = None
        principal = str(getattr(profile, "user_id", "") or "") if profile else ""
        if principal and principal in active:
            return principal
    return None


async def resolve_responsible_consultant(
    repos: Any, *, organization_id: Optional[str], item: Any = None
) -> tuple[Optional[str], str]:
    """Resolve the SINGLE responsible consultant for an affected client.

    Returns ``(user_id | None, reason)``. The reason is a stable diagnostic
    vocabulary (recorded in the audit trail when the case is a genuine product
    ambiguity). It is **never** a broadcast: at most one user id is returned.

    Resolution order (all server-side and authoritative):

    1. the item's durable consultant-firm provenance (D7 ``consultant_firm_id``)
       when that firm still holds an ACTIVE client grant;
    2. otherwise the sole ACTIVE ``consultant_clients`` relationship for the
       organisation.

    Anything else — no relationship, multiple relationships, a recorded firm
    whose relationship has ended, or no resolvable active firm member — returns
    ``None``. The event is then NOT emitted and NOT guessed.
    """
    if not organization_id:
        return None, "no_organization"
    grants = await _active_client_grants(repos, organization_id)
    if not grants:
        # A direct customer with no consultant relationship is a normal state,
        # not an ambiguity: nothing to notify, nothing to escalate.
        return None, "no_consultant_relationship"
    firm_id = (
        await _item_consultant_firm_id(repos, item) if item is not None else None
    )
    if firm_id:
        if not any(
            str(getattr(g, "consultant_id", "") or "") == firm_id for g in grants
        ):
            return None, "provenance_firm_relationship_ended"
        user = await _firm_responsible_user(repos, firm_id, grants)
        return (
            (user, "item_consultant_firm") if user
            else (None, "firm_member_unresolved")
        )
    if len(grants) != 1:
        return None, "multiple_consultant_relationships"
    firm_id = str(getattr(grants[0], "consultant_id", "") or "")
    if not firm_id:
        return None, "grant_without_firm"
    user = await _firm_responsible_user(repos, firm_id, grants)
    return (
        (user, "sole_consultant_relationship") if user
        else (None, "firm_member_unresolved")
    )


async def resolve_uploader(repos: Any, item: Any) -> Optional[str]:
    """The ORIGINAL uploader of the item's source document (or ``None``).

    Authoritative path (the actual ingestion path):
    ``manual_extraction_items.file_id`` -> ``organization_files`` ->
    ``uploaded_by`` (written once at upload from the authenticated actor).

    Never derived from the current assignee, the current PE, the current
    validator, the organisation owner or the consultant firm owner.
    """
    file_id = getattr(item, "file_id", None)
    if not file_id:
        return None
    getter = getattr(getattr(repos, "files", None), "get", None)
    if getter is None:
        return None
    try:
        record = await getter(str(file_id))
    except Exception:  # noqa: BLE001
        return None
    if record is None:
        return None
    if isinstance(record, dict):
        uploaded_by = record.get("uploaded_by")
    else:
        uploaded_by = getattr(record, "uploaded_by", None)
    uploaded_by = str(uploaded_by or "")
    return uploaded_by or None


async def _is_consultant_member(repos: Any, user_id: str) -> bool:
    """True when ``user_id`` is an ACTIVE member of any consultant firm."""
    getter = getattr(
        getattr(repos, "consultants", None), "get_active_memberships_by_user", None
    )
    if getter is None:
        return False
    try:
        return bool(await getter(str(user_id)) or [])
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Producer core (in-app only; best effort; idempotent)
# ---------------------------------------------------------------------------


async def _emit(
    repos: Any,
    *,
    recipients: list[str],
    event_key: str,
    notification_type: str,
    title: str,
    message: str,
    link: Optional[str] = None,
    link_for: Optional[Any] = None,
    priority: int = 30,
    actor_domain: Optional[str] = None,
) -> list[str]:
    """Persist one idempotent IN-APP notification per recipient.

    Mirrors the ratified producer convention (``services/consultant_lifecycle``,
    ``services/work_items``): the durable row is created through
    ``NotificationsRepository.create_idempotent``, the recipient set is already
    server-derived, and a failure is logged — never raised, never fatal.

    **No email.** No ``notification_delivery`` row is written and no mailer is
    invoked; this is the only producer responsibility in this module.
    """
    create = getattr(getattr(repos, "notifications", None), "create_idempotent", None)
    if create is None:
        return []
    delivered: list[str] = []
    for user_id in sorted({str(r) for r in recipients if r}):
        try:
            await create(
                user_id,
                event_key,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                link=(link_for(user_id) if link_for is not None else link),
                actor_domain=actor_domain,
            )
            delivered.append(user_id)
        except Exception:  # noqa: BLE001 — best effort, logged (never fatal)
            _log.warning(
                "manual-processing notification producer failed (%s / %s)",
                notification_type,
                event_key,
            )
    return delivered


async def _record_consultant_ambiguity(
    repos: Any,
    *,
    organization_id: str,
    reason: str,
    item_id: Optional[str] = None,
    batch_id: Optional[str] = None,
) -> None:
    """Record the fail-safe N3 outcome in the EXISTING append-only audit trail.

    The PO recipient rule forbids guessing or broadcasting. When an authorised
    N3 event cannot be deterministically attributed to one responsible
    consultant, the safest existing workflow path is: emit nothing, and record
    why — so the genuine product-model gap is visible for PO review.
    """
    from domain.audit import AuditEntry

    entity_type = (
        "manual_extraction_item" if item_id else "manual_extraction_batch"
    )
    entity_id = str(item_id or batch_id or organization_id)
    try:
        await repos.audit.record(
            AuditEntry(
                id=str(uuid.uuid4()),
                correlation_id=entity_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=AUDIT_CONSULTANT_UNRESOLVED,
                actor=SYSTEM_ACTOR,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={
                    "organization_id": organization_id,
                    "reason": reason,
                    "event": NOTIFICATION_TYPE_MP_ENTRY,
                },
                ip_address=None,
            )
        )
    except Exception:  # noqa: BLE001 — audit must never break the workflow
        _log.warning(
            "manual-processing consultant-ambiguity audit failed (%s)", reason
        )


# ---------------------------------------------------------------------------
# N1 — MP work assigned/routed to a Processing Entity
# ---------------------------------------------------------------------------


async def notify_pe_item_assignment(
    repos: Any,
    *,
    item_id: str,
    entity_id: str,
    assignment_id: Optional[str] = None,
    actor_domain: str = ACTOR_DOMAIN_INTERNAL_STAFF,
) -> list[str]:
    """N1: notify the assigned PE's active staff that MP work is now theirs.

    The D38 assignment is already committed (and remains authoritative). Only
    the ASSIGNED entity's active staff are notified; duplicate routing creates
    no second notification (the event key carries the assignment-row identity).
    """
    recipients = await pe_staff_recipients(repos, entity_id)
    if not recipients:
        return []
    return await _emit(
        repos,
        recipients=recipients,
        event_key=pe_assignment_event_key(
            item_id=str(item_id), assignment_id=assignment_id, entity_id=entity_id
        ),
        notification_type=NOTIFICATION_TYPE_PE_ASSIGNMENT,
        title="Manual processing work assigned",
        message=(
            "A manual processing work item has been assigned to your "
            "processing entity."
        ),
        link=LINK_PE_QUEUE,
        priority=30,
        actor_domain=actor_domain,
    )


async def notify_pe_batch_assignment(
    repos: Any,
    *,
    batch_id: str,
    entity_id: str,
    actor_domain: str = ACTOR_DOMAIN_INTERNAL_STAFF,
) -> list[str]:
    """N1: notify the assigned PE's active staff of a BATCH-level assignment."""
    recipients = await pe_staff_recipients(repos, entity_id)
    if not recipients:
        return []
    return await _emit(
        repos,
        recipients=recipients,
        event_key=pe_batch_assignment_event_key(
            batch_id=str(batch_id), entity_id=str(entity_id)
        ),
        notification_type=NOTIFICATION_TYPE_PE_ASSIGNMENT,
        title="Manual processing batch assigned",
        message=(
            "A manual processing batch has been assigned to your processing "
            "entity."
        ),
        link=LINK_PE_QUEUE,
        priority=30,
        actor_domain=actor_domain,
    )


# ---------------------------------------------------------------------------
# N2 — MP item/batch assigned to a specific CarbonTally internal validator
# ---------------------------------------------------------------------------


async def notify_validator_batch_assignment(
    repos: Any,
    *,
    batch_id: str,
    user_id: str,
    actor_domain: str = ACTOR_DOMAIN_INTERNAL_STAFF,
) -> list[str]:
    """N2: notify ONE internal validator that a batch is assigned to them.

    The item-level equivalent is the pre-existing ``work_item.assigned``
    producer in ``services/work_items.py`` (reused unchanged, never
    duplicated); this closes the batch-level D22 assignment, which previously
    notified nobody.
    """
    if not user_id:
        return []
    return await _emit(
        repos,
        recipients=[str(user_id)],
        event_key=validator_batch_assignment_event_key(
            batch_id=str(batch_id), user_id=str(user_id)
        ),
        notification_type=NOTIFICATION_TYPE_VALIDATOR_ASSIGNMENT,
        title="Manual processing batch assigned to you",
        message="A manual processing batch is assigned to you for validation.",
        link=LINK_NOTIFICATIONS,
        priority=30,
        actor_domain=actor_domain,
    )


# ---------------------------------------------------------------------------
# N3 — a document/batch enters Manual Processing -> responsible consultant
# ---------------------------------------------------------------------------


async def notify_manual_processing_entry(
    repos: Any,
    *,
    organization_id: Optional[str],
    item_id: Optional[str] = None,
    batch_id: Optional[str] = None,
) -> list[str]:
    """N3: notify the ONE responsible consultant for the affected client.

    Recipient rule (PO): the responsible consultant determined server-side from
    the authoritative consultant-client relationship model. There is NO
    broadcast to firm members, ``can_manage_clients`` members, the client
    organisation, or unrelated CarbonTally staff.

    Fail-safe (PO): when the responsible consultant cannot be deterministically
    resolved the event is NOT emitted, NOT guessed, and the ambiguity is
    recorded in the append-only audit trail for PO review.

    Emitted at the Manual Processing entry boundaries only (automatic-fallback
    routing of an item; explicit governed creation of an MP batch). It is NOT
    emitted for later assignment/reassignment of already-entered work, so the
    consultant is never notified repeatedly for the same entry event.
    """
    item = None
    if item_id:
        getter = getattr(
            getattr(repos, "manual_extraction", None), "get_item", None
        )
        if getter is not None:
            try:
                item = await getter(str(item_id))
            except Exception:  # noqa: BLE001
                item = None
    recipient, reason = await resolve_responsible_consultant(
        repos, organization_id=organization_id, item=item
    )
    if not recipient:
        if reason != "no_consultant_relationship":
            # A genuine ambiguity (relationship exists, attribution does not).
            await _record_consultant_ambiguity(
                repos,
                organization_id=str(organization_id or ""),
                reason=reason,
                item_id=item_id,
                batch_id=batch_id,
            )
        return []
    event_key = (
        mp_entry_item_event_key(item_id=str(item_id))
        if item_id
        else mp_entry_batch_event_key(batch_id=str(batch_id))
    )
    return await _emit(
        repos,
        recipients=[recipient],
        event_key=event_key,
        notification_type=NOTIFICATION_TYPE_MP_ENTRY,
        title="Work entered manual processing",
        message=(
            "A document has entered manual processing for one of your clients."
        ),
        link=LINK_CONSULTANT_WORKSPACE,
        priority=30,
        actor_domain=ACTOR_DOMAIN_INTERNAL_STAFF,
    )


# ---------------------------------------------------------------------------
# N4 — Manual Processing terminal validated state -> original uploader
# ---------------------------------------------------------------------------


async def notify_manual_processing_completion(repos: Any, *, item: Any) -> list[str]:
    """N4: notify the ORIGINAL uploader that manual processing is complete.

    Emitted ONLY at the item's terminal successful/validated state — the
    CarbonTally CT-QC approval (``ct_qc_approved``), which is the single point
    at which the required validation/review of manually processed work is
    satisfied. PE review/QC completion, PE release, an intermediate extraction
    stage and a closed work-item assignment are explicitly NOT this event.

    The recipient is the durable uploader provenance
    (``manual_extraction_items.file_id`` -> ``organization_files.uploaded_by``),
    which is never rewritten by reassignment. No client organisation user is
    notified (PO decision).
    """
    uploader = await resolve_uploader(repos, item)
    if not uploader:
        return []
    item_id = str(getattr(item, "id", "") or "")
    if not item_id:
        return []
    consultant_uploader = await _is_consultant_member(repos, uploader)
    return await _emit(
        repos,
        recipients=[uploader],
        event_key=completion_event_key(item_id=item_id),
        notification_type=NOTIFICATION_TYPE_COMPLETION,
        title="Manual processing complete",
        message=(
            "Manual processing and CarbonTally validation are complete for a "
            "document you uploaded."
        ),
        link_for=(
            (lambda _uid: LINK_CONSULTANT_WORKSPACE)
            if consultant_uploader
            else (lambda _uid: link_processing_item(item_id))
        ),
        priority=30,
        actor_domain=ACTOR_DOMAIN_INTERNAL_STAFF,
    )
