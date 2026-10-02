"""Integrity verification of a stored backup artifact (§12) — no database needed.

An operator (and the Admin Dashboard's *Verify Backup* action) must be able to
answer one question about an artifact **without decrypting it into a scratch
database**: *is this object intact, and is it the artifact the queue recorded?*

Three independent checks, in increasing cost:

1. **ciphertext digest** — SHA-256 of the stored bytes compared against the value
   recorded in ``backup_jobs.checksum_sha256`` at creation. This proves the stored
   object is byte-identical to what was uploaded and needs no key at all.
2. **authenticated decryption** — the AES-256-GCM tag over the envelope header and
   ciphertext (a wrong key, a tampered header and a tampered body all fail).
3. **content checksums + manifest consistency** — every member listed in
   ``integrity/checksums.sha256`` must be present and match, and every table the
   manifest inventories must have its ``data/<schema>__<table>.copy`` member.

Nothing here mutates anything, and no plaintext is written anywhere: the decrypted
archive is held in memory and discarded.

The module deliberately reports *structured problems* rather than raising for
ordinary integrity failures — a verification result is evidence, and
"verified: false, problems: [...]" is more useful to an operator than a traceback.
Structural problems (not an envelope at all) still raise the typed errors from
:mod:`backup.errors`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from core.logging import get_logger

from backup import crypto
from backup.artifact import (
    ARCHIVE_MEMBER_CATALOG,
    ARCHIVE_MEMBER_MANIFEST,
    BACKUP_FORMAT_NAME,
    BACKUP_FORMAT_VERSION,
    read_archive,
    sha256_hex,
    verify_content_checksums,
)
from backup.errors import BackupArtifactError, BackupIntegrityError
from backup.storage import ObjectStore

logger = get_logger(__name__)


@dataclass(frozen=True)
class ArtifactVerification:
    """The outcome of verifying one stored artifact. **Contains no plaintext.**"""

    object_key: str
    verified: bool
    backup_id: Optional[str] = None
    format_version: Optional[int] = None
    exporter_version: Optional[str] = None
    key_id: Optional[str] = None
    compression: Optional[str] = None
    member_count: int = 0
    content_checksums_verified: int = 0
    table_count: int = 0
    manifest_total_rows: int = 0
    ciphertext_sha256: Optional[str] = None
    expected_ciphertext_sha256: Optional[str] = None
    ciphertext_matches_record: Optional[bool] = None
    problems: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_key": self.object_key,
            "verified": self.verified,
            "backup_id": self.backup_id,
            "format_version": self.format_version,
            "exporter_version": self.exporter_version,
            "key_id": self.key_id,
            "compression": self.compression,
            "member_count": self.member_count,
            "content_checksums_verified": self.content_checksums_verified,
            "table_count": self.table_count,
            "manifest_total_rows": self.manifest_total_rows,
            "ciphertext_sha256": self.ciphertext_sha256,
            "expected_ciphertext_sha256": self.expected_ciphertext_sha256,
            "ciphertext_matches_record": self.ciphertext_matches_record,
            "problems": list(self.problems),
        }


def verify_envelope(
    envelope: bytes,
    key: bytes,
    *,
    object_key: str = "local",
    compression: str = "gzip",
    expected_ciphertext_sha256: Optional[str] = None,
) -> ArtifactVerification:
    """Verify artifact bytes already in hand (no object store involved)."""
    problems: list[str] = []
    ciphertext_sha256 = sha256_hex(bytes(envelope))
    matches: Optional[bool] = None
    if expected_ciphertext_sha256:
        matches = ciphertext_sha256 == expected_ciphertext_sha256
        if not matches:
            problems.append("stored ciphertext digest does not match the recorded digest")

    members: dict[str, bytes] = {}
    manifest: dict[str, Any] = {}
    try:
        archive = crypto.decrypt(bytes(envelope), key)
        members = read_archive(archive, compression=compression)
        verify_content_checksums(members)
    except BackupArtifactError as exc:
        problems.append(f"artifact structure invalid: {exc.message}")
    except BackupIntegrityError as exc:
        problems.append(f"artifact failed authentication: {exc.message}")

    verified_checksums = len(members) - 1 if members else 0
    if members:
        manifest_raw = members.get(ARCHIVE_MEMBER_MANIFEST)
        catalog_raw = members.get(ARCHIVE_MEMBER_CATALOG)
        if manifest_raw is None:
            problems.append("archive is missing its manifest member")
        if catalog_raw is None:
            problems.append("archive is missing its catalog member")
        if manifest_raw is not None:
            try:
                manifest = json.loads(manifest_raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                problems.append("manifest member is not valid JSON")
                manifest = {}
            else:
                fmt = manifest.get("backup_format") or {}
                if fmt.get("name") != BACKUP_FORMAT_NAME:
                    problems.append("manifest does not declare a CarbonTally backup format")
                if fmt.get("version") != BACKUP_FORMAT_VERSION:
                    problems.append("manifest declares an unsupported format version")
                inventory = (manifest.get("inventory") or {}).get("tables") or []
                missing = sorted(
                    str(entry.get("data_member"))
                    for entry in inventory
                    if str(entry.get("data_member") or "") not in members
                )
                if missing:
                    problems.append(
                        f"{len(missing)} inventoried table(s) have no data member: "
                        + ", ".join(missing[:3])
                    )
    counts = (manifest.get("counts") or {}) if manifest else {}
    encryption = (manifest.get("encryption") or {}) if manifest else {}

    return ArtifactVerification(
        object_key=object_key,
        verified=not problems,
        backup_id=manifest.get("backup_id"),
        format_version=(manifest.get("backup_format") or {}).get("version"),
        exporter_version=manifest.get("exporter_version"),
        key_id=encryption.get("key_id"),
        compression=(manifest.get("compression") or {}).get("algorithm"),
        member_count=len(members),
        content_checksums_verified=verified_checksums,
        table_count=int(counts.get("tables") or 0),
        manifest_total_rows=int(counts.get("rows") or 0),
        ciphertext_sha256=ciphertext_sha256,
        expected_ciphertext_sha256=expected_ciphertext_sha256,
        ciphertext_matches_record=matches,
        problems=tuple(problems),
    )


async def verify_stored_artifact(
    store: ObjectStore,
    object_key: str,
    key: bytes,
    *,
    compression: str = "gzip",
    expected_ciphertext_sha256: Optional[str] = None,
) -> ArtifactVerification:
    """Fetch one stored object and verify it (read-only; never mutates storage)."""
    envelope = await store.get_object(object_key)
    return verify_envelope(
        envelope,
        key,
        object_key=object_key,
        compression=compression,
        expected_ciphertext_sha256=expected_ciphertext_sha256,
    )


__all__ = ["ArtifactVerification", "verify_envelope", "verify_stored_artifact"]