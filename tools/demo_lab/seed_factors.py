#!/usr/bin/env python3
"""DEMO-T2-C — load the verified factor datasets into the local Demo Lab.

This is a **controlled seeder/orchestrator**, not a second importer:

* it calls the existing, independently verified CLIs
  (``src.commands.import_defra`` then ``src.commands.import_seai``) in ``sync``
  mode, one after the other — never concurrently (OHD finding **O-1** leaves the
  one-active-batch rule to importer code, so provider imports are serialised);
* it duplicates **no** parsing/mapping logic, writes **no** raw SQL factor rows
  and copies nothing from the reference database — every factor row, every
  ``import_batches`` row and every checksum comes from the verified importers;
* it targets **only** ``carbontally_demo_local``. The database name is checked
  before any write and the run aborts otherwise; a local hostname is never taken
  as evidence of safety.

Usage::

    python3 tools/demo_lab/seed_factors.py --dry-run     # plan only, no DB access
    python3 tools/demo_lab/seed_factors.py               # seed (DEFRA then SEAI)
    python3 tools/demo_lab/seed_factors.py --reset       # remove ONLY T2-C factors/batches

Evidence is written outside the repository (``<state dir>/evidence/``).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

SEEDER_VERSION = "DEMO-T2-C/1.0"

#: The only database this seeder may ever write to (enforced, never inferred).
TARGET_DB = "carbontally_demo_local"

#: Databases that must never be touched by this tool, named explicitly.
FORBIDDEN_DBS = (
    "postgres",               # local Supabase stack main DB (investor/reference dataset)
    "carbontally_test",       # dedicated integration test DB
    "carbontally_qa_phase8",  # persistent QA
    "_supabase",
)

FACTOR_WORKBOOK_DIR = lab.REPO_ROOT / "tools" / "carbon_data_factory" / "factors"
DEFRA_WORKBOOK = FACTOR_WORKBOOK_DIR / "ghg-conversion-factors-2025-flat-format.xlsx"
SEAI_WORKBOOK = FACTOR_WORKBOOK_DIR / "SEAI-conversion-and-emission-factors.xlsx"

DEFAULT_IMPORT_OUTPUT = lab.STATE_DIR / "factor_import"
LOG_DIR = lab.STATE_DIR / "logs"

#: Verification targets (NOT the mechanism — checksums are computed from the
#: workbooks by the importer; these values only flag unexpected dataset drift).
DEFRA_EXPECTED = {
    "provider_key": "defra",
    "provider_version": "2025 (V1)",
    "reporting_year": 2025,
    "factor_source": "DEFRA-DESNZ",
    "factor_set": "DEFRA-2025",
    "country": "GB",
    "imported": 7029,
    "skipped": 1711,
    "duplicates": 0,
    "sha256": "8bfdb45b81ec4a88e3bdf4584637330f62e6bd09ce1940e654c5d7b7f736de94",
}
SEAI_EXPECTED = {
    "provider_key": "seai",
    "provider_version": "2025 (V1.7)",
    "reporting_year": 2025,
    "factor_source": "SEAI",
    "factor_set": "SEAI-2025",
    "country": "IE",
    "imported": 20,
    "skipped": 8,
    "duplicates": 0,
    "sha256": "e64f4f91cf5546767d80fc2fe6be252946bcafedbd957d6b2981c9cf3f640e6d",
}
PROVIDERS = (
    ("defra", DEFRA_WORKBOOK, DEFRA_EXPECTED),
    ("seai", SEAI_WORKBOOK, SEAI_EXPECTED),
)


class GuardError(RuntimeError):
    """Raised when the target database is not provably the Demo Lab."""


# ---------------------------------------------------------------------------
# Target resolution + hard guard
# ---------------------------------------------------------------------------
def database_name(dsn: str) -> str:
    """Return the database name of a Postgres DSN ("" when no name is present).

    A DSN without an explicit database name must never be treated as naming a
    database, so ``postgresql://host:54426/`` yields "" and is refused.
    """
    path = dsn.split("?", 1)[0].strip()
    if "://" not in path:
        return ""
    after_scheme = path.split("://", 1)[1]
    if "/" not in after_scheme:
        return ""
    return after_scheme.rsplit("/", 1)[1].strip()


def assert_lab_target(dsn: str) -> str:
    """HARD FAIL unless ``dsn`` names exactly the Demo Lab database.

    A local host is *not* evidence of safety: other local databases hold the
    investor/reference dataset, the integration test database and QA clones.
    """
    if not dsn or not dsn.strip():
        raise GuardError(
            "refusing to run: no Demo Lab DSN resolved. Pass --db-url or set "
            "DEMO_LAB_DATABASE_URL (never a production or reference database)."
        )
    name = database_name(dsn)
    if name in FORBIDDEN_DBS or name.startswith("ct_"):
        raise GuardError(
            f"refusing to run against {name!r}: protected database, not the Demo Lab."
        )
    if name != TARGET_DB:
        raise GuardError(
            f"refusing to run against {name!r}: DEMO-T2-C may only write to "
            f"{TARGET_DB!r}. Provide the Demo Lab DSN via --db-url / "
            f"DEMO_LAB_DATABASE_URL."
        )
    return name


def resolve_dsn(args: argparse.Namespace) -> str:
    """Resolver order: --db-url → DEMO_LAB_DATABASE_URL → the lab's own env file."""
    if args.db_url:
        return args.db_url
    env_dsn = os.environ.get("DEMO_LAB_DATABASE_URL")
    if env_dsn:
        return env_dsn
    env_file = lab.STATE_DIR / "backend.env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    return (f"postgresql://{lab.STACK_DB_USER}:{lab.STACK_DB_PASSWORD}"
            f"@127.0.0.1:{lab.STACK_DB_PORT}/{lab.LAB_DB}")


