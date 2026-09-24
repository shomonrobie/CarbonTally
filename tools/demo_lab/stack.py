#!/usr/bin/env python3
"""DEMO-T1 — local Demo Lab stack: dedicated database + local REST/Auth/Gateway.

What it does (all LOCAL, all disposable):

1. creates a dedicated database ``carbontally_demo_local`` inside the developer's
   local Supabase cluster (no other database there is touched);
2. builds the **release schema** in it from ``supabase/migrations/*.sql`` (the
   authoritative source), plus the extensions those migrations require;
3. clones the GoTrue ``auth`` schema *structure* (no rows) from the local stack so
   authentication can run against the lab database;
4. starts three lab containers — PostgREST, GoTrue and an nginx gateway — on a
   single localhost-published port, so the release application resolves real
   identities through ``SUPABASE_URL=http://127.0.0.1:54430``.

Idempotent: re-running creates nothing twice and starts nothing twice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402
import storage as lab_storage  # noqa: E402


def psql_stdin(sql_text: str, *, timeout: int = 900):
    """Run SQL through stdin (used for migrations and schema dumps)."""
    return lab.run(
        ["docker", "exec", "-i", lab.STACK_DB_CONTAINER, "psql", "-v", "ON_ERROR_STOP=0",
         "-q", "-U", lab.STACK_DB_USER, "-d", lab.LAB_DB],
        stdin_text=sql_text, timeout=timeout)


def ensure_database() -> dict:
    """Create the lab database and build the release schema in it.

    DEMO-T1 ordering (P12 Step-2 correction, 2026-09-24):
    ``auth`` bootstrap → release migrations. The Supabase ``auth`` schema and its
    enums/RLS helpers (``auth.uid()`` …) are a *prerequisite* of the release
    migrations: ``20260803000000_rc2_rls.sql`` and every later RLS migration call
    ``auth.uid()``, so without ``auth`` the first RLS migration aborts its
    transaction and the whole migration chain cascades (every downstream
    ``public.is_org_member(uuid)`` RLS migration then fails). Previously
    ``ensure_auth_bootstrap`` ran *after* ``ensure_database``, which only worked
    because an already-provisioned database had ``auth`` from a prior pass.

    The storage substrate is now applied by :func:`main` AFTER the migrations:
    the four approved D32 policies reference ``public.organization_members``
    (created by the migrations) and ``ensure_d32_policies`` requires all four to
    exist, so on a fresh database the substrate cannot be created first. The
    D32 migration ``20260823000000_d32_private_documents_storage.sql`` validates
    the approved policy definitions when they are already present.
    """
    summary = {"created": False, "migration_files": 0, "migrations_with_errors": [],
               "migration_seconds": 0.0}
    if not lab.database_exists():
        result = lab.psql(f'CREATE DATABASE "{lab.LAB_DB}"', db="postgres")
        if result.returncode != 0 and "already exists" not in result.stderr:
            raise RuntimeError(f"could not create database: {result.stderr[:300]}")
        summary["created"] = True

    lab.psql(
        'CREATE SCHEMA IF NOT EXISTS extensions; '
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions; '
        'CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA extensions; '
        'CREATE EXTENSION IF NOT EXISTS "pg_trgm" WITH SCHEMA extensions;')

    # P12 Step-2 — the auth bootstrap MUST precede the release migrations.
    summary["auth_bootstrap"] = ensure_auth_bootstrap()

    import time
    started = time.monotonic()
    files = sorted(lab.MIGRATIONS_DIR.glob("*.sql"))
    summary["migration_files"] = len(files)
    for path in files:
        result = psql_stdin(path.read_text())
        # A migration that hits an existing object is tolerated (idempotent DDL);
        # any other error is recorded for the report rather than silently ignored.
        if "ERROR" in result.stderr:
            real = [line for line in result.stderr.splitlines()
                    if "ERROR" in line and "already exists" not in line
                    and "must be owner" not in line]
            if real:
                summary["migrations_with_errors"].append(
                    {"file": path.name, "errors": real[:2]})
    summary["migration_seconds"] = round(time.monotonic() - started, 1)
    return summary



# DR-003 — the lab's canonical browser origin: the CRA dev server the release frontend
# runs on. Mirrors `backend/config.py` ALLOWED_ORIGINS ("http://localhost:3000") and the
# local stack GoTrue `GOTRUE_SITE_URL`, so app, backend and gateway agree on one origin.
BROWSER_ORIGIN = "http://localhost:3000"


def _cors_headers() -> str:
    """Gateway-served CORS for the explicit browser origin (no wildcard).

    The local stack GoTrue validates the preflight's requested-headers list and drops
    `Access-Control-Allow-Origin` when the browser sends `apikey` (which supabase-js
    always does); the lab storage API behaves the same way. Serving preflight and the
    response headers here keeps the allowed origin explicit and deterministic without
    touching the shared auth/storage containers (DR-003).
    """
    return ("    proxy_hide_header Access-Control-Allow-Origin;\n"
            "    proxy_hide_header Vary;\n"
            "    add_header Access-Control-Allow-Origin $lab_cors_origin always;\n"
            "    add_header Access-Control-Expose-Headers"
            " \"content-length, content-range, x-total-count\" always;\n"
            "    add_header Vary \"Origin\" always;\n"
            "    if ($request_method = OPTIONS) {\n"
            "      add_header Access-Control-Allow-Origin $lab_cors_origin always;\n"
            "      add_header Access-Control-Allow-Methods"
            " \"GET, POST, PUT, PATCH, DELETE, OPTIONS\" always;\n"
            "      add_header Access-Control-Allow-Headers \"authorization, apikey,"
            " content-type, accept, x-client-info, x-supabase-api-version\" always;\n"
            "      add_header Access-Control-Max-Age 86400 always;\n"
            "      add_header Vary \"Origin, Access-Control-Request-Method,"
            " Access-Control-Request-Headers\" always;\n"
            "      return 204;\n"
            "    }\n")


def ensure_containers() -> dict:
    """Start the lab's PostgREST and gateway containers (idempotent).

    Authentication is delegated to the developer's **local stack GoTrue** (the same
    image, already healthy, and the only auth runtime whose ``auth`` schema matches
    this release's expectations): the gateway proxies ``/auth/v1`` there while
    ``/rest/v1`` serves the lab's own database. PostgREST is configured with the
    stack's JWT secret so tokens issued by GoTrue — or minted by the lab — validate
    everywhere.
    """
    lab.ensure_dirs()
    secret = lab.session_secret()
    state: dict = {"started": [], "restarted": [], "already_running": []}

    db_url = (f"postgres://{lab.STACK_DB_USER}:{lab.STACK_DB_PASSWORD}"
              f"@{lab.STACK_DB_CONTAINER}:5432/{lab.LAB_DB}")

    specs = {
        lab.POSTGREST_CONTAINER: [
            "docker", "run", "-d", "--name", lab.POSTGREST_CONTAINER,
            "--network", lab.STACK_NETWORK, "--restart", "unless-stopped",
            "-e", f"PGRST_DB_URI={db_url}",
            "-e", "PGRST_DB_SCHEMAS=public",
            "-e", "PGRST_DB_ANON_ROLE=anon",
            "-e", "PGRST_DB_EXTRA_SEARCH_PATH=public,extensions",
            "-e", f"PGRST_JWT_SECRET={secret}",
            "-e", "PGRST_SERVER_PORT=3000",
            lab.IMAGES["postgrest"]],
    }

    for name, command in specs.items():
        current = lab.container_state(name)
        spec_hash = hashlib.sha256(" ".join(command).encode()).hexdigest()[:16]
        state_file = lab.load_state()
        if current == "running" and state_file.get(f"{name}_spec_hash") == spec_hash:
            state["already_running"].append(name)
            continue
        # Config changed (or the container is absent/stopped) → recreate so the
        # running container always matches this script's declared configuration.
        lab.run(["docker", "rm", "-f", name])
        result = lab.run(command, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"could not start {name}: {result.stderr[:300]}")
        state_file[f"{name}_spec_hash"] = spec_hash
        lab.save_state(state_file)
        state["started"].append(name)

    # DEMO-T3-IMP-001 (Scope A) — the lab-owned storage API must be up BEFORE the
    # gateway is (re)created: nginx resolves the upstream name at startup.
    state["storage"] = lab_storage.ensure_container()
    state["storage_health"] = lab_storage.container_health()

    # Gateway: the only container that publishes a host port (localhost only).
    conf = lab.GENERATED_DIR / "nginx.conf"
    conf.write_text(
        # DR-003 — one explicit browser origin (no wildcard); $lab_cors_origin is empty
        # for any other origin, so unlisted callers receive no CORS grant.
        "map $http_origin $lab_cors_origin {\n"
        "  default \"\";\n"
        f"  \"{BROWSER_ORIGIN}\" $http_origin;\n"
        "}\n"
        "server {\n"
        "  listen 80;\n"
        "  client_max_body_size 64m;\n"
        f"  location /auth/v1/ {{\n{_cors_headers()}"
        f"    proxy_pass http://{lab.STACK_AUTH_CONTAINER}:9999/;\n"
        "    proxy_set_header Host $host;\n"
        "  }\n"
        f"  location /rest/v1/ {{ proxy_pass http://{lab.POSTGREST_CONTAINER}:3000/;"
        " proxy_set_header Host $host; }\n"
        f"  location /storage/v1/ {{\n{_cors_headers()}"
        f"    proxy_pass http://{lab.STORAGE_CONTAINER}:5000/;\n"
        "    proxy_set_header Host $host;\n"
        "    client_max_body_size 64m;\n"
        "  }\n"
        "  location / { return 404; }\n"
        "}\n")
    conf_hash = hashlib.sha256(conf.read_text().encode()).hexdigest()[:16]
    state_file = lab.load_state()
    mounted = lab.run(["docker", "inspect", "-f", "{{range .Mounts}}{{.Source}}{{end}}",
                       lab.GATEWAY_CONTAINER]).stdout.strip()
    if (lab.container_up(lab.GATEWAY_CONTAINER) and mounted == str(conf)
            and state_file.get("gateway_conf_hash") == conf_hash):
        state["already_running"].append(lab.GATEWAY_CONTAINER)
    else:
        lab.run(["docker", "rm", "-f", lab.GATEWAY_CONTAINER])
        result = lab.run([
            "docker", "run", "-d", "--name", lab.GATEWAY_CONTAINER,
            "--network", lab.STACK_NETWORK, "--restart", "unless-stopped",
            "-p", f"127.0.0.1:{lab.GATEWAY_PORT}:80",
            "-v", f"{conf}:/etc/nginx/conf.d/default.conf:ro",
            lab.IMAGES["gateway"]], timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"could not start gateway: {result.stderr[:300]}")
        state_file["gateway_conf_hash"] = conf_hash
        lab.save_state(state_file)
        state["started"].append(lab.GATEWAY_CONTAINER)
    return state


def _clone_auth_schema_structure() -> dict:
    """Clone the stack's ``auth`` schema **structure** into the lab database.

    P12 Step-2 correction (2026-09-24). ``provision.py`` mirrors the lab users'
    ids and e-mails into the lab database's ``auth.users`` to satisfy the release
    foreign keys (README §7 limitation 2), but nothing created that relation on a
    freshly created lab database: GoTrue owns ``auth`` and, as the README records,
    a fresh isolated ``auth`` schema cannot be bootstrapped by GoTrue itself. The
    previous lab database only had ``auth.users`` because an earlier provisioning
    attempt had run a lab-owned GoTrue which migrated the schema part-way.

    The stack's ``auth`` schema is therefore used as the structural source of
    truth — the same mechanism :mod:`storage` already uses for ``storage`` — and
    only structure is copied (``--schema-only``; no rows, no hashes, no sessions,
    no secrets). Idempotent: it does nothing when ``auth.users`` already exists.
    """
    if lab.psql_scalar("SELECT to_regclass('auth.users') IS NOT NULL") == "t":
        return {"cloned": False, "reason": "auth.users already present"}
    dump = lab.run(
        ["docker", "exec", lab.STACK_DB_CONTAINER, "pg_dump", "-U", lab.STACK_DB_USER,
         "-d", "postgres", "--schema-only", "--schema=auth", "--no-owner",
         "--no-privileges"], timeout=600)
    if dump.returncode != 0 or len(dump.stdout) < 1000:
        raise RuntimeError(f"could not clone the auth schema: {dump.stderr[:300]}")
    applied = psql_stdin(dump.stdout)
    errors = [line for line in applied.stderr.splitlines()
              if "ERROR" in line and "already exists" not in line]
    if errors:
        raise RuntimeError(f"auth schema clone errors: {errors[:3]}")
    return {"cloned": True, "tables_after": int(lab.psql_scalar(
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='auth'") or 0)}


def ensure_auth_bootstrap() -> dict:
    """Copy the Supabase auth-bootstrap base objects the lab needs (LOCAL only).

    GoTrue migrates its own tables but relies on Supabase's platform bootstrap for
    the ``auth`` schema, its enums (e.g. ``auth.code_challenge_method``) and the
    RLS helper functions (``auth.uid()`` …) that the release's policies call.
    Those are read (READ-ONLY) from the developer's local stack and applied to the
    lab database; the source stack is never modified.
    """
    lab.psql("CREATE SCHEMA IF NOT EXISTS auth")
    applied = {"structure": _clone_auth_schema_structure(),
               "enums": 0, "functions": 0, "enum_errors": [], "function_errors": []}


    for statement in lab.stack_auth_enum_ddl():
        guarded = ("DO $$ BEGIN " + statement + "; EXCEPTION WHEN duplicate_object "
                   "THEN NULL; END $$;")
        result = lab.psql(guarded)
        if "ERROR" in result.stderr and "duplicate_object" not in result.stderr:
            applied["enum_errors"].append(result.stderr.strip()[:160])
        else:
            applied["enums"] += 1

    for statement in lab.stack_auth_helper_function_ddl():
        result = lab.psql(statement.rstrip().rstrip(";") + ";")
        if "ERROR" in result.stderr:
            applied["function_errors"].append(result.stderr.strip()[:160])
        else:
            applied["functions"] += 1

    lab.psql("GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role; "
             "GRANT ALL ON ALL TABLES IN SCHEMA auth TO service_role; "
             "GRANT ALL ON ALL SEQUENCES IN SCHEMA auth TO service_role;")
    return applied


def ensure_grants() -> dict:
    """Apply the baseline schema grants a Supabase project normally provides.

    The release migrations create tables and RLS policies but rely on Supabase's
    project defaults for ``GRANT``s. Without them PostgREST answers
    "permission denied for table …" for every role. This grants the same baseline
    (RLS still applies to ``anon``/``authenticated``; ``service_role`` bypasses RLS
    by attribute, exactly as on Supabase).
    """
    lab.psql(
        "GRANT USAGE ON SCHEMA public, extensions TO anon, authenticated, service_role; "
        "GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role; "
        "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role; "
        "GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role; "
        "GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated; "
        "GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public "
        "TO authenticated; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT ON TABLES TO anon, authenticated;")
    granted = int(lab.psql_scalar(
        "SELECT count(DISTINCT grantee) FROM information_schema.role_table_grants "
        "WHERE table_schema='public' "
        "AND grantee IN ('anon','authenticated','service_role')") or 0)
    return {"roles_with_public_grants": granted}


def wait_healthy() -> dict:
    base = f"http://127.0.0.1:{lab.GATEWAY_PORT}"
    rest = lab.wait_for(f"{base}/rest/v1/", expect_in=(200, 401))
    auth = lab.wait_for(f"{base}/auth/v1/health", expect_in=(200,))
    return {"rest_status": rest, "auth_status": auth,
            "healthy": rest in (200, 401) and auth == 200}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure the local Demo Lab stack")
    parser.add_argument("--skip-containers", action="store_true")
    args = parser.parse_args()

    summary: dict = {"database": lab.LAB_DB,
                     "tables_before": lab.table_count() if lab.database_exists() else 0}
    summary["database_step"] = ensure_database()
    # P12 Step-2 ordering correction (2026-09-24) — the storage substrate (the
    # platform ``storage`` schema, the four approved D32 policies and the two
    # private buckets) is applied AFTER the release migrations: the D32 policies
    # reference ``public.organization_members``, which the migrations create, and
    # ``ensure_d32_policies`` requires all four to exist. The substrate still
    # precedes the containers, and the D32 migration validates the approved policy
    # definitions because they are already present.
    summary["storage_substrate"] = lab_storage.provision(include_container=False)
    summary["tables_after"] = lab.table_count()
    summary["grants"] = ensure_grants()

    if not args.skip_containers:
        summary["containers"] = ensure_containers()
        summary["health"] = wait_healthy()
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
