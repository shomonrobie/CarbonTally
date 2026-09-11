"""Backup artifact format: versioning, manifest, integrity and envelope parsing.

The artifact is a **deterministic tar archive** (normalised member metadata:
``mtime=0``, uid/gid 0, empty uname/gname, sorted member order, mode ``0o600``)
that is optionally gzip-compressed and finally **encrypted before it reaches any
storage** (D3).

Archive layout (inside the tar):

======================  ====================================================
Member                  Purpose
======================  ====================================================
``manifest.json``       format/version, identity, inventory, counts, checksums,
                        compression + encryption metadata, limitations
``catalog/catalog.json`` structured catalog extraction (authoritative for a
                        future restore implementation)
``catalog/ddl.sql``     best-effort reconstructed DDL (informational only)
``catalog/sequences.json`` sequence definitions **and** current state (OID-2)
``data/<schema>__<table>.copy``  PostgreSQL ``COPY … TO STDOUT`` text payload
``integrity/checksums.sha256``   ``<sha256>  <member path>`` lines, sorted
======================  ====================================================

Checksum semantics (three deliberately distinct values):

* **content checksums** — per-member SHA-256 in ``integrity/checksums.sha256``,
  computed over plaintext member bytes;
* **``archive_sha256``** — SHA-256 of the compressed *plaintext* archive, i.e.
  the bytes immediately before encryption; a restore verifies this after
  decryption;
* **``ciphertext_sha256``** — SHA-256 of the stored encrypted object, used to
  verify stored bytes without decrypting them.

A malformed or truncated artifact raises :class:`BackupArtifactError` and must
never be treated as a usable backup.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from backup.errors import BackupArtifactError, BackupValidationError
from backup.settings import DEFAULT_COMPRESSION_LEVEL

BACKUP_FORMAT_NAME = "carbontally-logical-backup"
BACKUP_FORMAT_VERSION = 1
EXPORTER_VERSION = "0.1.0"

ARCHIVE_MEMBER_MANIFEST = "manifest.json"
ARCHIVE_MEMBER_CATALOG = "catalog/catalog.json"
ARCHIVE_MEMBER_DDL = "catalog/ddl.sql"
ARCHIVE_MEMBER_SEQUENCES = "catalog/sequences.json"
ARCHIVE_MEMBER_CHECKSUMS = "integrity/checksums.sha256"
ARCHIVE_DATA_PREFIX = "data/"

#: Tar member metadata is normalised to these constants so two exports of the
#: same logical content produce byte-identical uncompressed archives.
_NORMALISED_MODE = 0o600
_NORMALISED_MTIME = 0

#: Documented limitations recorded in every manifest so a consumer knows exactly
#: what was and was not captured (see the Phase-1 implementation document).
MANIFEST_LIMITATIONS: tuple[str, ...] = (
    "Restore is not implemented in Phase 1; this artifact is export-only.",
    "Role definitions are captured as safe metadata only (no passwords/secrets).",
    "Extension internals are not dumped; extension names and versions are metadata.",
    "Storage objects (Supabase Storage) are NOT part of a database backup.",
    "Row ordering is deterministic only for tables that have a primary key.",
    "Data payloads use the PostgreSQL COPY text format (not the binary format).",
)


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex SHA-256 of ``data``."""
    return hashlib.sha256(data).hexdigest()


#: Backup identifiers are interpolated into storage object keys, so they are
#: restricted to a conservative allow-list (finding F10): ASCII letters/digits
#: first, then letters/digits/``_``/``-``. Dots are excluded, which removes
#: ``.``/``..`` path segments; separators, absolute paths, control characters and
#: leading punctuation cannot occur at all.
BACKUP_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def validate_backup_id(value: str) -> str:
    """Return ``value`` when it is a safe backup identifier, else raise.

    Args:
        value: caller-supplied backup identifier.

    Returns:
        The identifier unchanged.

    Raises:
        BackupValidationError: when the value is not a string, is empty, exceeds
            128 characters, or contains anything outside the allow-list (for
            example ``/``, ``\\``, ``..``, an absolute path, whitespace or a
            control character). Failing closed guarantees a backup identifier can
            never influence the storage key beyond a flat segment.
    """
    if not isinstance(value, str) or not BACKUP_ID_PATTERN.match(value):
        raise BackupValidationError(
            "backup_id must be 1-128 characters of [A-Za-z0-9_-] and start with a "
            "letter or digit; path separators, dots and control characters are not "
            "permitted",
            details={"length": len(value) if isinstance(value, str) else None},
        )
    return value


