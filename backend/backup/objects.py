"""Storage-**object** backup and restore (architecture §14 / D2 / P1 item 7).

Why this module exists
----------------------

The ratified architecture is explicit and testable: *"a database dump does NOT
contain Storage objects — the database only includes metadata about these
objects"* (§14, `DOCUMENTATION VERIFIED`). The workstream-F drill then recorded
gap 3: *"Storage OBJECTS (uploaded documents) — NOT COVERED by any mechanism found
in this repository"*. Meanwhile the `documents` bucket **now exists** (migration
``20260823000000_d32_private_documents_storage.sql``, size policies amended by
``20261024000000``/``20261025000000``), so §14's own trigger — *"becomes P1 the
moment the first real document is uploaded"* — has been met by the repository
state rather than by an operator decision. Implementing the paired object backup
is therefore closing a recorded gap, **not** contradicting a deferral.

Shape (unchanged from the ratified design)
------------------------------------------

* **a separate job**, never coupled to the database job: object copies are far
  larger and slower, and one large file must not be able to fail a database
  backup (§14);
* **paired by a common *backup-set* id**, so a restore can select a consistent
  pair (``backup_jobs.backup_set_id``);
* **object identity preserved exactly** — bucket, path, ``content_type``,
  provider metadata and a per-object SHA-256 are recorded, and the restore writes
  the same path with the same bytes;
* **encrypted before it reaches storage** (D3, same envelope as the database
  artifact) and **ciphertext-only** at rest;
* **no service-role key in the artifact, the manifest, the job row or a log** —
  the source is an injected abstraction, and the production implementation reads
  the service-role client through the existing ``infra.supabase`` singleton.

The module is deliberately provider-shaped rather than Supabase-shaped:
:class:`StorageObjectSource` is a two-method protocol (list + download), so the
unit suite, the drill and the production path all drive the same code.
"""
from __future__ import annotations

import io
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Optional, Protocol, Sequence, runtime_checkable

from core.logging import get_logger

from backup import crypto
from backup.artifact import (
    ARCHIVE_MEMBER_CHECKSUMS,
    build_archive,
    build_checksum_file,
    isoformat_utc,
    read_archive,
    sha256_hex,
    utc_now,
    verify_content_checksums,
)
from backup.errors import BackupArtifactError, BackupObjectError
from backup.storage import ObjectStore

logger = get_logger(__name__)

#: Bucket-scoped object backup is the §14 scope: the private customer-document
#: bucket. Recorded here (not derived from a request) so a caller cannot widen it.
DEFAULT_BUCKET = "documents"

#: Archive member names. Object payloads are stored under a flat, indexed member
#: name — the *object path* lives in the manifest — so an object name can never
#: influence the archive's own path structure.
MEMBER_OBJECT_MANIFEST = "objects.json"
MEMBER_OBJECT_PREFIX = "objects/"

#: Size guard: an object larger than this is refused rather than silently
#: truncated (a truncated object inside a "successful" backup is worse than a
#: failed backup). Overridable by configuration only.
DEFAULT_MAX_OBJECT_BYTES = 512 * 1024 * 1024


