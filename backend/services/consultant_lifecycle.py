"""P6-2E (D11) — Consultant lifecycle notifications.

Ratified: ``PO-PHASE6-D11-20260910`` (five consultant lifecycle events) and
``PO-PHASE6-D8-20260910`` (reuse the existing conversation model — untouched
here). Implemented per
``CARBONTALLY_PHASE6_REMAINDER_IMPLEMENTATION_CONTRACT_V1.0.md`` §7.2.

The five events:

1. ``accepted``           — the client organisation accepted the engagement
2. ``submitted_to_qc``    — the consultant submitted reviewed work to CT-QC
3. ``qc_outcome``         — the CarbonTally QC decision (approved/rejected)
4. ``customer_decision``  — the client approved/rejected the processed item
5. ``rework``             — work routed back for rework (QC rejection or
                            consultant-review rejection)

Design rules (centralised here):

* **Durable, not ephemeral.** Events are persisted through the existing
  ``notifications`` table via ``NotificationsRepository.create_idempotent``.
  The in-process ``EventBus`` is deliberately NOT used (fire-and-forget,
  non-durable).
* **Deterministic, server-generated keys.** ``lifecycle_event_key`` builds a
  namespaced key from the stable business identity of the event. No randomness,
  no client input. Database uniqueness (``uq_notifications_event_key``) is the
  final idempotency boundary.
* **Server-derived recipients only.** Recipient sets come from the
  authoritative relationships (consultant firm membership, active consultant
  client grants, internal CarbonTally ops staff). A request can never choose a
  recipient.
* **Best effort, never fatal.** Mirrors the existing emitter convention
  (``services/work_items.py``): the business action is already committed, so a
  notification failure is logged and never breaks the workflow.
* **Emitted only after a successful transition.** Callers invoke these helpers
  after authorization + the state mutation succeed, so a denied request emits
  nothing.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

_log = logging.getLogger("carbon_tally.consultant_lifecycle")

#: The five ratified lifecycle events (stable vocabulary).
EVENT_ACCEPTED = "accepted"
EVENT_SUBMITTED_TO_QC = "submitted_to_qc"
EVENT_QC_OUTCOME = "qc_outcome"
EVENT_CUSTOMER_DECISION = "customer_decision"
EVENT_REWORK = "rework"

CONSULTANT_LIFECYCLE_EVENTS: tuple[str, ...] = (
    EVENT_ACCEPTED,
    EVENT_SUBMITTED_TO_QC,
    EVENT_QC_OUTCOME,
    EVENT_CUSTOMER_DECISION,
    EVENT_REWORK,
)

#: Rework sources (stable discriminators; never client-supplied).
REWORK_SOURCE_CT_QC_REJECTED = "ct_qc_rejected"
REWORK_SOURCE_CONSULTANT_REVIEW_REJECTED = "consultant_review_rejected"

#: ``notification_type`` per event (free-form column; one value per event).
NOTIFICATION_TYPE: dict[str, str] = {
    event: f"consultant.lifecycle.{event}" for event in CONSULTANT_LIFECYCLE_EVENTS
}

#: ``actor_domain`` of the actor whose action produced the event (informational
#: on the notification row; the column has no CHECK constraint).
ACTOR_DOMAIN_BY_EVENT: dict[str, str] = {
    EVENT_ACCEPTED: "organisation_member",
    EVENT_SUBMITTED_TO_QC: "consultant",
    EVENT_QC_OUTCOME: "internal_staff",
    EVENT_CUSTOMER_DECISION: "organisation_member",
    EVENT_REWORK: "internal_staff",
}

_KEY_NAMESPACE = "consultant.lifecycle"


def lifecycle_event_key(
    event: str, *, identity: str, discriminator: Optional[str] = None
) -> str:
    """Deterministic, server-generated event key for a lifecycle event.

    Shape: ``consultant.lifecycle.<event>:<identity>[:<discriminator>]``, where
    ``identity`` is the stable business identity (``engagement:<id>`` or
    ``item:<id>``) and ``discriminator`` distinguishes a meaningful outcome
    (approved/rejected, rework source). The same business event always yields
    the same key; a different outcome is a different event with its own key.
    No randomness is involved.
    """
    if event not in NOTIFICATION_TYPE:
        raise ValueError(f"unknown consultant lifecycle event: {event!r}")
    parts = [f"{_KEY_NAMESPACE}.{event}", str(identity)]
    if discriminator:
        parts.append(str(discriminator))
    return ":".join(parts)


# ---------------------------------------------------------------------------
# Recipient derivation (server-side only)
# ---------------------------------------------------------------------------


async def _firm_recipient_user_ids(repos: Any, firm_id: Optional[str]) -> list[str]:
    """Active members of ``firm_id`` (the authoritative firm relationship)."""
    if not firm_id:
        return []
    getter = getattr(repos.consultants, "list_firm_members", None)
    if getter is None:
        return []
    members = await getter(str(firm_id))
    return sorted(
        {
            str(getattr(m, "user_id", "") or "")
            for m in members
            if getattr(m, "is_active", True) and getattr(m, "user_id", None)
        }
    )


async def _engaged_firm_ids(repos: Any, organization_id: Optional[str]) -> list[str]:
    """Firms holding an ACTIVE consultant-client grant for the organisation."""
    if not organization_id:
        return []
    getter = getattr(repos.consultants, "list_active_client_grants", None)
    if getter is None:
        return []
    grants = await getter(str(organization_id))
    return sorted(
        {
            str(getattr(g, "consultant_id", "") or "")
            for g in grants
            if getattr(g, "consultant_id", None)
        }
    )


async def _internal_ops_recipient_user_ids(repos: Any) -> list[str]:
    """Internal CarbonTally operations recipients (existing resolver)."""
    getter = getattr(repos.notifications, "support_staff_user_ids", None)
    if getter is None:
        return []
    return sorted({str(u) for u in await getter()})


async def _organization_id_for_item(
    repos: Any, item: Any, batch: Any = None
) -> Optional[str]:
    """The item's authoritative organisation (server-derived, never request)."""
    if batch is not None:
        return str(getattr(batch, "organization_id", "") or "") or None
    batch_id = getattr(item, "batch_id", None)
    if not batch_id:
        return None
    getter = getattr(repos.manual_extraction, "get_batch", None)
    loaded = await getter(str(batch_id)) if getter is not None else None
    if loaded is None:
        return None
    return str(getattr(loaded, "organization_id", "") or "") or None


