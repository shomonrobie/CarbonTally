"""Durable backup-job model (BACKUP-01 architecture §10/§11).

The ratified architecture
(``docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md``
§9–§11) requires that a backup *request* create only a durable ``queued`` row and
that **no export work happen in the request path**. This module is that queued
job model, and nothing else:

* :class:`BackupJobStore` — the ``public.backup_jobs`` access layer: create with
  the ratified single-flight guard, claim with ``FOR UPDATE SKIP LOCKED``,
  bounded state transitions, retention/expiry and listing;
* :func:`run_claimed_job` — the worker side: hand one claimed job to the existing
  :class:`backup.service.BackupService` and record the *sanitised* outcome.

Deliberate boundaries (mirroring :mod:`backup.service`):

* **no database work in the request path** — creation is a single INSERT;
* **no provider SDK, no new dependency** — plain ``asyncpg`` over an injectable
  connection factory, so the unit suite needs no live database;
* the package stays self-contained — this module imports neither ``api`` nor
  ``data``. Audit and notification fan-out (§9) live in the API layer, which is
  what keeps the ``backup`` package reusable by a standalone worker.

Ciphertext-only still holds: the store records metadata (key id, byte count,
checksum) and never sees, persists or logs plaintext, the archive contents, or
the encryption key.
"""
from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Optional

from core.logging import get_logger

from backup.artifact import isoformat_utc, utc_now
from backup.errors import (
    BackupJobConflictError,
    BackupJobError,
    BackupJobNotFoundError,
)
from backup.service import BackupRecord, BackupService

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Status machine (§10/§11) — must stay in step with the migration CHECK.
# ---------------------------------------------------------------------------
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_EXPIRED = "expired"
STATUS_DELETED = "deleted"

#: States that occupy the single-flight slot (§11). At most one row with a
#: status in this tuple may exist (partial unique index in the migration).
ACTIVE_STATUSES: tuple[str, ...] = (STATUS_QUEUED, STATUS_RUNNING)

ALL_STATUSES: tuple[str, ...] = (
    STATUS_QUEUED,
    STATUS_RUNNING,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_EXPIRED,
    STATUS_DELETED,
)

# ---------------------------------------------------------------------------
# Scope vocabulary — fixed, never free-form (§10).
# ---------------------------------------------------------------------------
#: The only ratified scope: the application's public schema plus its roles.
SCOPE_FULL = "public+schema+roles"
ALLOWED_SCOPES: tuple[str, ...] = (SCOPE_FULL,)
#: Readable alias used by the API layer and tests.
SCOPE_DATABASE = SCOPE_FULL

#: Bounded retry budget for a failed job (§11: ``failed → queued`` is bounded).
DEFAULT_MAX_ATTEMPTS = 3
#: A ``running`` job whose lock is older than this is reclaimable (§11).
DEFAULT_STALE_LOCK_SECONDS = 3600
#: ``error_reason`` is sanitised and truncated before it is persisted.
MAX_ERROR_REASON_LENGTH = 200

# ---------------------------------------------------------------------------
# Job kinds (§14) — the database artifact and the object artifact are separate
# jobs, paired by a common ``backup_set_id``. Each kind has its OWN single-flight
# slot, so an object job can never block a database job (or vice versa).
# ---------------------------------------------------------------------------
KIND_DATABASE = "database"
KIND_OBJECTS = "objects"
ALLOWED_KINDS: tuple[str, ...] = (KIND_DATABASE, KIND_OBJECTS)

# ---------------------------------------------------------------------------
# Verification state (§12) — set by the *Verify Backup* action, never by a claim.
# ---------------------------------------------------------------------------
VERIFICATION_UNVERIFIED = "unverified"
VERIFICATION_VERIFIED = "verified"
VERIFICATION_FAILED = "failed"
ALL_VERIFICATION_STATUSES: tuple[str, ...] = (
    VERIFICATION_UNVERIFIED,
    VERIFICATION_VERIFIED,
    VERIFICATION_FAILED,
)

