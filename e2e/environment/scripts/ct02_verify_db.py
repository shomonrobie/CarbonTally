#!/usr/bin/env python3
"""CT-IMPLEMENT-02 — database verification suite runner.

Runs ``ct02_db_suite.sql`` against a DISPOSABLE canonical-schema database and
turns its NOTICE-level PASS/FAIL assertions into a machine-readable verdict.

WHAT IT VERIFIES (see the SQL file for the assertions themselves):
  * R-10.6 / PD-4  the canonical audit ledger is append-only for UPDATE, DELETE
                   AND TRUNCATE, for every role, with INSERT preserved;
  * F-5 / R-10.6   the retained legacy audit surfaces accept no UPDATE/DELETE/
                   TRUNCATE and no client INSERT;
  * PD-1           report sharing: version-bound, immutable-version-only,
                   tenant-scoped, recipient-explicit, revocable, one-way,
                   append-only access history;
  * PD-2           scheduled reporting: engine-truthful report types, real IANA
                   timezones, non-empty recipients, idempotent execution per due
                   slot, terminal-state immutability;
  * R-9            tenant isolation: READ and WRITE, with a positive control for
                   every negative assertion, consultant acting-for included, and
                   anonymous access denied by privilege;
  * R-3            source-to-report provenance resolves through real keys.

SAFETY
  * Refuses any target whose database name matches qa/demo/investor/prod/live
    (F-046-1 discipline) unless CT_ALLOW_PROTECTED_TARGET=1 is set explicitly.
  * The suite runs inside ONE transaction ending in ROLLBACK, so it persists
    nothing — no fixture row survives, whatever the target.
  * It performs no DDL and no destructive statement outside that transaction.

Usage:
  CT02_DB_PASSWORD=... python3 ct02_verify_db.py --host 127.0.0.1 --port 55470 \
      --db postgres --user postgres [--json out.json]

Exit: 0 all assertions PASS; 1 any FAIL; 2 the suite could not run.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SUITE_SQL = SCRIPT_DIR / "ct02_db_suite.sql"

FORBIDDEN_DB_PATTERNS = ("qa", "demo", "investor", "prod", "live")

#: The suite must emit at least this many PASS assertions before a PASS verdict
#: is credible. Pinned deliberately: if the SQL suite grows, this must grow too,
#: so an early abort can never masquerade as a clean run.
EXPECTED_MIN_ASSERTIONS = 50

_PASS_RE = re.compile(r"(?:NOTICE:\s*)?PASS\s+(\S+)")
_FAIL_RE = re.compile(r"(?:NOTICE:\s*)?FAIL\s+(\S+)")


def _refuse_protected(db_name: str) -> None:
    lowered = db_name.lower()
    for pattern in FORBIDDEN_DB_PATTERNS:
        if pattern in lowered:
            if os.getenv("CT_ALLOW_PROTECTED_TARGET") == "1":
                return
            sys.exit(
                f"REFUSED: target database {db_name!r} looks like a protected "
                f"environment (matched {pattern!r}). The suite is for disposable "
                "canonical environments only. Set CT_ALLOW_PROTECTED_TARGET=1 "
                "only if you have verified the target is disposable."
            )


def run_suite(host: str, port: str, db: str, user: str, password: str,
              search_path: str) -> tuple[int, str]:
    env = dict(os.environ, PGPASSWORD=password)
    cmd = [
        "psql", "-h", host, "-p", port, "-U", user, "-d", db,
        "-X", "-q", "-v", "ON_ERROR_STOP=0",
        "-c", f"SET search_path = {search_path}",
        "-f", str(SUITE_SQL),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    # NOTICE output is emitted on stderr; keep both streams.
    return proc.returncode, proc.stdout + "\n" + proc.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=os.getenv("E2E_DB_PORT", "55470"))
    parser.add_argument("--db", default=os.getenv("E2E_DB_NAME", "postgres"))
    parser.add_argument("--user", default=os.getenv("E2E_DB_USER", "postgres"))
    parser.add_argument("--password", default=os.getenv("CT02_DB_PASSWORD", ""))
    parser.add_argument("--search-path", default="public, extensions, pg_temp")
    parser.add_argument("--json", default="")
    args = parser.parse_args()

    _refuse_protected(args.db)

    if not SUITE_SQL.is_file():
        print(f"FAIL  suite SQL not found at {SUITE_SQL}")
        return 2

    rc, output = run_suite(args.host, args.port, args.db, args.user,
                           args.password, args.search_path)

    passed = sorted(set(_PASS_RE.findall(output)))
    failed = sorted(set(_FAIL_RE.findall(output)))
    completed = "CT02_DB_SUITE_END" in output
    aborted = "current transaction is aborted" in output

    print(output.strip())
    print()
    print(f"assertions_passed={len(passed)}")
    print(f"assertions_failed={len(failed)}")
    if failed:
        print("failed_assertions=" + ",".join(failed))
    print(f"suite_completed={completed}")
    print(f"transaction_aborted_early={aborted}")

    # A suite that produced no assertions (or fewer than the pinned minimum) has
    # not verified anything. Reporting PASS in that state would be a false
    # success, so it is reported as a FAIL with the reason.
    defect = None
    if aborted:
        defect = ("a statement failed outside an expected-failure block, so the "
                  "transaction aborted and the remaining assertions never ran")
    elif not completed:
        defect = "the suite did not run to completion"
    elif len(passed) < EXPECTED_MIN_ASSERTIONS:
        defect = (f"only {len(passed)} assertions ran, expected at least "
                  f"{EXPECTED_MIN_ASSERTIONS}")

    verdict = {
        "suite": "ct02_db_suite",
        "host": args.host,
        "port": args.port,
        "database": args.db,
        "psql_returncode": rc,
        "suite_completed": completed,
        "transaction_aborted_early": aborted,
        "assertions_passed": passed,
        "assertions_failed": failed,
        "expected_min_assertions": EXPECTED_MIN_ASSERTIONS,
        "defect": defect,
        "verdict": "PASS" if (defect is None and not failed) else "FAIL",
    }
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(verdict, indent=2) + "\n")
        print(f"json={args.json}")

    if defect is not None:
        print(f"VERDICT: FAIL — {defect}.")
        return 2
    if failed:
        print("VERDICT: FAIL — see failed_assertions above.")
        return 1
    print("VERDICT: PASS — every CT-IMPLEMENT-02 database assertion holds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
