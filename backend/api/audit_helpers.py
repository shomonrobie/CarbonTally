"""Shared best-effort audit helpers for the V3 API surfaces.

WS4 Gate 6 (workstream W4 / gap G6-D): human extraction edits on a work item
must be attributable. Item-level human extraction saves historically only
stamped ``manual_extraction_items.extracted_by`` (overwriting the machine
zero-UUID marker when the extraction originated from automation) without an
audit-trail event. This helper records one append-only item event through the
existing audit repository so the human correction is distinguishable from the
machine extraction (action + actor) while staying correlated to the item and,
when known, the automatic-processing job.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from core.logging import get_logger
from domain.audit import AuditEntry

logger = get_logger(__name__)

#: The machine/system extractor marker the worker stamps on synced items
#: (``services.automatic_processing._SYSTEM_ACTOR``).
MACHINE_EXTRACTOR = "00000000-0000-0000-0000-000000000000"


def changed_extraction_keys(
    before: Optional[dict], after: Optional[dict]
) -> list[str]:
    """Return the top-level extraction keys whose value changed (best-effort).

    Deliberately compact: never stores the full payloads in the audit trail.
    """
    before = before or {}
    after = after or {}
    keys = sorted(set(before) | set(after))
    return [k for k in keys if before.get(k) != after.get(k)]


async def record_item_extraction_edit(
    repos: Any,
    *,
    item_id: str,
    action: str,
    actor: str,
    correlation_id: Optional[str],
    job_id: Optional[str],
    status_from: Optional[str],
    status_to: Optional[str],
    previous_extracted_by: Optional[str],
    changed_keys: Optional[list[str]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Best-effort append-only audit of one human extraction edit on an item.

    Actor is always the authenticated human from the request context (never a
    client-supplied field). The event distinguishes a human correction from the
    machine extraction via ``corrected_machine_output`` when the previous
    extractor was the machine zero-UUID marker. No payloads are stored.
    """
    machine_origin = bool(
        previous_extracted_by
        and str(previous_extracted_by) == MACHINE_EXTRACTOR
    )
    extra: dict[str, Any] = {
        "status_from": status_from,
        "status_to": status_to,
        "previous_extracted_by": previous_extracted_by,
        "corrected_machine_output": machine_origin,
    }
    if job_id:
        extra["job_id"] = job_id
    if changed_keys:
        extra["changed_keys"] = changed_keys
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=correlation_id or item_id,
        entity_type="manual_extraction_item",
        entity_id=item_id,
        action=action,
        actor=actor,
        occurred_at=datetime.now(timezone.utc),
        changed_fields=extra,
        ip_address=ip_address,
    )
    try:
        await repos.audit.record(entry)
    except Exception:  # noqa: BLE001 — audit must never break the human edit
        logger.exception(
            "item extraction-edit audit (%s) failed for item %s", action, item_id
        )