async def _emit(
    repos: Any,
    *,
    event: str,
    event_key: str,
    recipients: list[str],
    title: str,
    message: str,
    link: Optional[str] = None,
    link_for: Optional[Callable[[str], str]] = None,
    priority: int = 30,
    actor_domain: Optional[str] = None,
) -> list[str]:
    """Persist one idempotent notification per recipient (best effort).

    ``link`` sets one deep link for every recipient; ``link_for`` (preferred for
    item events) resolves a per-recipient link, because a consultant item deep
    link must carry the recipient firm's own engagement id.
    """
    delivered: list[str] = []
    for user_id in sorted({str(r) for r in recipients if r}):
        try:
            await repos.notifications.create_idempotent(
                user_id,
                event_key,
                notification_type=NOTIFICATION_TYPE[event],
                title=title,
                message=message,
                priority=priority,
                link=(link_for(user_id) if link_for is not None else link),
                actor_domain=actor_domain or ACTOR_DOMAIN_BY_EVENT[event],
            )
            delivered.append(user_id)
        except Exception:  # noqa: BLE001 — best effort, logged (never fatal)
            _log.warning(
                "consultant lifecycle producer failed for %s (%s)",
                event,
                event_key,
            )
    return delivered


def _item_label(item: Any) -> str:
    return str(getattr(item, "file_name", None) or getattr(item, "id", "") or "item")


async def _firm_and_ops(
    repos: Any, *, organization_id: Optional[str], include_ops: bool = False
) -> list[str]:
    """Firm recipients for the organisation's active grants (+ optional ops)."""
    recipients: set[str] = set()
    for firm_id in await _engaged_firm_ids(repos, organization_id):
        recipients.update(await _firm_recipient_user_ids(repos, firm_id))
    if include_ops:
        recipients.update(await _internal_ops_recipient_user_ids(repos))
    return sorted(recipients)


