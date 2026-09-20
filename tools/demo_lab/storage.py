#!/usr/bin/env python3
"""DEMO-T3-IMP-001 (Scope A) — Demo Lab storage substrate.

The release application stores customer documents in Supabase Storage
(`services/storage.py` → `DOCUMENTS_BUCKET = "documents"`) and reads them back
through the same service client; B4 report artefacts use the private
`report-artifacts` bucket (`domain/report_artefact.ARTEFACT_BUCKET`). The Demo Lab
therefore needs the platform's `storage` schema **plus a storage API the lab
gateway can proxy**, bound to the lab database.

This module provides exactly that, using the platform's own abstraction rather
than bypassing the application layer:

1. the `storage` schema is cloned **structurally** (schema only, no rows) from the
   developer's local Supabase stack — the same technique T1 uses for `auth`;
2. the four approved D32 policies on `storage.objects` are created in the lab from
   the single source of truth (the D32 migration text);
3. the private `documents` and `report-artifacts` buckets are ensured;
4. a **lab-owned** storage-api container (same image as the stack) runs with
   ``DATABASE_URL`` pointed at ``carbontally_demo_local`` and its own file volume;
5. nothing is written to the stack database or to any other database.

Idempotent: re-running creates nothing twice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

#: Document bucket (backend/services/storage.py:26).
DOCUMENTS_BUCKET = "documents"
#: Frozen report-artefact bucket (backend/domain/report_artefact.py:24).
ARTEFACT_BUCKET = "report-artifacts"

#: Storage-api migration floor — mirrors the running stack container so the lab
#: schema is at the same revision (no drift, no surprise DDL).
FROZEN_MIGRATION = "optimize-existing-functions-again"

#: The four approved D32 policies (verbatim predicates from
#: supabase/migrations/20260823000000_d32_private_documents_storage.sql).
#: In the lab, `postgres` owns the freshly cloned storage schema, so the lab can
#: create them directly instead of needing Supabase's provider context.
D32_POLICIES: tuple[tuple[str, str], ...] = (
    ("d32_documents_select_org_member",
     "FOR SELECT TO authenticated USING (bucket_id = 'documents' "
     "AND (storage.foldername(name))[1] = 'uploads' "
     "AND (storage.foldername(name))[2]::uuid IN (SELECT organization_id "
     "FROM public.organization_members WHERE user_id = auth.uid() "
     "AND is_active = TRUE))"),
    ("d32_documents_insert_org_member",
     "FOR INSERT TO authenticated WITH CHECK (bucket_id = 'documents' "
     "AND (storage.foldername(name))[1] = 'uploads' "
     "AND (storage.foldername(name))[2]::uuid IN (SELECT organization_id "
     "FROM public.organization_members WHERE user_id = auth.uid() "
     "AND is_active = TRUE))"),
    ("d32_documents_update_org_member",
     "FOR UPDATE TO authenticated USING (bucket_id = 'documents' "
     "AND (storage.foldername(name))[1] = 'uploads' "
     "AND (storage.foldername(name))[2]::uuid IN (SELECT organization_id "
     "FROM public.organization_members WHERE user_id = auth.uid() "
     "AND is_active = TRUE))"),
    ("d32_documents_delete_org_member",
     "FOR DELETE TO authenticated USING (bucket_id = 'documents' "
     "AND (storage.foldername(name))[1] = 'uploads' "
     "AND (storage.foldername(name))[2]::uuid IN (SELECT organization_id "
     "FROM public.organization_members WHERE user_id = auth.uid() "
     "AND is_active = TRUE))"),
)


def psql_scalar(sql: str, db: str = lab.LAB_DB) -> str:
    return lab.psql_scalar(sql, db=db)


def psql_stdin(sql_text: str, db: str = lab.LAB_DB):
    """Apply SQL text through stdin (uses the stack's psql client)."""
    return lab.run(
        ["docker", "exec", "-i", lab.STACK_DB_CONTAINER, "psql", "-v", "ON_ERROR_STOP=0",
         "-q", "-U", lab.STACK_DB_USER, "-d", db],
        stdin_text=sql_text, timeout=900)


def storage_schema_present() -> bool:
    return psql_scalar(
        "SELECT count(*) FROM pg_namespace WHERE nspname = 'storage'") == "1"


def ensure_storage_schema() -> dict:
    """Clone the stack's ``storage`` schema structure into the lab database."""
    summary = {"cloned": False, "from": lab.STACK_STORAGE_CONTAINER,
               "tables_after": 0, "functions_after": 0}
    if storage_schema_present():
        summary["tables_after"] = int(psql_scalar(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema='storage'") or 0)
        summary["functions_after"] = int(psql_scalar(
            "SELECT count(*) FROM information_schema.routines WHERE routine_schema='storage'") or 0)
        return summary

    lab.ensure_dirs()
    dump_path = lab.GENERATED_DIR / "storage_schema.sql"
    dump = lab.run(
        ["docker", "exec", lab.STACK_DB_CONTAINER, "pg_dump", "-U", lab.STACK_DB_USER,
         "-d", "postgres", "--schema-only", "--schema=storage", "--no-owner",
         "--no-privileges"], timeout=600)
    if dump.returncode != 0 or len(dump.stdout) < 1000:
        raise RuntimeError(f"could not clone the storage schema: {dump.stderr[:300]}")
    dump_path.write_text(dump.stdout)
    applied = psql_stdin(dump.stdout)
    errors = [line for line in applied.stderr.splitlines()
              if "ERROR" in line and "already exists" not in line]
    if errors:
        raise RuntimeError(f"storage schema clone errors: {errors[:3]}")
    summary["cloned"] = True
    summary["tables_after"] = int(psql_scalar(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='storage'") or 0)
    summary["functions_after"] = int(psql_scalar(
        "SELECT count(*) FROM information_schema.routines WHERE routine_schema='storage'") or 0)
    summary["dump"] = str(dump_path)
    return summary


def ensure_storage_grants() -> dict:
    """Apply the platform's baseline storage grants (mirrors Supabase defaults).

    The schema clone deliberately omits privileges, so the roles PostgREST and the
    storage API switch into (``anon`` / ``authenticated`` / ``service_role``) need
    the same baseline the platform provides — otherwise the storage API answers
    ``permission denied for schema storage``.
    """
    if not storage_schema_present():
        return {"granted_roles": 0}
    lab.psql(
        "GRANT USAGE ON SCHEMA storage TO anon, authenticated, service_role; "
        "GRANT ALL ON ALL TABLES IN SCHEMA storage TO anon, authenticated, service_role; "
        "GRANT ALL ON ALL SEQUENCES IN SCHEMA storage TO anon, authenticated, service_role; "
        "GRANT ALL ON ALL FUNCTIONS IN SCHEMA storage TO anon, authenticated, service_role; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA storage GRANT ALL ON TABLES "
        "TO anon, authenticated, service_role; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA storage GRANT ALL ON FUNCTIONS "
        "TO anon, authenticated, service_role;")
    granted = int(psql_scalar(
        "SELECT count(DISTINCT grantee) FROM information_schema.role_usage_grants "
        "WHERE object_schema='storage' "
        "AND grantee IN ('anon','authenticated','service_role')") or 0)
    return {"granted_roles": granted}


def ensure_d32_policies() -> dict:
    """Create the four approved D32 policies on ``storage.objects`` (lab-only)."""
    if not storage_schema_present():
        return {"policies": 0, "skipped": "storage schema absent"}
    statements = []
    for name, clause in D32_POLICIES:
        statements.append(f'DROP POLICY IF EXISTS "{name}" ON storage.objects;')
        statements.append(f'CREATE POLICY "{name}" ON storage.objects {clause};')
    result = psql_stdin("\n".join(statements))
    errors = [line for line in result.stderr.splitlines()
              if "ERROR" in line and "does not exist" not in line]
    if errors:
        raise RuntimeError(f"D32 policy errors: {errors[:3]}")
    count = int(psql_scalar(
        "SELECT count(*) FROM pg_policies WHERE schemaname='storage' "
        "AND tablename='objects' AND policyname LIKE 'd32_documents_%'") or 0)
    if count != len(D32_POLICIES):
        raise RuntimeError(f"expected {len(D32_POLICIES)} D32 policies, found {count}")
    return {"policies": count,
            "names": [name for name, _ in D32_POLICIES],
            "anon_or_public_policies": int(psql_scalar(
                "SELECT count(*) FROM pg_policies WHERE schemaname='storage' "
                "AND tablename='objects' AND roles::text ~ 'anon|public'") or 0)}


def ensure_buckets() -> dict:
    """Ensure both private buckets exist (idempotent)."""
    if not storage_schema_present():
        return {"buckets": []}
    sql = (
        "INSERT INTO storage.buckets (id, name, public, file_size_limit, "
        "allowed_mime_types) VALUES "
        f"('{DOCUMENTS_BUCKET}', '{DOCUMENTS_BUCKET}', false, 52428800, NULL), "
        f"('{ARTEFACT_BUCKET}', '{ARTEFACT_BUCKET}', false, 52428800, NULL) "
        "ON CONFLICT (id) DO UPDATE SET public = false;")
    result = psql_stdin(sql)
    if "ERROR" in result.stderr:
        raise RuntimeError(f"bucket provisioning failed: {result.stderr.strip()[:300]}")
    rows = lab.psql(
        "SELECT id || '|' || public::text FROM storage.buckets "
        f"WHERE id IN ('{DOCUMENTS_BUCKET}','{ARTEFACT_BUCKET}') ORDER BY id")
    return {"buckets": [line for line in (rows.stdout or "").splitlines() if line.strip()]}


#: JWKS endpoint of the local stack GoTrue (lab authentication authority).
#: The lab GoTrue signs with **ES256** asymmetric keys, so a shared-secret-only
#: configuration cannot verify user tokens (B-2/O-A): the storage API is given the
#: JWKS URL in addition to the secret — verification is strengthened, never weakened.
JWKS_URL = f"http://{lab.STACK_AUTH_CONTAINER}:9999/.well-known/jwks.json"


def storage_env() -> list[str]:
    """Environment for the lab-owned storage-api container.

    Keys come from the lab's own local secret so tokens minted by the lab (or by
    the local GoTrue) validate here — the same pattern PostgREST already uses.
    """
    secret = lab.session_secret()
    db_url = (f"postgresql://{lab.STACK_DB_USER}:{lab.STACK_DB_PASSWORD}"
              f"@{lab.STACK_DB_CONTAINER}:5432/{lab.LAB_DB}")
    return [
        "-e", f"DATABASE_URL={db_url}",
        "-e", f"PGRST_JWT_SECRET={secret}",
        "-e", f"JWT_JWKS={JWKS_URL}",
        "-e", f"ANON_KEY={lab.anon_key(secret)}",
        "-e", f"SERVICE_KEY={lab.service_key(secret)}",
        "-e", "TENANT_ID=stub",
        "-e", "REGION=local",
        "-e", "STORAGE_BACKEND=file",
        "-e", "FILE_STORAGE_BACKEND_PATH=/mnt",
        "-e", "STORAGE_S3_REGION=local",
        "-e", "GLOBAL_S3_BUCKET=stub",
        "-e", f"DB_MIGRATIONS_FREEZE_AT={FROZEN_MIGRATION}",
        "-e", "VECTOR_ENABLED=false",
        "-e", "S3_PROTOCOL_ENABLED=false",
        "-e", "ENABLE_IMAGE_TRANSFORMATION=false",
        "-e", "FILE_SIZE_LIMIT=52428800",
        "-e", "UPLOAD_FILE_SIZE_LIMIT=52428800000",
        "-e", "SIGNED_UPLOAD_URL_EXPIRATION_TIME=7200",
        "-e", "TUS_URL_PATH=/storage/v1/upload/resumable",
    ]


def ensure_container() -> dict:
    """Start (or reconcile) the lab-owned storage-api container."""
    lab.ensure_dirs()
    state: dict = {}
    command = (["docker", "run", "-d", "--name", lab.STORAGE_CONTAINER,
                "--network", lab.STACK_NETWORK, "--restart", "unless-stopped",
                "-v", f"{lab.LAB_ID}_storage:/mnt"]
               + storage_env() + [lab.IMAGES["storage"]])
    spec_hash = hashlib.sha256(" ".join(command).encode()).hexdigest()[:16]
    saved = lab.load_state()
    if (lab.container_state(lab.STORAGE_CONTAINER) == "running"
            and saved.get(f"{lab.STORAGE_CONTAINER}_spec_hash") == spec_hash):
        state["already_running"] = True
    else:
        lab.run(["docker", "rm", "-f", lab.STORAGE_CONTAINER])
        result = lab.run(command, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"could not start storage: {result.stderr[:300]}")
        saved[f"{lab.STORAGE_CONTAINER}_spec_hash"] = spec_hash
        lab.save_state(saved)
        state["started"] = True
    state["spec_hash"] = spec_hash
    return state


def container_health(attempts: int = 30) -> dict:
    """Wait for the lab storage API to answer (``/version`` needs no apikey)."""
    import time
    last = None
    for _ in range(attempts):
        probe = lab.run(["docker", "exec", lab.GATEWAY_CONTAINER, "wget", "-q", "-O", "-",
                         f"http://{lab.STORAGE_CONTAINER}:5000/version"], timeout=60)
        last = f"{probe.stdout}\n{probe.stderr}".strip()
        if probe.returncode == 0 and probe.stdout.strip():
            return {"healthy": True, "version": probe.stdout.strip()[:40]}
        time.sleep(1)
    logs = lab.run(["docker", "logs", "--tail", "20", lab.STORAGE_CONTAINER], timeout=60)
    return {"healthy": False, "probe": (last or "")[-300:],
            "logs": (logs.stdout + logs.stderr)[-900:]}


def provision(include_container: bool = True) -> dict:
    """Full idempotent provisioning (schema → policies → buckets → container)."""
    summary = {"schema": ensure_storage_schema()}
    summary["grants"] = ensure_storage_grants()
    summary["d32"] = ensure_d32_policies()
    summary["buckets"] = ensure_buckets()
    if include_container:
        summary["container"] = ensure_container()
        summary["health"] = container_health()
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DEMO-T3-IMP-001 — ensure the Demo Lab storage substrate")
    parser.add_argument("--check", action="store_true",
                        help="report state only; change nothing")
    parser.add_argument("--skip-container", action="store_true")
    args = parser.parse_args()
    if args.check:
        summary = {
            "database": lab.LAB_DB,
            "storage_schema": storage_schema_present(),
            "storage_tables": int(psql_scalar(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema='storage'") or 0),
            "d32_policies": int(psql_scalar(
                "SELECT count(*) FROM pg_policies WHERE schemaname='storage' "
                "AND tablename='objects' AND policyname LIKE 'd32_documents_%'") or 0),
            "buckets": [line for line in (lab.psql(
                "SELECT id || '|' || public::text FROM storage.buckets "
                "ORDER BY id").stdout or "").splitlines() if line.strip()],
            "container_state": lab.container_state(lab.STORAGE_CONTAINER),
        }
    else:
        summary = provision(include_container=not args.skip_container)
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
