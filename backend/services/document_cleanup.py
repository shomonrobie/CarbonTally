"""Storage Management Step 2F/2E/2G — abandoned-upload reaping and quarantine disposition.

Scope, and the ratified rules it is bound by:

* **Retention is configurable and only configured durations are enforced**
  (``services.retention``).  This module therefore never invents a retention
  period: it reaps rows using an *existing* lifecycle constant —
  ``UPLOAD_COMPLETION_WINDOW_SECONDS`` (24 h) — which is the window after which
  Step 1 already refuses to complete an upload.  Reaping is the bookkeeping half
  of a rule that already exists.
* **Rows are never hard-deleted** by retention (soft conventions only).  The reap
  therefore moves an abandoned ``pending_upload`` row to the terminal
  ``upload_expired`` state; it does not delete the document row.
* **No object bytes are deleted, moved or re-homed.**  An abandoned upload may
  have left an orphan object; physical disposition of orphans and of
  security-rejected (quarantined) objects needs a ratified destruction rule that
  the repository does not contain (see :func:`physical_disposition_policy`), so
  this module performs no destructive storage action at all.
* **Cleanup is idempotent and auditable**: the transition is only applied to rows
  still in ``pending_upload``, a re-run reaps nothing further, and each reaped
  row appends a ``document.upload_authorisation_expired`` audit entry plus one
  ``document.cleanup`` entry for the pass.

The client organisation remains the owner throughout.  Nothing here creates a
consultant namespace, and provenance on the row is untouched.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from api.upload_gate import ACTION_CLEANUP, ACTION_UPLOAD_EXPIRED, record_document_event
from services.document_security import (
    STATUS_PENDING_UPLOAD,
    STATUS_UPLOAD_EXPIRED,
    can_transition,
)
from services.storage import UPLOAD_COMPLETION_WINDOW_SECONDS

#: Hard bound on how many rows one reap pass will transition (a scheduled job
#: must not attempt an unbounded table sweep in a single statement).
DEFAULT_REAP_BATCH = 500


def physical_disposition_policy() -> dict:
    """The unresolved physical-disposition requirement, stated explicitly.

    Storage Management Step 2E asked for rejected/quarantined objects to be
    dealt with *only* if a ratified retention/destruction rule exists.  The
    repository contains no such rule for (a) security-rejected objects or
    (b) orphaned objects with no valid document record, so Step 2 implements the
    safe lifecycle state only and reports the gap instead of inventing a policy.

    This function is the machine-readable statement of that gap: it is asserted
    by the Step 2 tests so a later change cannot quietly turn an unratified
    destructive rule into "implemented" behaviour.
    """
    return {
        "rejected_objects": {
            "lifecycle_state": "rejected (quarantined: not processable, not downloadable)",
            "physical_deletion": "not_authorized",
            "owner": "the client organisation (consultant provenance is metadata only)",
            "reason": (
                "no Product-Owner-ratified retention/destruction rule exists for "
                "rejected customer objects; Step 2 does not invent one and does "
                "not delete, move or re-home customer evidence"
            ),
        },
        "orphaned_objects": {
            "lifecycle_state": "no document record",
            "physical_deletion": "not_authorized",
            "reason": (
                "orphan-object cleanup has no ratified semantics; a bounded "
                "object inventory is recorded by the storage baseline instead"
            ),
        },
        "expired_pending_uploads": {
            "lifecycle_state": "upload_expired (terminal, retained, not downloadable)",
            "physical_deletion": "not_authorized",
            "reason": (
                "the row is retained for audit/provenance; only the state change "
                "is authorized"
            ),
        },
        "retention_duration_source": (
            "system_settings.document_retention_days via services.retention "
            "(configured-only enforcement); this module adds no duration"
        ),
    }


def reap_cutoff(
    *, now: Optional[datetime] = None, window_seconds: Optional[int] = None
) -> datetime:
    """The instant before which a ``pending_upload`` row is abandoned."""
    moment = now or datetime.now(timezone.utc)
    window = (
        UPLOAD_COMPLETION_WINDOW_SECONDS
        if window_seconds is None
        else int(window_seconds)
    )
    return moment - timedelta(seconds=window)


async def reap_abandoned_uploads(
    repos: Any,
    *,
    now: Optional[datetime] = None,
    dry_run: bool = True,
    limit: int = DEFAULT_REAP_BATCH,
    window_seconds: Optional[int] = None,
) -> dict[str, Any]:
    """Transition abandoned ``pending_upload`` rows to ``upload_expired``.

    ``dry_run=True`` (the default) reports what would change and writes nothing —
    the same convention as ``services.retention.enforce_retention``.  No object
    is read, written, signed or deleted by this function.

    The result is JSON-safe and includes ``eligible``/``changed`` counts, the ids
    it acted on, and an explicit ``objects_deleted: 0`` so an operator (and a
    verifier) can see that nothing destructive happened.
    """
    cutoff = reap_cutoff(now=now, window_seconds=window_seconds)
    report: dict[str, Any] = {
        "dry_run": dry_run,
        "cutoff": cutoff.isoformat(),
        "window_seconds": (
            UPLOAD_COMPLETION_WINDOW_SECONDS
            if window_seconds is None
            else int(window_seconds)
        ),
        "from_status": STATUS_PENDING_UPLOAD,
        "to_status": STATUS_UPLOAD_EXPIRED,
        "eligible": 0,
        "changed": 0,
        "skipped": 0,
        "document_ids": [],
        "objects_deleted": 0,
        "supported": True,
    }

    files = getattr(repos, "files", None)
    lister = getattr(files, "list_abandoned_pending_uploads", None)
    if not callable(lister):
        report.update(
            supported=False,
            reason=(
                "the document repository does not expose "
                "list_abandoned_pending_uploads; no cleanup was attempted"
            ),
        )
        return report

    candidates = list(await lister(cutoff, limit=limit) or [])
    report["eligible"] = len(candidates)

    for candidate in candidates:
        document_id = str(
            candidate.get("id")
            if isinstance(candidate, dict)
            else getattr(candidate, "id", "")
            or ""
        )
        status = (
            candidate.get("status")
            if isinstance(candidate, dict)
            else getattr(candidate, "status", None)
        )
        organization_id = str(
            candidate.get("organization_id")
            if isinstance(candidate, dict)
            else getattr(candidate, "organization_id", "")
            or ""
        )
        # Idempotency: only a row that is STILL pending is reaped.  A second pass
        # therefore changes nothing, and a row that advanced meanwhile is left
        # alone.
        if not document_id or status != STATUS_PENDING_UPLOAD or not can_transition(
            status, STATUS_UPLOAD_EXPIRED
        ):
            report["skipped"] += 1
            continue
        if dry_run:
            report["document_ids"].append(document_id)
            continue
        updater = getattr(files, "update_status", None)
        if not callable(updater):  # pragma: no cover - repository contract
            report["skipped"] += 1
            continue
        await updater(document_id, STATUS_UPLOAD_EXPIRED)
        report["changed"] += 1
        report["document_ids"].append(document_id)
        await record_document_event(
            repos=repos,
            action=ACTION_UPLOAD_EXPIRED,
            actor=None,
            actor_id="system",
            actor_type="system",
            organization_id=organization_id,
            entity_id=document_id,
            changed_fields={
                "from_status": STATUS_PENDING_UPLOAD,
                "to_status": STATUS_UPLOAD_EXPIRED,
                "cutoff": report["cutoff"],
                "objects_deleted": 0,
            },
            reason=(
                "the upload authorisation expired without a completed upload; "
                "the row is retained but can no longer be completed, downloaded "
                "or processed"
            ),
        )

    if not dry_run:
        await record_document_event(
            repos=repos,
            action=ACTION_CLEANUP,
            actor=None,
            actor_id="system",
            actor_type="system",
            organization_id="",
            entity_id="abandoned_uploads",
            changed_fields={
                "eligible": report["eligible"],
                "changed": report["changed"],
                "skipped": report["skipped"],
                "objects_deleted": 0,
                "cutoff": report["cutoff"],
            },
            reason="abandoned direct-upload reaping pass (idempotent, non-destructive)",
            outcome="success",
        )
    return report
