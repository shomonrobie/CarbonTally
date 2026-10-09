#!/usr/bin/env python3
"""CT-MP-SUB-004 — NV-9 Manual Processing performance baseline (local Demo Lab).

Reproducible latency baseline for the Manual Processing critical paths, measured
END-TO-END against the RUNNING local stack (gateway + FastAPI + Supabase
Postgres) with REAL password-grant logins for the deterministic PD-5 fixture
identities. Nothing is simulated.

Critical paths measured:

  backend   entitlement lookup            GET  /organizations/{id}/manual-processing
            consultant coverage lookup   GET  /consultants/me/.../coverage
            admin coverage lookup        GET  /admin/manual-processing/coverage/{firm}
            admin client search          GET  /admin/manual-processing/organizations
            allocate (write)             POST /consultants/me/.../allocations
            release  (write)             DELETE .../allocations/{id}

  database  the allocation ledger indexes the hot queries depend on.

The two writes are the SAME client allocate→release pair the PD-5 browser
harness already uses, so they leave the fixture baseline unchanged.

THRESHOLDS: these are LOCAL Demo-Lab INTERACTIVE budgets (the UI must render its
data within roughly one second on a developer workstation), NOT a production
throughput/latency SLO. No production-scale SLO exists in the repository; if one
is required it is a PO decision (see the report §11 / §18).

Usage::

    python3 tools/demo_lab/perf_mp_baseline.py
    python3 tools/demo_lab/perf_mp_baseline.py --iterations 25 --json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402
import fixture_mp_coverage as fixture  # noqa: E402

BACKEND = f"http://127.0.0.1:{lab.BACKEND_PORT}"

#: Local interactive budgets (milliseconds) — see the module docstring.
BUDGETS = {
    "customer_entitlement": 500,
    "consultant_coverage": 500,
    "admin_coverage": 500,
    "admin_client_search": 500,
    "allocate": 750,
    "release": 750,
}

#: The index set the hot Manual Processing queries rely on.
REQUIRED_INDEXES = (
    "uq_consultant_mp_allocations_active",
    "idx_consultant_mp_allocations_firm",
    "idx_consultant_mp_allocations_org",
)


def _percentile(samples: list[int], pct: float) -> int:
    if not samples:
        return 0
    ordered = sorted(samples)
    idx = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * len(ordered))) - 1))
    return ordered[idx]


def _call(method: str, path: str, token: str, body: dict | None = None):
    return lab.http_json(
        f"{BACKEND}{path}", method=method,
        headers={"Authorization": f"Bearer {token}"},
        body=body if method != "GET" else None)


def _time_call(method: str, path: str, token: str, body: dict | None = None):
    start = time.perf_counter()
    status, payload, _raw = _call(method, path, token, body)
    return status, payload, round((time.perf_counter() - start) * 1000)


def measure(name: str, iterations: int, fn) -> dict:
    samples: list[int] = []
    statuses: set[int] = set()
    for _ in range(iterations):
        status, _payload, ms = fn()
        statuses.add(status)
        samples.append(ms)
    budget = BUDGETS.get(name)
    return {
        "operation": name,
        "iterations": iterations,
        "statuses": sorted(statuses),
        "p50_ms": _percentile(samples, 50),
        "p95_ms": _percentile(samples, 95),
        "max_ms": max(samples) if samples else 0,
        "budget_ms": budget,
        "ok": bool(statuses == {200} and _percentile(samples, 95) <= (budget or 10**9)),
    }


def _write_measure(op: str, samples: list[int], statuses: set[int]) -> dict:
    budget = BUDGETS[op]
    return {
        "operation": op,
        "iterations": len(samples),
        "statuses": sorted(statuses),
        "p50_ms": _percentile(samples, 50),
        "p95_ms": _percentile(samples, 95),
        "max_ms": max(samples) if samples else 0,
        "budget_ms": budget,
        "ok": bool(statuses == {200} and _percentile(samples, 95) <= budget),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CT-MP-SUB-004 NV-9 baseline")
    parser.add_argument("--iterations", type=int, default=15)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    org = fixture.org_ids()
    logins = fixture.fixture_logins()
    password = lab.demo_password()

    tokens = {
        "owner_dual": fixture.login(logins["u_owner_dual"], password),
        "consultant": fixture.login(logins["u_consultant_selected"], password),
        "admin": fixture.login(f"platform.admin@{lab.EMAIL_DOMAIN}", password),
    }

    results: list[dict] = []
    results.append(measure(
        "customer_entitlement", args.iterations,
        lambda: _time_call(
            "GET", f"/api/v3/organizations/{org['org_client_dual']}/manual-processing",
            tokens["owner_dual"])))
    results.append(measure(
        "consultant_coverage", args.iterations,
        lambda: _time_call(
            "GET", "/api/v3/consultants/me/manual-processing/coverage",
            tokens["consultant"])))
    results.append(measure(
        "admin_coverage", args.iterations,
        lambda: _time_call(
            "GET",
            f"/api/v3/admin/manual-processing/coverage/{fixture.fid('firm:firm_selected')}",
            tokens["admin"])))
    results.append(measure(
        "admin_client_search", args.iterations,
        lambda: _time_call(
            "GET", "/api/v3/admin/manual-processing/organizations?q=MP-FX",
            tokens["admin"])))

    # Write path: allocate then release the SAME unallocated fixture client, so
    # the fixture baseline is restored after each pair.
    alloc_samples: list[int] = []
    rel_samples: list[int] = []
    write_statuses: set[int] = set()
    for _ in range(max(3, args.iterations // 3)):
        status, payload, ms = _time_call(
            "POST", "/api/v3/consultants/me/manual-processing/allocations",
            tokens["consultant"], {"organization_id": org["org_client_unallocated"]})
        write_statuses.add(status)
        alloc_samples.append(ms)
        alloc_id = ((payload or {}).get("allocation") or {}).get("id")
        if alloc_id:
            status, _p, ms = _time_call(
                "DELETE",
                f"/api/v3/consultants/me/manual-processing/allocations/{alloc_id}",
                tokens["consultant"])
            write_statuses.add(status)
            rel_samples.append(ms)
    results.append(_write_measure("allocate", alloc_samples, write_statuses))
    results.append(_write_measure("release", rel_samples, write_statuses))

    # Database: the indexes the hot queries depend on must exist.
    indexes = {}
    for name in REQUIRED_INDEXES:
        row = lab.psql_scalar(
            "SELECT indexname FROM pg_indexes "
            "WHERE schemaname='public' AND indexname='" + name + "'")
        indexes[name] = bool(row and row.strip())

    failed = [r["operation"] for r in results if not r["ok"]]
    failed += [n for n, present in indexes.items() if not present]

    evidence = {
        "fixture": fixture.FIXTURE_ID,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            "stack": "local Demo Lab (gateway + FastAPI + Supabase Postgres)",
            "backend": BACKEND,
            "data_scale": "fixture-scale (a handful of rows), NOT production scale",
        },
        "iterations": args.iterations,
        "budgets_ms": BUDGETS,
        "results": results,
        "database_indexes": indexes,
        "summary": {"failed": failed},
    }
    evidence["evidence"] = fixture._write_evidence("mp_perf_baseline", evidence)

    if args.json:
        print(json.dumps(evidence, indent=1, default=str))
    else:
        for r in results:
            flag = "PASS" if r["ok"] else "FAIL"
            print(f"  [{flag}] {r['operation']:<22} n={r['iterations']:<3} "
                  f"p50={r['p50_ms']}ms p95={r['p95_ms']}ms "
                  f"max={r['max_ms']}ms budget={r['budget_ms']}ms "
                  f"statuses={r['statuses']}")
        for name, present in indexes.items():
            print(f"  [{'PASS' if present else 'FAIL'}] index {name}")
        print(f"evidence: {evidence['evidence']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

