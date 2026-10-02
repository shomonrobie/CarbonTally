"""V3 Admin — backup management surface (BACKUP-01/02 §9, §12, §14).

The dashboard-facing half of the backup capability. It is deliberately thin: the
database and object artifacts are produced by a **worker**, and the request path
only ever *records* a queued job (architecture §9: "creates a **queued** row only;
no work in the request path").

Authorization
-------------

Every route is gated by ``Depends(require_backup_manager())`` — admin authority
**plus** the explicit ``can_manage_backups`` capability (§9). The router is
mounted under the existing admin prefix (``/api/v3/admin/backups``), so it
inherits the platform's established auth boundaries rather than inventing a
surface. Ordinary customer users, consultants, client users and ordinary staff
have no path to any of it, and Processing Entity staff are denied before the
capability is even consulted.

What is exposed — and what never is
-----------------------------------

Responses carry **non-secret metadata only**: job id, status, timestamps, sizes,
checksums, key *version*, retention/expiry, verification outcome, and counts. No
route returns an encryption key, a storage credential, a database DSN, a service
key, or artifact contents in plaintext. The download route hands back the
**ciphertext** the provider stores (the artifact is already encrypted at rest by
D3), so even a leaked download is useless without the key held in separate
custody.

Audit and notifications
-----------------------

Every state-changing action writes one append-only ``audit_trail`` entry through
the existing repository (§17) — ``backup.requested``, ``backup.verified``,
``backup.downloaded``, ``backup.policy_updated`` — and completion/failure
notifications reuse ``NotificationsRepository.create_idempotent`` with a
deterministic ``event_key``, so a retried action can never duplicate a
notification and a notification failure can never turn a successful backup into a
failed one.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_backup_manager
from core.logging import get_logger
from backup.errors import BackupError
from backup.jobs import (
    KIND_DATABASE,
    KIND_OBJECTS,
    STATUS_COMPLETED,
    STATUS_FAILED,
    BackupJob,
    BackupJobConflictError,
    BackupJobNotFoundError,
    BackupJobStore,
)
from backup.objects import DEFAULT_BUCKET
from backup.policy import policy_from_stored, validate_policy_update
from backup.settings import BackupSettings
from backup.storage import build_object_store
from backup.verification import verify_stored_artifact
from domain.audit import AuditEntry

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v3/admin/backups", tags=["V3 — Admin Backups"])

#: Bounded history page so an admin read can never stream an unbounded table.
MAX_PAGE = 200
DEFAULT_PAGE = 50


class CreateBackupRequest(BaseModel):
    """Body of ``POST /api/v3/admin/backups``.

    ``confirm`` is the server-side half of §9's explicit-confirmation rule: a
    stray request that does not carry it is refused, so a backup cannot be started
    by a client that did not mean to start one.
    """

    confirm: bool = False
    include_objects: Optional[bool] = None
    reason: Optional[str] = None


class PolicyUpdatePayload(BaseModel):
    """Partial update of the operational policy (extra keys are validated below).

    Extras are deliberately *allowed through* the model so that
    :func:`backup.policy.validate_policy_update` can answer a request that names a
    non-configurable property (for example ``encryption``) with the reason, instead
    of a generic schema error.
    """

    model_config = ConfigDict(extra="allow")

    enabled: Optional[bool] = None
    retention_days: Optional[int] = None
    frequency: Optional[str] = None
    object_backup_enabled: Optional[bool] = None
    object_prefix: Optional[str] = None


# ---------------------------------------------------------------------------
# Wiring (lazy: importing this module must not read configuration or connect)
# ---------------------------------------------------------------------------


def _settings() -> BackupSettings:
    return BackupSettings.from_env()


def _job_store() -> BackupJobStore:
    """The queue store. Tests override this dependency."""
    return BackupJobStore()


def _object_store(settings: BackupSettings):
    return build_object_store(settings)


def _correlation(request: Optional[Request], fallback: str) -> str:
    context = getattr(getattr(request, "state", None), "request_context", None)
    return str(getattr(context, "correlation_id", None) or fallback)


async def _audit(
    repos: RepositoryBundle,
    request: Optional[Request],
    *,
    action: str,
    job_id: str,
    actor: str,
    changed_fields: Optional[dict[str, Any]] = None,
) -> None:
    """Best-effort append-only audit entry (never breaks the request).

    ``changed_fields`` carries identifiers and metadata only — the same contract
    the rest of the audit ledger uses, and the reason §17 can say "no secrets".
    """
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=_correlation(request, job_id),
        entity_type="backup_job",
        entity_id=job_id,
        action=action,
        actor=actor,
        occurred_at=datetime.now(timezone.utc),
        changed_fields=dict(changed_fields or {}),
        ip_address=(
            request.client.host if request is not None and request.client else None
        ),
    )
    try:
        await repos.audit.record(entry)
    except Exception:  # noqa: BLE001 — audit must never break the operation
        logger.exception("backup audit (%s) failed for job %s", action, job_id)


async def _notify(
    repos: RepositoryBundle,
    *,
    recipient: Optional[str],
    event_key: str,
    title: str,
    message: str,
    priority: int = 0,
    link: Optional[str] = None,
) -> None:
    """Idempotent notification (best effort).

    ``event_key`` is deterministic per (recipient, business event), so a retried
    action or a duplicated worker can never produce a second notification. A
    notification failure is logged and swallowed — reporting a *successful* backup
    as failed because a notification queue was unavailable would be a lie.
    """
    if not recipient:
        return
    try:
        await repos.notifications.create_idempotent(
            recipient,
            event_key,
            notification_type="backup",
            title=title,
            message=message,
            priority=priority,
            link=link,
            actor_domain="system",
        )
    except Exception:  # noqa: BLE001 — notifications must never break the operation
        logger.exception("backup notification (%s) failed", event_key)


def _job_metadata(job: BackupJob) -> dict[str, Any]:
    """Non-secret projection of one job (never a lock token or a key)."""
    payload = job.as_dict()
    payload.pop("lock_token", None)
    payload.pop("locked_at", None)
    return payload


async def _require_job(store: BackupJobStore, job_id: str) -> BackupJob:
    job = await store.get(job_id)
    if job is None:
        raise BackupJobNotFoundError(f"no backup job with id {job_id}")
    return job


def _health(jobs: list[BackupJob]) -> dict[str, Any]:
    """Overview facts for the dashboard, computed from the job rows only."""
    completed = [job for job in jobs if job.status == STATUS_COMPLETED]
    failed = [job for job in jobs if job.status == STATUS_FAILED]
    verified = [job for job in completed if job.verification_status == "verified"]
    latest = max(jobs, key=lambda job: job.requested_at, default=None)
    return {
        "last_successful": _job_metadata(completed[0]) if completed else None,
        "last_failed": _job_metadata(failed[0]) if failed else None,
        "last_request": _job_metadata(latest) if latest is not None else None,
        "latest_verification": (
            _job_metadata(verified[0]) if verified else None
        ),
        "counts": {
            "completed": len(completed),
            "failed": len(failed),
            "verified": len(verified),
            "unverified_completed": len(completed) - len(verified),
        },
    }


async def _effective_policy(repos: RepositoryBundle):
    """The stored policy merged with the retention setting (one source of truth)."""
    retention = await repos.settings.get_retention()
    stored = await repos.settings.get_backup_policy()
    policy = policy_from_stored(
        stored, retention_days=retention.get("backup_retention_days")
    )
    return policy, stored, retention


def _destination(settings: BackupSettings) -> dict[str, Any]:
    """A non-secret description of where artifacts go (never a credential)."""
    return {
        "provider": settings.object_store,
        "bucket": settings.s3_bucket or None,
        "prefix": settings.s3_prefix or None,
        "local_root": (
            settings.local_root if settings.object_store == "local" else None
        ),
        "encryption": "AES-256-GCM (applied before upload)",
        "key_id": settings.key_id,
        "encryption_key_configured": bool(settings.encryption_key),
        "verify_readback": settings.verify_readback,
    }


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------


@router.get("/status")
async def backup_status(
    current_user: AuthUser = Depends(require_backup_manager()),
    repos: RepositoryBundle = Depends(get_repositories),
    store: BackupJobStore = Depends(_job_store),
):
    """Backup system status for the dashboard overview (§9).

    Reports the effective policy, the destination (no credentials), the current
    single-flight occupants and the recent-history summary. Read-only.
    """
    policy, stored, retention = await _effective_policy(repos)
    settings = _settings()
    try:
        active = await store.get_active()
    except Exception:  # noqa: BLE001 — a missing queue is reported, not fatal here
        logger.exception("backup status: could not read the active job")
        active = None
    jobs = await store.list_recent(limit=MAX_PAGE)
    health = _health(jobs)
    return {
        "status": {
            "enabled": policy.enabled,
            "policy": policy.as_dict(),
            "policy_updated_at": stored.get("updated_at"),
            "policy_updated_by": stored.get("updated_by"),
            "retention": {
                "days": retention.get("backup_retention_days"),
                "explicitly_configured": retention.get("backup_retention_days")
                is not None,
            },
            "destination": _destination(settings),
            "active_job": _job_metadata(active) if active is not None else None,
            "object_backup": {
                "enabled": policy.object_backup_enabled,
                "bucket": DEFAULT_BUCKET,
                "prefix": policy.object_prefix,
            },
            "scheduling": {
                "configured_intent": policy.frequency,
                "automation": "not implemented — §16 defers schedule-driven backups",
            },
            **health,
        }
    }


@router.get("")
async def list_backups(
    limit: int = DEFAULT_PAGE,
    offset: int = 0,
    current_user: AuthUser = Depends(require_backup_manager()),
    store: BackupJobStore = Depends(_job_store),
):
    """Backup history (newest first) — non-secret metadata only (§9)."""
    bounded = max(1, min(int(limit), MAX_PAGE))
    jobs = await store.list_recent(limit=bounded, offset=max(0, int(offset)))
    return {
        "backups": [_job_metadata(job) for job in jobs],
        "limit": bounded,
        "offset": max(0, int(offset)),
    }


@router.get("/policy")
async def get_backup_policy(
    current_user: AuthUser = Depends(require_backup_manager()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The effective operational policy plus the non-configurable invariants (§16).

    Declared before ``/{job_id}`` so the literal path wins over the path parameter.
    """
    policy, stored, retention = await _effective_policy(repos)
    return {
        "policy": policy.as_dict(),
        "retention_days": retention.get("backup_retention_days"),
        "updated_at": stored.get("updated_at"),
        "updated_by": stored.get("updated_by"),
        "configurable_fields": [
            "enabled",
            "retention_days",
            "frequency",
            "object_backup_enabled",
            "object_prefix",
        ],
        "not_configurable": [
            "encryption",
            "private_storage",
            "authorization",
            "tenant_isolation",
            "integrity_verification",
        ],
    }


