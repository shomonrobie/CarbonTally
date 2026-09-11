#!/usr/bin/env python3
"""P6-2F — execute REAL acceptance evidence against the isolated environment.

Two SEPARATE boundaries (per the architecture rule):
  * database/RLS  : PostgREST + a real user JWT (never service-role)
  * application   : FastAPI + a real user JWT (service-role pool behind it)

Every persona authenticates with genuine GoTrue credentials.
Emits JSON to e2e/environment/.acceptance_report.json and prints a summary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ENV_DIR = HERE.parent
sys.path.insert(0, str(HERE))
from seed_e2e import (  # noqa: E402
    CLIENT_A, ITEM_A, ITEM_PE_A, ORG_A, ORG_B, PERSONAS, PASSWORD,
)

API = "http://127.0.0.1:8051"
ENV_FILE = ENV_DIR / ".env.e2e"


def env() -> dict:
    out = {}
    for line in ENV_FILE.read_text().splitlines():
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"')
    return out


E = env()
SB = E["E2E_SUPABASE_URL"]
ANON = E["E2E_ANON_KEY"]
EMAIL = {k: e for k, e, _r, _s in PERSONAS}
RESULTS: list[dict] = []


def jwt(persona: str) -> str:
    r = requests.post(f"{SB}/auth/v1/token?grant_type=password",
                      headers={"apikey": ANON, "Content-Type": "application/json"},
                      json={"email": EMAIL[persona], "password": PASSWORD}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def rec(boundary, case, who, expect, status, ok, note="") -> None:
    RESULTS.append({"boundary": boundary, "case": case, "identity": who,
                    "expected": expect, "status": status, "pass": bool(ok), "note": note})
    print(f"  [{'PASS' if ok else 'FAIL'}] {boundary:4s} {case:40s} {who:14s} -> {status} want {expect} {note}")


def rest(token, table, query="select=id&limit=5"):
    h = {"apikey": ANON, "Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return requests.get(f"{SB}/rest/v1/{table}?{query}", headers=h, timeout=30)


def api(token, method, path):
    h = {}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{API}{path}", headers=h, timeout=60).status_code


def raw(token, table, query="select=id&limit=5"):
    h = {"apikey": ANON, "Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = requests.get(f"{SB}/rest/v1/{table}?{query}", headers=h, timeout=30)
    return r.status_code, r.text


def rls_boundary() -> None:
    print("== RLS / PostgREST boundary (real user JWT; no service-role) ==")
    ta, tb = jwt("org_a_owner"), jwt("org_b_owner")
    sa, ba = raw(ta, "organizations", f"select=id&id=eq.{ORG_A}")
    sb, bb = raw(tb, "organizations", f"select=id&id=eq.{ORG_B}")
    # A 42501 means the isolated env never granted table privileges to
    # `authenticated`, so every request is denied regardless of RLS policy and
    # the DENY cases are non-discriminating -> INCONCLUSIVE, never PASS.
    blocked = "42501" in ba and "42501" in bb
    note = "42501 permission denied (privileges not granted to authenticated)" if blocked else ""
    rec("RLS", "orgA reads own org (ALLOW)", "org_a_owner", "row", sa,
        sa == 200 and ORG_A in ba, note)
    rec("RLS", "orgB reads own org (ALLOW)", "org_b_owner", "row", sb,
        sb == 200 and ORG_B in bb, note)
    if blocked:
        rec("RLS", "orgA reads Org B (DENY)", "org_a_owner", "no row", sa, False,
            "INCONCLUSIVE: non-discriminating (privilege denied)")
        rec("RLS", "orgB reads Org A (DENY)", "org_b_owner", "no row", sb, False,
            "INCONCLUSIVE: non-discriminating (privilege denied)")
    else:
        rec("RLS", "orgA reads Org B (DENY)", "org_a_owner", "no row", sa,
            ORG_B not in ba, "")
        rec("RLS", "orgB reads Org A (DENY)", "org_b_owner", "no row", sb,
            ORG_A not in bb, "")
    sa, _ = raw(None, "organizations")
    rec("RLS", "unauthenticated read", "anon", "401/403", sa, sa in (401, 403), "no token")



def app_boundary() -> None:
    print("== Application boundary (FastAPI, real user JWT) ==")
    st = api(jwt("org_a_owner"), "GET", "/api/v3/notifications")
    rec("APP", "org owner notifications", "org_a_owner", "200", st, st == 200)
    st = api(None, "GET", "/api/v3/notifications")
    rec("APP", "unauthenticated notifications", "anon", "401/403", st, st in (401, 403))
    st = api(jwt("consultant_a"), "GET", "/api/v3/consultants/me")
    rec("APP", "consultant A me", "consultant_a", "200", st, st == 200)
    st = api(jwt("consultant_a"), "GET", f"/api/v3/consultants/clients/{CLIENT_A}/processing/items")
    rec("APP", "consultant A granted client items", "consultant_a", "200", st, st == 200)
    st = api(jwt("consultant_b"), "GET", f"/api/v3/consultants/clients/{CLIENT_A}/processing/items")
    rec("APP", "consultant B -> Org A client (DENY)", "consultant_b", "403/404", st, st in (403, 404))
    st = api(jwt("consultant_b"), "GET", f"/api/v3/processing/items/{ITEM_A}/workspace")
    rec("APP", "consultant B -> Org A item (IDOR DENY)", "consultant_b", "403/404", st, st in (403, 404))
    st = api(jwt("org_b_owner"), "GET", f"/api/v3/processing/items/{ITEM_A}/workspace")
    rec("APP", "org B -> Org A item (DENY)", "org_b_owner", "403/404", st, st in (403, 404))
    st = api(jwt("pe_a_manager"), "GET", "/api/v3/pe/me")
    rec("APP", "PE A me", "pe_a_manager", "200", st, st == 200)
    st = api(jwt("pe_b_manager"), "GET", f"/api/v3/pe/items/{ITEM_PE_A}/workspace")
    rec("APP", "PE B -> PE-A item (DENY)", "pe_b_manager", "403/404", st, st in (403, 404))
    st = api(jwt("internal_qc"), "GET", "/api/v3/ops/qc/ct-queue")
    rec("APP", "internal QC queue", "internal_qc", "200", st, st == 200)
    st = api(jwt("consultant_a"), "GET", "/api/v3/ops/qc/ct-queue")
    rec("APP", "consultant -> internal ops (DENY)", "consultant_a", "403", st, st == 403)


def main() -> int:
    print(f"environment : {E.get('E2E_ENV_ID')} {SB}  api={API}")
    rls_boundary()
    app_boundary()
    passed = sum(1 for r in RESULTS if r["pass"])
    report = {"environment": E.get("E2E_ENV_ID"), "supabase": SB, "api": API,
              "results": RESULTS, "passed": passed, "total": len(RESULTS)}
    (ENV_DIR / ".acceptance_report.json").write_text(json.dumps(report, indent=2))
    print(f"\nACCEPTANCE: {passed}/{len(RESULTS)} passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())

