"""Unit tests for the backup artifact format (``backup.artifact``)."""
from __future__ import annotations

import json

import pytest

from backup.artifact import (
    ARCHIVE_MEMBER_CATALOG,
    ARCHIVE_MEMBER_CHECKSUMS,
    ARCHIVE_MEMBER_DDL,
    ARCHIVE_MEMBER_MANIFEST,
    ARCHIVE_MEMBER_SEQUENCES,
    BACKUP_FORMAT_NAME,
    BACKUP_FORMAT_VERSION,
    BackupManifest,
    build_archive,
    build_checksum_file,
    isoformat_utc,
    parse_checksum_file,
    read_archive,
    sha256_hex,
    verify_content_checksums,
)
from backup.errors import BackupArtifactError
from datetime import datetime, timezone


def _manifest(**overrides: object) -> BackupManifest:
    payload = {
        "backup_id": "bkp-1",
        "created_at": "2026-09-11T00:00:00Z",
        "exporter_version": "0.1.0",
        "database_identity": {"database": "postgres", "server_version": "17.6"},
        "inventory": {"tables": []},
        "counts": {"tables": 0, "rows": 0},
        "compression": {"algorithm": "gzip", "level": 6},
        "encryption": {"algorithm": "AES-256-GCM", "key_id": "test-key"},
        "integrity": {"content_checksums_file": ARCHIVE_MEMBER_CHECKSUMS},
    }
    payload.update(overrides)
    return BackupManifest(**payload)  # type: ignore[arg-type]


class TestManifest:
    def test_manifest_records_format_identity_and_version(self) -> None:
        manifest = _manifest()
        rendered = manifest.as_dict()
        assert rendered["backup_format"] == {
            "name": BACKUP_FORMAT_NAME,
            "version": BACKUP_FORMAT_VERSION,
        }
        assert rendered["exporter_version"] == "0.1.0"
        assert rendered["encryption"]["key_id"] == "test-key"

    def test_manifest_serialisation_is_sorted_and_stable(self) -> None:
        first = _manifest().to_json_bytes()
        second = _manifest().to_json_bytes()
        assert first == second
        keys = list(json.loads(first.decode("utf-8")).keys())
        assert keys == sorted(keys)
        assert first.endswith(b"\n")

    def test_manifest_declares_limitations(self) -> None:
        limitations = _manifest().as_dict()["limitations"]
        assert any("Restore is not implemented" in item for item in limitations)
        assert any("Storage objects" in item for item in limitations)

    def test_isoformat_is_utc_z(self) -> None:
        moment = datetime(2026, 9, 11, 12, 30, tzinfo=timezone.utc)
        assert isoformat_utc(moment) == "2026-09-11T12:30:00Z"


class TestChecksumFile:
    def test_build_and_parse_round_trip_is_sorted(self) -> None:
        payload = build_checksum_file({"b.txt": "22", "a.txt": "11"})
        assert payload.decode("utf-8").splitlines() == ["11  a.txt", "22  b.txt"]
        assert parse_checksum_file(payload) == {"a.txt": "11", "b.txt": "22"}

    def test_malformed_line_is_rejected(self) -> None:
        with pytest.raises(BackupArtifactError):
            parse_checksum_file(b"not-a-valid-line")


class TestArchive:
    def _members(self) -> list[tuple[str, bytes]]:
        return [
            (ARCHIVE_MEMBER_CATALOG, b'{"tables": []}\n'),
            (ARCHIVE_MEMBER_DDL, b"CREATE SCHEMA IF NOT EXISTS \"public\";\n"),
            (ARCHIVE_MEMBER_SEQUENCES, b"[]\n"),
            (ARCHIVE_MEMBER_MANIFEST, _manifest().to_json_bytes()),
        ]

    def test_archive_round_trip_gzip(self) -> None:
        archive = build_archive(self._members(), compression="gzip")
        members = read_archive(archive, compression="gzip")
        assert set(members) == {path for path, _ in self._members()}

    def test_archive_round_trip_uncompressed(self) -> None:
        archive = build_archive(self._members(), compression="none")
        members = read_archive(archive, compression="none")
        assert members[ARCHIVE_MEMBER_CATALOG] == b'{"tables": []}\n'

    def test_archive_is_deterministic_for_identical_input(self) -> None:
        first = build_archive(self._members(), compression="gzip")
        second = build_archive(list(reversed(self._members())), compression="gzip")
        assert first == second
        assert sha256_hex(first) == sha256_hex(second)

    def test_archive_is_sorted_by_member_path(self) -> None:
        archive = build_archive(self._members(), compression="none")
        assert archive.find(b"catalog/catalog.json") < archive.find(b"catalog/ddl.sql")

    def test_truncated_archive_is_rejected(self) -> None:
        archive = build_archive(self._members(), compression="gzip")
        with pytest.raises(BackupArtifactError):
            read_archive(archive[: len(archive) // 2], compression="gzip")

    def test_unsupported_compression_is_rejected(self) -> None:
        with pytest.raises(BackupArtifactError):
            build_archive(self._members(), compression="bzip2")


class TestContentChecksums:
    def _with_checksums(self) -> dict[str, bytes]:
        members = {
            ARCHIVE_MEMBER_CATALOG: b'{"tables": []}\n',
            ARCHIVE_MEMBER_DDL: b"CREATE SCHEMA;\n",
        }
        members[ARCHIVE_MEMBER_CHECKSUMS] = build_checksum_file(
            {path: sha256_hex(payload) for path, payload in members.items()}
        )
        return members

    def test_verification_accepts_intact_members(self) -> None:
        expected = verify_content_checksums(self._with_checksums())
        assert ARCHIVE_MEMBER_CATALOG in expected

    def test_verification_rejects_tampered_member(self) -> None:
        members = self._with_checksums()
        members[ARCHIVE_MEMBER_CATALOG] = b'{"tables": ["tampered"]}\n'
        with pytest.raises(BackupArtifactError):
            verify_content_checksums(members)

    def test_verification_rejects_missing_checksum_file(self) -> None:
        members = self._with_checksums()
        del members[ARCHIVE_MEMBER_CHECKSUMS]
        with pytest.raises(BackupArtifactError):
            verify_content_checksums(members)
