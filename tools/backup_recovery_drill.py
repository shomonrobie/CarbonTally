#!/usr/bin/env python3
"""CarbonTally backup/recovery drill (workstream F) — real, disposable, repeatable.

Answers the only question that matters for recovery: **can CarbonTally get its data back?**
without touching any environment whose data matters.

PHASE 1  the project's OWN capability (``backend/backup``): run the D1 logical exporter and
         the production ``BackupService`` end to end, read the stored artifact back, verify
         the envelope/checksums, decrypt it, and report exactly what it contains and what it
         could rebuild (restore D4 is not implemented; the DDL member is informational).
PHASE 2  actual recovery with the platform's native tooling (``pg_dump``/``pg_restore``):
         dump the disposable source, restore into a FRESH disposable database, verify schema
         (tables/indexes/constraints/RLS policies), representative data and bucket config.
PHASE 3  the reconstruction must accept the shipped migrations (state compatibility).
PHASE 4  the application must run against the reconstruction (integration lifecycle suite).

Usage: python tools/backup_recovery_drill.py --source ct_step2_070

Safety: both names must be disposable (``ct_*`` or ``carbontally_test``) and must not look
like qa/demo/investor/prod/live. Nothing else is ever dropped or modified; production is
never contacted.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import pathlib
import subprocess
import sys
import time
import uuid

REPO = pathlib.Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
HOST = "postgresql://postgres:postgres@127.0.0.1:54426"
ADMIN = f"{HOST}/postgres"

_FORBIDDEN = ("qa", "demo", "investor", "prod", "live", "production")
_ALLOWED_MAINS = ("carbontally_test",)


def assert_disposable(name: str, role: str) -> str:
    lowered = name.lower()
    if lowered in _ALLOWED_MAINS:
        return name
    if not lowered.startswith("ct_"):
        raise SystemExit(
            f"refusing to use {role} database {name!r}: disposable names start with 'ct_' "
            f"or are one of {_ALLOWED_MAINS}"
        )
    for token in _FORBIDDEN:
        if token in lowered:
            raise SystemExit(
                f"refusing to use {role} database {name!r}: it looks like a persistent "
                f"environment ({token!r})"
            )
    return name


async def _connect(db: str):
    import asyncpg

    return await asyncpg.connect(f"{HOST}/{db}")


async def _drop_if_exists(db: str) -> None:
    import asyncpg

    admin = await asyncpg.connect(ADMIN)
    try:
        await admin.execute(f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)')
    finally:
        await admin.close()


async def _create_fresh(db: str) -> None:
    import asyncpg

    admin = await asyncpg.connect(ADMIN)
    try:
        await admin.execute(f'CREATE DATABASE "{db}"')
    finally:
        await admin.close()


def _runner(command: list[str]) -> tuple[int, str]:
    proc = subprocess.run(command, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()



async def _fingerprint(db: str) -> dict:
    """A comparable fingerprint of the schema and the data that matters."""
    conn = await _connect(db)
    try:
        tables = await conn.fetch(
            "SELECT c.relname AS name FROM pg_class c JOIN pg_namespace n "
            "ON n.oid = c.relnamespace WHERE n.nspname = 'public' "
            "AND c.relkind IN ('r','p') ORDER BY 1"
        )
        indexes = await conn.fetchval(
            "SELECT count(*) FROM pg_indexes WHERE schemaname = 'public'")
        constraints = await conn.fetchval(
            "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n "
            "ON n.oid = c.connamespace WHERE n.nspname = 'public'")
        rls_tables = await conn.fetchval(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relrowsecurity")
        policies = await conn.fetchval(
            "SELECT count(*) FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public'")
        counts = {}
        for row in tables:
            try:
                counts[row["name"]] = await conn.fetchval(
                    f'SELECT count(*) FROM public."{row["name"]}"')
            except Exception:  # noqa: BLE001
                counts[row["name"]] = -1
        buckets = await conn.fetchval("SELECT count(*) FROM storage.buckets")
        return {
            "tables": sorted(r["name"] for r in tables),
            "indexes": int(indexes or 0),
            "constraints": int(constraints or 0),
            "rls_tables": int(rls_tables or 0),
            "policies": int(policies or 0),
            "row_counts": counts,
            "buckets": int(buckets or 0),
        }
    finally:
        await conn.close()


async def phase1_project_backup(source: str, workdir: pathlib.Path) -> dict:
    """Run the shipped BackupService against the disposable source; verify the artifact."""
    sys.path.insert(0, str(BACKEND))
    import asyncpg  # noqa: E402

    from backup import crypto  # noqa: E402
    from backup.artifact import (  # noqa: E402
        ARCHIVE_DATA_PREFIX,
        ARCHIVE_MEMBER_CATALOG,
        ARCHIVE_MEMBER_DDL,
        ARCHIVE_MEMBER_MANIFEST,
        read_archive,
        verify_content_checksums,
    )
    from backup.service import BackupService  # noqa: E402
    from backup.settings import BackupSettings  # noqa: E402

    store_root = workdir / "object_store"
    store_root.mkdir(parents=True, exist_ok=True)
    drill_key = base64.b64encode(os.urandom(32)).decode()   # drill-only, never committed
    settings = BackupSettings.from_env({
        "CT_BACKUP_OBJECT_STORE": "local",
        "CT_BACKUP_LOCAL_ROOT": str(store_root),
        "CT_BACKUP_SCHEMAS": "public",
        "CT_BACKUP_ENCRYPTION_KEY": drill_key,
        "CT_BACKUP_VERIFY_READBACK": "1",
    })

    async def factory():
        return await asyncpg.connect(f"{HOST}/{source}")

    record = await BackupService(settings, connection_factory=factory).create_backup(
        requested_by="ct-step2-workstream-F-drill",
        reason="disposable recovery drill (local)",
        backup_id=uuid.uuid4().hex,
    )

    stored = sorted(p for p in store_root.rglob("*") if p.is_file())
    artifact_bytes = stored[0].read_bytes() if stored else b""
    envelope_metadata = crypto.read_envelope_metadata(artifact_bytes)
    plaintext = crypto.decrypt(artifact_bytes, settings.require_encryption_key())
    members = read_archive(plaintext, compression=settings.compression)
    verified = verify_content_checksums(members)
    manifest = json.loads(members[ARCHIVE_MEMBER_MANIFEST].decode("utf-8"))
    inventory = manifest.get("inventory") or {}
    counts = manifest.get("counts") or {}
    ddl_text = members.get(ARCHIVE_MEMBER_DDL, b"").decode("utf-8", "ignore")
    data_members = [name for name in members if name.startswith(ARCHIVE_DATA_PREFIX)]

    return {
        "backup_id": getattr(record, "backup_id", None),
        "artifact_object": str(stored[0].relative_to(store_root)) if stored else None,
        "artifact_bytes": len(artifact_bytes),
        "ciphertext_only": b"CarbonTally logical backup" not in artifact_bytes,
        "envelope": envelope_metadata,
        "members": len(members),
        "catalog_member": ARCHIVE_MEMBER_CATALOG in members,
        "ddl_member": ARCHIVE_MEMBER_DDL in members,
        "data_members": len(data_members),
        "checksums_verified": len(verified),
        "manifest_counts": counts,
        "manifest_inventory_schemas": inventory.get("schemas"),
        "manifest_policies": len(inventory.get("policies") or []),
        "manifest_triggers": len(inventory.get("triggers") or []),
        "manifest_functions": len(inventory.get("functions") or []),
        "ddl_can_rebuild": {
            "create_table": "CREATE TABLE" in ddl_text,
            "primary_key": "PRIMARY KEY" in ddl_text,
            "foreign_key": "FOREIGN KEY" in ddl_text or "REFERENCES" in ddl_text,
            "create_index": "CREATE INDEX" in ddl_text,
            "unique": "UNIQUE" in ddl_text,
            "rls_enabled": "ENABLE ROW LEVEL SECURITY" in ddl_text,
            "policy": "POLICY" in ddl_text,
        },
    }



async def phase2_platform_recovery(source: str, target: str, workdir: pathlib.Path) -> dict:
    """pg_dump the disposable source and restore it into a FRESH disposable database."""
    dump = workdir / f"{source}.dump"
    code, out = _runner(["pg_dump", "--format=custom", "--file", str(dump), f"{HOST}/{source}"])
    if code != 0:
        raise SystemExit(f"pg_dump failed: {out}")

    await _drop_if_exists(target)
    await _create_fresh(target)
    code, out = _runner([
        "pg_restore", "--no-owner", "--no-privileges",
        "--dbname", f"{HOST}/{target}", str(dump),
    ])
    errors = [] if code == 0 else [ln for ln in out.splitlines() if "error" in ln.lower()]

    source_fp = await _fingerprint(source)
    target_fp = await _fingerprint(target)
    mismatches = {
        table: (source_fp["row_counts"].get(table), target_fp["row_counts"].get(table))
        for table in source_fp["tables"]
        if source_fp["row_counts"].get(table, 0) > 0
        and source_fp["row_counts"].get(table) != target_fp["row_counts"].get(table)
    }
    return {
        "dump_bytes": dump.stat().st_size,
        "restore_returncode": code,
        "restore_errors": errors[:5],
        "source": {k: v for k, v in source_fp.items() if k != "row_counts"},
        "target": {k: v for k, v in target_fp.items() if k != "row_counts"},
        "missing_tables": sorted(set(source_fp["tables"]) - set(target_fp["tables"])),
        "row_count_mismatches": mismatches,
        "index_delta": target_fp["indexes"] - source_fp["indexes"],
        "constraint_delta": target_fp["constraints"] - source_fp["constraints"],
        "policy_delta": target_fp["policies"] - source_fp["policies"],
        "rls_table_delta": target_fp["rls_tables"] - source_fp["rls_tables"],
        "bucket_delta": target_fp["buckets"] - source_fp["buckets"],
    }


async def phase3_migrations_to_head(target: str) -> dict:
    """The restored database must accept the shipped migrations (state compatibility)."""
    migrations = sorted((REPO / "supabase" / "migrations").glob("*.sql"))
    conn = await _connect(target)
    applied, present, failed = 0, 0, []
    for path in migrations:
        try:
            async with conn.transaction():
                await conn.execute(path.read_text())
            applied += 1
        except Exception as exc:  # noqa: BLE001
            first = str(exc).splitlines()[0][:110]
            if "already exists" in first or "must be owner" in first:
                present += 1
            else:
                failed.append((path.name, first))
    await conn.close()
    return {"migrations": len(migrations), "applied": applied,
            "already_present": present, "failed": failed[:5]}


def phase4_app_check(target: str) -> dict:
    """The application must be able to run against the reconstruction."""
    env = dict(os.environ, INTEGRATION_DATABASE_URL=f"{HOST}/{target}")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/integration/test_f039_1_adjudication_lifecycle_runtime.py",
         "-q", "-p", "no:cacheprovider"],
        cwd=str(BACKEND), env=env, capture_output=True, text=True, timeout=900,
    )
    tail = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()][-2:]
    return {"returncode": proc.returncode, "summary": tail}



async def main() -> int:
    parser = argparse.ArgumentParser(description="CarbonTally backup/recovery drill")
    parser.add_argument("--source", default="ct_step2_070")
    parser.add_argument("--target", default=None)
    parser.add_argument("--skip-app-check", action="store_true")
    parser.add_argument("--keep-target", action="store_true")
    args = parser.parse_args()

    source = assert_disposable(args.source, "source")
    target = assert_disposable(
        args.target or f"{source}_restored_{int(time.time()) % 100000}", "target")
    if target == source:
        raise SystemExit("source and target must differ")

    workdir = pathlib.Path("/tmp") / f"ct_backup_drill_{target}"
    workdir.mkdir(parents=True, exist_ok=True)
    print(f"drill: source={source} target={target} workdir={workdir}", flush=True)

    print("\n== PHASE 1 — the project's own export capability ==", flush=True)
    for key, value in (await phase1_project_backup(source, workdir)).items():
        print(f"  {key}: {value}", flush=True)

    print("\n== PHASE 2 — platform recovery (pg_dump -> pg_restore) ==", flush=True)
    phase2 = await phase2_platform_recovery(source, target, workdir)
    for key in ("dump_bytes", "restore_returncode", "restore_errors", "missing_tables",
                "row_count_mismatches", "index_delta", "constraint_delta", "policy_delta",
                "rls_table_delta", "bucket_delta"):
        print(f"  {key}: {phase2[key]}", flush=True)
    print(f"  source: {phase2['source']}", flush=True)

    print("\n== PHASE 3 — the restored database accepts the shipped migrations ==", flush=True)
    print(f"  {await phase3_migrations_to_head(target)}", flush=True)

    if not args.skip_app_check:
        print("\n== PHASE 4 — the application runs against the reconstruction ==", flush=True)
        for key, value in phase4_app_check(target).items():
            print(f"  {key}: {value}", flush=True)

    if not args.keep_target:
        await _drop_if_exists(target)
        print(f"\ntarget {target} dropped (--keep-target to keep it)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
