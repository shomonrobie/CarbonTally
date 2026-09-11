"""Phase 5 / WS1 (D38) - canonical V3 WorkItem assignment service.

Assignment / reassignment / attribution over the canonical work-item
representation (``manual_extraction_items``). The append-only
``work_item_assignments`` ledger holds current + historical attribution;
current assignment is changeable, while V1.2 immutable processing provenance
(``processing_origin`` / ``processing_entity_id``) is NEVER modified here.

Both access contracts (CarbonTally internal Operations via /api/v3/ops and
Processing Entity staff via /api/v3/pe) call THIS service so the same
authorization/attribution semantics apply regardless of workspace.

Security chain is enforced by the routers (authentication to actor/domain to
workspace to role/capability to resource scope) and re-checked here at the
resource level (item exists, batch not cancelled, entity ownership).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from domain.audit import AuditEntry

INTERNAL_STAFF = "internal_staff"
PROCESSING_ENTITY = "processing_entity"


class WorkItemError(Exception):
    """Domain error carrying the HTTP status to surface to the caller."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _deny(detail: str) -> WorkItemError:
    return WorkItemError(403, detail)


def _str(value) -> Optional[str]:
    return str(value) if value is not None else None


import logging  # noqa: E402

_log = logging.getLogger("carbon_tally.work_items")


async def _notify_assignee(repos, *, user_id, event_key, item_id, action, actor_domain):
    """Best-effort D40 notification for an internal assignment event.

    The assignment/audit are already committed; a notification failure must not
    fail the business action but is logged so it is detectable.
    """
    try:
        await repos.notifications.create_idempotent(
            user_id,
            event_key,
            notification_type="work_item.assigned",
            title="Work item assigned",
            message=f"Work item assigned to you ({action})",
            priority=30,
            link=f"/ops/items/{item_id}",
            actor_domain=actor_domain,
        )
    except Exception:  # pragma: no cover - best effort, logged
        _log.warning("notification producer failed for work_item %s", item_id)


async def _load_item_and_batch(repos, item_id: str):
    item = await repos.manual_extraction.get_item(item_id)
    if item is None:
        raise WorkItemError(404, "work item not found")
    batch = await repos.manual_extraction.get_batch(item.batch_id)
    if batch is None or batch.status == "cancelled":
        raise WorkItemError(409, "work item batch is unavailable")
    return item, batch


async def _origin(repos, item_id: str) -> dict:
    origin = await repos.manual_extraction.get_item_origin(item_id)
    return {
        "processing_origin": (origin or {}).get("processing_origin"),
        "processing_entity_id": (origin or {}).get("processing_entity_id"),
    }


async def _audit(repos, *, item_id, action, actor, changed_fields, correlation_id=None):
    await repos.audit.record(
        AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=correlation_id or item_id,
            entity_type="manual_extraction_item",
            entity_id=item_id,
            action=action,
            actor=actor,
            occurred_at=datetime.now(timezone.utc),
            changed_fields=changed_fields,
            ip_address=None,
        )
    )


async def work_item_read(repos, item_id: str) -> dict:
    """Read-only current assignment + full history for a work item."""
    item, batch = await _load_item_and_batch(repos, item_id)
    current = await repos.manual_extraction.work_item_current(item_id)
    history = await repos.manual_extraction.work_item_history(item_id)
    origin = await _origin(repos, item_id)
    effective = await work_item_effective(repos, item_id)
    return {
        "item_id": item.id,
        "batch_id": item.batch_id,
        "batch_entity_id": _str(batch.entity_id),
        "item_status": item.status,
        "current": current,
        "history": history,
        "effective": effective,
        **origin,
    }


# ---------------------------------------------------------------------------
# CarbonTally internal Operations domain
# ---------------------------------------------------------------------------


