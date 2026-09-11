#!/usr/bin/env python3
"""Database QA runner (read-only) — spec §8, §34.

Executes the read-only DB audits against the configured Postgres. If the
database is unreachable or the driver is missing, prints
``SKIPPED — DATABASE UNREACHABLE`` / ``SKIPPED — TOOL UNAVAILABLE`` and exits
with a distinct code instead of crashing.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, List, Optional
from urllib.parse import quote

from qa_harness.core.config import load_config
from qa_harness.core.findings import FindingClassification, FindingStatus
from qa_harness.core.status import ToolUnavailable
from qa_harness.db import (
    ConstraintAudit,
    IndexAudit,
    IntegrityAudit,
    MigrationAudit,
    RlsAudit,
    SchemaInventory,
    SchemaProbe,
)
from qa_harness.scripts.common import HARNESS_ROOT, add_common_args, load_env_file
from qa_harness.scripts.preflight import git_sha

EXIT_OK = 0
EXIT_SKIPPED = 3
EXIT_FAIL = 1

try:
    import psycopg2  # type: ignore
    _PSYCOPG2 = True
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore
    _PSYCOPG2 = False


def _resolve_dsn(env: Any = None) -> str:
    """Resolve a read-only Postgres DSN from the environment — never a guess.

    Precedence (V1.2 calibration):

    1. ``SUPABASE_DB_URL`` — alias kept for backward compatibility.
    2. the environment's ``postgres_dsn_env`` (local: ``DATABASE_URL``).
    3. structured build from ``POSTGRES_PASSWORD`` plus optional
       ``POSTGRES_USER`` / ``POSTGRES_HOST`` / ``POSTGRES_PORT`` /
       ``POSTGRES_DB``. Component defaults come from environments.yaml
       (local Supabase stack: postgres@127.0.0.1:54426/postgres).

    The password is never logged or echoed; the returned DSN is only ever
    passed straight to ``psycopg2.connect``.
    """
    dsn_env = (env.postgres_dsn_env if env and env.postgres_dsn_env
               else "DATABASE_URL")
    url = os.environ.get("SUPABASE_DB_URL") or os.environ.get(dsn_env)
    if url:
        return url
    password = os.environ.get("POSTGRES_PASSWORD")
    if password:
        user = os.environ.get("POSTGRES_USER", "postgres")
        host = os.environ.get(
            "POSTGRES_HOST",
            env.postgres_host if env and env.postgres_host else "127.0.0.1",
        )
        port = os.environ.get(
            "POSTGRES_PORT",
            str(env.postgres_port) if env and env.postgres_port else "54426",
        )
        db = os.environ.get(
            "POSTGRES_DB",
            env.postgres_db if env and env.postgres_db else "postgres",
        )
        return f"postgresql://{user}:{quote(password, safe='')}@{host}:{port}/{db}"
    missing = [dsn_env] if dsn_env != "DATABASE_URL" else ["SUPABASE_DB_URL", "DATABASE_URL"]
    raise ToolUnavailable(
        "database url",
        f"{' / '.join(missing)} (or POSTGRES_PASSWORD for the local Supabase "
        "stack: postgres@127.0.0.1:54426/postgres) not set",
    )


def _dsn_from_supabase_status(env: Any = None, config: Any = None) -> Optional[str]:
    """Optional auto-discovery of the LOCAL Supabase stack's DB URL.

    Uses the operator's own ``supabase status`` CLI (JSON output) and extracts
    ONLY the ``DB_URL`` field. Restricted to the ``local`` environment and
    gated by ``database.allow_supabase_status_discovery`` in qa_config.yaml.
    The raw CLI output contains API keys; it is parsed in-process and never
    logged, stored, or returned. Returns ``None`` when unavailable.
    """
    if not (env and env.name == "local"):
        return None
    main = (config.raw.get("qa_config.yaml", {})
            if config and hasattr(config, "raw") else {})
    if not main.get("database", {}).get("allow_supabase_status_discovery"):
        return None
    import json
    import shutil
    import subprocess
    cli = shutil.which("supabase")
    if not cli:
        return None
    try:
        proc = subprocess.run(
            [cli, "status", "--output", "json"],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode != 0:
            return None
        data = json.loads(proc.stdout)
    except Exception:
        return None
    url = data.get("DB_URL") if isinstance(data, dict) else None
    return url if isinstance(url, str) and url.startswith("postgresql") else None


def _resolve_connection(env: Any = None, config: Any = None) -> Any:
    """Resolve (dsn, source_label) without ever printing the credential.

    DSN precedence: SUPABASE_DB_URL → DATABASE_URL (postgres_dsn_env) →
    POSTGRES_PASSWORD structured build → local ``supabase status`` discovery.
    """
    if not _PSYCOPG2:
        raise ToolUnavailable("psycopg2", "pip install psycopg2-binary")
    try:
        return _resolve_dsn(env), "environment"
    except ToolUnavailable:
        dsn = _dsn_from_supabase_status(env, config)
        if dsn:
            return dsn, "local supabase status discovery"
        raise


def _write_db_evidence(ctx: Any, *, probed: Any, integrity_results: Dict[str, int],
                       no_rls: List[str], index_missing: List[Any],
                       constraint_violations: List[Any], migration_summary: Dict[str, object],
                       inventory: Any) -> None:
    """Persist DB evidence ONLY from a completed, successful collection.

    Evidence is never written from a failed or partial query run: this helper
    is invoked only after every probe completed (see run_db). All payloads
    pass through the redactor so a stray value can never leak a secret.
    """
    import json

    def _table_dict(info: Any) -> Dict[str, object]:
        return {
            "columns": len(info.columns),
            "column_types": info.column_types,
            "primary_key": info.primary_key,
            "foreign_keys": info.foreign_keys,
            "unique_constraints": info.unique_constraints,
            "check_constraints": info.check_constraints,
            "indexes": info.indexes,
            "triggers": info.triggers,
            "rls_enabled": info.rls_enabled,
            "rls_forced": info.rls_forced,
        }

    schema = {
        "tables_probed": len(probed),
        "expected_tables": len(inventory.expected_tables),
        "missing_tables": inventory.missing_tables(probed),
        "missing_columns": inventory.missing_columns(probed),
        "tables": {name: _table_dict(info) for name, info in sorted(probed.items())},
    }
    rls = {
        "tables_without_rls": no_rls,
        "rls_state": {
            name: {"enabled": info.rls_enabled, "forced": info.rls_forced}
            for name, info in sorted(probed.items())
        },
    }
    integrity = {
        rule_id: (count if count >= 0 else "rule could not run (e.g. missing table)")
        for rule_id, count in sorted(integrity_results.items())
    }
    indexes = {
        "missing": [
            {"table": exp.table, "column": exp.column, "reason": exp.reason,
             "severity": exp.severity}
            for exp in index_missing
        ]
    }
    constraints = {
        "violations": [
            {"kind": exp.kind, "table": exp.table, "name": exp.name,
             "severity": exp.severity, "reason": exp.reason}
            for exp in constraint_violations
        ]
    }
    payloads = {
        "db_schema": schema,
        "db_rls": rls,
        "db_integrity": integrity,
        "db_indexes": indexes,
        "db_constraints": constraints,
        "db_migrations": dict(migration_summary),
    }
    for name, payload in payloads.items():
        path = ctx.evidence.write(
            "db", ctx.run_id, "db", name,
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            ext="json",
        )
        print(f"    evidence: {path.relative_to(ctx.evidence.base_dir)}")


def run_db(args: argparse.Namespace, ctx: Any = None) -> int:
    config = load_config(HARNESS_ROOT / "config")
    env_name = args.env or config.default_environment
    env = config.environment(env_name)
    print(f"DB QA — environment: {env_name}")
    owned_ctx = ctx is None
    if ctx is None:
        from qa_harness.core.run_context import RunContext
        ctx = RunContext(env=env, env_name=env_name, git_sha=git_sha(),
                         read_only=args.read_only)
    try:
        dsn, dsn_source = _resolve_connection(env, config)
        connection = psycopg2.connect(dsn)  # type: ignore[call-arg]
    except ToolUnavailable as exc:
        print(f"SKIPPED — TOOL UNAVAILABLE ({exc.tool}: {exc.reason})")
        if owned_ctx:
            ctx.emit_skipped("DB", "Database QA unavailable",
                             reason=str(exc), source="run_db.py")
            ctx.finish()
        return EXIT_SKIPPED
    except Exception as exc:
        print(f"SKIPPED — DATABASE UNREACHABLE ({exc})")
        if owned_ctx:
            ctx.emit_skipped("DB", "Database QA unavailable",
                             reason=str(exc), source="run_db.py")
            ctx.finish()
        return EXIT_SKIPPED
    print(f"  database connection: {dsn_source} (read-only)")

    exit_code = EXIT_OK
    # A failure while COLLECTING (a query error, a harness bug, a missing
    # extension) is a harness/tool failure — never an application finding and
    # never evidence from a partial result. Only a fully completed collection
    # may emit findings + evidence.
    try:
        with connection:
            probed = SchemaProbe(connection).probe()
            inventory = SchemaInventory()
            missing = inventory.missing_tables(probed)
            missing_cols = inventory.missing_columns(probed)
            integrity = IntegrityAudit(connection)
            results = integrity.run()
            rls = RlsAudit()
            no_rls = rls.tables_without_rls(probed)
            index_audit = IndexAudit()
            index_missing = index_audit.missing_indexes(probed)
            constraint_audit = ConstraintAudit()
            constraint_violations = constraint_audit.violations(probed)
            migrations = MigrationAudit(HARNESS_ROOT.parent / "supabase" / "migrations")
            migration_summary = migrations.summary(connection=connection)

            # All queries completed — the collection is trustworthy. Now the
            # deterministic comparisons may run and evidence may be written.
            _write_db_evidence(
                ctx, probed=probed, integrity_results=results, no_rls=no_rls,
                index_missing=index_missing, constraint_violations=constraint_violations,
                migration_summary=migration_summary, inventory=inventory,
            )

            print(f"  tables probed: {len(probed)}; expected: "
                  f"{len(inventory.expected_tables)}; missing: {len(missing)}")
            for table in missing:
                print(f"    - MISSING {table}")
                ctx.emit(
                    "DB", "P1",
                    f"Missing table: {table}",
                    expected="table exists (schema inventory)",
                    actual="table absent",
                    description=(
                        f"Schema inventory expects table '{table}' but the live "
                        "schema does not contain it. Read-only inspection."
                    ),
                    source="run_db.py",
                )
                exit_code = EXIT_FAIL

            print(f"  tables with missing key columns: {len(missing_cols)}")
            for table, cols in missing_cols.items():
                print(f"    - {table}: missing {', '.join(cols)}")
                ctx.emit(
                    "DB", "P2",
                    f"Missing key columns in {table}: {', '.join(cols)}",
                    expected="key columns present", actual="columns absent",
                    source="run_db.py",
                )

            above = integrity.violations_above_threshold(results)
            print(f"  integrity rules: {len(results)}; above threshold: {len(above)}")
            for rule in above:
                print(f"    - {rule.id} ({rule.severity}): {rule.description}")
                ctx.emit(
                    "DB", rule.severity,
                    f"Integrity violation: {rule.id}",
                    expected=rule.expected, actual=rule.actual,
                    description=rule.description,
                    source="run_db.py",
                )
                if rule.severity in ("P0", "P1"):
                    exit_code = EXIT_FAIL

            print(f"  RLS expectations: {len(rls.expectations)}; "
                  f"expected tables without RLS: {len(no_rls)}")
            for table in no_rls:
                print(f"    - NO RLS {table}")
                ctx.emit(
                    "RLS", "P0" if table in ("organizations", "organization_members",
                                             "organization_files", "messages") else "P1",
                    f"Table {table} has RLS disabled",
                    expected="row-level security enabled", actual="RLS disabled",
                    description=(
                        "Read-only RLS inspection: table expected to have RLS "
                        "enabled has none. This is a security-boundary signal."
                    ),
                    source="run_db.py",
                )
                exit_code = EXIT_FAIL

            print(f"  expected indexes missing: {len(index_missing)}")
            for exp in index_missing:
                print(f"    - {exp.table}.{exp.column} ({exp.severity}): {exp.reason}")
                ctx.emit(
                    "DB", exp.severity,
                    f"Missing index: {exp.table}({exp.column})",
                    expected="operational index present", actual="index absent",
                    description=exp.reason or "Expected operational index is absent.",
                    source="run_db.py",
                )

            print(f"  expected constraints violated: {len(constraint_violations)}")
            for exp in constraint_violations:
                print(f"    - {exp.table}: {exp.name} ({exp.severity})")
                ctx.emit(
                    "DB", exp.severity,
                    f"Missing constraint: {exp.name}",
                    expected="constraint present", actual="constraint absent",
                    description=exp.reason,
                    source="run_db.py",
                )

            print(f"  migrations: repo={migration_summary['repo_migrations']} "
                  f"applied={migration_summary['applied_versions']} "
                  f"pending={migration_summary['pending_count']}")
            if migration_summary.get("pending_count", 0):
                ctx.emit(
                    "DB", "P2",
                    f"{migration_summary['pending_count']} migration(s) not applied",
                    expected="migration state matches repo",
                    actual=f"{migration_summary['pending_count']} pending",
                    source="run_db.py",
                )

            ctx.record_checks(
                len(probed) + len(results) + len(rls.expectations)
                + len(index_audit.expected) + len(constraint_audit.expected)
                + int(migration_summary["repo_migrations"])
            )
    except Exception as exc:
        # Harness/tool failure, not an application finding. No app findings
        # were emitted above (findings are only produced after collection
        # completed), and no partial evidence was written. The finding is
        # emitted into the shared context too so a run_all report captures
        # the tool failure (it is excluded from the verdict by its
        # classification).
        print(f"[db] ERROR (harness/tool): {type(exc).__name__}: {exc}")
        ctx.emit(
            "DB", "P1",
            "DB collection failed — harness/tool error, application state "
            "not assessed",
            expected="DB collector completes against the configured database",
            actual=f"{type(exc).__name__}: {exc}",
            description=(
                "The read-only DB collector could not complete. This is a "
                "harness/runtime or environment failure, not an application "
                "defect; no DB findings were produced and no DB evidence "
                "was written for this run."
            ),
            classification=FindingClassification.HARNESS_RUNTIME_ERROR,
            status=FindingStatus.OPEN,
            source="run_db.py",
        )
        if owned_ctx:
            ctx.finish()
        return EXIT_FAIL
    finally:
        connection.close()
    if owned_ctx:
        ctx.finish()
    print("RESULT: PASS (read-only DB inspection complete)" if exit_code == EXIT_OK
          else "RESULT: FAIL (read-only DB inspection found defects)")
    return exit_code


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="CarbonTally QA — database (read-only)")
    add_common_args(parser)
    args = parser.parse_args(argv)
    load_env_file()
    return run_db(args)


if __name__ == "__main__":
    raise SystemExit(main())