@router.put("/policy")
async def update_backup_policy(
    payload: PolicyUpdatePayload,
    request: Request,
    current_user: AuthUser = Depends(require_backup_manager()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Update the operational policy (§16).

    Only the allow-listed operational fields are accepted. A request that names a
    non-configurable security property (encryption, private storage, authorization,
    tenant isolation, integrity verification) is refused with the invariant's own
    reason — those properties are enforced in code and have no switch to flip.
    """
    supplied = {
        **payload.model_dump(exclude_unset=True),
        **(payload.model_extra or {}),
    }
    try:
        normalized = validate_policy_update(supplied)
    except BackupError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc

    retention_days = normalized.pop("retention_days", None)
    stored = await repos.settings.update_backup_policy(
        fields=normalized, updated_by=current_user.user_id
    )
    retention = await repos.settings.get_retention()
    if retention_days is not None:
        # Retention has exactly one home (the `backup_retention_days` column), so
        # setting it here routes through the retention surface rather than
        # duplicating the value into the policy row.
        retention = await repos.settings.update_retention(
            audit_log_retention_days=retention.get("audit_log_retention_days"),
            data_retention_days=retention.get("data_retention_days"),
            document_retention_days=retention.get("document_retention_days"),
            backup_retention_days=int(retention_days),
            operational_telemetry_retention_days=retention.get(
                "operational_telemetry_retention_days"
            ),
            updated_by=current_user.user_id,
        )

    policy, _, _ = await _effective_policy(repos)
    await _audit(
        repos,
        request,
        action="backup.policy_updated",
        job_id="policy",
        actor=current_user.user_id,
        changed_fields={
            **normalized,
            "retention_days": retention.get("backup_retention_days"),
        },
    )
    return {
        "policy": policy.as_dict(),
        "retention_days": retention.get("backup_retention_days"),
    }


@router.get("/{job_id}")
async def get_backup(
    job_id: str,
    current_user: AuthUser = Depends(require_backup_manager()),
    store: BackupJobStore = Depends(_job_store),
):
    """One job's status/details (§9)."""
    job = await _require_job(store, job_id)
    return {"backup": _job_metadata(job)}


@router.get("/{job_id}/pair")
async def get_backup_pair(
    job_id: str,
    current_user: AuthUser = Depends(require_backup_manager()),
    store: BackupJobStore = Depends(_job_store),
):
    """Both halves of the backup set this job belongs to (§14).

    This is what a restore procedure reads to know whether a *consistent pair* of
    the database artifact and its object artifact is available.
    """
    job = await _require_job(store, job_id)
    backup_set_id = job.backup_set_id or job.id
    members = await store.list_by_backup_set(backup_set_id)
    by_kind = {member.kind: _job_metadata(member) for member in members}
    database = by_kind.get(KIND_DATABASE)
    objects = by_kind.get(KIND_OBJECTS)
    return {
        "backup_set_id": backup_set_id,
        "database": database,
        "objects": objects,
        "pair_complete": bool(
            database
            and database.get("status") == STATUS_COMPLETED
            and objects
            and objects.get("status") == STATUS_COMPLETED
        ),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_backup(
    payload: CreateBackupRequest,
    request: Request,
    current_user: AuthUser = Depends(require_backup_manager()),
    repos: RepositoryBundle = Depends(get_repositories),
    store: BackupJobStore = Depends(_job_store),
):
    """Queue one backup set: a database job and, by default, its object job (§9/§14).

    No export work happens here — the request records ``queued`` rows and returns
    (architecture §9: "creates a **queued** row only; no work in the request
    path"). A second concurrent request, or a replayed one carrying the same
    ``Idempotency-Key``, resolves to the existing job rather than starting a second
    dump; that is §11's single-flight guarantee, enforced by the database rather
    than by this code.
    """
    if not payload.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Creating a backup copies the production database and object "
                "storage; the request must carry confirm=true"
            ),
        )

    policy, _, _ = await _effective_policy(repos)
    if not policy.enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Backup is disabled by the platform policy",
        )

    idempotency_key = request.headers.get("Idempotency-Key") or None
    job, created = await store.create_queued_job(
        requested_by=current_user.user_id,
        idempotency_key=idempotency_key,
        kind=KIND_DATABASE,
    )
    backup_set_id = job.backup_set_id or job.id
    if not job.backup_set_id:
        job = await store.attach_backup_set(job.id, backup_set_id)

    object_job: Optional[BackupJob] = None
    include_objects = (
        payload.include_objects
        if payload.include_objects is not None
        else policy.object_backup_enabled
    )
    if include_objects:
        object_job, _object_created = await store.create_queued_job(
            requested_by=current_user.user_id,
            idempotency_key=(f"{idempotency_key}:objects" if idempotency_key else None),
            kind=KIND_OBJECTS,
            backup_set_id=backup_set_id,
        )
        if not object_job.backup_set_id:
            object_job = await store.attach_backup_set(object_job.id, backup_set_id)

    if created:
        await _audit(
            repos,
            request,
            action="backup.requested",
            job_id=job.id,
            actor=current_user.user_id,
            changed_fields={
                "scope": job.scope,
                "kind": KIND_DATABASE,
                "backup_set_id": backup_set_id,
                "include_objects": include_objects,
                "reason": (payload.reason or "")[:200] or None,
            },
        )

    return {
        "created": created,
        "backup_set_id": backup_set_id,
        "job": _job_metadata(job),
        "object_job": _job_metadata(object_job) if object_job is not None else None,
        "message": (
            "Backup queued; the worker will run it."
            if created
            else "A backup was already queued or running; the existing job was returned."
        ),
    }