async def work_item_effective(repos, item_id: str) -> dict:
    """Effective processing assignment (service mirror of the RLS helper).

    Returns ``{kind, assignee, source}``: kind is processing_entity |
    internal_staff | unassigned; assignee is the entity id / internal user id;
    source is 'item' (open D38 ledger row) | 'batch' (batch default) | None.
    An open item assignment takes precedence; an open internal_staff
    assignment overrides a PE batch default (kind internal).
    """
    item, batch = await _load_item_and_batch(repos, item_id)
    current = await repos.manual_extraction.work_item_current(item_id)
    if current is not None:
        if current.get("assignee_kind") == PROCESSING_ENTITY:
            return {"kind": PROCESSING_ENTITY,
                    "assignee": _str(current.get("processing_entity_id")),
                    "source": "item"}
        return {"kind": INTERNAL_STAFF,
                "assignee": _str(current.get("assigned_to")),
                "source": "item"}
    if batch.entity_id is not None:
        return {"kind": PROCESSING_ENTITY, "assignee": _str(batch.entity_id),
                "source": "batch"}
    if batch.assigned_to is not None:
        return {"kind": INTERNAL_STAFF, "assignee": _str(batch.assigned_to),
                "source": "batch"}
    return {"kind": "unassigned", "assignee": None, "source": None}


async def ops_assign_item(
    repos, *, item_id, actor_user_id,
    target_user_id=None, target_entity_id=None,
    actor_domain=INTERNAL_STAFF, reason=None,
    action="assign", close_action="superseded",
) -> dict:
    """CarbonTally Operations: (re)assign an item to internal staff OR to a
    processing entity (item-level D38). Exactly one target is required. An open
    item assignment always overrides the batch default, so a PE batch default
    never blocks a CarbonTally item-level assignment/reassignment. Atomic
    close+open via ``work_item_open`` preserves single-open and ``previous_*``;
    ``processing_origin`` is never written."""
    if (target_user_id is None) == (target_entity_id is None):
        raise WorkItemError(
            422, "exactly one of target_user_id / target_entity_id is required")
    item, batch = await _load_item_and_batch(repos, item_id)
    current = await repos.manual_extraction.work_item_current(item_id)

    if target_user_id is not None:
        if not await repos.manual_extraction.is_active_internal_staff(target_user_id):
            raise WorkItemError(
                422, "assignee must be an active CarbonTally internal staff member")
        assignee_kind, assigned_to, pe_id = INTERNAL_STAFF, target_user_id, None
        current_target = _str((current or {}).get("assigned_to"))
    else:
        entity = await repos.entities.get(target_entity_id)
        if entity is None:
            raise WorkItemError(422, "target processing entity not found")
        if getattr(entity, "status", None) != "active":
            raise WorkItemError(422, "target processing entity is not active")
        assignee_kind, assigned_to, pe_id = PROCESSING_ENTITY, None, target_entity_id
        current_target = _str((current or {}).get("processing_entity_id"))

    if current is not None and current.get("assignee_kind") == assignee_kind \
            and current_target == (target_user_id or target_entity_id):
        return {"item_id": item_id, "current": current, "changed": False}

    new_row = await repos.manual_extraction.work_item_open(
        item_id=item_id, action=action, assignee_kind=assignee_kind,
        assigned_to=assigned_to, processing_entity_id=pe_id,
        actor=actor_user_id, actor_domain=actor_domain,
        reason=reason, close_action=close_action,
    )
    origin = await _origin(repos, item_id)
    await _audit(
        repos, item_id=item_id, action=f"work_item:{action}",
        actor=actor_user_id,
        changed_fields={
            "assignee_kind": assignee_kind,
            "assigned_to": _str(assigned_to),
            "processing_entity_id": _str(pe_id),
            "previous_assigned_to": _str((current or {}).get("assigned_to")),
            "previous_processing_entity_id": _str(
                (current or {}).get("processing_entity_id")),
            "actor_domain": actor_domain, "reason": reason, **origin,
        },
    )
    if assigned_to is not None and assigned_to != actor_user_id:
        await _notify_assignee(
            repos, user_id=assigned_to,
            event_key=f"work_item:{action}:{item_id}:{new_row['id']}",
            item_id=item_id, action=action, actor_domain=actor_domain,
        )
    return {"item_id": item_id, "current": new_row, "changed": True}


async def ops_claim_item(repos, *, item_id, actor_user_id, reason=None) -> dict:
    return await ops_assign_item(
        repos, item_id=item_id, target_user_id=actor_user_id,
        actor_user_id=actor_user_id, reason=reason,
        action="claim", close_action="reassigned",
    )