def backend_python() -> str:
    """Interpreter that runs the verified importers (backend venv by default)."""
    env_python = os.environ.get("DEMO_LAB_PYTHON")
    if env_python and pathlib.Path(env_python).exists():
        return env_python
    candidate = lab.REPO_ROOT / "backend" / ".venv" / "bin" / "python"
    if not candidate.exists():
        raise SystemExit(
            f"cannot find the importer interpreter at {candidate}. Install the backend "
            f"venv (or set DEMO_LAB_PYTHON) before seeding."
        )
    return str(candidate)


def sha256_file(path: pathlib.Path) -> str:
    """SHA-256 of a file (computed here, never assumed)."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 256), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# ---------------------------------------------------------------------------
# Verified importer invocation (no parsing/mapping logic is duplicated here)
# ---------------------------------------------------------------------------
_DONE_RE = re.compile(r"imported=(\d+)\s+skipped=(\d+)\s+duplicates=(\d+)")
_BATCH_RE = re.compile(r"batch[= ]([0-9a-fA-F-]{36})")


def run_importer(provider: str, workbook: pathlib.Path, dsn: str, output_dir: pathlib.Path,
                 label: str) -> dict:
    """Run one verified importer CLI in ``sync`` mode against the Demo Lab.

    The DSN is passed both as ``--db-url`` and through the environment so the
    importer cannot silently fall back to another database.
    """
    module = f"src.commands.import_{provider}"
    cmd = [backend_python(), "-m", module,
           "--workbook", str(workbook),
           "--mode", "sync",
           "--db-url", dsn,
           "--output-dir", str(output_dir)]
    env = dict(os.environ)
    env["DATABASE_URL"] = dsn              # DEFRA resolver fallback
    env["SEAI_DATABASE_URL"] = dsn         # SEAI resolver fallback
    env["SUPABASE_DB_URL"] = dsn
    env["POSTGRES_URL"] = dsn
    env["PYTHONUNBUFFERED"] = "1"

    started = time.time()
    proc = subprocess.run(cmd, cwd=str(lab.REPO_ROOT), env=env, text=True,
                          capture_output=True)
    elapsed = round(time.time() - started, 1)
    log_path = LOG_DIR / f"seed_factors_{label}_{provider}.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        f"$ {' '.join(cmd)}\n\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}\n")

    combined = f"{proc.stdout}\n{proc.stderr}"
    done = _DONE_RE.search(combined)
    batch_hint = _BATCH_RE.search(combined)
    result = {
        "provider_key": provider,
        "module": module,
        "command": cmd[:-1] + ["--output-dir", "<state>/factor_import"],
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "parsed_imported": int(done.group(1)) if done else None,
        "parsed_skipped": int(done.group(2)) if done else None,
        "parsed_duplicates": int(done.group(3)) if done else None,
        "batch_id_hint": batch_hint.group(1) if batch_hint else None,
        "log": str(log_path),
    }
    if proc.returncode != 0:
        tail = "\n".join(combined.strip().splitlines()[-25:])
        raise SystemExit(f"{provider} importer failed (rc={proc.returncode}):\n{tail}")
    return result


# ---------------------------------------------------------------------------
# Read-only Demo Lab probes (docker exec psql SELECTs only)
# ---------------------------------------------------------------------------
def _q_lines(sql: str) -> list:
    """All result lines of a read-only probe (one string per row)."""
    proc = lab.psql(sql, db=TARGET_DB)
    out = (proc.stdout or "").strip()
    if "ERROR" in (proc.stderr or "") or "ERROR" in out:
        raise SystemExit(f"read probe failed: {sql}\n{(proc.stderr or out).strip()}")
    return [line for line in out.splitlines() if line.strip()]


def _q(sql: str) -> str:
    """Single scalar/row probe (read-only)."""
    rows = _q_lines(sql)
    return rows[0].strip() if rows else ""


def _factor_count(factor_set: str, extra: str = "") -> int:
    raw = _q(f"SELECT count(*) FROM emission_factors WHERE factor_set='{factor_set}'{extra}")
    return int(raw or 0)


def lab_state() -> dict:
    """Current factor/batch/identity state of the Demo Lab (read-only)."""
    state = {
        "emission_factors_total": int(_q("SELECT count(*) FROM emission_factors") or 0),
        "customer_factors": int(_q("SELECT count(*) FROM customer_factors") or 0),
        "import_batches": int(_q("SELECT count(*) FROM import_batches") or 0),
        "organizations": int(_q("SELECT count(*) FROM organizations") or 0),
        "organization_members": int(_q("SELECT count(*) FROM organization_members") or 0),
    }
    for _provider, _wb, expected in PROVIDERS:
        fs = expected["factor_set"]
        state[f"{fs}_factors"] = _factor_count(fs)
        state[f"{fs}_linked"] = _factor_count(fs, " AND import_batch_id IS NOT NULL")
        state[f"{fs}_unlinked"] = _factor_count(fs, " AND import_batch_id IS NULL")
    return state


def provider_batches(provider_key: str, reporting_year: int = 2025) -> list[dict]:
    """All provenance batch rows for a provider/year (read-only, oldest first).

    Repeat ``sync`` imports intentionally keep the superseded batch as an
    immutable, deactivated provenance record, so this can return more than one
    row; :func:`active_only` narrows it to the current batch.
    """
    sql = ("SELECT id || '|' || COALESCE(provider_version,'') || '|' || "
           "COALESCE(source_file,'') || '|' || COALESCE(source_checksum,'') || '|' || "
           "COALESCE(rows_total::text,'') || '|' || COALESCE(rows_imported::text,'') || '|' || "
           "COALESCE(rows_skipped::text,'') || '|' || COALESCE(rows_duplicate::text,'') || '|' || "
           "COALESCE(status,'') || '|' || COALESCE(is_active::text,'') "
           f"FROM import_batches WHERE provider_key='{provider_key}' "
           f"AND reporting_year={reporting_year} ORDER BY created_at")
    rows = []
    for line in _q_lines(sql):
        parts = line.split("|")
        if len(parts) != 10:
            raise SystemExit(f"unexpected import_batches row shape ({len(parts)} fields): "
                             f"{line!r}")
        rows.append(dict(zip(
            ["id", "provider_version", "source_file", "source_checksum",
             "rows_total", "rows_imported", "rows_skipped", "rows_duplicate",
             "status", "is_active"], parts)))
    return rows


def active_only(batches: list) -> list:
    """The subset of provenance rows currently flagged active."""
    return [b for b in batches if str(b.get("is_active", "")).lower() in ("t", "true")]


def _check(checks: list, name: str, ok: bool, expected, actual) -> None:
    checks.append({"check": name, "ok": bool(ok),
                   "expected": expected, "actual": actual})



# ---------------------------------------------------------------------------
# Independent post-load verification (queries emission_factors directly)
# ---------------------------------------------------------------------------
def verify_datasets(computed: dict) -> dict:
    """Verify the lab's factor state, provenance and identity preservation."""
    checks: list = []
    state = lab_state()
    detail: dict = {"state": state}

    for provider, workbook, expected in PROVIDERS:
        fs = expected["factor_set"]
        _check(checks, f"{fs}: factor rows", state[f"{fs}_factors"] == expected["imported"],
               expected["imported"], state[f"{fs}_factors"])
        _check(checks, f"{fs}: rows with import_batch_id",
               state[f"{fs}_linked"] == expected["imported"], expected["imported"],
               state[f"{fs}_linked"])
        _check(checks, f"{fs}: rows without import_batch_id",
               state[f"{fs}_unlinked"] == 0, 0, state[f"{fs}_unlinked"])
        for column, key in (("country", "country"), ("factor_source", "factor_source")):
            actual = _q(f"SELECT DISTINCT {column} FROM emission_factors "
                        f"WHERE factor_set='{fs}'")
            _check(checks, f"{fs}: {column}", actual == expected[key], expected[key], actual)

        all_batches = provider_batches(provider, expected["reporting_year"])
        active = active_only(all_batches)
        detail[f"{fs}_batches"] = all_batches
        detail[f"{fs}_active_batches"] = active
        _check(checks, f"{fs}: exactly one active batch", len(active) == 1, 1, len(active))
        _check(checks, f"{fs}: provenance batches all completed",
               all(b["status"] == "completed" for b in all_batches), True,
               [b["status"] for b in all_batches])
        if active:
            batch = active[-1]
            _check(checks, f"{fs}: batch provider_version",
                   batch["provider_version"] == expected["provider_version"],
                   expected["provider_version"], batch["provider_version"])
            _check(checks, f"{fs}: batch checksum == workbook SHA-256",
                   batch["source_checksum"] == computed[provider], computed[provider],
                   batch["source_checksum"])
            _check(checks, f"{fs}: batch source_file is the workbook",
                   pathlib.Path(batch["source_file"]).name == workbook.name,
                   workbook.name, pathlib.Path(batch["source_file"]).name)
            _check(checks, f"{fs}: batch status completed",
                   batch["status"] == "completed", "completed", batch["status"])
            not_on_active = _q("SELECT count(*) FROM emission_factors WHERE factor_set="
                               f"'{fs}' AND import_batch_id IS DISTINCT FROM '{batch['id']}'")
            _check(checks, f"{fs}: all rows linked to the active batch",
                   not_on_active in ("0", ""), 0, not_on_active or "0")

    _check(checks, "total emission_factors", state["emission_factors_total"] == 7049, 7049,
           state["emission_factors_total"])
    _check(checks, "Demo Lab organizations preserved", state["organizations"] == 4, 4,
           state["organizations"])
    _check(checks, "Demo Lab organization_members preserved",
           state["organization_members"] == 8, 8, state["organization_members"])

    ok = all(c["ok"] for c in checks)
    return {"ok": ok, "checks": checks, "detail": detail,
            "failed": [c["check"] for c in checks if not c["ok"]]}