#: Link fallback for recipients without a consultant item context (e.g. internal
#: ops). ``/notifications`` is a valid authenticated route — never a broken path.
_NOTIFICATIONS_LINK = "/notifications"


def _consultant_item_link(item_id: str, client_id: Optional[str]) -> str:
    """Deep link to the consultant item workspace.

    Route: ``/consultant/items/:clientId/:itemId`` (``:clientId`` is the
    recipient firm's engagement id). Falls back to ``/notifications`` when the
    engagement id cannot be resolved. **P6-2F (IV-N6 fix):** P6-2E emitted
    ``/consultant/items/{item_id}``, which does not match the route and did not
    resolve in the UI.
    """
    if client_id and item_id:
        return f"/consultant/items/{client_id}/{item_id}"
    return _NOTIFICATIONS_LINK


async def _client_id_by_firm(
    repos: Any, organization_id: Optional[str]
) -> dict[str, str]:
    """``{firm_id: engagement_id}`` for the organisation's ACTIVE grants.

    The engagement id (``consultant_clients.id``) is the ``:clientId`` the
    consultant item route needs, so each firm's members receive their own valid
    deep link (recipients may span more than one engaged firm).
    """
    if not organization_id:
        return {}
    getter = getattr(repos.consultants, "list_active_client_grants", None)
    if getter is None:
        return {}
    grants = await getter(str(organization_id))
    out: dict[str, str] = {}
    for g in grants:
        firm_id = str(getattr(g, "consultant_id", "") or "")
        client_id = str(getattr(g, "id", "") or "")
        if firm_id and client_id and firm_id not in out:
            out[firm_id] = client_id
    return out


async def _consultant_link_for(
    repos: Any, *, organization_id: Optional[str], item_id: str
) -> Callable[[str], str]:
    """Per-recipient link resolver for consultant item lifecycle events."""
    links: dict[str, str] = {}
    for firm_id, client_id in (await _client_id_by_firm(repos, organization_id)).items():
        link = _consultant_item_link(str(item_id), client_id)
        for user_id in await _firm_recipient_user_ids(repos, firm_id):
            links.setdefault(str(user_id), link)

    def _resolve(user_id: str) -> str:
        return links.get(str(user_id), _NOTIFICATIONS_LINK)

    return _resolve


# ---------------------------------------------------------------------------
# The five lifecycle events
# ---------------------------------------------------------------------------


async def notify_engagement_accepted(repos: Any, *, client: Any) -> list[str]:
    """Event 1 — the client organisation accepted the consultant engagement.

    Recipients: the active members of the firm that holds the engagement (that
    firm must act on the accepted relationship). The client is the actor here,
    so the client organisation is not notified of its own decision.
    """
    firm_id = str(getattr(client, "consultant_id", "") or "") or None
    event_key = lifecycle_event_key(
        EVENT_ACCEPTED, identity=f"engagement:{getattr(client, 'id', '')}"
    )
    recipients = await _firm_recipient_user_ids(repos, firm_id)
    return await _emit(
        repos,
        event=EVENT_ACCEPTED,
        event_key=event_key,
        recipients=recipients,
        title="Engagement accepted",
        message=(
            "Your client organisation accepted the engagement request. "
            "You can now operate on their processing work."
        ),
        link="/consultant",
    )


async def notify_submitted_to_qc(
    repos: Any, *, item: Any, batch: Any = None
) -> list[str]:
    """Event 2 — the consultant submitted reviewed work to CarbonTally QC.

    Recipients: the engaged firm's members (submission confirmation) plus the
    internal CarbonTally operations recipients (QC intake visibility).
    """
    organization_id = await _organization_id_for_item(repos, item, batch)
    event_key = lifecycle_event_key(
        EVENT_SUBMITTED_TO_QC, identity=f"item:{getattr(item, 'id', '')}"
    )
    recipients = await _firm_and_ops(
        repos, organization_id=organization_id, include_ops=True
    )
    return await _emit(
        repos,
        event=EVENT_SUBMITTED_TO_QC,
        event_key=event_key,
        recipients=recipients,
        title="Work submitted to CarbonTally QC",
        message=(
            f"Your client's item ({_item_label(item)}) was submitted to "
            "CarbonTally QC."
        ),
        link_for=await _consultant_link_for(
            repos,
            organization_id=organization_id,
            item_id=str(getattr(item, "id", "")),
        ),
    )