#: Column projection used by every statement (kept in one place so the row
#: mapper and the SQL can never drift).
_COLUMNS = (
    "id, status, scope, requested_by, requested_at, started_at, finished_at, "
    "attempt_count, lock_token, locked_at, storage_key, storage_bucket, "
    "artifact_bytes, checksum_sha256, key_version, manifest, release_commit, "
    "error_reason, expires_at, deleted_at, deleted_by, idempotency_key, "
    "kind, backup_set_id, object_count, object_bytes, verification_status, "
    "verification_checked_at, verification_error"
)


@dataclass(frozen=True)
class BackupJob:
    """One durable backup-queue row. **Contains no plaintext and no key.**"""

    id: str
    status: str
    scope: str
    requested_by: Optional[str] = None
    requested_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    attempt_count: int = 0
    lock_token: Optional[str] = None
    locked_at: Optional[datetime] = None
    storage_key: Optional[str] = None
    storage_bucket: Optional[str] = None
    artifact_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    key_version: Optional[str] = None
    manifest: Optional[dict[str, Any]] = None
    release_commit: Optional[str] = None
    error_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    idempotency_key: Optional[str] = None
    # §14 — the artifact kind and the pairing id shared by the database job and
    # its object job, so a restore can select a consistent pair.
    kind: str = KIND_DATABASE
    backup_set_id: Optional[str] = None
    object_count: Optional[int] = None
    object_bytes: Optional[int] = None
    # §12 — verification state (set by the Verify Backup action).
    verification_status: str = VERIFICATION_UNVERIFIED
    verification_checked_at: Optional[datetime] = None
    verification_error: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """True while this job occupies the single-flight slot (§11)."""
        return self.status in ACTIVE_STATUSES

    @property
    def is_terminal(self) -> bool:
        return self.status in (STATUS_COMPLETED, STATUS_EXPIRED, STATUS_DELETED)

    def as_dict(self) -> dict[str, Any]:
        """JSON-safe projection (datetimes as ISO-8601 UTC strings)."""
        return {
            "id": self.id,
            "status": self.status,
            "scope": self.scope,
            "requested_by": self.requested_by,
            "requested_at": _as_iso(self.requested_at),
            "started_at": _as_iso(self.started_at),
            "finished_at": _as_iso(self.finished_at),
            "attempt_count": self.attempt_count,
            "storage_key": self.storage_key,
            "storage_bucket": self.storage_bucket,
            "artifact_bytes": self.artifact_bytes,
            "checksum_sha256": self.checksum_sha256,
            "key_version": self.key_version,
            "manifest": self.manifest,
            "release_commit": self.release_commit,
            "error_reason": self.error_reason,
            "expires_at": _as_iso(self.expires_at),
            "deleted_at": _as_iso(self.deleted_at),
            "deleted_by": self.deleted_by,
            "idempotency_key": self.idempotency_key,
            "kind": self.kind,
            "backup_set_id": self.backup_set_id,
            "object_count": self.object_count,
            "object_bytes": self.object_bytes,
            "verification_status": self.verification_status,
            "verification_checked_at": _as_iso(self.verification_checked_at),
            "verification_error": self.verification_error,
        }


def _as_iso(value: Optional[datetime]) -> Optional[str]:
    return isoformat_utc(value) if isinstance(value, datetime) else None


def _as_str(value: Any) -> Optional[str]:
    """uuid/UUID columns arrive as ``uuid.UUID`` under asyncpg — normalise."""
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def _as_manifest(value: Any) -> Optional[dict[str, Any]]:
    """``jsonb`` comes back as ``str`` from asyncpg unless a codec is set."""
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except ValueError:
            return None
        return decoded if isinstance(decoded, dict) else None
    return value if isinstance(value, dict) else None


