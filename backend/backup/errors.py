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
