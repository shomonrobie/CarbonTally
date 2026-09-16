"""Operator entrypoint for the existing Phase-1 backup exporter (M-2).

Bounded, thin wrapper around :class:`backup.service.BackupService` so an operator
can run **one** encrypted logical backup without adding an API route, an admin
UI, a scheduler or any new backup architecture. The exporter, artifact format,
encryption, integrity checks and fail-closed behaviour are all unchanged.

Safety contract (all enforced here, none relaxed):

* the destination is supplied explicitly and **must not** live inside the
  repository working tree (so an artifact can never be committed);
* a base64 32-byte ``CT_BACKUP_ENCRYPTION_KEY`` is mandatory — the export fails
  closed before the database is touched (``require_encryption_key``);
* the DSN is read from the environment by the existing application path
  (``DATABASE_URL``, fallback ``SUPABASE_DB_URL``) and is **never** printed;
* only the non-secret :class:`backup.service.BackupRecord` metadata is printed or
  written (its docstring guarantees "no plaintext and no key");
* a non-zero exit code is returned on any failure.

Usage (run from ``backend/``)::

    CT_BACKUP_ENCRYPTION_KEY=<base64-32-bytes> \
    DATABASE_URL=<session-pooler-dsn> \
    python -m tools.backup_export --destination /secure/backups --reason "pre-migration"
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from backup.errors import BackupError
from backup.service import BackupService
from backup.settings import BackupSettings

#: The repository working tree — artifacts must never be written inside it.
REPO_ROOT = Path(__file__).resolve().parents[2]

DSN_ENV_PRIMARY = "DATABASE_URL"
DSN_ENV_FALLBACK = "SUPABASE_DB_URL"
KEY_ENV = "CT_BACKUP_ENCRYPTION_KEY"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.backup_export",
        description=(
            "Run one encrypted CarbonTally logical backup with the existing "
            "Phase-1 exporter (operator entrypoint; no new backup architecture)."
        ),
    )
    parser.add_argument(
        "--destination",
        required=True,
        help="absolute directory for the encrypted artifacts (must be outside the repository)",
    )
    parser.add_argument(
        "--schema",
        action="append",
        default=None,
        help="schema to export (repeatable; default: CT_BACKUP_SCHEMAS or 'public')",
    )
    parser.add_argument("--key-id", default=None, help="non-secret key identifier (default key-v1)")
    parser.add_argument("--requested-by", default=None, help="acting operator identifier (metadata)")
    parser.add_argument("--reason", default=None, help="free-text reason recorded in the manifest")
    parser.add_argument(
        "--metadata-out",
        default=None,
        help="optional path to write the non-secret BackupRecord JSON (mode 0600)",
    )
    return parser


def _fail(message: str, code: int = 2) -> int:
    print(f"backup-export: {message}", file=sys.stderr)
    return code


def _guarded_destination(raw: str) -> Path:
    """Validate the destination before any work happens."""
    destination = Path(raw).expanduser()
    if not destination.is_absolute():
        raise ValueError("--destination must be an absolute path")
    resolved = destination.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ValueError(
            "--destination must be outside the repository working tree "
            f"({REPO_ROOT}) so artifacts are never committed"
        )
    if resolved == Path("/"):
        raise ValueError("--destination must not be the filesystem root")
    resolved.mkdir(parents=True, exist_ok=True)
    os.chmod(resolved, 0o700)
    return resolved


def _settings_from_args(args: argparse.Namespace, destination: Path) -> BackupSettings:
    env = dict(os.environ)
    env["CT_BACKUP_OBJECT_STORE"] = "local"
    env["CT_BACKUP_LOCAL_ROOT"] = str(destination)
    if args.key_id:
        env["CT_BACKUP_KEY_ID"] = args.key_id
    if args.schema:
        env["CT_BACKUP_SCHEMAS"] = ",".join(args.schema)
    # Any other CT_BACKUP_* value (compression, read-back verification, denied-schema
    # override) is taken from the environment untouched — never overridden here.
    return BackupSettings.from_env(env)


async def _run(args: argparse.Namespace, destination: Path) -> int:
    settings = _settings_from_args(args, destination)
    # Fail closed on a missing/invalid key BEFORE any database connection.
    settings.require_encryption_key()

    service = BackupService(settings)
    record = await service.create_backup(
        requested_by=args.requested_by or "operator:backup_export",
        reason=args.reason or "operator-invoked encrypted logical backup",
    )

    payload = record.as_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.metadata_out:
        metadata_path = Path(args.metadata_out).expanduser().resolve()
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        os.chmod(metadata_path, 0o600)
        print(f"metadata written: {metadata_path}")

    print(
        f"backup-export: OK backup_id={record.backup_id} tables={record.table_count} "
        f"rows={record.total_rows} bytes={record.size_bytes} key_id={record.key_id}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not any(os.environ.get(name) for name in (DSN_ENV_PRIMARY, DSN_ENV_FALLBACK)):
        return _fail(
            f"no database DSN in the environment; set {DSN_ENV_PRIMARY} "
            f"(fallback {DSN_ENV_FALLBACK})"
        )
    if not os.environ.get(KEY_ENV):
        return _fail(f"{KEY_ENV} is not set; an artifact must never be written unencrypted")

    try:
        destination = _guarded_destination(args.destination)
    except ValueError as exc:
        return _fail(str(exc))

    try:
        return asyncio.run(_run(args, destination))
    except BackupError as exc:
        return _fail(f"backup failed (fail-closed): {type(exc).__name__}: {exc}", code=3)
    except Exception as exc:  # noqa: BLE001 — never leak a traceback that may carry secrets
        return _fail(f"backup failed (unexpected): {type(exc).__name__}", code=4)


if __name__ == "__main__":
    sys.exit(main())
