"""Backup retention — expiry and the authorised removal of expired artifacts (§16).

Two deliberately separate steps, because the ratified state machine separates them:

* **expiry** (``completed → expired``) is *metadata only*: the artifact stays where
  it is and the row records that the retention window has passed. Nothing is
  destroyed and the action is reversible by policy.
* **pruning** (``expired → deleted``) actually removes the stored object. It is
  **off by default** in this module and is only performed when a caller explicitly
  asks for it, because §16 requires deletion to be an authorised action
  (``can_manage_backups`` + an audit entry), never a side effect of a timer.

Object-store failures during pruning are **recorded, not hidden**: a job whose
artifact could not be deleted is left in ``expired`` and reported in
``artifact_errors``, so a leak is visible instead of being marked deleted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.logging import get_logger

from backup.errors import BackupStorageError
from backup.jobs import BackupJobStore
from backup.storage import ObjectStore

logger = get_logger(__name__)


@dataclass
class RetentionOutcome:
    """What the sweep did (evidence, not a claim)."""

    expired: int = 0
    deleted: int = 0
    artifacts_deleted: int = 0
    artifact_errors: list[str] = field(default_factory=list)
    prune_requested: bool = False

    def as_dict(self) -> dict:
        return {
            "expired": self.expired,
            "deleted": self.deleted,
            "artifacts_deleted": self.artifacts_deleted,
            "artifact_errors": list(self.artifact_errors),
            "prune_requested": self.prune_requested,
        }


async def expire_and_prune(
    jobs: BackupJobStore,
    store: Optional[ObjectStore] = None,
    *,
    now: Optional[datetime] = None,
    delete_artifacts: bool = False,
    actor: str = "system:retention",
    limit: int = 200,
) -> RetentionOutcome:
    """Expire completed jobs past ``expires_at`` and, on request, prune artifacts.

    ``delete_artifacts=False`` (the default) is a pure expiry sweep — safe to run
    from a worker tick. ``True`` additionally removes the encrypted objects of the
    jobs that are already ``expired``; that is the authorised removal, so the
    caller is responsible for the capability check and the audit entry.
    """
    outcome = RetentionOutcome(prune_requested=delete_artifacts)
    outcome.expired = await jobs.mark_expired(now=now)
    if outcome.expired:
        logger.info("retention: %d backup job(s) expired", outcome.expired)

    if not delete_artifacts or store is None:
        return outcome

    for job in await jobs.list_expired(limit=limit):
        if job.storage_key:
            try:
                await store.delete_object(job.storage_key)
                outcome.artifacts_deleted += 1
            except BackupStorageError as exc:
                message = f"job {job.id}: {exc.message}"
                outcome.artifact_errors.append(message)
                logger.warning("retention: could not delete artifact for %s", job.id)
                continue
        try:
            await jobs.mark_deleted(job.id, deleted_by=actor, now=now)
            outcome.deleted += 1
        except Exception:  # noqa: BLE001 — a concurrent change is not a sweep failure
            logger.warning("retention: job %s could not be marked deleted", job.id)
    return outcome


__all__ = ["RetentionOutcome", "expire_and_prune"]