"""Narrow private object-storage abstraction (D2 / OID-3).

This module deliberately implements **only an interface plus local providers**:

* :class:`ObjectStore` — the provider-neutral protocol;
* :class:`LocalFilesystemObjectStore` — a private local-directory provider used
  for local/disposable verification;
* :class:`InMemoryObjectStore` — an in-process provider for unit tests.

**No production provider is selected, provisioned or contacted**, no credentials
are created, and no cloud SDK is added (D2 / OID-3). A future implementation adds
a provider (for example an S3-compatible client) that satisfies the same
protocol; nothing else in the foundation changes.

The abstraction receives **ciphertext only** — the service encrypts before it
calls :meth:`ObjectStore.put_object` (see ``backup.service``).
"""
from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Protocol, runtime_checkable

from backup.errors import BackupStorageError
from backup.settings import BackupSettings

_DIR_MODE = 0o700
_FILE_MODE = 0o600


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class StoredObject:
    """Metadata about one stored object (never contains plaintext).

    Checksum semantics (F11) — the two digests are **not interchangeable**:

    ``content_sha256``
        The application's SHA-256 over the stored bytes. It is populated **only**
        when the provider contract guarantees a SHA-256 of the object content
        (the in-memory and local-filesystem providers read back what they wrote).
        A provider that cannot guarantee SHA-256 must leave this ``None``.
    ``provider_checksum`` / ``provider_checksum_algorithm``
        The provider's **native** value (an S3-style ETag, an MD5, …) together
        with the algorithm that produced it. Consumers must **never** compare
        this value against an application SHA-256.
    """

    key: str
    size_bytes: int
    created_at: str
    content_sha256: Optional[str] = None
    provider_checksum: Optional[str] = None
    provider_checksum_algorithm: Optional[str] = None
    content_type: str = "application/octet-stream"
    metadata: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
            "content_sha256": self.content_sha256,
            "provider_checksum": self.provider_checksum,
            "provider_checksum_algorithm": self.provider_checksum_algorithm,
            "content_type": self.content_type,
            "metadata": dict(self.metadata),
        }


