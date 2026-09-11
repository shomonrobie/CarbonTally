"""CarbonTally backup foundation (Phase 1).

Bounded, production-compatible **export** foundation for the ratified backup
architecture (D1–D5 in
``docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md``
Part 2).

Scope of this package (Phase 1):

* a pure-Python ``asyncpg`` logical exporter (D1 — no Docker, no Supabase CLI,
  no ``pg_dump`` subprocess);
* a versioned artifact format with a manifest, catalog definition, table data,
  sequence state and integrity metadata;
* application-level authenticated encryption (D3 — AES-256-GCM) applied
  **before** the artifact reaches any storage;
* SHA-256 integrity support (plaintext and ciphertext semantics are distinct and
  documented);
* a narrow private object-storage **interface** plus local/in-memory providers
  (D2 — no production provider is selected, provisioned or contacted).

Explicitly **not** implemented here: restore (D4), scheduling, the admin UI,
Storage-object backup, and any production provisioning. See
``docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md``.
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
    BackupStorageError,
    BackupValidationError,
)
from backup.service import BackupRecord, BackupService
from backup.settings import (
    DENIED_SCHEMAS,
    DENIED_SCHEMA_OVERRIDE_PHRASE,
    BackupSettings,
    validate_schemas,
)
from backup.storage import InMemoryObjectStore, LocalFilesystemObjectStore, ObjectStore

__all__ = [
    "ARCHIVE_MEMBER_MANIFEST",
    "BACKUP_FORMAT_NAME",
    "BACKUP_FORMAT_VERSION",
    "DENIED_SCHEMAS",
    "DENIED_SCHEMA_OVERRIDE_PHRASE",
    "EXPORTER_VERSION",
    "BackupArtifactError",
    "BackupConfigurationError",
    "BackupError",
    "BackupExportError",
    "BackupIntegrityError",
    "BackupManifest",
    "BackupRecord",
    "BackupService",
    "BackupSettings",
    "BackupStorageError",
    "BackupValidationError",
    "InMemoryObjectStore",
    "LocalFilesystemObjectStore",
    "ObjectStore",
    "TableInventoryEntry",
    "validate_backup_id",
    "validate_schemas",
]
