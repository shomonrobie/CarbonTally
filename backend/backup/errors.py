"""Error hierarchy for the backup foundation.

All errors derive from :class:`core.exceptions.CarbonTallyError` so the API
layer can translate them into consistent responses later (Phase 2/3) without
knowing the concrete type. Codes are stable across releases.
"""
from __future__ import annotations

from typing import Any, Optional

from core.exceptions import CarbonTallyError


class BackupError(CarbonTallyError):
    """Base class for every backup-foundation failure."""

    code = "BACKUP_ERROR"
    http_status = 500

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, details=details)


class BackupConfigurationError(BackupError):
    """Missing or invalid backup configuration (e.g. no encryption key).

    Raised *before* any database or storage work begins.
    """

    code = "BACKUP_CONFIGURATION_ERROR"
    http_status = 500


class BackupValidationError(BackupError):
    """A caller-supplied value failed backup-layer validation (F10).

    Raised **before** any database or storage work. Currently used for
    ``backup_id`` validation, so that an identifier can never influence the
    storage key in an unsafe way.
    """

    code = "BACKUP_VALIDATION_ERROR"
    http_status = 400


class BackupExportError(BackupError):
    """The logical export (catalog inspection or COPY) failed.

    A failed export never yields a final artifact: the service removes its
    temporary material and re-raises.
    """

    code = "BACKUP_EXPORT_ERROR"
    http_status = 500


class BackupIntegrityError(BackupError):
    """An integrity check failed.

    Covers checksum mismatches, authenticated-decryption failure (wrong key or
    tampered ciphertext) and malformed envelope/format structures.
    """

    code = "BACKUP_INTEGRITY_ERROR"
    http_status = 500


class BackupArtifactError(BackupIntegrityError):
    """The artifact envelope or archive is structurally invalid.

    A subclass of :class:`BackupIntegrityError` because a malformed artifact is
    indistinguishable, operationally, from a corrupted one — and must never be
    treated as a usable backup.
    """

    code = "BACKUP_ARTIFACT_ERROR"
    http_status = 500


class BackupStorageError(BackupError):
    """The object-storage provider failed (put/get/list/delete)."""

    code = "BACKUP_STORAGE_ERROR"
    http_status = 502


class BackupJobError(BackupError):
    """The backup **job model** failed (enqueue, claim or state transition).

    Distinct from the artifact errors above: nothing has been exported, stored
    or verified when this is raised — the durable queue row is the only thing in
    play.
    """

    code = "BACKUP_JOB_ERROR"
    http_status = 500


class BackupJobConflictError(BackupJobError):
    """The queue is not in a state that permits the requested transition.

    Covers the ratified single-flight guard (a ``queued``/``running`` job already
    exists — §11) and the attempt budget being exhausted. ``http_status`` is 409
    so the caller can surface the *existing* job id instead of an opaque failure.
    """

    code = "BACKUP_JOB_CONFLICT"
    http_status = 409


class BackupJobNotFoundError(BackupJobError):
    """No backup job exists for the supplied identifier."""

    code = "BACKUP_JOB_NOT_FOUND"
    http_status = 404


class BackupRestoreError(BackupError):
    """Restore from a CarbonTally artifact failed (D4).

    Restore is the dangerous half of the capability, so every failure is a typed,
    fail-closed error: the target is never left in a state that is *claimed* to be
    a completed restore. A partially applied restore is reported as a failure with
    the exact statement that failed, and the caller (an operator tool, never a
    normal admin action) decides what to do with the disposable target.
    """

    code = "BACKUP_RESTORE_ERROR"
    http_status = 500


class BackupRestoreTargetError(BackupRestoreError):
    """The restore target may not be used for a restore (fail-closed guard).

    Raised *before* any statement runs when the target is not a disposable/
    recovery database, or when it already holds user objects — restoring into a
    populated database would silently overwrite live data, which is exactly the
    hazard §13 of the ratified architecture requires us to refuse.
    """

    code = "BACKUP_RESTORE_TARGET_REFUSED"
    http_status = 400


class BackupObjectError(BackupError):
    """Storage-**object** backup or restore failed (§14).

    Objects are a separate, sequenced job paired with a database job by a common
    *backup-set* id; a failure here must never affect the database artifact.
    """

    code = "BACKUP_OBJECT_ERROR"
    http_status = 502