def utc_now() -> datetime:
    """Return the current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def isoformat_utc(moment: datetime) -> str:
    """Render a datetime as an explicit UTC ISO-8601 string (``…Z``)."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class TableInventoryEntry:
    """One exported table and how it was captured."""

    schema: str
    name: str
    data_member: str
    row_count: int
    has_primary_key: bool
    ordered_by_primary_key: bool
    column_count: int
    rls_enabled: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BackupManifest:
    """The manifest written as ``manifest.json`` inside the archive."""

    backup_id: str
    created_at: str
    exporter_version: str
    database_identity: dict[str, Any]
    inventory: dict[str, Any]
    counts: dict[str, Any]
    compression: dict[str, Any]
    encryption: dict[str, Any]
    integrity: dict[str, Any]
    requested_by: Optional[str] = None
    reason: Optional[str] = None
    limitations: tuple[str, ...] = field(default_factory=lambda: MANIFEST_LIMITATIONS)

    def as_dict(self) -> dict[str, Any]:
        return {
            "backup_format": {"name": BACKUP_FORMAT_NAME, "version": BACKUP_FORMAT_VERSION},
            "backup_id": self.backup_id,
            "created_at": self.created_at,
            "exporter_version": self.exporter_version,
            "requested_by": self.requested_by,
            "reason": self.reason,
            "database_identity": self.database_identity,
            "inventory": self.inventory,
            "counts": self.counts,
            "compression": self.compression,
            "encryption": self.encryption,
            "integrity": self.integrity,
            "limitations": list(self.limitations),
        }

    def to_json_bytes(self) -> bytes:
        """Serialise deterministically (sorted keys, UTF-8, trailing newline)."""
        return (
            json.dumps(self.as_dict(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")


def build_checksum_file(entries: dict[str, str]) -> bytes:
    """Render ``{member_path: sha256}`` as a sorted ``sha256sum``-style file."""
    lines = [f"{digest}  {path}" for path, digest in sorted(entries.items())]
    return ("\n".join(lines) + "\n").encode("utf-8")


def parse_checksum_file(payload: bytes) -> dict[str, str]:
    """Parse a checksum file back into ``{member_path: sha256}``."""
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BackupArtifactError("checksum file is not valid UTF-8") from exc
    result: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise BackupArtifactError("malformed checksum file line", details={"line": line})
        digest, path = parts[0].strip(), parts[1].strip()
        result[path] = digest
    return result


def build_archive(
    members: Iterable[tuple[str, bytes]],
    *,
    compression: str = "gzip",
    compression_level: int = DEFAULT_COMPRESSION_LEVEL,
) -> bytes:
    """Build the deterministic (optionally compressed) plaintext archive bytes.

    Args:
        members: ``(member_path, payload)`` pairs; stored in sorted-path order.
        compression: ``gzip`` or ``none``.
        compression_level: gzip level (1–9).

    Returns:
        Archive bytes (plaintext — encryption happens later, at the service
        boundary).
    """
    raw = _build_tar_bytes(members)
    if compression == "none":
        return raw
    if compression != "gzip":
        raise BackupArtifactError(
            "unsupported compression algorithm", details={"compression": compression}
        )
    import gzip

    buffer = io.BytesIO()
    # mtime=0 keeps gzip output deterministic (no embedded timestamp).
    with gzip.GzipFile(
        filename="", mode="wb", fileobj=buffer, compresslevel=compression_level, mtime=0
    ) as gz:
        gz.write(raw)
    return buffer.getvalue()


def _build_tar_bytes(members: Iterable[tuple[str, bytes]]) -> bytes:
    """Build a tar archive with fully normalised, deterministic metadata."""
    ordered = sorted(((path, payload) for path, payload in members), key=lambda item: item[0])
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.GNU_FORMAT) as tar:
        for path, payload in ordered:
            info = tarfile.TarInfo(name=path)
            info.size = len(payload)
            info.mode = _NORMALISED_MODE
            info.mtime = _NORMALISED_MTIME
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            tar.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def read_archive(archive: bytes, *, compression: str = "gzip") -> dict[str, bytes]:
    """Read every regular-file member of an archive into ``{path: payload}``.

    Raises:
        BackupArtifactError: when the archive is malformed or truncated.
    """
    if compression == "gzip":
        import gzip

        try:
            raw = gzip.decompress(archive)
        except (OSError, EOFError) as exc:
            raise BackupArtifactError("archive is not valid gzip data") from exc
    elif compression == "none":
        raw = archive
    else:
        raise BackupArtifactError(
            "unsupported compression algorithm", details={"compression": compression}
        )

    members: dict[str, bytes] = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                extracted = tar.extractfile(member)
                if extracted is None:  # pragma: no cover - defensive
                    continue
                members[member.name] = extracted.read()
    except tarfile.TarError as exc:
        raise BackupArtifactError("archive is not a valid tar stream") from exc
    return members


def verify_content_checksums(members: dict[str, bytes]) -> dict[str, str]:
    """Verify ``integrity/checksums.sha256`` against the archive members.

    Returns:
        The parsed ``{member: sha256}`` mapping on success.

    Raises:
        BackupArtifactError: when the checksum file is missing/malformed, a
            listed member is absent, or a member fails verification.
    """
    payload = members.get(ARCHIVE_MEMBER_CHECKSUMS)
    if payload is None:
        raise BackupArtifactError("archive is missing its checksum file")
    expected = parse_checksum_file(payload)
    for path, digest in expected.items():
        actual = members.get(path)
        if actual is None:
            raise BackupArtifactError(
                "archive member listed in checksums is missing", details={"member": path}
            )
        if sha256_hex(actual) != digest:
            raise BackupArtifactError(
                "archive member failed checksum verification", details={"member": path}
            )
    return expected