# ---------------------------------------------------------------------------
# Evidence (written outside the repository)
# ---------------------------------------------------------------------------
def repo_state() -> dict:
    """Read-only git facts for the evidence file."""
    def git(*args: str) -> str:
        try:
            proc = subprocess.run(["git", *args], cwd=str(lab.REPO_ROOT), text=True,
                                  capture_output=True)
            return proc.stdout.strip()
        except OSError:  # pragma: no cover
            return ""
    return {"commit": git("rev-parse", "HEAD"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(git("status", "--porcelain"))}


def workbook_plan(provider: str, workbook: pathlib.Path, expected: dict) -> dict:
    """Filesystem-only dataset plan used by --dry-run and the evidence file."""
    exists = workbook.exists()
    checksum = sha256_file(workbook) if exists else None
    return {
        "provider_key": provider,
        "importer": f"src.commands.import_{provider}",
        "workbook": str(workbook),
        "workbook_exists": exists,
        "workbook_bytes": workbook.stat().st_size if exists else None,
        "computed_sha256": checksum,
        "reference_sha256": expected["sha256"],
        "sha256_matches_reference": (checksum == expected["sha256"]) if exists else None,
        "expected_imported": expected["imported"],
        "expected_skipped": expected["skipped"],
        "expected_duplicates": expected["duplicates"],
        "expected_provider_version": expected["provider_version"],
        "expected_factor_source": expected["factor_source"],
        "expected_factor_set": expected["factor_set"],
        "expected_country": expected["country"],
        "reporting_year": expected["reporting_year"],
    }


def write_evidence(payload: dict, kind: str) -> pathlib.Path:
    """Persist an evidence JSON outside the Git repository."""
    lab.ensure_dirs()
    lab.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    target = lab.EVIDENCE_DIR / f"t2c_{kind}_{stamp}.json"
    body = json.dumps(payload, indent=2, default=str) + "\n"
    target.write_text(body)
    (lab.EVIDENCE_DIR / f"t2c_{kind}_latest.json").write_text(body)
    return target


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
def seed(dsn: str, output_root: pathlib.Path) -> dict:
    """Load DEFRA then SEAI into the Demo Lab, strictly serially."""
    target_db = assert_lab_target(dsn)      # HARD guard BEFORE any database write
    baseline = lab_state()
    print(f"target database : {target_db} (guard passed)")
    print(f"baseline        : {json.dumps(baseline)}")

    results: list = []
    for provider, workbook, expected in PROVIDERS:   # serial: never concurrent
        if not workbook.exists():
            raise SystemExit(f"workbook missing: {workbook}")
        import_dir = output_root / provider
        import_dir.mkdir(parents=True, exist_ok=True)
        started = _ts()
        print(f"[{started}] {provider}: importing {workbook.name} (mode=sync) ...")
        result = run_importer(provider, workbook, dsn, import_dir, "seed")
        result.update({
            "started_at": started,
            "finished_at": _ts(),
            "workbook": str(workbook),
            "computed_sha256": sha256_file(workbook),
        })
        results.append(result)
        print(f"[{result['finished_at']}] {provider}: rc={result['returncode']} "
              f"imported={result['parsed_imported']} skipped={result['parsed_skipped']} "
              f"duplicates={result['parsed_duplicates']} "
              f"({result['elapsed_seconds']}s)")

    computed = {r["provider_key"]: r["computed_sha256"] for r in results}
    verification = verify_datasets(computed)
    serial_ok = all(results[i]["finished_at"] <= results[i + 1]["started_at"]
                    for i in range(len(results) - 1))
    final_state = verification["detail"]["state"]

    for result, (_provider, _workbook, expected) in zip(results, PROVIDERS):
        result["expected"] = {k: v for k, v in expected.items() if k != "sha256"}
        result["sha256_matches_reference"] = result["computed_sha256"] == expected["sha256"]
        result["linked_factor_count"] = final_state[f"{expected['factor_set']}_factors"]
        active = verification["detail"][f"{expected['factor_set']}_active_batches"]
        result["active_batch"] = active[-1] if active else None
        result["active_batch_count"] = len(active)
        result["provenance_batch_rows"] = len(
            verification["detail"][f"{expected['factor_set']}_batches"])

    payload = {
        "task": "DEMO-T2-C",
        "seeder": "tools/demo_lab/seed_factors.py",
        "seeder_version": SEEDER_VERSION,
        "executed_at": _ts(),
        "mode": "sync",
        "target_database": target_db,
        "providers_serial": True,
        "provider_order": [r["provider_key"] for r in results],
        "serial_execution_verified": serial_ok,
        "baseline_state": baseline,
        "final_state": final_state,
        "defra": next(r for r in results if r["provider_key"] == "defra"),
        "seai": next(r for r in results if r["provider_key"] == "seai"),
        "verification": verification,
        "repo": repo_state(),
        "o2_note": "import_batches.rows_imported is the INSERT count (OHD finding O-2): a "
                   "repeat sync reports 0 while every factor is linked to the new batch. "
                   "Linked-factor counts are read from emission_factors, not from the batch.",
        "reset_supported": "python3 tools/demo_lab/seed_factors.py --reset (factor_set "
                           "IN ('DEFRA-2025','SEAI-2025') + their batches only)",
    }
    evidence = write_evidence(payload, "seed")
    payload["evidence_path"] = str(evidence)

    print(f"verification    : {'ALL CHECKS OK' if verification['ok'] else 'FAILED'}")
    for item in verification["checks"]:
        if not item["ok"]:
            print(f"  FAIL {item['check']}: expected={item['expected']} "
                  f"actual={item['actual']}")
    print(f"final state     : {json.dumps(final_state)}")
    print(f"serial order    : {payload['provider_order']} (non-overlapping={serial_ok})")
    print(f"evidence        : {evidence}")
    if not verification["ok"]:
        raise SystemExit(4)
    return payload


# ---------------------------------------------------------------------------
# Reset (factor-scoped only)
# ---------------------------------------------------------------------------
def _exec_write(sql: str, label: str) -> None:
    """Run one write statement against the Demo Lab and fail loudly on error."""
    proc = lab.psql(sql, db=TARGET_DB)
    err = (proc.stderr or "").strip()
    if "ERROR" in err:
        raise SystemExit(f"statement failed ({label}): {err}")


def reset(dsn: str) -> dict:
    """Remove ONLY the T2-C factor rows and their provenance batches."""
    target_db = assert_lab_target(dsn)      # HARD guard BEFORE any database write
    before = lab_state()
    batches_before = {p: provider_batches(p, 2025) for p, _w, _e in PROVIDERS}
    print(f"target database : {target_db} (guard passed)")
    print(f"state before    : {json.dumps(before)}")
    print("resetting only  : emission_factors WHERE factor_set IN "
          "('DEFRA-2025','SEAI-2025') and their import_batches rows")

    _exec_write(
        "BEGIN;"
        "DELETE FROM emission_factors WHERE factor_set IN ('DEFRA-2025','SEAI-2025');"
        "DELETE FROM import_batches WHERE provider_key IN ('defra','seai') "
        "AND reporting_year=2025;"
        "COMMIT;", "factor+provenance deletion")

    after = lab_state()
    removed_factors = before["DEFRA-2025_factors"] + before["SEAI-2025_factors"]
    removed_batches = sum(len(b) for b in batches_before.values())
    checks: list = []
    for _provider, _workbook, expected in PROVIDERS:
        fs = expected["factor_set"]
        remaining = provider_batches(expected["provider_key"], 2025)
        _check(checks, f"{fs}: factors removed", after[f"{fs}_factors"] == 0, 0,
               after[f"{fs}_factors"])
        _check(checks, f"{fs}: provenance batches removed", len(remaining) == 0, 0,
               len(remaining))
    _check(checks, "unrelated factor rows preserved",
           after["emission_factors_total"] == before["emission_factors_total"] - removed_factors,
           before["emission_factors_total"] - removed_factors,
           after["emission_factors_total"])
    _check(checks, "unrelated import_batches preserved",
           after["import_batches"] == before["import_batches"] - removed_batches,
           before["import_batches"] - removed_batches, after["import_batches"])
    _check(checks, "Demo Lab organizations preserved", after["organizations"] == 4, 4,
           after["organizations"])
    _check(checks, "Demo Lab organization_members preserved",
           after["organization_members"] == 8, 8, after["organization_members"])
    _check(checks, "customer_factors untouched",
           after["customer_factors"] == before["customer_factors"],
           before["customer_factors"], after["customer_factors"])

    ok = all(c["ok"] for c in checks)
    payload = {
        "task": "DEMO-T2-C",
        "seeder": "tools/demo_lab/seed_factors.py",
        "seeder_version": SEEDER_VERSION,
        "executed_at": _ts(),
        "mode": "reset",
        "target_database": target_db,
        "scope": "emission_factors WHERE factor_set IN ('DEFRA-2025','SEAI-2025') "
                 "+ import_batches WHERE provider_key IN ('defra','seai') AND reporting_year=2025",
        "state_before": before,
        "batches_removed": batches_before,
        "state_after": after,
        "verification": {"ok": ok, "checks": checks,
                         "failed": [c["check"] for c in checks if not c["ok"]]},
        "repo": repo_state(),
    }
    evidence = write_evidence(payload, "reset")
    print(f"state after     : {json.dumps(after)}")
    print(f"verification    : {'ALL CHECKS OK' if ok else 'FAILED'}")
    print(f"evidence        : {evidence}")
    if not ok:
        raise SystemExit(4)
    return payload


# ---------------------------------------------------------------------------
# Dry run (NO database access of any kind)
# ---------------------------------------------------------------------------
def _redact(dsn: str) -> str:
    if "@" not in dsn:
        return dsn
    scheme, rest = dsn.split("://", 1) if "://" in dsn else ("postgresql", dsn)
    return f"{scheme}://***@{rest.split('@', 1)[1]}"


def dry_run(dsn: str, output_root: pathlib.Path) -> dict:
    """Print the load plan, checksums and target. Touches the database never.

    Only filesystem reads and SHA-256 hashing happen here: the write path lives
    exclusively in :func:`seed` / :func:`reset`, which this function cannot reach.
    """
    try:
        guard = {"ok": True, "database": assert_lab_target(dsn), "reason": None}
    except GuardError as exc:
        guard = {"ok": False, "database": database_name(dsn), "reason": str(exc)}

    plans = [workbook_plan(p, wb, exp) for p, wb, exp in PROVIDERS]
    plan_ok = all(p["workbook_exists"] and p["sha256_matches_reference"] for p in plans)

    print("DEMO-T2-C dry run — no database access, no writes")
    print(f"target dsn      : {_redact(dsn)}")
    print(f"target database : {guard['database']} (guard {'PASS' if guard['ok'] else 'FAIL'})")
    if not guard["ok"]:
        print(f"guard reason    : {guard['reason']}")
    print(f"import output   : {output_root} (outside the repository)")
    for plan in plans:
        print(f"  {plan['provider_key']:5s} workbook : {plan['workbook']}")
        print(f"        exists   : {plan['workbook_exists']} "
              f"({plan['workbook_bytes']} bytes)")
        print(f"        sha256   : {plan['computed_sha256']} "
              f"(matches reference: {plan['sha256_matches_reference']})")
        print(f"        expect   : {plan['expected_imported']} imported, "
              f"{plan['expected_skipped']} skipped, {plan['expected_duplicates']} duplicates")
        print(f"        provenance: factor_set={plan['expected_factor_set']} "
              f"country={plan['expected_country']} provider_version="
              f"{plan['expected_provider_version']} year={plan['reporting_year']}")
        print(f"        command  : python -m {plan['importer']} --workbook <file> "
              f"--mode sync --db-url <redacted> --output-dir {output_root / plan['provider_key']}")
    print(f"execution order : {[p['provider_key'] for p in plans]} (serial; O-1 unresolved)")

    payload = {
        "task": "DEMO-T2-C", "seeder": "tools/demo_lab/seed_factors.py",
        "seeder_version": SEEDER_VERSION, "executed_at": _ts(), "mode": "dry-run",
        "database_access": False, "database_writes": False,
        "target_dsn_redacted": _redact(dsn), "guard": guard,
        "plan_ok": plan_ok, "providers": plans,
        "repo": repo_state(),
        "note": "rows_imported is the insert count (O-2); linked-factor counts come "
                "from emission_factors",
    }
    evidence = write_evidence(payload, "dryrun")
    print(f"evidence        : {evidence}")
    if not plan_ok:
        raise SystemExit(1)
    return payload


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="seed_factors.py",
        description="DEMO-T2-C: load the verified DEFRA/SEAI factor datasets into the "
                    "local Demo Lab (carbontally_demo_local only).")
    parser.add_argument("--db-url", default=None,
                        help="Demo Lab DSN (default: $DEMO_LAB_DATABASE_URL, then the "
                             "lab's backend.env, then the lab's docker-published port)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan and checksums; performs NO database access")
    parser.add_argument("--reset", action="store_true",
                        help="delete ONLY factor_set IN ('DEFRA-2025','SEAI-2025') and "
                             "their import_batches rows")
    parser.add_argument("--output-dir", default=str(DEFAULT_IMPORT_OUTPUT),
                        help="importer artifact directory (kept outside the repository)")
    parser.add_argument("--json", action="store_true", help="also print the JSON payload")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run and args.reset:
        print("refusing: --dry-run and --reset are mutually exclusive", file=sys.stderr)
        return 2

    dsn = resolve_dsn(args)
    output_root = pathlib.Path(args.output_dir)

    try:
        if args.dry_run:
            payload = dry_run(dsn, output_root)
        elif args.reset:
            payload = reset(dsn)
        else:
            payload = seed(dsn, output_root)
    except GuardError as exc:
        print(f"GUARD BLOCKED — {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    print("DEMO-T2-C seeder complete — READY FOR INDEPENDENT VERIFICATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