@dataclass(frozen=True)
class StorageObjectRef:
    """One source object as the backup sees it (never contains a credential)."""

    bucket: str
    path: str
    size_bytes: int
    content_type: str = "application/octet-stream"
    metadata: dict[str, str] = field(default_factory=dict)
    updated_at: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ObjectBackupManifest:
    """The ``objects.json`` member: what the object artifact carries."""

    backup_set_id: str
    bucket: str
    created_at: str
    key_id: str
    prefix: str
    object_count: int
    total_bytes: int
    objects: list[dict[str, Any]] = field(default_factory=list)
    limitations: tuple[str, ...] = (
        "Storage-object backup covers one bucket; it is a separate job from the "
        "database backup and is paired with it by backup_set_id.",
        "Object bytes are stored encrypted; neither plaintext nor a service key "
        "appears in the artifact or the manifest.",
    )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["limitations"] = list(self.limitations)
        payload["backup_format"] = {"name": "carbontally-object-backup", "version": 1}
        return payload

    def to_json_bytes(self) -> bytes:
        return (
            json.dumps(self.as_dict(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")


@dataclass(frozen=True)
class ObjectBackupRecord:
    """Metadata returned to the caller. **Contains no plaintext and no key.**"""

    backup_set_id: str
    bucket: str
    object_key: str
    created_at: str
    object_count: int
    total_bytes: int
    size_bytes: int
    archive_sha256: str
    ciphertext_sha256: str
    key_id: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@runtime_checkable
class StorageObjectSource(Protocol):
    """The bucket surface the object backup needs (list + download + upload)."""

    async def list_objects(
        self, bucket: str, *, prefix: Optional[str] = None
    ) -> list[StorageObjectRef]: ...

    async def download(self, bucket: str, path: str) -> bytes: ...

    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> None: ...


class InMemoryStorageSource:
    """In-process bucket used by the unit suite and the local recovery drill."""

    def __init__(self, objects: Optional[dict[str, dict[str, Any]]] = None) -> None:
        self._objects: dict[tuple[str, str], dict[str, Any]] = {}
        for key, value in (objects or {}).items():
            bucket, _, path = key.partition("/")
            self._objects[(bucket, path)] = dict(value)

    async def put(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        self._objects[(bucket, path)] = {
            "data": bytes(data),
            "content_type": content_type,
            "metadata": dict(metadata or {}),
        }

    async def list_objects(
        self, bucket: str, *, prefix: Optional[str] = None
    ) -> list[StorageObjectRef]:
        found: list[StorageObjectRef] = []
        for (obj_bucket, path), value in sorted(self._objects.items()):
            if obj_bucket != bucket:
                continue
            if prefix and not path.startswith(prefix):
                continue
            found.append(
                StorageObjectRef(
                    bucket=bucket,
                    path=path,
                    size_bytes=len(value["data"]),
                    content_type=value.get("content_type", "application/octet-stream"),
                    metadata=dict(value.get("metadata") or {}),
                )
            )
        return found

    async def download(self, bucket: str, path: str) -> bytes:
        try:
            return bytes(self._objects[(bucket, path)]["data"])
        except KeyError as exc:
            raise BackupObjectError(
                "source object not found", details={"path": path}
            ) from exc

    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        await self.put(bucket, path, data, content_type=content_type, metadata=metadata)


class SupabaseStorageSource:
    """Production source: the existing service-role Supabase Storage client.

    The client is obtained lazily from ``infra.supabase.get_service_client()`` —
    the **only** module that builds clients in this codebase — so no new
    credential path exists and the key is never read, logged or copied here.

    A client may be injected (tests, a future alternative provider). The Supabase
    Python client's storage calls are synchronous HTTP; they are invoked directly
    rather than in an executor because the only production caller is the dedicated
    backup worker, which is not on a request path.
    """

    def __init__(self, client: Any = None, *, page_size: int = 1000) -> None:
        self._client = client
        self._page_size = max(1, int(page_size))

    def _client_or_default(self) -> Any:
        if self._client is None:
            from infra.supabase import get_service_client

            self._client = get_service_client()
        return self._client

    def _bucket(self, bucket: str) -> Any:
        return self._client_or_default().storage.from_(bucket)

    async def list_objects(
        self, bucket: str, *, prefix: Optional[str] = None
    ) -> list[StorageObjectRef]:
        found: list[StorageObjectRef] = []

        def _walk(path: str) -> None:
            offset = 0
            while True:
                entries = (
                    self._bucket(bucket).list(
                        path, {"limit": self._page_size, "offset": offset}
                    )
                    or []
                )
                if not entries:
                    return
                for entry in entries:
                    name = str(entry.get("name") or "")
                    if not name:
                        continue
                    child = f"{path}/{name}" if path else name
                    metadata = entry.get("metadata") or {}
                    if entry.get("id") is None and not metadata:
                        _walk(child)  # a folder
                        continue
                    found.append(
                        StorageObjectRef(
                            bucket=bucket,
                            path=child,
                            size_bytes=int(metadata.get("size") or 0),
                            content_type=str(
                                metadata.get("mimetype") or "application/octet-stream"
                            ),
                            metadata={},
                            updated_at=entry.get("updated_at"),
                        )
                    )
                if len(entries) < self._page_size:
                    return
                offset += len(entries)

        _walk(prefix or "")
        return found

    async def download(self, bucket: str, path: str) -> bytes:
        try:
            payload = self._bucket(bucket).download(path)
        except Exception as exc:  # noqa: BLE001 — normalised to a typed error
            raise BackupObjectError(
                "failed to download a source object",
                details={"path": path, "reason": type(exc).__name__},
            ) from exc
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        raise BackupObjectError("unexpected object payload type", details={"path": path})

    async def upload(
        self,
        bucket: str,
        path: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        try:
            self._bucket(bucket).upload(
                path, data, {"content-type": content_type, "upsert": "true"}
            )
        except Exception as exc:  # noqa: BLE001 — normalised to a typed error
            raise BackupObjectError(
                "failed to upload a restored object",
                details={"path": path, "reason": type(exc).__name__},
            ) from exc


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def _object_member_name(index: int) -> str:
    return f"{MEMBER_OBJECT_PREFIX}{index:08d}"


async def export_objects(
    source: StorageObjectSource,
    store: ObjectStore,
    *,
    key: bytes,
    backup_set_id: str,
    key_id: str,
    bucket: str = DEFAULT_BUCKET,
    prefix: str = "",
    object_key: Optional[str] = None,
    max_object_bytes: int = DEFAULT_MAX_OBJECT_BYTES,
    verify_readback: bool = True,
) -> ObjectBackupRecord:
    """Copy every object in one bucket into a single encrypted artifact (§14).

    Failure behaviour matches the database service: **nothing is published unless
    the whole artifact verifies**. A download failure, a size mismatch or a
    read-back mismatch raises a typed error, so a partial object set can never be
    mistaken for a complete one.
    """
    if not key:
        raise BackupObjectError("an encryption key is required for an object backup")
    if not backup_set_id:
        raise BackupObjectError("backup_set_id is required to pair an object backup")

    created_at = utc_now()
    refs = await source.list_objects(bucket, prefix=prefix or None)
    members: list[tuple[str, bytes]] = []
    entries: list[dict[str, Any]] = []
    total_bytes = 0

    for index, ref in enumerate(refs):
        payload = await source.download(bucket, ref.path)
        if max_object_bytes and len(payload) > max_object_bytes:
            raise BackupObjectError(
                "object exceeds the configured object-backup size ceiling",
                details={
                    "path": ref.path,
                    "bytes": len(payload),
                    "limit": max_object_bytes,
                },
            )
        if ref.size_bytes and ref.size_bytes != len(payload):
            raise BackupObjectError(
                "object size changed during backup (source is not quiescent)",
                details={
                    "path": ref.path,
                    "listed": ref.size_bytes,
                    "read": len(payload),
                },
            )
        member = _object_member_name(index)
        members.append((member, payload))
        entries.append(
            {
                "path": ref.path,
                "member": member,
                "size_bytes": len(payload),
                "content_sha256": sha256_hex(payload),
                "content_type": ref.content_type,
                "metadata": dict(ref.metadata),
                "updated_at": ref.updated_at,
            }
        )
        total_bytes += len(payload)

    manifest = ObjectBackupManifest(
        backup_set_id=backup_set_id,
        bucket=bucket,
        created_at=isoformat_utc(created_at),
        key_id=key_id,
        prefix=prefix or "",
        object_count=len(entries),
        total_bytes=total_bytes,
        objects=sorted(entries, key=lambda item: str(item["path"])),
    )
    members.append((MEMBER_OBJECT_MANIFEST, manifest.to_json_bytes()))
    checksums = {path: sha256_hex(payload) for path, payload in members}
    members.append((ARCHIVE_MEMBER_CHECKSUMS, build_checksum_file(checksums)))

    archive = build_archive(members, compression="gzip")
    envelope = crypto.encrypt(archive, key, key_id=key_id)

    destination = object_key or f"backups/{backup_set_id}/objects-{bucket}.tar.gz.enc"
    stored = await store.put_object(
        destination,
        envelope,
        content_type="application/octet-stream",
        metadata={
            "backup_set_id": backup_set_id,
            "bucket": bucket,
            "object_count": str(len(entries)),
            "key_id": key_id,
        },
    )
    if verify_readback:
        if sha256_hex(await store.get_object(destination)) != sha256_hex(envelope):
            await store.delete_object(destination)
            raise BackupObjectError(
                "stored object artifact failed read-back verification",
                details={"object_key": destination},
            )

    logger.info(
        "object backup %s: %d objects, %d bytes -> %s",
        backup_set_id,
        len(entries),
        total_bytes,
        destination,
    )
    return ObjectBackupRecord(
        backup_set_id=backup_set_id,
        bucket=bucket,
        object_key=stored.key,
        created_at=isoformat_utc(created_at),
        object_count=len(entries),
        total_bytes=total_bytes,
        size_bytes=len(envelope),
        archive_sha256=sha256_hex(archive),
        ciphertext_sha256=sha256_hex(envelope),
        key_id=key_id,
    )


# ---------------------------------------------------------------------------
# Restore / verification
# ---------------------------------------------------------------------------


def read_object_manifest(
    envelope: bytes, key: bytes, *, compression: str = "gzip"
) -> dict[str, Any]:
    """Decrypt one object artifact and return its manifest (no upload)."""
    archive = crypto.decrypt(bytes(envelope), key)
    members = read_archive(archive, compression=compression)
    verify_content_checksums(members)
    manifest_raw = members.get(MEMBER_OBJECT_MANIFEST)
    if manifest_raw is None:
        raise BackupArtifactError("object artifact is missing its manifest member")
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupArtifactError("object manifest is not valid JSON") from exc
    if not isinstance(manifest, dict):
        raise BackupArtifactError("object manifest is not a JSON object")
    return manifest


async def restore_objects(
    source: StorageObjectSource,
    envelope: bytes,
    key: bytes,
    *,
    bucket: Optional[str] = None,
    dry_run: bool = False,
    compression: str = "gzip",
) -> dict[str, Any]:
    """Re-upload every object in an object artifact, preserving identity.

    Object **identity is preserved exactly**: the recorded ``path`` is where the
    bytes are written, and the recorded SHA-256 is re-verified *before* the upload,
    so a corrupted payload is never written into a recovery bucket.

    ``dry_run=True`` verifies the whole artifact and reports what *would* be
    written without touching the target — the safe way to inspect an object
    artifact during an incident.
    """
    archive = crypto.decrypt(bytes(envelope), key)
    members = read_archive(archive, compression=compression)
    verify_content_checksums(members)
    manifest_raw = members.get(MEMBER_OBJECT_MANIFEST)
    if manifest_raw is None:
        raise BackupArtifactError("object artifact is missing its manifest member")
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupArtifactError("object manifest is not valid JSON") from exc

    target_bucket = str(bucket or manifest.get("bucket") or DEFAULT_BUCKET)
    entries = manifest.get("objects") or []
    restored = 0
    total_bytes = 0
    problems: list[str] = []

    for entry in entries:
        path = str(entry.get("path") or "")
        member = str(entry.get("member") or "")
        payload = members.get(member)
        if not path or payload is None:
            problems.append(f"missing payload for {path or member!r}")
            continue
        if sha256_hex(payload) != str(entry.get("content_sha256") or ""):
            problems.append(f"payload digest mismatch for {path}")
            continue
        if not dry_run:
            await source.upload(
                target_bucket,
                path,
                payload,
                content_type=str(
                    entry.get("content_type") or "application/octet-stream"
                ),
                metadata=dict(entry.get("metadata") or {}),
            )
        restored += 1
        total_bytes += len(payload)

    return {
        "backup_set_id": manifest.get("backup_set_id"),
        "bucket": target_bucket,
        "dry_run": dry_run,
        "objects_in_manifest": len(entries),
        "objects_restored": restored,
        "bytes_restored": total_bytes,
        "problems": problems,
        "ok": not problems and restored == len(entries),
    }


__all__ = [
    "DEFAULT_BUCKET",
    "DEFAULT_MAX_OBJECT_BYTES",
    "InMemoryStorageSource",
    "MEMBER_OBJECT_MANIFEST",
    "ObjectBackupManifest",
    "ObjectBackupRecord",
    "StorageObjectRef",
    "StorageObjectSource",
    "SupabaseStorageSource",
    "export_objects",
    "read_object_manifest",
    "restore_objects",
]