def _row_to_job(record: Any) -> BackupJob:
    """Map one ``asyncpg`` record onto :class:`BackupJob`."""
    return BackupJob(
        id=_as_str(record["id"]) or "",
        status=str(record["status"]),
        scope=str(record["scope"]),
        requested_by=_as_str(record["requested_by"]),
        requested_at=record["requested_at"],
        started_at=record["started_at"],
        finished_at=record["finished_at"],
        attempt_count=int(record["attempt_count"] or 0),
        lock_token=record["lock_token"],
        locked_at=record["locked_at"],
        storage_key=record["storage_key"],
        storage_bucket=record["storage_bucket"],
        artifact_bytes=record["artifact_bytes"],
        checksum_sha256=record["checksum_sha256"],
        key_version=record["key_version"],
        manifest=_as_manifest(record["manifest"]),
        release_commit=record["release_commit"],
        error_reason=record["error_reason"],
        expires_at=record["expires_at"],
        deleted_at=record["deleted_at"],
        deleted_by=_as_str(record["deleted_by"]),
        idempotency_key=record["idempotency_key"],
        kind=str(record["kind"] or KIND_DATABASE),
        backup_set_id=_as_str(record["backup_set_id"]),
        object_count=record["object_count"],
        object_bytes=record["object_bytes"],
        verification_status=str(
            record["verification_status"] or VERIFICATION_UNVERIFIED
        ),
        verification_checked_at=record["verification_checked_at"],
        verification_error=record["verification_error"],
    )


def sanitise_reason(exc: BaseException) -> str:
    """Reduce an exception to a bounded, secret-free ``error_reason``.

    The class name is always kept (so operators can triage); the message is
    whitespace-collapsed and truncated to :data:`MAX_ERROR_REASON_LENGTH`.
    Backup-layer messages are already written to be free of credentials and
    payloads, so this only bounds the size — nothing key-shaped can land in the
    queue row.
    """
    raw = " ".join(str(exc).split())
    text = f"{type(exc).__name__}: {raw}" if raw else type(exc).__name__
    return text[:MAX_ERROR_REASON_LENGTH]


async def _pool_connection_factory() -> Any:
    """Default factory: the shared service-role pool's **acquire context**.

    The factory returns ``pool.acquire()`` — asyncpg's documented "use this
    connection, then return it to the pool" context — and *not* an already
    acquired connection. Returning the context is what lets
    :meth:`BackupJobStore._connection` hand the connection back on every exit path
    (success, exception and cancellation); returning an acquired connection leaves
    no release path at all, which is exactly how the backup worker starved the
    five-slot service pool one tick at a time (FINAL-02 §15.2, B7).

    Mirrors ``backup.service._pool_connection_factory`` — a caller that injects its
    own factory (tests, the standalone worker and the recovery drill) keeps full
    control of the connection's lifecycle.
    """
    from infra.supabase import get_service_pool  # lazy: no import-time DB config

    pool = await get_service_pool()
    return pool.acquire()


