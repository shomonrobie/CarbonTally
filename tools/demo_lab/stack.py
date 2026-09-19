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


def psql_stdin(sql_text: str, *, timeout: int = 900):
    """Run SQL through stdin (used for migrations and schema dumps)."""
    return lab.run(
        ["docker", "exec", "-i", lab.STACK_DB_CONTAINER, "psql", "-v", "ON_ERROR_STOP=0",
         "-q", "-U", lab.STACK_DB_USER, "-d", lab.LAB_DB],
        stdin_text=sql_text, timeout=timeout)


def ensure_database() -> dict:
    """Create the lab database and build the release schema in it."""
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

    # Gateway: the only container that publishes a host port (localhost only).
    conf = lab.GENERATED_DIR / "nginx.conf"
    conf.write_text(
        "server {\n"
        "  listen 80;\n"
        "  client_max_body_size 64m;\n"
        f"  location /auth/v1/ {{ proxy_pass http://{lab.STACK_AUTH_CONTAINER}:9999/;"
        " proxy_set_header Host $host; }\n"
        f"  location /rest/v1/ {{ proxy_pass http://{lab.POSTGREST_CONTAINER}:3000/;"
        " proxy_set_header Host $host; }\n"
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


def ensure_auth_bootstrap() -> dict:
    """Copy the Supabase auth-bootstrap base objects the lab needs (LOCAL only).

    GoTrue migrates its own tables but relies on Supabase's platform bootstrap for
    the ``auth`` schema, its enums (e.g. ``auth.code_challenge_method``) and the
    RLS helper functions (``auth.uid()`` …) that the release's policies call.
    Those are read (READ-ONLY) from the developer's local stack and applied to the
    lab database; the source stack is never modified.
    """
    lab.psql("CREATE SCHEMA IF NOT EXISTS auth")
    applied = {"enums": 0, "functions": 0, "enum_errors": [], "function_errors": []}

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
    summary["tables_after"] = lab.table_count()
    summary["auth_bootstrap"] = ensure_auth_bootstrap()
    summary["grants"] = ensure_grants()
    if not args.skip_containers:
        summary["containers"] = ensure_containers()
        summary["health"] = wait_healthy()
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