@runtime_checkable
class ObjectStore(Protocol):
    """Provider-neutral object storage contract.

    Implementations must be safe for concurrent use and must never log or return
    the object body in error messages.
    """

    async def put_object(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> StoredObject:
        """Store ``data`` under ``key`` and return its metadata.

        The returned :class:`StoredObject` must populate ``content_sha256``
        **only** if the provider guarantees an application SHA-256 over the stored
        bytes. Any other provider-native digest belongs in ``provider_checksum``
        with its algorithm (F11) and must not be presented as SHA-256.
        """

    async def get_object(self, key: str) -> bytes:
        """Return the stored bytes for ``key``."""

    async def head_object(self, key: str) -> StoredObject:
        """Return metadata for ``key`` without transferring the body."""

    async def list_objects(self, prefix: str = "") -> list[StoredObject]:
        """List objects whose key starts with ``prefix`` (sorted by key)."""

    async def delete_object(self, key: str) -> None:
        """Delete ``key`` (idempotent)."""


class InMemoryObjectStore:
    """In-process object store used by unit tests."""

    def __init__(self) -> None:
        self._objects: dict[str, StoredObject] = {}
        self._bodies: dict[str, bytes] = {}

    async def put_object(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> StoredObject:
        stored = StoredObject(
            key=key,
            size_bytes=len(data),
            created_at=_now_iso(),
            content_sha256=hashlib.sha256(data).hexdigest(),
            content_type=content_type,
            metadata=dict(metadata or {}),
        )
        self._objects[key] = stored
        self._bodies[key] = data
        return stored

    async def get_object(self, key: str) -> bytes:
        try:
            return self._bodies[key]
        except KeyError as exc:
            raise BackupStorageError("object not found", details={"key": key}) from exc

    async def head_object(self, key: str) -> StoredObject:
        try:
            return self._objects[key]
        except KeyError as exc:
            raise BackupStorageError("object not found", details={"key": key}) from exc

    async def list_objects(self, prefix: str = "") -> list[StoredObject]:
        return [self._objects[key] for key in sorted(self._objects) if key.startswith(prefix)]

    async def delete_object(self, key: str) -> None:
        self._objects.pop(key, None)
        self._bodies.pop(key, None)


class LocalFilesystemObjectStore:
    """Private local-directory provider (local/disposable verification only).

    Security properties: the root and per-key directories are created ``0o700``,
    objects are written ``0o600`` through a temporary file and atomically
    published with :func:`os.replace`, and keys that would escape the root are
    rejected.
    """

    def __init__(self, root: str) -> None:
        self._root = os.path.abspath(root)
        os.makedirs(self._root, mode=_DIR_MODE, exist_ok=True)

    @property
    def root(self) -> str:
        return self._root

    async def put_object(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> StoredObject:
        path = self._path_for(key)
        directory = os.path.dirname(path)
        try:
            os.makedirs(directory, mode=_DIR_MODE, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(prefix=".ct-put-", dir=directory)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(data)
                os.chmod(tmp_path, _FILE_MODE)
                os.replace(tmp_path, path)
            finally:
                if os.path.exists(tmp_path):  # pragma: no cover - defensive
                    os.unlink(tmp_path)
        except OSError as exc:
            raise BackupStorageError(
                "failed to write object", details={"key": key, "reason": str(exc)}
            ) from exc
        return StoredObject(
            key=key,
            size_bytes=len(data),
            created_at=_now_iso(),
            content_sha256=hashlib.sha256(data).hexdigest(),
            content_type=content_type,
            metadata=dict(metadata or {}),
        )

    async def get_object(self, key: str) -> bytes:
        path = self._path_for(key)
        try:
            with open(path, "rb") as handle:
                return handle.read()
        except FileNotFoundError as exc:
            raise BackupStorageError("object not found", details={"key": key}) from exc
        except OSError as exc:
            raise BackupStorageError(
                "failed to read object", details={"key": key, "reason": str(exc)}
            ) from exc

    async def head_object(self, key: str) -> StoredObject:
        payload = await self.get_object(key)
        return StoredObject(
            key=key,
            size_bytes=len(payload),
            created_at=_now_iso(),
            content_sha256=hashlib.sha256(payload).hexdigest(),
        )

    async def list_objects(self, prefix: str = "") -> list[StoredObject]:
        found: list[StoredObject] = []
        for directory, _dirs, files in os.walk(self._root):
            for name in files:
                if name.startswith(".ct-put-"):
                    continue
                absolute = os.path.join(directory, name)
                key = os.path.relpath(absolute, self._root).replace(os.sep, "/")
                if not key.startswith(prefix):
                    continue
                try:
                    size = os.path.getsize(absolute)
                except OSError:  # pragma: no cover - race, defensive
                    continue
                found.append(
                    StoredObject(key=key, size_bytes=size, created_at=_now_iso())
                )
        return sorted(found, key=lambda item: item.key)

    async def delete_object(self, key: str) -> None:
        path = self._path_for(key)
        try:
            os.unlink(path)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise BackupStorageError(
                "failed to delete object", details={"key": key, "reason": str(exc)}
            ) from exc

    def _path_for(self, key: str) -> str:
        candidate = os.path.abspath(os.path.join(self._root, key))
        if candidate != self._root and not candidate.startswith(self._root + os.sep):
            raise BackupStorageError(
                "object key escapes the storage root", details={"key": key}
            )
        return candidate


def build_object_store(settings: BackupSettings) -> ObjectStore:
    """Construct the configured provider (local or in-memory).

    No production provider exists by design in Phase 1.
    """
    if settings.object_store == "memory":
        return InMemoryObjectStore()
    if settings.object_store == "local":
        return LocalFilesystemObjectStore(settings.local_root)
    raise BackupStorageError(
        "unsupported object store", details={"object_store": settings.object_store}
    )