@router.post("/{job_id}/verify")
async def verify_backup(
    job_id: str,
    request: Request,
    current_user: AuthUser = Depends(require_backup_manager()),
    repos: RepositoryBundle = Depends(get_repositories),
    store: BackupJobStore = Depends(_job_store),
):
    """Verify a stored artifact's integrity (§12) and record the outcome.

    Read-only against storage: the object is fetched, authenticated, decrypted and
    its content checksums recomputed; nothing is written except this job's
    verification columns and the audit entry. The recorded outcome is what the
    dashboard's *latest verification status* shows.
    """
    job = await _require_job(store, job_id)
    if job.status != STATUS_COMPLETED or not job.storage_key:
        raise BackupJobConflictError(
            "only a completed artifact that has a stored object can be verified"
        )

    settings = _settings()
    key = settings.require_encryption_key()
    verification = await verify_stored_artifact(
        _object_store(settings),
        job.storage_key,
        key,
        compression=settings.compression,
        expected_ciphertext_sha256=job.checksum_sha256,
    )
    updated = await store.mark_verified(
        job.id,
        verified=verification.verified,
        error_reason=(
            None if verification.verified else "; ".join(verification.problems)
        ),
    )
    await _audit(
        repos,
        request,
        action="backup.verified",
        job_id=job.id,
        actor=current_user.user_id,
        changed_fields={
            "verified": verification.verified,
            "problems": list(verification.problems),
            "member_count": verification.member_count,
            "content_checksums_verified": verification.content_checksums_verified,
        },
    )
    if not verification.verified:
        # A *failed verification* is the one outcome worth notifying: it means the
        # artifact may not be recoverable, and an operator must not discover that
        # during an incident.
        await _notify(
            repos,
            recipient=job.requested_by,
            event_key=f"backup:{job.id}:verification_failed",
            title="Backup verification failed",
            message=(
                f"Artifact {job.id} failed integrity verification: "
                + "; ".join(verification.problems[:3])
            ),
            priority=2,
        )
    return {"backup": _job_metadata(updated), "verification": verification.as_dict()}


