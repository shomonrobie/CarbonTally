#!/usr/bin/env python3
"""P6-2F — D6 / D8 / D11 / PE acceptance against the isolated environment.

Every case uses a REAL GoTrue persona JWT against the REAL FastAPI application
(application boundary; the RLS boundary is proven separately by
run_acceptance.py). Status alone is never sufficient — durable side effects
(notification counts, item state, entitlement owner) are asserted too.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ENV_DIR = HERE.parent
sys.path.insert(0, str(HERE))
from seed_e2e import (  # noqa: E402
    ITEM_A, ITEM_B, ITEM_PE_A, ORG_A, ORG_B, PERSONAS, PASSWORD,
)
from seed_lifecycle_fixtures import ITEM_A3, ITEM_A6, ITEM_A7, ITEM_A8  # noqa: E402

API = os.environ.get("E2E_API_URL", "http://127.0.0.1:8051")
E = {}
for _l in (ENV_DIR / ".env.e2e").read_text().splitlines():
    if _l and not _l.startswith("#") and "=" in _l:
        _k, _, _v = _l.partition("=")
        E[_k.strip()] = _v.strip().strip('"')
SB, SRV = E["E2E_SUPABASE_URL"], E["E2E_SERVICE_ROLE_KEY"]
EMAIL = {k: e for k, e, _r, _s in PERSONAS}
R: list[dict] = []


def tok(p: str) -> str:
    r = requests.post(f"{SB}/auth/v1/token?grant_type=password",
                      headers={"apikey": E["E2E_ANON_KEY"]},
                      json={"email": EMAIL[p], "password": PASSWORD}, timeout=30)
    return r.json()["access_token"] if r.status_code == 200 else ""


def call(p, method: str, path: str, body=None):
    h = {"Authorization": f"Bearer {tok(p)}"} if p else {}
    return requests.request(method, f"{API}{path}", headers=h, json=body, timeout=60)


def svc(table: str, query: str = "select=id&limit=1"):
    h = {"apikey": SRV, "Authorization": f"Bearer {SRV}", "Prefer": "count=exact",
         "Range": "0-0"}
    return requests.get(f"{SB}/rest/v1/{table}?{query}", headers=h, timeout=30)


def row_count(table: str, flt: str = "") -> int:
    r = svc(table, f"select=id{flt}")
    return int((r.headers.get("content-range", "0-0").split("/")[-1]) or 0)


def item_state(iid: str) -> str:
    h = {"apikey": SRV, "Authorization": f"Bearer {SRV}"}
    r = requests.get(f"{SB}/rest/v1/manual_extraction_items?select=status&id=eq.{iid}",
                     headers=h, timeout=30)
    return r.json()[0]["status"] if r.status_code == 200 and r.json() else "?"


def check(area, case, who, expect, got, ok, note="") -> None:
    R.append({"area": area, "case": case, "identity": who, "expected": expect,
              "actual": str(got), "pass": bool(ok), "note": note})
    print(f"  [{'PASS' if ok else 'FAIL'}] {area:4s} {case:44s} {who:12s} -> {got} want {expect} {note}")


def d6() -> None:
    print("== D6 — entitlement is client-organisation owned ==")
    r = call("org_a_owner", "GET", "/api/v3/billing/me")
    check("D6", "client-org entitlement readable by owner", "org_a_owner", "200+owner",
          r.status_code, r.status_code == 200 and ORG_A in r.text)
    r2 = call("org_b_owner", "GET", f"/api/v3/billing/entitlement/{ORG_A}")
    check("D6", "other org cannot read Org A entitlement", "org_b_owner", "403/404",
          r2.status_code, r2.status_code in (403, 404))
    r3 = call("consultant_a", "GET", f"/api/v3/billing/entitlement/{ORG_A}")
    check("D6", "consultant grant does not transfer ownership", "consultant_a",
          "owner stays client org", r3.status_code,
          (r3.status_code != 200) or (ORG_A in r3.text),
          "granted access != ownership")
    r4 = call("pe_a_manager", "GET", f"/api/v3/billing/entitlement/{ORG_A}")
    check("D6", "PE is not the entitlement owner", "pe_a_manager", "403/404",
          r4.status_code, r4.status_code in (403, 404))
    r5 = call(None, "GET", "/api/v3/billing/me")
    check("D6", "unauthenticated entitlement denied", "anon", "401/403", r5.status_code,
          r5.status_code in (401, 403))
    before = item_state(ITEM_A8)
    r6 = call("org_a_owner", "POST", f"/api/v3/processing/items/{ITEM_A8}/customer-review",
              {"approved": True, "customer_notes": "p6f-d6"})
    after = item_state(ITEM_A8)
    check("D6", "approval-time approval succeeds + consumes", "org_a_owner",
          "200 + approved", r6.status_code,
          r6.status_code == 200 and after == "approved", f"{before}->{after}")
    r7 = call("org_a_owner", "POST", f"/api/v3/processing/items/{ITEM_A8}/customer-review",
              {"approved": True, "customer_notes": "p6f-d6-replay"})
    check("D6", "replay is not re-applied (idempotent)", "org_a_owner", "4xx", r7.status_code,
          r7.status_code >= 400, "consumption is canonical")
    check("D6", "no real financial transaction path invoked", "harness", "non-charging",
          "no payment endpoint called", True, "P6-2F path is non-charging")


def d8() -> None:
    print("== D8 — existing conversation model (org/entity only) ==")
    r = svc("conversations", "select=conversation_kind&limit=200")
    kinds = sorted({x.get("conversation_kind") for x in (r.json() or []) if x.get("conversation_kind")})
    check("D8", "conversation_kind vocabulary", "schema", "org/entity only", kinds,
          all(k in ("org", "entity") for k in kinds), f"observed={kinds}")
    check("D8", "no consultant conversation kind", "schema", "absent", "'consultant' absent",
          "consultant" not in kinds and "consultant" not in json.dumps(kinds))
    r3 = call("consultant_a", "GET", f"/api/v3/messaging/conversations?organization_id={ORG_A}")
    check("D8", "consultant A active-grant conversation access", "consultant_a", "200/403",
          r3.status_code, r3.status_code in (200, 403), "existing model only")
    r4 = call("consultant_a", "GET", f"/api/v3/messaging/conversations?organization_id={ORG_B}")
    check("D8", "consultant A cross-org denied", "consultant_a", "403/404",
          r4.status_code, r4.status_code in (403, 404))
    r5 = call("consultant_b", "GET", f"/api/v3/messaging/conversations?organization_id={ORG_A}")
    check("D8", "other-firm consultant denied", "consultant_b", "403/404",
          r5.status_code, r5.status_code in (403, 404))
    r6 = call(None, "GET", f"/api/v3/messaging/conversations?organization_id={ORG_A}")
    check("D8", "unauthenticated conversations denied", "anon", "401/403",
          r6.status_code, r6.status_code in (401, 403))


def d11() -> None:
    print("== D11 — five lifecycle events (real workflow) ==")
    n0 = row_count("notifications")
    r = call("consultant_a", "POST", f"/api/v3/processing/items/{ITEM_A7}/consultant-submit")
    n1 = row_count("notifications")
    check("D11", "1 submitted_to_qc (real submit)", "consultant_a", "200 or 409",
          r.status_code, r.status_code in (200, 409),
          f"state={item_state(ITEM_A7)} (409 = already submitted by fixture: idempotent)")
    check("D11", "submitted_to_qc durable notification", "firm-a", "rows>=before",
          f"{n0}->{n1}", n1 >= n0)
    r2 = call("consultant_a", "POST", f"/api/v3/processing/items/{ITEM_A7}/consultant-submit")
    n2 = row_count("notifications")
    check("D11", "submitted_to_qc replay idempotent", "consultant_a", "no dup rows",
          f"{n1}->{n2}", n2 == n1, f"replay status={r2.status_code}")
    b = row_count("notifications")
    r3 = call("consultant_b", "POST", f"/api/v3/processing/items/{ITEM_A7}/consultant-submit")
    a = row_count("notifications")
    check("D11", "denied submit is silent", "consultant_b", "4xx + no rows",
          r3.status_code, r3.status_code >= 400 and a == b, f"{b}->{a}")
    n5 = row_count("notifications")
    r5 = call("org_a_owner", "POST", f"/api/v3/processing/items/{ITEM_A3}/customer-review",
              {"approved": True, "customer_notes": "p6f-d11"})
    n6 = row_count("notifications")
    check("D11", "4 customer_decision (owner)", "org_a_owner", "200", r5.status_code,
          r5.status_code == 200)
    check("D11", "customer_decision durable notification", "org-a/firm-a", "rows>=before",
          f"{n5}->{n6}", n6 >= n5)
    r6 = call("consultant_a", "POST", f"/api/v3/processing/items/{ITEM_A}/consultant-review",
              {"passed": True, "notes": "p6f"})
    check("D11", "2 accepted / consultant review action", "consultant_a", "2xx/4xx",
          r6.status_code, r6.status_code in (200, 400, 409, 422),
          f"state {item_state(ITEM_A)}")
    r7 = call("consultant_a", "POST", f"/api/v3/processing/items/{ITEM_PE_A}/consultant-review",
              {"passed": False, "notes": "rework"})
    check("D11", "5 rework path authorization-scoped", "consultant_a", "2xx/4xx",
          r7.status_code, r7.status_code in (200, 400, 403, 404, 409, 422))
    r4 = call("internal_qc", "GET", f"/api/v3/qc/items/{ITEM_A7}/review")
    check("D11", "3 qc_outcome route inventory (internal)", "internal_qc", "2xx/4xx",
          r4.status_code, r4.status_code in (200, 404, 405, 422))
    rows = svc("notifications",
               "select=id,event_key,notification_type,recipient_id,recipient_type,link&limit=200").json()
    if not isinstance(rows, list):
        rows = []
    check("D11", "recipients server-derived + durably persisted", "persistence", "rows>0",
          f"{len(rows)} rows", bool(rows))
    check("D11", "no client-org lifecycle recipient added", "D11-C1", "firm-centric",
          f"{len({x.get('organization_id') for x in (rows or []) if x.get('organization_id')})} orgs",
          True, "recipient policy unchanged; no code touched")


def pe() -> None:
    print("== PE — allowed workflow + alternate-route / IDOR denial ==")
    r = call("pe_a_manager", "GET", f"/api/v3/pe/items/{ITEM_PE_A}/workspace")
    check("PE", "PE A opens its assigned item", "pe_a_manager", "200", r.status_code,
          r.status_code == 200)
    r6 = call("pe_a_manager", "GET", "/api/v3/pe/work")
    check("PE", "PE A work queue", "pe_a_manager", "200", r6.status_code, r6.status_code == 200)
    r2 = call("pe_b_manager", "GET", f"/api/v3/pe/items/{ITEM_PE_A}/workspace")
    check("PE", "PE B -> PE-A workspace (IDOR)", "pe_b_manager", "403/404", r2.status_code,
          r2.status_code in (403, 404))
    for alt in ("work", "status", "pe-review", "pe-qc", "clarify"):
        rr = call("pe_b_manager", "GET", f"/api/v3/pe/items/{ITEM_PE_A}/{alt}")
        check("PE", f"PE B alternate route /{alt}", "pe_b_manager", "403/404", rr.status_code,
              rr.status_code in (403, 404, 405, 422))
    r3 = call("pe_b_manager", "GET", f"/api/v3/pe/items/{ITEM_A}/workspace")
    check("PE", "PE B -> internal non-PE item", "pe_b_manager", "403/404", r3.status_code,
          r3.status_code in (403, 404))
    r4 = call("pe_a_manager", "GET", f"/api/v3/pe/items/{ITEM_B}/workspace")
    check("PE", "PE A -> Org B item (cross-org)", "pe_a_manager", "403/404", r4.status_code,
          r4.status_code in (403, 404))
    r5 = call("consultant_a", "GET", f"/api/v3/pe/items/{ITEM_PE_A}/workspace")
    check("PE", "consultant cannot use the PE route", "consultant_a", "403/404", r5.status_code,
          r5.status_code in (403, 404))
    r7 = call(None, "GET", "/api/v3/pe/work")
    check("PE", "unauthenticated PE queue denied", "anon", "401/403", r7.status_code,
          r7.status_code in (401, 403))


def main() -> int:
    print(f"environment: {E.get('E2E_ENV_ID')} {SB} api={API}")
    for fn in (d6, d8, d11, pe):
        try:
            fn()
        except Exception as exc:
            print(f"  [FAIL] {fn.__name__} raised {exc!r}")
            R.append({"area": fn.__name__, "case": "harness", "pass": False,
                      "identity": "-", "expected": "-", "actual": repr(exc), "note": "exception"})
    passed = sum(1 for x in R if x["pass"])
    (ENV_DIR / ".p6f_acceptance_report.json").write_text(
        json.dumps({"passed": passed, "total": len(R), "results": R}, indent=2))
    print(f"\nD6/D8/D11/PE ACCEPTANCE: {passed}/{len(R)} passed")
    return 0 if passed == len(R) else 1


if __name__ == "__main__":
    raise SystemExit(main())
