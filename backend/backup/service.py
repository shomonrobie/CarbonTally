"""Backup orchestration (Phase 1 / Phase 1.1).

Sequence — and the order matters, because the storage boundary must only ever see
**ciphertext** (D2/D3):

1. validate the caller-supplied ``backup_id`` (F10) and the requested schemas (F2);
2. create an isolated temporary directory (``0o700``) under the configured root;
3. run the logical export inside one read-only snapshot (``backup.exporter``);
4. compute per-member SHA-256 checksums and write ``integrity/checksums.sha256``;
5. build the manifest (embedding content checksums, compression + encryption
   metadata, inventory, sequence/partition metadata and counts);
6. build the deterministic compressed archive and compute ``archive_sha256``;
7. **encrypt** the archive (AES-256-GCM) and compute ``ciphertext_sha256``;
8. hand the ciphertext to the object store;
9. verify the published object without assuming any provider digest (F11) —
   provider-declared SHA-256 when offered, plus an application read-back; on
   mismatch the object is discarded and a typed failure is raised;
10. delete the temporary directory on **every** exit path.

Failure behaviour: any exception removes the temporary directory and re-raises a
typed error. There is no code path in which a partially written artifact is
promoted to the object store, and none in which an unencrypted dump reaches
storage.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from core.logging import get_logger

from backup import crypto
from backup.artifact import (
    ARCHIVE_MEMBER_CHECKSUMS,
    BACKUP_FORMAT_NAME,
    BACKUP_FORMAT_VERSION,
    EXPORTER_VERSION,
    BackupManifest,
    build_archive,
    build_checksum_file,
    isoformat_utc,
    sha256_hex,
    utc_now,
    validate_backup_id,
)
from backup.errors import BackupIntegrityError
from backup.exporter import collect_members, export_schemas
from backup.settings import BackupSettings, validate_schemas
from backup.storage import ObjectStore, StoredObject, build_object_store

logger = get_logger(__name__)

OBJECT_KEY_PREFIX = "backups"


@dataclass(frozen=True)
class BackupRecord:
    """Metadata returned to the caller. **Contains no plaintext and no key.**"""

    backup_id: str
    object_key: str
    created_at: str
    format_version: int
    exporter_version: str
    archive_sha256: str
    ciphertext_sha256: str
    size_bytes: int
    table_count: int
    total_rows: int
    key_id: str
    compression: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "object_key": self.object_key,
            "created_at": self.created_at,
            "format_version": self.format_version,
            "exporter_version": self.exporter_version,
            "archive_sha256": self.archive_sha256,
            "ciphertext_sha256": self.ciphertext_sha256,
            "size_bytes": self.size_bytes,
            "table_count": self.table_count,
            "total_rows": self.total_rows,
            "key_id": self.key_id,
            "compression": self.compression,
        }


class BackupService:
    """Runs a single logical backup and stores it (encrypted) off-site."""

    def __init__(
        self,
        settings: BackupSettings,
        *,
        object_store: Optional[ObjectStore] = None,
        connection_factory: Optional[Any] = None,
    ) -> None:
        """
        Args:
            settings: resolved configuration (the encryption key is required).
            object_store: provider override (tests inject local/in-memory stores).
            connection_factory: async callable returning an ``asyncpg`` connection.
                Defaults to acquiring one from ``infra.supabase.get_service_pool()``.
        """
        self._settings = settings
        self._store = object_store or build_object_store(settings)
        self._connection_factory = connection_factory or _pool_connection_factory

    async def create_backup(
        self,
        *,
        requested_by: Optional[str] = None,
        reason: Optional[str] = None,
        created_at: Optional[datetime] = None,
        backup_id: Optional[str] = None,
    ) -> BackupRecord:
        """Create, encrypt and store one backup.

        Args:
            requested_by: acting identifier recorded in the manifest (metadata).
            reason: free-text reason recorded in the manifest (metadata).
            created_at: timestamp override used by determinism tests.
            backup_id: identifier override used by tests.

        Raises:
            BackupConfigurationError: the encryption key is not configured, or a
                credential-bearing schema was requested without the override (F2).
            BackupValidationError: the supplied ``backup_id`` is not a safe
                identifier (F10).
            BackupExportError: the snapshot/export failed.
            BackupStorageError: the provider rejected the upload.
            BackupIntegrityError: post-publication verification failed (F11).
        """
        key = self._settings.require_encryption_key()
        key_id = crypto.resolved_key_id(self._settings.key_id)
        # F10 / N1: only ``None`` means "not supplied"; an explicitly supplied value
        # (including the empty string) must reach the validator and fail closed.
        resolved_id = (
            validate_backup_id(backup_id) if backup_id is not None else uuid.uuid4().hex
        )
        # F2: defence in depth — the exporter validates too, but never depend on one
        # layer alone for a credential-exposure guard.
        validate_schemas(
            list(self._settings.schemas), allow_override=self._settings.allow_denied_schemas
        )
        moment = created_at or utc_now()

        temp_dir = tempfile.mkdtemp(prefix="ct_backup_", dir=self._settings.temp_root)
        os.chmod(temp_dir, 0o700)
        try:
            connection = await self._connection_factory()
            result = await export_schemas(
                connection,
                list(self._settings.schemas),
                output_dir=temp_dir,
                allow_denied_schemas=self._settings.allow_denied_schemas,
            )
            _write_checksums(temp_dir, _content_checksums(temp_dir))

            manifest = _build_manifest(
                settings=self._settings,
                result=result,
                backup_id=resolved_id,
                created_at=isoformat_utc(moment),
                key_id=key_id,
                requested_by=requested_by,
                reason=reason,
            )
            members = collect_members(temp_dir, manifest_json=manifest.to_json_bytes())
            return await self._publish(members, manifest, key, key_id)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def _publish(
        self,
        members: list[tuple[str, bytes]],
        manifest: BackupManifest,
        key: bytes,
        key_id: str,
    ) -> BackupRecord:
        """Archive, checksum, encrypt and store an artifact. Ciphertext only."""
        archive = build_archive(
            members,
            compression=self._settings.compression,
            compression_level=self._settings.compression_level,
        )
        archive_sha256 = sha256_hex(archive)

        envelope = crypto.encrypt(archive, key, key_id=key_id)
        ciphertext_sha256 = sha256_hex(envelope)

        object_key = (
            f"{OBJECT_KEY_PREFIX}/{manifest.backup_id}/"
            f"{BACKUP_FORMAT_NAME}-v{BACKUP_FORMAT_VERSION}.tar.gz.enc"
        )
        stored: StoredObject = await self._store.put_object(
            object_key,
            envelope,
            content_type="application/octet-stream",
            metadata={
                "backup_id": manifest.backup_id,
                "format_version": str(BACKUP_FORMAT_VERSION),
                "key_id": key_id,
                "ciphertext_sha256": ciphertext_sha256,
                "encrypted": "true",
            },
        )
        await self._verify_published(object_key, stored, ciphertext_sha256)

        record = BackupRecord(
            backup_id=manifest.backup_id,
            object_key=object_key,
            created_at=manifest.created_at,
            format_version=BACKUP_FORMAT_VERSION,
            exporter_version=EXPORTER_VERSION,
            archive_sha256=archive_sha256,
            ciphertext_sha256=ciphertext_sha256,
            size_bytes=len(envelope),
            table_count=int(manifest.counts.get("tables", 0)),
            total_rows=int(manifest.counts.get("rows", 0)),
            key_id=key_id,
            compression=self._settings.compression,
        )
        logger.info(
            "backup stored: id=%s tables=%d rows=%d bytes=%d key_id=%s",
            record.backup_id,
            record.table_count,
            record.total_rows,
            record.size_bytes,
            key_id,
        )
        return record



    async def _verify_published(
        self, object_key: str, stored: StoredObject, ciphertext_sha256: str
    ) -> None:
        """Verify a published object without assuming any provider digest (F11).

        Two independent checks, in order:

        1. **Provider-declared SHA-256** — compared only when the provider states
           that ``StoredObject.content_sha256`` is the application SHA-256 of the
           stored bytes. A provider ETag/MD5 is **never** compared against a
           SHA-256, so an incompatible provider cannot false-trip this guard.
        2. **Application read-back** — when ``verify_readback`` is enabled (default),
           the stored object is read back and its SHA-256 recomputed. This is
           provider-independent and authoritative.

        On any mismatch the just-published object is discarded (best effort) and a
        typed :class:`BackupIntegrityError` is raised, so a failed verification can
        never be reported as a successful backup.
        """
        if stored.content_sha256 and stored.content_sha256 != ciphertext_sha256:
            await self._discard_published(object_key)
            raise BackupIntegrityError(
                "provider-declared content SHA-256 does not match the uploaded ciphertext",
                details={"object_key": object_key},
            )
        if self._settings.verify_readback:
            payload = await self._store.get_object(object_key)
            if sha256_hex(payload) != ciphertext_sha256:
                await self._discard_published(object_key)
                raise BackupIntegrityError(
                    "stored object failed read-back SHA-256 verification",
                    details={"object_key": object_key},
                )
        if stored.provider_checksum:
            logger.info(
                "provider reported a native %s checksum for %s; it is recorded but "
                "never interpreted as a SHA-256",
                stored.provider_checksum_algorithm or "unspecified",
                object_key,
            )

    async def _discard_published(self, object_key: str) -> None:
        """Best-effort removal of a just-published object that failed verification.

        If the discard itself fails the object is orphaned; the log states clearly
        that it must not be treated as a successful backup, and the caller still
        receives a typed failure.
        """
        try:
            await self._store.delete_object(object_key)
            logger.warning(
                "discarded published object after failed verification: %s", object_key
            )
        except Exception as exc:  # noqa: BLE001 - cleanup must never mask the failure
            logger.error(
                "could not discard published object %s after failed verification (%s); "
                "it must NOT be treated as a successful backup",
                object_key,
                exc.__class__.__name__,
            )


def _build_manifest(
    *,
    settings: BackupSettings,
    result: Any,
    backup_id: str,
    created_at: str,
    key_id: str,
    requested_by: Optional[str],
    reason: Optional[str],
) -> BackupManifest:
    """Assemble the manifest from the export result (metadata only)."""
    catalog = result.catalog
    return BackupManifest(
        backup_id=backup_id,
        created_at=created_at,
        exporter_version=EXPORTER_VERSION,
        database_identity=catalog.identity,
        inventory={
            "schemas": catalog.schemas,
            "tables": [entry.as_dict() for entry in result.inventory],
            "sequences": result.sequence_states,
            "functions": [f"{item['schema']}.{item['name']}" for item in catalog.functions],
            "triggers": [
                f"{item['schema']}.{item['table_name']}.{item['trigger_name']}"
                for item in catalog.triggers
            ],
            "policies": [
                f"{item['schema']}.{item['table_name']}.{item['policy_name']}"
                for item in catalog.policies
            ],
            "views": [f"{item['schema']}.{item['name']}" for item in catalog.views],
            "extensions": [f"{item['name']}@{item['version']}" for item in catalog.extensions],
            "partitions": catalog.partitions,
        },
        counts={
            "tables": len(result.inventory),
            "rows": result.total_rows,
            "sequences": len(result.sequence_states),
            "functions": len(catalog.functions),
            "triggers": len(catalog.triggers),
            "policies": len(catalog.policies),
            "views": len(catalog.views),
            "partitions": len(catalog.partitions),
        },
        compression={"algorithm": settings.compression, "level": settings.compression_level},
        encryption={
            "algorithm": crypto.ALGORITHM,
            "envelope_version": crypto.ENVELOPE_VERSION,
            "key_id": key_id,
        },
        integrity={
            "content_checksums_file": ARCHIVE_MEMBER_CHECKSUMS,
            "archive_sha256_semantics": "SHA-256 of the compressed plaintext archive",
            "ciphertext_sha256_semantics": "SHA-256 of the stored encrypted envelope",
            "archive_sha256": "see BackupRecord.archive_sha256 for the authoritative value",
        },
        requested_by=requested_by,
        reason=reason,
    )


def _content_checksums(temp_dir: str) -> dict[str, str]:
    """SHA-256 for every member file (excluding the checksum file itself)."""
    checksums: dict[str, str] = {}
    for directory, _dirs, files in os.walk(temp_dir):
        for name in sorted(files):
            absolute = os.path.join(directory, name)
            relative = os.path.relpath(absolute, temp_dir).replace(os.sep, "/")
            if relative == ARCHIVE_MEMBER_CHECKSUMS:
                continue
            with open(absolute, "rb") as handle:
                checksums[relative] = hashlib.sha256(handle.read()).hexdigest()
    return checksums


def _write_checksums(temp_dir: str, checksums: dict[str, str]) -> None:
    """Write ``integrity/checksums.sha256`` into the staging directory."""
    path = os.path.join(temp_dir, ARCHIVE_MEMBER_CHECKSUMS)
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(build_checksum_file(checksums))
    os.chmod(path, 0o600)


async def _pool_connection_factory() -> Any:
    """Acquire a connection from the existing service-role pool.

    Reuses ``infra.supabase.get_service_pool()``; nothing new is introduced and no
    credential is read from anywhere but the environment.
    """
    from infra.supabase import get_service_pool

    pool = await get_service_pool()
    return await pool.acquire()


__all__ = ["BackupRecord", "BackupService", "OBJECT_KEY_PREFIX"]

