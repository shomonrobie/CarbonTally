"""CarbonTally backup foundation (Phases 1–3: export, jobs, restore, objects).

Bounded, production-compatible backup **and recovery** foundation for the ratified
architecture (D1–D5 in
``docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md``
Part 2).

Scope of this package:

* a pure-Python ``asyncpg`` logical exporter (D1 — no Docker, no Supabase CLI,
  no ``pg_dump`` subprocess);
* a versioned artifact format with a manifest, catalog definition, table data,
  sequence state and integrity metadata;
* application-level authenticated encryption (D3 — AES-256-GCM) applied
  **before** the artifact reaches any storage;
* SHA-256 integrity support (plaintext and ciphertext semantics are distinct and
  documented) and a **verification** surface (:mod:`backup.verification`);
* a narrow private object-storage **interface** with local/in-memory providers
  and an S3-compatible production provider (:mod:`backup.s3store`) whose
  requests are signed in-process by :mod:`backup.sigv4` (OID-3 — no provider SDK);
* a **durable job model** (:mod:`backup.jobs`) — the ``public.backup_jobs``
  queue, its §11 single-flight guard, the database/object job kinds (§14) and the
  worker entrypoints, so a request records a queued row and performs no export
  work in the request path;
* the **worker** (:mod:`backup.worker`) that drains the queue, plus the retention
  sweep (:mod:`backup.retention`);
* **restore** (:mod:`backup.restore`, D4) — a full reconstruction of a database
  from the artifact's own ``catalog.json``, including RLS and policies, with a
  post-restore verification of every object class;
* **Storage-object backup/restore** (:mod:`backup.objects`, §14) as a separate job
  paired by ``backup_set_id``;
* the **operational policy** (:mod:`backup.policy`) — the only configurable
  layer; encryption, private storage, authorization, tenant isolation and
  integrity verification are not settings.

Explicitly **not** implemented here: automatic schedule-driven backups (§16 defers
scheduling), and any production provisioning. See
``docs/architecture/CT-BACKUP-COMPLETE-IMPLEMENTATION-20261001.md``.
"""
from __future__ import annotations

from backup.artifact import (
    ARCHIVE_MEMBER_MANIFEST,
    BACKUP_FORMAT_NAME,
    BACKUP_FORMAT_VERSION,
    EXPORTER_VERSION,
    BackupManifest,
    TableInventoryEntry,
    validate_backup_id,
)
from backup.errors import (
    BackupArtifactError,
    BackupConfigurationError,
    BackupError,
    BackupExportError,
    BackupIntegrityError,
    BackupJobConflictError,
    BackupJobError,
    BackupJobNotFoundError,
    BackupObjectError,
    BackupRestoreError,
    BackupRestoreTargetError,
    BackupStorageError,
    BackupValidationError,
)
from backup.jobs import (
    KIND_DATABASE,
    KIND_OBJECTS,
    BackupJob,
    BackupJobStore,
    run_claimed_job,
    run_next_job,
)
from backup.objects import (
    DEFAULT_BUCKET,
    InMemoryStorageSource,
    SupabaseStorageSource,
    export_objects,
    restore_objects,
)
from backup.policy import (
    MANDATORY_INVARIANTS,
    BackupPolicy,
    policy_from_stored,
    validate_policy_update,
)
from backup.restore import (
    RestoreMembers,
    RestoreResult,
    assert_disposable_target,
    read_members_from_envelope,
    restore_artifact,
    restore_members,
    restore_plan,
    verify_restored,
)
from backup.retention import RetentionOutcome, expire_and_prune
from backup.service import BackupRecord, BackupService
from backup.settings import (
    DENIED_SCHEMAS,
    DENIED_SCHEMA_OVERRIDE_PHRASE,
    BackupSettings,
    validate_schemas,
)
from backup.sigv4 import SignedRequest, sign_request
from backup.storage import InMemoryObjectStore, LocalFilesystemObjectStore, ObjectStore
from backup.verification import (
    ArtifactVerification,
    verify_envelope,
    verify_stored_artifact,
)
from backup.worker import BackupWorker, get_backup_worker

__all__ = [
    "ARCHIVE_MEMBER_MANIFEST",
    "BACKUP_FORMAT_NAME",
    "BACKUP_FORMAT_VERSION",
    "DENIED_SCHEMAS",
    "DENIED_SCHEMA_OVERRIDE_PHRASE",
    "DEFAULT_BUCKET",
    "EXPORTER_VERSION",
    "KIND_DATABASE",
    "KIND_OBJECTS",
    "MANDATORY_INVARIANTS",
    "ArtifactVerification",
    "BackupArtifactError",
    "BackupConfigurationError",
    "BackupError",
    "BackupExportError",
    "BackupIntegrityError",
    "BackupJob",
    "BackupJobConflictError",
    "BackupJobError",
    "BackupJobNotFoundError",
    "BackupJobStore",
    "BackupManifest",
    "BackupObjectError",
    "BackupPolicy",
    "BackupRecord",
    "BackupRestoreError",
    "BackupRestoreTargetError",
    "BackupService",
    "BackupSettings",
    "BackupStorageError",
    "BackupValidationError",
    "BackupWorker",
    "InMemoryObjectStore",
    "InMemoryStorageSource",
    "LocalFilesystemObjectStore",
    "ObjectStore",
    "RestoreMembers",
    "RestoreResult",
    "RetentionOutcome",
    "SignedRequest",
    "SupabaseStorageSource",
    "TableInventoryEntry",
    "assert_disposable_target",
    "expire_and_prune",
    "export_objects",
    "get_backup_worker",
    "policy_from_stored",
    "read_members_from_envelope",
    "restore_artifact",
    "restore_members",
    "restore_objects",
    "restore_plan",
    "run_claimed_job",
    "run_next_job",
    "sign_request",
    "validate_backup_id",
    "validate_policy_update",
    "validate_schemas",
    "verify_envelope",
    "verify_restored",
    "verify_stored_artifact",
]
