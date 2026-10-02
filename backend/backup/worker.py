"""Backup worker — the lifespan-managed loop that drains ``public.backup_jobs``.

Shape (deliberately the same as the existing
:class:`workers.automatic_processing.AutomaticProcessingWorker`):

* lifespan-managed ``asyncio`` task, started/stopped by the FastAPI lifespan;
* job state in the database, so a restart resumes instead of losing work;
* ``FOR UPDATE SKIP LOCKED`` claiming with a bounded attempt budget and stale-lock
  recovery (both are properties of the claim statement in :mod:`backup.jobs`);
* **a failed tick never kills the loop** — it is logged and the loop continues, and
  a failed *job* is recorded on its own row by
  :func:`backup.jobs.run_claimed_job` / the object path below;
* **an undeployed BACKUP schema is terminal and backed off** (FINAL-02 §15.2,
  FINAL-03 gate P1): when PostgreSQL reports that a ``backup_*`` relation does not
  exist, the condition is reported **once** and the loop then re-checks at
  :data:`DEFAULT_MISSING_TABLE_BACKOFF_SECONDS` instead of raising a traceback every
  tick. The migrations are applied by an operator, minutes-to-hours away, so a
  per-tick error was pure noise — and, with the pre-fix lease, the growth it masked
  starved the shared pool. A succeeding tick resets the flag, so a later failure is
  reported again rather than silently swallowed.

What it runs
------------

* ``kind = 'database'`` → :class:`backup.service.BackupService` through
  :func:`backup.jobs.run_claimed_job` (deterministic ``backup_id`` per job, so a
  retry produces a *replacement* artifact rather than an ambiguous second one);
* ``kind = 'objects'`` → :func:`backup.objects.export_objects` (§14). The object
  job is separate and sequenced: **its failure is recorded on its own row and can
  never fail the database job**;
* a retention sweep every tick: expiry (metadata only) plus, only when explicitly
  enabled, pruning of already-expired artifacts (see :mod:`backup.retention`).

What it does not do
-------------------

No scheduling. §16 is explicit that automatic schedule-driven backups are the
deferred item; the worker drains what an authorised administrator queued.

The worker never logs, returns or persists an encryption key, a DSN or a storage
credential: it holds only the service objects it needs.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Optional

from core.logging import get_logger

from backup.errors import BackupObjectError  # noqa: F401 — re-exported for the API layer
from backup.jobs import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_STALE_LOCK_SECONDS,
    KIND_DATABASE,
    KIND_OBJECTS,
    STATUS_COMPLETED,
    STATUS_FAILED,
    BackupJob,
    BackupJobStore,
    run_claimed_job,
    sanitise_reason,
)
from backup.objects import DEFAULT_BUCKET, StorageObjectSource, export_objects
from backup.retention import expire_and_prune
from backup.service import BackupService
from backup.settings import BackupSettings
from backup.storage import ObjectStore, build_object_store

logger = get_logger(__name__)

#: PostgreSQL's SQLSTATE for "relation does not exist" (``UndefinedTableError``).
UNDEFINED_TABLE_SQLSTATE = "42P01"

#: How long the loop waits before re-checking while the BACKUP schema is absent.
#: Deliberately far longer than the poll interval: the tables can only appear when
#: an operator applies the migrations, so a fast retry adds nothing but load.
DEFAULT_MISSING_TABLE_BACKOFF_SECONDS = 300.0


def is_missing_backup_table(exc: BaseException) -> bool:
    """True when ``exc`` says a **backup** relation is not deployed yet.

    Matches on SQLSTATE rather than on exception class so the worker needs no
    ``asyncpg`` import (this package is imported by the API process, and the check
    must also work for a pool that wraps driver errors). Only ``backup_*`` relations
    qualify: any *other* missing table is a genuine schema fault and keeps its
    per-tick traceback.
    """
    if getattr(exc, "sqlstate", None) != UNDEFINED_TABLE_SQLSTATE:
        return False
    return "backup_" in str(exc).lower()


class BackupWorker:
    """Claims and runs backup jobs; drains the queue, records every outcome."""

    def __init__(
        self,
        *,
        poll_interval_seconds: float = 10.0,
        batch_size: int = 1,
        stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        retention_prune: bool = False,
        missing_table_backoff_seconds: float = DEFAULT_MISSING_TABLE_BACKOFF_SECONDS,
        object_bucket: str = DEFAULT_BUCKET,
        settings: Optional[BackupSettings] = None,
        job_store: Optional[BackupJobStore] = None,
        object_store: Optional[ObjectStore] = None,
        object_source: Optional[StorageObjectSource] = None,
        notify: Optional[Any] = None,
    ) -> None:
        self._poll_interval_seconds = poll_interval_seconds
        self._batch_size = max(1, int(batch_size))
        self._stale_lock_seconds = stale_lock_seconds
        self._max_attempts = max_attempts
        self._retention_prune = retention_prune
        #: Delay applied while the BACKUP schema is absent (P1 clause 2).
        self._missing_table_backoff_seconds = max(
            0.0, float(missing_table_backoff_seconds)
        )
        self._object_bucket = object_bucket
        self._settings = settings
        self._jobs = job_store or BackupJobStore()
        self._store = object_store
        self._object_source = object_source
        #: Optional outcome notifier: ``notify(recipient, event_key, title, message)``.
        #: Injected by the application (``main.py``) so this package keeps its
        #: documented boundary — it never imports ``data`` or ``api`` itself.
        self._notify = notify
        self._task: Optional[asyncio.Task] = None
        self._stopping = False
        #: True while the loop is backing off because the BACKUP schema is absent;
        #: cleared by the first tick that succeeds.
        self._tables_missing = False
        #: Stable per-process claim token, so this worker's own stale locks are
        #: recognisable (the same idiom the document worker uses).
        self._lock_token = f"backup-worker::{os.getpid()}::{uuid.uuid4().hex[:8]}"

    # -- lifecycle ----------------------------------------------------------

    async def start(self) -> None:
        """Begin the background loop (idempotent)."""
        if self._task is not None and not self._task.done():
            return
        self._stopping = False
        self._tables_missing = False
        self._task = asyncio.create_task(self._run_loop(), name="backup-worker")
        logger.info(
            "backup worker started (poll %.1fs, batch %d, worker %s)",
            self._poll_interval_seconds,
            self._batch_size,
            self._lock_token,
        )

    async def stop(self) -> None:
        """Cancel the loop and wait for it to unwind (safe to call twice)."""
        self._stopping = True
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        except Exception:  # noqa: BLE001 — shutdown only, never re-raised
            logger.exception("backup worker loop raised during shutdown")
        self._task = None
        logger.info("backup worker stopped")

    @property
    def is_running(self) -> bool:
        """True while the background loop is alive."""
        return self._task is not None and not self._task.done()

    def set_notifier(self, notify: Any) -> None:
        """Attach (or replace) the outcome notifier.

        Called by the composition root (``main.py``) *after* the singleton exists,
        so the application can supply a database-backed notifier without this
        package ever importing ``data`` or ``api``.
        """
        self._notify = notify

    async def _run_loop(self) -> None:
        while not self._stopping:
            delay = self._poll_interval_seconds
            try:
                await self.tick()
                # Getting past `release_stale` and `claim_next` proves the schema is
                # deployed, so re-arm the one-shot missing-table report.
                self._tables_missing = False
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — a failed tick must never kill the loop
                delay = self._backoff_for_failed_tick(exc)
            await asyncio.sleep(delay)

    def _backoff_for_failed_tick(self, exc: BaseException) -> float:
        """Report a failed tick, and return the delay before the next attempt.

        An absent BACKUP schema is terminal and backed off rather than a per-tick
        error (FINAL-02 §15.2, FINAL-03 gate P1): the condition repeats on *every*
        statement, the fix is an operator applying two migrations, and until then a
        traceback per tick is pure noise. It is therefore reported **once** and then
        sampled at :attr:`_missing_table_backoff_seconds`. Everything else keeps the
        long-standing behaviour: a full traceback per tick, on the poll interval.
        """
        if not is_missing_backup_table(exc):
            logger.exception("backup worker tick failed (loop continues)")
            return self._poll_interval_seconds
        if not self._tables_missing:
            self._tables_missing = True
            logger.error(
                "backup tables are absent (SQLSTATE %s): backing off %.0fs before "
                "re-checking; apply 20261026000000_ct_backup_01_backup_jobs.sql and "
                "20261027000000_ct_backup_02_backup_sets_and_verification.sql to enable "
                "backups (cause: %s)",
                UNDEFINED_TABLE_SQLSTATE,
                self._missing_table_backoff_seconds,
                exc,
            )
        return self._missing_table_backoff_seconds

    # -- one tick -----------------------------------------------------------

    async def tick(self) -> list[BackupJob]:
        """Reclaim stale locks, sweep retention, then run up to ``batch_size`` jobs."""
        await self._jobs.release_stale(stale_after_seconds=self._stale_lock_seconds)
        try:
            outcome = await expire_and_prune(
                self._jobs, self._store_or_none(), delete_artifacts=self._retention_prune
            )
            if outcome.expired or outcome.deleted:
                logger.info("backup retention sweep: %s", outcome.as_dict())
        except Exception as exc:  # noqa: BLE001 — retention must not stop the queue
            # A missing BACKUP schema is reported once by the loop, never once per
            # statement; any other sweep failure keeps its traceback.
            if not is_missing_backup_table(exc):
                logger.exception("backup retention sweep failed")

        processed: list[BackupJob] = []
        for _ in range(self._batch_size):
            job = await self._jobs.claim_next(
                lock_token=self._lock_token,
                max_attempts=self._max_attempts,
                stale_after_seconds=self._stale_lock_seconds,
            )
            if job is None:
                break
            processed.append(await self.run_job(job))
        return processed

    # -- one job ------------------------------------------------------------

    async def run_job(self, job: BackupJob) -> BackupJob:
        """Run one claimed job, record its outcome, then notify the requester."""
        result = await self._dispatch(job)
        await self._notify_outcome(result)
        return result

    async def _notify_outcome(self, job: BackupJob) -> None:
        """Best-effort, idempotent notification of a terminal job (§17).

        The event key is deterministic per (recipient, job, status), so a retried
        job can never produce a second notification. A notification failure is
        logged and swallowed: it must never change a job's recorded outcome — in
        particular, a successful backup is never *reported* as failed because a
        notification could not be delivered.
        """
        if self._notify is None or not job.requested_by:
            return
        if job.status not in (STATUS_COMPLETED, STATUS_FAILED):
            return
        ok = job.status == STATUS_COMPLETED
        title = "Backup completed" if ok else "Backup failed"
        message = (
            f"{job.kind} backup {job.id} completed"
            if ok
            else f"{job.kind} backup {job.id} failed: {job.error_reason}"
        )
        try:
            await self._notify(
                job.requested_by, f"backup:{job.id}:{job.status}", title, message
            )
        except Exception:  # noqa: BLE001 — never changes the recorded outcome
            logger.exception("backup outcome notification failed for %s", job.id)

    async def _dispatch(self, job: BackupJob) -> BackupJob:
        """Route one claimed job to the implementation for its kind."""
        if job.kind == KIND_OBJECTS:
            return await self._run_object_job(job)
        if job.kind != KIND_DATABASE:
            return await self._jobs.mark_failed(
                job.id, error_reason=f"unsupported backup job kind: {job.kind!r}"
            )
        try:
            settings = self._settings_or_default()
            settings.require_encryption_key()
            service = BackupService(
                settings,
                object_store=self._store_or_none(),
                connection_factory=None,
            )
            return await run_claimed_job(
                self._jobs,
                job,
                service,
                retention_days=self._retention_days(),
                storage_bucket=getattr(settings, "s3_bucket", None) or None,
            )
        except Exception as exc:  # noqa: BLE001 — the row must record the failure
            logger.exception("backup job %s could not run", job.id)
            return await self._jobs.mark_failed(job.id, error_reason=sanitise_reason(exc))

    async def _run_object_job(self, job: BackupJob) -> BackupJob:
        """Back up the private bucket's objects as a paired, separate job (§14)."""
        try:
            settings = self._settings_or_default()
            key = settings.require_encryption_key()
            store = self._store_or_default(settings)
            record = await export_objects(
                self._source_or_default(),
                store,
                key=key,
                backup_set_id=job.backup_set_id or job.id,
                key_id=settings.key_id,
                bucket=self._object_bucket,
                prefix=str((job.manifest or {}).get("object_prefix") or ""),
            )
            return await self._jobs.mark_completed_objects(
                job.id,
                object_key=record.object_key,
                size_bytes=record.size_bytes,
                ciphertext_sha256=record.ciphertext_sha256,
                key_version=record.key_id,
                object_count=record.object_count,
                object_bytes=record.total_bytes,
                manifest_extra={
                    "job_id": job.id,
                    "kind": KIND_OBJECTS,
                    "backup_set_id": record.backup_set_id,
                    "bucket": record.bucket,
                },
                retention_days=self._retention_days(),
            )
        except Exception as exc:  # noqa: BLE001 — recorded on this row only
            logger.exception("object backup job %s failed", job.id)
            return await self._jobs.mark_failed(job.id, error_reason=sanitise_reason(exc))

    # -- dependencies -------------------------------------------------------

    def _settings_or_default(self) -> BackupSettings:
        if self._settings is None:
            self._settings = BackupSettings.from_env()
        return self._settings

    def _store_or_none(self) -> Optional[ObjectStore]:
        """The configured destination, or ``None`` when it cannot be built.

        Retention *expiry* does not need storage, so an unbuildable destination must
        not stop the sweep — the pruning half simply has nothing to talk to.
        """
        if self._store is not None:
            return self._store
        try:
            self._store = build_object_store(self._settings_or_default())
        except Exception:  # noqa: BLE001 — expiry still works without a store
            logger.warning("backup destination is not configured; expiry only")
            return None
        return self._store

    def _store_or_default(self, settings: BackupSettings) -> ObjectStore:
        if self._store is None:
            self._store = build_object_store(settings)
        return self._store

    def _source_or_default(self) -> StorageObjectSource:
        if self._object_source is None:
            from backup.objects import SupabaseStorageSource

            self._object_source = SupabaseStorageSource()
        return self._object_source

    def _retention_days(self) -> Optional[int]:
        """Retention from the environment-declared policy, if any.

        The durable policy row is read by the API layer (it is a database read and
        the worker holds no repository dependency); ``CT_BACKUP_RETENTION_DAYS`` is
        the worker-side equivalent and defaults to "not configured" (no expiry).
        """
        raw = os.getenv("CT_BACKUP_RETENTION_DAYS", "").strip()
        if not raw:
            return None
        try:
            days = int(raw)
        except ValueError:
            logger.warning("CT_BACKUP_RETENTION_DAYS is not an integer; ignoring")
            return None
        return days if days > 0 else None


#: Process-wide worker singleton (started/stopped by the FastAPI lifespan).
_worker: Optional[BackupWorker] = None


def get_backup_worker(
    *,
    notify: Optional[Any] = None,
    retention_prune: Optional[bool] = None,
    **options: Any,
) -> BackupWorker:
    """Return the process-wide backup worker singleton.

    The application (``main.py``) passes the notifier and any operational options
    through here, so this package never imports ``data`` or ``api`` to obtain them.
    The first call constructs the worker; a later call during the same process may
    still attach/replace the notifier, which keeps a reloaded lifespan or a test
    from silently losing notifications.
    """
    global _worker
    if _worker is None:
        if notify is not None:
            options["notify"] = notify
        if retention_prune is not None:
            options["retention_prune"] = retention_prune
        _worker = BackupWorker(**options)
    elif notify is not None:
        _worker.set_notifier(notify)
    return _worker


def reset_backup_worker() -> None:
    """Drop the singleton (used by tests)."""
    global _worker
    _worker = None


__all__ = [
    "BackupWorker",
    "DEFAULT_MISSING_TABLE_BACKOFF_SECONDS",
    "get_backup_worker",
    "is_missing_backup_table",
    "reset_backup_worker",
]