class BackupJobStore:
    """``public.backup_jobs`` access layer (BACKUP-01 §10/§11).

    Every method is a single statement against an injected connection, so the
    store is trivially unit-testable and holds no state of its own.
    """

    def __init__(self, *, connection_factory: Optional[Any] = None) -> None:
        """
        Args:
            connection_factory: async callable returning either an ``asyncpg``
                connection (the injector then owns its lifecycle, as before) or an
                ``asyncpg`` acquire context — a connection that is returned to its
                pool when the ``async with`` block exits. Defaults to the shared
                service-role pool's acquire context.
        """
        self._connection_factory = connection_factory or _pool_connection_factory

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[Any]:
        """Lease one connection for the statements inside the ``async with`` block.

        Two factory shapes are supported, and neither leaves a connection held
        after the block:

        * an **acquire context** (what the default factory returns) — entered with
          ``async with``, so asyncpg returns the connection to the pool on the way
          out, including when the body raises and when the task is cancelled (B7,
          FINAL-02 §15.2/§18);
        * a **connection** (an injected factory: the unit doubles, the loopback
          integration suites, the recovery drill) — yielded unchanged, so its
          lifecycle stays with the injector exactly as before.

        Before the B7 fix this method was ``return await self._connection_factory()``
        and no call site ever released anything: one pooled connection was lost per
        store call, so the application's five-connection pool was exhausted after
        ≈5 calls and every DB-backed endpoint then hung.
        """
        acquired = await self._connection_factory()
        if hasattr(acquired, "__aenter__") and hasattr(acquired, "__aexit__"):
            async with acquired as connection:
                yield connection
            return
        yield acquired

    async def create_queued_job(
        self,
        *,
        requested_by: Optional[str],
        scope: str = SCOPE_FULL,
        idempotency_key: Optional[str] = None,
        release_commit: Optional[str] = None,
        kind: str = KIND_DATABASE,
        backup_set_id: Optional[str] = None,
    ) -> tuple[BackupJob, bool]:
        """Create a ``queued`` row, or return the job that already holds the slot.

        Implements the ratified §11 guarantees in one statement:

        * the partial unique index makes at most **one** ``queued``/``running``
          row exist, so two admins starting at once cannot both queue a dump;
        * ``ON CONFLICT DO NOTHING`` is bare, so *either* unique index (the
          single-flight slot **and** the idempotency key) resolves the request to
          the existing job rather than failing.

        Returns:
            ``(job, created)``. ``created`` is ``False`` when the request was
            satisfied by an existing job — the caller then returns that job's id
            instead of an error.
        """
        if scope not in ALLOWED_SCOPES:
            raise BackupJobError(f"unsupported backup scope: {scope!r}")
        if kind not in ALLOWED_KINDS:
            raise BackupJobError(f"unsupported backup kind: {kind!r}")

        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"""
                INSERT INTO public.backup_jobs (
                    status, scope, requested_by, idempotency_key, release_commit,
                    kind, backup_set_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
                RETURNING {_COLUMNS}
                """,
                STATUS_QUEUED,
                scope,
                requested_by,
                idempotency_key,
                release_commit,
                kind,
                backup_set_id,
            )
            if row is not None:
                return _row_to_job(row), True

            existing = await self._find_existing(
                connection, idempotency_key=idempotency_key, kind=kind
            )
            if existing is None:  # pragma: no cover — defensive: conflict without a row
                raise BackupJobError(
                    "backup job insert conflicted but no existing job was found"
                )
            return existing, False

    async def _find_existing(
        self,
        connection: Any,
        *,
        idempotency_key: Optional[str],
        kind: Optional[str] = None,
    ) -> Optional[BackupJob]:
        """Resolve a satisfied request to the row that caused the conflict."""
        if idempotency_key:
            row = await connection.fetchrow(
                f"SELECT {_COLUMNS} FROM public.backup_jobs "
                "WHERE idempotency_key = $1 LIMIT 1",
                idempotency_key,
            )
            if row is not None:
                return _row_to_job(row)
        if kind:
            # Each kind has its own single-flight slot (§14), so the fallback must
            # not hand a database request the object job that holds *that* slot.
            row = await connection.fetchrow(
                f"SELECT {_COLUMNS} FROM public.backup_jobs "
                "WHERE status = ANY($1::text[]) AND kind = $2 "
                "ORDER BY requested_at ASC LIMIT 1",
                list(ACTIVE_STATUSES),
                kind,
            )
            return _row_to_job(row) if row is not None else None
        row = await connection.fetchrow(
            f"SELECT {_COLUMNS} FROM public.backup_jobs "
            "WHERE status = ANY($1::text[]) ORDER BY requested_at ASC LIMIT 1",
            list(ACTIVE_STATUSES),
        )
        return _row_to_job(row) if row is not None else None

    async def get_active(self, *, kind: Optional[str] = None) -> Optional[BackupJob]:
        """Return the job currently holding a single-flight slot, if any."""
        async with self._connection() as connection:
            return await self._find_existing(
                connection, idempotency_key=None, kind=kind
            )

    async def claim_next(
        self,
        *,
        lock_token: str,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        stale_after_seconds: int = DEFAULT_STALE_LOCK_SECONDS,
        now: Optional[datetime] = None,
    ) -> Optional[BackupJob]:
        """Atomically claim the next runnable job for this worker (§11).

        One statement, three problems solved at once:

        * ``FOR UPDATE SKIP LOCKED`` — two workers never claim the same job, and
          a concurrent claim never blocks;
        * the ``attempt_count`` guard bounds the ``failed → queued`` retry loop,
          so a permanently broken job stops being retried;
        * the stale-lock clause releases a job whose worker died mid-run, which
          is the same recovery idiom the existing document worker uses.

        ``attempt_count`` is incremented as part of the claim, so a crash *after*
        the claim still consumes one attempt (no infinite retry).
        """
        moment = now or utc_now()
        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"""
                UPDATE public.backup_jobs
                SET status = $2,
                    started_at = COALESCE(started_at, $3),
                    locked_at = $3,
                    lock_token = $4,
                    attempt_count = attempt_count + 1,
                    error_reason = NULL
                WHERE id = (
                    SELECT id FROM public.backup_jobs
                    WHERE status = $5
                       OR (status = $6 AND attempt_count < $1)
                       OR (status = $7
                           AND locked_at IS NOT NULL
                           AND locked_at < $3::timestamptz - make_interval(secs => $8))
                    ORDER BY requested_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING {_COLUMNS}
                """,
                max_attempts,
                STATUS_RUNNING,
                moment,
                lock_token,
                STATUS_QUEUED,
                STATUS_FAILED,
                STATUS_RUNNING,
                stale_after_seconds,
            )
            if row is None:
                return None
            job = _row_to_job(row)
        logger.info(
            "claimed backup job %s (attempt %s, scope %s)",
            job.id,
            job.attempt_count,
            job.scope,
        )
        return job

    async def release_stale(
        self,
        *,
        stale_after_seconds: int = DEFAULT_STALE_LOCK_SECONDS,
        now: Optional[datetime] = None,
    ) -> int:
        """Re-queue jobs whose lock outlived its worker (§11). Returns the count.

        The attempt was already counted at claim time, so a poisoned job still
        hits its attempt ceiling instead of looping forever.
        """
        moment = now or utc_now()
        async with self._connection() as connection:
            status = await connection.execute(
                """
                UPDATE public.backup_jobs
                SET status = $1, lock_token = NULL, locked_at = NULL
                WHERE status = $2
                  AND locked_at IS NOT NULL
                  AND locked_at < $3::timestamptz - make_interval(secs => $4)
                """,
                STATUS_QUEUED,
                STATUS_RUNNING,
                moment,
                stale_after_seconds,
            )
        return _affected_rows(status)

    async def mark_completed(
        self,
        job_id: str,
        *,
        record: BackupRecord,
        manifest_extra: Optional[dict[str, Any]] = None,
        storage_bucket: Optional[str] = None,
        retention_days: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> BackupJob:
        """Record a successful artifact and close the job (§12 metadata).

        Only the resulting ``BackupRecord`` (key id, byte count, checksums,
        counts) is persisted — never plaintext and never the key. ``expires_at``
        is derived from the existing ``backup_retention_days`` setting; when that
        setting is unset (``None``) the artifact carries **no automatic expiry**,
        which is the honest representation of "retention not configured".

        The ``status = 'running'`` guard is deliberate: a job may only be
        completed from ``running``, so a duplicated worker cannot overwrite a
        terminal row.
        """
        moment = now or utc_now()
        manifest = dict(record.as_dict())
        if manifest_extra:
            manifest.update(manifest_extra)
        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"""
                UPDATE public.backup_jobs
                SET status = $2,
                    finished_at = $3,
                    lock_token = NULL,
                    locked_at = NULL,
                    storage_key = $4,
                    storage_bucket = $5,
                    artifact_bytes = $6,
                    checksum_sha256 = $7,
                    key_version = $8,
                    manifest = COALESCE(manifest, '{{}}'::jsonb) || $9::jsonb,
                    expires_at = CASE
                        WHEN $10::integer IS NULL THEN NULL
                        ELSE $3::timestamptz + make_interval(days => $10)
                    END
                WHERE id = $1 AND status = $11
                RETURNING {_COLUMNS}
                """,
                job_id,
                STATUS_COMPLETED,
                moment,
                record.object_key,
                storage_bucket,
                record.size_bytes,
                record.ciphertext_sha256,
                record.key_id,
                json.dumps(manifest, default=str),
                retention_days,
                STATUS_RUNNING,
            )
            if row is None:
                raise BackupJobConflictError(
                    f"backup job {job_id} is not running; refusing to complete it"
                )
            job = _row_to_job(row)
        logger.info("backup job %s completed (%s bytes)", job.id, job.artifact_bytes)
        return job

    async def mark_completed_objects(
        self,
        job_id: str,
        *,
        object_key: str,
        size_bytes: int,
        ciphertext_sha256: str,
        key_version: str,
        object_count: int,
        object_bytes: int,
        manifest_extra: Optional[dict[str, Any]] = None,
        retention_days: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> BackupJob:
        """Close an ``objects`` job after its artifact is stored (§14).

        The object job records its own byte counts (``object_count``,
        ``object_bytes``) in addition to the artifact size, so the Admin Dashboard
        can show what a backup set actually contains without fetching anything.
        Guarded on ``status = 'running'`` for the same reason as the database job:
        a duplicated worker must not overwrite a terminal row.
        """
        moment = now or utc_now()
        manifest = dict(manifest_extra or {})
        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"""
                UPDATE public.backup_jobs
                SET status = $2,
                    finished_at = $3,
                    lock_token = NULL,
                    locked_at = NULL,
                    storage_key = $4,
                    artifact_bytes = $5,
                    checksum_sha256 = $6,
                    key_version = $7,
                    manifest = COALESCE(manifest, '{{}}'::jsonb) || $8::jsonb,
                    object_count = $9,
                    object_bytes = $10,
                    expires_at = CASE
                        WHEN $11::integer IS NULL THEN NULL
                        ELSE $3::timestamptz + make_interval(days => $11)
                    END
                WHERE id = $1 AND status = $12
                RETURNING {_COLUMNS}
                """,
                job_id,
                STATUS_COMPLETED,
                moment,
                object_key,
                size_bytes,
                ciphertext_sha256,
                key_version,
                json.dumps(manifest, default=str),
                object_count,
                object_bytes,
                retention_days,
                STATUS_RUNNING,
            )
            if row is None:
                raise BackupJobConflictError(
                    f"backup job {job_id} is not running; refusing to complete it"
                )
            job = _row_to_job(row)
        logger.info(
            "object backup job %s completed (%s objects, %s bytes)",
            job.id,
            job.object_count,
            job.object_bytes,
        )
        return job

    async def mark_verified(
        self,
        job_id: str,
        *,
        verified: bool,
        error_reason: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> BackupJob:
        """Record the outcome of the **Verify Backup** action (§12).

        Only a ``completed`` artifact can be verified — verifying a queued or
        failed job would record a claim about an object that does not exist — so
        the guard raises :class:`~backup.errors.BackupJobConflictError` instead.
        """
        moment = now or utc_now()
        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"""
                UPDATE public.backup_jobs
                SET verification_status = $2,
                    verification_checked_at = $3,
                    verification_error = $4
                WHERE id = $1 AND status = $5
                RETURNING {_COLUMNS}
                """,
                job_id,
                VERIFICATION_VERIFIED if verified else VERIFICATION_FAILED,
                moment,
                (error_reason or "")[:MAX_ERROR_REASON_LENGTH] or None,
                STATUS_COMPLETED,
            )
            if row is None:
                raise BackupJobConflictError(
                    f"backup job {job_id} is not a completed artifact; nothing to verify"
                )
            return _row_to_job(row)

    async def list_expired(self, *, limit: int = 200) -> list[BackupJob]:
        """``expired`` jobs that still reference an artifact (retention pruning).

        Pruning candidates only: an expired job whose storage reference was already
        cleared is not returned, so a sweep never repeats work.
        """
        async with self._connection() as connection:
            rows = await connection.fetch(
                f"""
                SELECT {_COLUMNS} FROM public.backup_jobs
                WHERE status = $1 AND storage_key IS NOT NULL
                ORDER BY expires_at ASC NULLS LAST
                LIMIT $2
                """,
                STATUS_EXPIRED,
                limit,
            )
        return [_row_to_job(row) for row in rows]

    async def list_by_backup_set(self, backup_set_id: str) -> list[BackupJob]:
        """Both halves of a backup set (the database job and its object job)."""
        async with self._connection() as connection:
            rows = await connection.fetch(
                f"SELECT {_COLUMNS} FROM public.backup_jobs "
                "WHERE backup_set_id = $1 ORDER BY requested_at ASC",
                backup_set_id,
            )
        return [_row_to_job(row) for row in rows]

    async def attach_backup_set(self, job_id: str, backup_set_id: str) -> BackupJob:
        """Record the backup-set pairing id on a job that does not have one yet.

        ``COALESCE`` makes this idempotent *and* safe against replay: an already
        paired job is returned unchanged, so a repeated request cannot move an
        existing job into a different set (and therefore cannot mispair a restore).
        """
        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"""
                UPDATE public.backup_jobs
                SET backup_set_id = COALESCE(backup_set_id, $2::uuid)
                WHERE id = $1
                RETURNING {_COLUMNS}
                """,
                job_id,
                backup_set_id,
            )
            if row is None:
                raise BackupJobNotFoundError(f"no backup job with id {job_id}")
            return _row_to_job(row)

    async def mark_failed(
        self,
        job_id: str,
        *,
        error_reason: str,
        now: Optional[datetime] = None,
    ) -> BackupJob:
        """Close a ``running`` job with a sanitised, bounded reason (§10).

        The reason is passed through :func:`sanitise_reason` by the caller (the
        orchestrator); this method additionally truncates, so a direct call can
        never store an unbounded or secret-bearing string.
        """
        moment = now or utc_now()
        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"""
                UPDATE public.backup_jobs
                SET status = $2,
                    finished_at = $3,
                    lock_token = NULL,
                    locked_at = NULL,
                    error_reason = $4
                WHERE id = $1 AND status = $5
                RETURNING {_COLUMNS}
                """,
                job_id,
                STATUS_FAILED,
                moment,
                error_reason[:MAX_ERROR_REASON_LENGTH],
                STATUS_RUNNING,
            )
            if row is None:
                raise BackupJobConflictError(
                    f"backup job {job_id} is not running; refusing to fail it"
                )
            job = _row_to_job(row)
        logger.warning("backup job %s failed: %s", job.id, job.error_reason)
        return job

    async def mark_expired(self, *, now: Optional[datetime] = None) -> int:
        """Move completed jobs past ``expires_at`` to ``expired``. Returns count.

        Expiry is metadata-only here: it never touches storage. Removing the
        artifact is a separate, explicitly authorised action (deletion is
        distinct from expiry in the ratified state machine).
        """
        moment = now or utc_now()
        async with self._connection() as connection:
            status = await connection.execute(
                """
                UPDATE public.backup_jobs
                SET status = $1, lock_token = NULL, locked_at = NULL
                WHERE status = $2
                  AND expires_at IS NOT NULL
                  AND expires_at <= $3
                """,
                STATUS_EXPIRED,
                STATUS_COMPLETED,
                moment,
            )
        return _affected_rows(status)

    async def mark_deleted(
        self, job_id: str, *, deleted_by: Optional[str], now: Optional[datetime] = None
    ) -> BackupJob:
        """Mark an artifact row deleted (the row is retained for audit)."""
        moment = now or utc_now()
        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"""
                UPDATE public.backup_jobs
                SET status = $2, deleted_at = $3, deleted_by = $4
                WHERE id = $1 AND status = ANY($5::text[])
                RETURNING {_COLUMNS}
                """,
                job_id,
                STATUS_DELETED,
                moment,
                deleted_by,
                [STATUS_COMPLETED, STATUS_EXPIRED, STATUS_FAILED],
            )
            if row is None:
                raise BackupJobConflictError(
                    f"backup job {job_id} cannot be deleted from its current state"
                )
            return _row_to_job(row)

    async def get(self, job_id: str) -> Optional[BackupJob]:
        """Return one job by id, or ``None`` when it does not exist."""
        async with self._connection() as connection:
            row = await connection.fetchrow(
                f"SELECT {_COLUMNS} FROM public.backup_jobs WHERE id = $1",
                job_id,
            )
        return _row_to_job(row) if row is not None else None

    async def list_recent(
        self, *, limit: int = 50, offset: int = 0
    ) -> list[BackupJob]:
        """Admin history, newest first (§9 "Admin Backup History")."""
        async with self._connection() as connection:
            rows = await connection.fetch(
                f"SELECT {_COLUMNS} FROM public.backup_jobs "
                "ORDER BY requested_at DESC, id DESC LIMIT $1 OFFSET $2",
                limit,
                offset,
            )
        return [_row_to_job(row) for row in rows]


