"""M-2 — operator backup entrypoint tests (pure; no database, no production).

Covers only the driver's own safety contract: the exporter itself keeps its
existing ``tests/unit/backup`` coverage.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import pytest

from tools import backup_export
from tools.backup_export import REPO_ROOT, build_parser, main

VALID_KEY = base64.b64encode(b"0123456789abcdef0123456789abcdef").decode()
DSN = "postgresql://operator:secret@127.0.0.1:1/nonexistent"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (backup_export.KEY_ENV, "DATABASE_URL", "SUPABASE_DB_URL"):
        monkeypatch.delenv(name, raising=False)


def _args(**overrides: object) -> list[str]:
    values = {"--destination": "/tmp/ct_backup_export_test"}
    values.update(overrides)
    argv: list[str] = []
    for key, value in values.items():
        argv += [key, str(value)]
    return argv


class TestFailClosed:
    def test_missing_dsn_is_refused(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(_args()) == 2
        assert "no database DSN" in capsys.readouterr().err

    def test_missing_key_is_refused(self, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        monkeypatch.setenv("DATABASE_URL", DSN)
        assert main(_args()) == 2
        assert backup_export.KEY_ENV in capsys.readouterr().err

    def test_destination_inside_repository_is_refused(
        self, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.setenv("DATABASE_URL", DSN)
        monkeypatch.setenv(backup_export.KEY_ENV, VALID_KEY)
        inside = REPO_ROOT / "backend" / "ct_p5_should_not_exist"
        assert main(["--destination", str(inside)]) == 2
        assert "outside the repository" in capsys.readouterr().err
        assert not inside.exists()

    def test_relative_destination_is_refused(
        self, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.setenv("DATABASE_URL", DSN)
        monkeypatch.setenv(backup_export.KEY_ENV, VALID_KEY)
        assert main(["--destination", "relative/backups"]) == 2
        assert "absolute" in capsys.readouterr().err


class TestDestinationGuard:
    def test_absolute_outside_repository_is_created_private(self, tmp_path: Path) -> None:
        target = tmp_path / "store"
        resolved = backup_export._guarded_destination(str(target))
        assert resolved == target.resolve()
        assert oct(resolved.stat().st_mode)[-3:] == "700"

    def test_filesystem_root_is_refused(self) -> None:
        with pytest.raises(ValueError):
            backup_export._guarded_destination("/")


class TestSettingsAndDryRun:
    def test_settings_map_argparse_to_existing_env_contract(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DATABASE_URL", DSN)
        monkeypatch.setenv(backup_export.KEY_ENV, VALID_KEY)
        args = build_parser().parse_args(
            ["--destination", str(tmp_path), "--schema", "public", "--key-id", "k7"]
        )
        settings = backup_export._settings_from_args(args, tmp_path)
        assert settings.object_store == "local"
        assert settings.local_root == str(tmp_path)
        assert list(settings.schemas) == ["public"]
        assert settings.key_id == "k7"
        assert settings.require_encryption_key() == base64.b64decode(VALID_KEY)

    def test_reused_exporter_is_invoked_and_only_metadata_is_printed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        monkeypatch.setenv("DATABASE_URL", DSN)
        monkeypatch.setenv(backup_export.KEY_ENV, VALID_KEY)
        created: dict[str, object] = {}

        class _FakeRecord:
            backup_id = "abc123"
            object_key = "backups/abc123/artifact.enc"
            created_at = "2026-09-16T00:00:00Z"
            format_version = 1
            exporter_version = "0.1.0"
            archive_sha256 = "a" * 64
            ciphertext_sha256 = "b" * 64
            size_bytes = 10
            table_count = 1
            total_rows = 2
            key_id = "key-v1"
            compression = "gzip"

            def as_dict(self) -> dict[str, object]:
                return {"backup_id": self.backup_id, "ciphertext_sha256": self.ciphertext_sha256}

        class _FakeService:
            def __init__(self, settings: object) -> None:
                created["settings"] = settings

            async def create_backup(self, **kwargs: object) -> _FakeRecord:
                created["kwargs"] = kwargs
                return _FakeRecord()

        monkeypatch.setattr(backup_export, "BackupService", _FakeService)
        metadata = tmp_path / "record.json"
        exit_code = main(
            _args(
                **{
                    "--destination": str(tmp_path),
                    "--reason": "rehearsal",
                    "--requested-by": "operator:test",
                    "--metadata-out": str(metadata),
                }
            )
        )
        assert exit_code == 0
        assert created["kwargs"] == {"requested_by": "operator:test", "reason": "rehearsal"}
        printed = capsys.readouterr().out
        assert "backup-export: OK backup_id=abc123" in printed
        assert VALID_KEY not in printed
        assert DSN not in printed
        assert os.stat(metadata).st_mode & 0o777 == 0o600
        assert json.loads(metadata.read_text())["backup_id"] == "abc123"