async def ops_reassign_item(
    repos, *, item_id, actor_user_id,
    target_user_id=None, target_entity_id=None, reason=None,
) -> dict:
    """CarbonTally item reassignment (internal staff OR processing entity)."""
    return await ops_assign_item(
        repos, item_id=item_id, target_user_id=target_user_id,
        target_entity_id=target_entity_id,
        actor_user_id=actor_user_id, reason=reason,
        action="reassign", close_action="reassigned",
    )


async def ops_recover_item(
    repos, *, item_id, actor_user_id,
    target_user_id=None, target_entity_id=None, reason=None,
) -> dict:
    """CarbonTally partial-work recovery (internal staff OR processing entity)."""
    return await ops_assign_item(
        repos, item_id=item_id, target_user_id=target_user_id,
        target_entity_id=target_entity_id,
        actor_user_id=actor_user_id, reason=reason,
        action="recover", close_action="recovered",
    )



async def _ops_close(repos, *, item_id, actor_user_id, close_action,
                     action_label, reason=None) -> dict:
    item, batch = await _load_item_and_batch(repos, item_id)
    effective = await work_item_effective(repos, item_id)
    if effective["kind"] == PROCESSING_ENTITY:
        raise _deny(
            "Item is assigned to a Processing Entity; use the PE surface or a "
            "CarbonTally item reassignment"
        )
    current = await repos.manual_extraction.work_item_current(item_id)
    if current is None:
        raise WorkItemError(409, f"no open assignment to {action_label}")
    closed = await repos.manual_extraction.work_item_close(
        item_id=item_id, close_action=close_action, actor=actor_user_id, reason=reason
    )
    origin = await _origin(repos, item_id)
    await _audit(
        repos,
        item_id=item_id,
        action=f"work_item:{action_label}",
        actor=actor_user_id,
        changed_fields={
            "closed_assignment_id": current.get("id"),
            "assigned_to": current.get("assigned_to"),
            "close_action": close_action,
            "actor_domain": INTERNAL_STAFF,
            "reason": reason,
            **origin,
        },
    )
    return {"item_id": item_id, "closed": closed, "changed": closed is not None}


async def ops_release_item(repos, *, item_id, actor_user_id, reason=None) -> dict:
    return await _ops_close(repos, item_id=item_id, actor_user_id=actor_user_id,
                            close_action="released", action_label="release",
                            reason=reason)


async def ops_complete_item(repos, *, item_id, actor_user_id, reason=None) -> dict:
    item, batch = await _load_item_and_batch(repos, item_id)
    effective = await work_item_effective(repos, item_id)
    if effective["kind"] == PROCESSING_ENTITY:
        raise _deny(
            "Item is assigned to a Processing Entity; use the PE surface or a "
            "CarbonTally item reassignment"
        )
    current = await repos.manual_extraction.work_item_current(item_id)
    if current is None:
        history = await repos.manual_extraction.work_item_history(item_id, limit=1)
        if history and history[0].get("close_action") == "completed":
            return {"item_id": item_id, "closed": history[0], "changed": False}
        raise WorkItemError(409, "no open assignment to complete")
    closed = await repos.manual_extraction.work_item_close(
        item_id=item_id, close_action="completed", actor=actor_user_id, reason=reason
    )
    origin = await _origin(repos, item_id)
    await _audit(
        repos,
        item_id=item_id,
        action="work_item:complete",
        actor=actor_user_id,
        changed_fields={
            "closed_assignment_id": current.get("id"),
            "assigned_to": current.get("assigned_to"),
            "close_action": "completed",
            "actor_domain": INTERNAL_STAFF,
            "reason": reason,
            **origin,
        },
    )
    return {"item_id": item_id, "closed": closed, "changed": closed is not None}


# ---------------------------------------------------------------------------
# Processing Entity domain (own entity only)
# ---------------------------------------------------------------------------


async def _pe_entity_item(repos, *, item_id, entity_id):
    """Require the item's EFFECTIVE processing entity to be ``entity_id``.

    WS4 Gate 3 / Option B: item-level open D38 assignment takes precedence over
    the batch default, so a PE is authorised only when
    ``effective_entity(item) == entity_id``. An open internal_staff assignment
    (or unassigned) is never PE-visible even when the batch default matches.
    """
    item, batch = await _load_item_and_batch(repos, item_id)
    effective = await work_item_effective(repos, item_id)
    if effective["kind"] != PROCESSING_ENTITY \
            or effective["assignee"] != entity_id:
        raise _deny("Work item is not effectively assigned to this processing entity")
    return item, batch