def _affected_rows(command_tag: str) -> int:
    """Parse asyncpg's ``UPDATE <n>`` command tag (``0`` when unrecognised)."""
    _, _, count = command_tag.partition(" ")
    return int(count) if count.isdigit() else 0


async def run_claimed_job(
    store: BackupJobStore,
    job: BackupJob,
    service: BackupService,
    *,
    retention_days: Optional[int] = None,
    storage_bucket: Optional[str] = None,
    release_commit: Optional[str] = None,
    now: Optional[datetime] = None,
) -> BackupJob:
    """Run one already-claimed job through the existing service, then record it.

    Export/storage failures are **absorbed into the row** (status ``failed`` plus
    a sanitised reason) rather than propagated, so one poisoned job cannot kill a
    worker loop. An impossible state transition still raises
    :class:`~backup.errors.BackupJobConflictError`, because that means another
    actor concurrently changed a job this worker owns — an anomaly that must be
    surfaced, not swallowed.
    """
    commit = release_commit if release_commit is not None else job.release_commit
    try:
        record = await service.create_backup(
            requested_by=job.requested_by, reason=f"backup job {job.id}"
        )
    except Exception as exc:  # noqa: BLE001 — the row must record the failure
        logger.exception("backup job %s failed", job.id)
        return await store.mark_failed(
            job.id, error_reason=sanitise_reason(exc), now=now
        )

    manifest_extra: dict[str, Any] = {
        "job_id": job.id,
        "scope": job.scope,
        "attempt_count": job.attempt_count,
        "requested_by": job.requested_by,
    }
    if commit:
        manifest_extra["release_commit"] = commit
    return await store.mark_completed(
        job.id,
        record=record,
        manifest_extra=manifest_extra,
        storage_bucket=storage_bucket,
        retention_days=retention_days,
        now=now,
    )


async def run_next_job(
    store: BackupJobStore,
    service: BackupService,
    *,
    lock_token: Optional[str] = None,
    retention_days: Optional[int] = None,
    storage_bucket: Optional[str] = None,
) -> Optional[BackupJob]:
    """Claim one runnable job and run it. Returns ``None`` when the queue is empty.

    The claim token defaults to a fresh random hex string; a real worker passes a
    stable per-process token so its own stale locks are recognisable.
    """
    job = await store.claim_next(lock_token=lock_token or uuid.uuid4().hex)
    if job is None:
        return None
    return await run_claimed_job(
        store,
        job,
        service,
        retention_days=retention_days,
        storage_bucket=storage_bucket,
    )