@router.get("/{job_id}/download")
async def download_backup(
    job_id: str,
    request: Request,
    current_user: AuthUser = Depends(require_backup_manager()),
    repos: RepositoryBundle = Depends(get_repositories),
    store: BackupJobStore = Depends(_job_store),
):
    """Authorised, audited download of the **encrypted** artifact (§9).

    Server-mediated: the caller must already hold the backup capability, the fetch
    happens with the worker's own destination credential, and the bytes returned are
    the ciphertext the provider stores — never plaintext and never a permanent
    public URL. The response is marked ``no-store`` so a proxy cannot cache a copy
    of production data, and the audit entry records the *fact* of the download
    without recording the artifact or any credential.
    """
    job = await _require_job(store, job_id)
    if job.status != STATUS_COMPLETED or not job.storage_key:
        raise BackupJobConflictError(
            "only a completed artifact that has a stored object can be downloaded"
        )

    settings = _settings()
    try:
        envelope = await _object_store(settings).get_object(job.storage_key)
    except BackupError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalised to a backup-layer error
        raise BackupError(
            "the artifact could not be read from the backup destination"
        ) from exc

    await _audit(
        repos,
        request,
        action="backup.downloaded",
        job_id=job.id,
        actor=current_user.user_id,
        changed_fields={
            "bytes": len(envelope),
            "key_version": job.key_version,
            "backup_set_id": job.backup_set_id,
        },
    )
    filename = f"carbontally-{job.kind}-{job.id}.tar.gz.enc"
    return Response(
        content=envelope,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


__all__ = ["router"]