async def notify_qc_outcome(
    repos: Any, *, item: Any, approved: bool, batch: Any = None
) -> list[str]:
    """Event 3 — the CarbonTally QC decision (approved or rejected).

    Recipients: the engaged firm's members (they must act on a rejection and
    are informed of an approval). The QC actor is internal staff, so staff are
    not notified of their own decision.
    """
    organization_id = await _organization_id_for_item(repos, item, batch)
    outcome = "approved" if approved else "rejected"
    event_key = lifecycle_event_key(
        EVENT_QC_OUTCOME,
        identity=f"item:{getattr(item, 'id', '')}",
        discriminator=outcome,
    )
    recipients = await _firm_and_ops(repos, organization_id=organization_id)
    return await _emit(
        repos,
        event=EVENT_QC_OUTCOME,
        event_key=event_key,
        recipients=recipients,
        title=f"CarbonTally QC {outcome}",
        message=(
            f"CarbonTally QC {outcome} the item ({_item_label(item)}) "
            "submitted for your client."
        ),
        link_for=await _consultant_link_for(
            repos,
            organization_id=organization_id,
            item_id=str(getattr(item, "id", "")),
        ),
    )


async def notify_customer_decision(
    repos: Any, *, item: Any, approved: bool, batch: Any = None
) -> list[str]:
    """Event 4 — the client approved/rejected the processed item.

    Recipients: the engaged firm's members (they need the client's outcome).
    The client is the actor, so the client organisation is not notified of its
    own decision.
    """
    organization_id = await _organization_id_for_item(repos, item, batch)
    outcome = "approved" if approved else "rejected"
    event_key = lifecycle_event_key(
        EVENT_CUSTOMER_DECISION,
        identity=f"item:{getattr(item, 'id', '')}",
        discriminator=outcome,
    )
    recipients = await _firm_and_ops(repos, organization_id=organization_id)
    return await _emit(
        repos,
        event=EVENT_CUSTOMER_DECISION,
        event_key=event_key,
        recipients=recipients,
        title=f"Customer {outcome}",
        message=f"Your client {outcome} the item ({_item_label(item)}).",
        link_for=await _consultant_link_for(
            repos,
            organization_id=organization_id,
            item_id=str(getattr(item, "id", "")),
        ),
    )


async def notify_rework(
    repos: Any, *, item: Any, source: str, batch: Any = None
) -> list[str]:
    """Event 5 — work was routed back for rework.

    Recipients: the engaged firm's members — the party that must rework the
    item. ``source`` is one of the two stable rework sources
    (:data:`REWORK_SOURCE_CT_QC_REJECTED`,
    :data:`REWORK_SOURCE_CONSULTANT_REVIEW_REJECTED`) and forms part of the
    deterministic event key.
    """
    organization_id = await _organization_id_for_item(repos, item, batch)
    event_key = lifecycle_event_key(
        EVENT_REWORK, identity=f"item:{getattr(item, 'id', '')}", discriminator=source
    )
    recipients = await _firm_and_ops(repos, organization_id=organization_id)
    return await _emit(
        repos,
        event=EVENT_REWORK,
        event_key=event_key,
        recipients=recipients,
        title="Rework required",
        message=f"The item ({_item_label(item)}) was returned for rework.",
        link_for=await _consultant_link_for(
            repos,
            organization_id=organization_id,
            item_id=str(getattr(item, "id", "")),
        ),
        actor_domain=(
            "internal_staff"
            if source == REWORK_SOURCE_CT_QC_REJECTED
            else "consultant"
        ),
    )