async def pe_claim_item(repos, *, item_id, entity_id, actor_user_id,
                        actor_domain=PROCESSING_ENTITY, reason=None) -> dict:
    item, batch = await _pe_entity_item(repos, item_id=item_id, entity_id=entity_id)
    current = await repos.manual_extraction.work_item_current(item_id)
    if current is not None:
        if (current.get("assignee_kind") == PROCESSING_ENTITY
                and current.get("processing_entity_id") == entity_id):
            return {"item_id": item_id, "current": current, "changed": False}
        raise WorkItemError(409, "work item already has an open assignment")
    new_row = await repos.manual_extraction.work_item_open(
        item_id=item_id,
        action="claim",
        assignee_kind=PROCESSING_ENTITY,
        assigned_to=None,
        processing_entity_id=entity_id,
        actor=actor_user_id,
        actor_domain=actor_domain,
        reason=reason,
        close_action="superseded",
    )
    origin = await _origin(repos, item_id)
    await _audit(
        repos,
        item_id=item_id,
        action="work_item:claim",
        actor=actor_user_id,
        changed_fields={
            "assignee_kind": PROCESSING_ENTITY,
            "processing_entity_id": entity_id,
            "actor_domain": actor_domain,
            "reason": reason,
            **origin,
        },
    )
    return {"item_id": item_id, "current": new_row, "changed": True}


async def pe_release_item(repos, *, item_id, entity_id, actor_user_id,
                          actor_domain=PROCESSING_ENTITY, reason=None) -> dict:
    item, batch = await _pe_entity_item(repos, item_id=item_id, entity_id=entity_id)
    current = await repos.manual_extraction.work_item_current(item_id)
    if current is None:
        raise WorkItemError(409, "no open assignment to release")
    if (current.get("assignee_kind") == PROCESSING_ENTITY
            and current.get("processing_entity_id") != entity_id):
        raise _deny("Open assignment belongs to another processing entity")
    closed = await repos.manual_extraction.work_item_close(
        item_id=item_id, close_action="released", actor=actor_user_id, reason=reason
    )
    origin = await _origin(repos, item_id)
    await _audit(
        repos,
        item_id=item_id,
        action="work_item:release",
        actor=actor_user_id,
        changed_fields={
            "closed_assignment_id": current.get("id"),
            "processing_entity_id": entity_id,
            "close_action": "released",
            "actor_domain": actor_domain,
            "reason": reason,
            **origin,
        },
    )
    return {"item_id": item_id, "closed": closed, "changed": closed is not None}


async def pe_complete_item(repos, *, item_id, entity_id, actor_user_id,
                           actor_domain=PROCESSING_ENTITY, reason=None) -> dict:
    item, batch = await _pe_entity_item(repos, item_id=item_id, entity_id=entity_id)
    current = await repos.manual_extraction.work_item_current(item_id)
    if current is None:
        history = await repos.manual_extraction.work_item_history(item_id, limit=1)
        if history and history[0].get("close_action") == "completed":
            return {"item_id": item_id, "closed": history[0], "changed": False}
        raise WorkItemError(409, "no open assignment to complete")
    if (current.get("assignee_kind") == PROCESSING_ENTITY
            and current.get("processing_entity_id") != entity_id):
        raise _deny("Open assignment belongs to another processing entity")
    closed = await repos.manual_extraction.work_item_close(
        item_id=item_id, close_action="completed", actor=actor_user_id, reason=reason
    )
    origin = await _origin(repos, item_id)
    await _audit(
        repos,
        item_id=item_id,
        action="work_item:complete",
        actor=actor_user_id,
        changed_fields={
            "closed_assignment_id": current.get("id"),
            "processing_entity_id": entity_id,
            "close_action": "completed",
            "actor_domain": actor_domain,
            "reason": reason,
            **origin,
        },
    )
    return {"item_id": item_id, "closed": closed, "changed": closed is not None}
