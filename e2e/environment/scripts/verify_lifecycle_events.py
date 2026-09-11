#!/usr/bin/env python3
"""P6-2F — D11 lifecycle-event verification and lifecycle-transition regression.

Runs ONLY against the isolated E2E project (refuses unless the target is port
55325) and exercises the REAL backend endpoints with REAL GoTrue personas, so it
also acts as the regression guard for the repository SQL paths those endpoints
use (`ConsultantsRepository.transition_client_lifecycle` / `update_task_status`).

Why this script exists (P6-2F finding LT-1): those two statements assigned a
parameter to a ``character varying`` status column while also comparing it with
text literals. PostgreSQL rejected the statement ("inconsistent types deduced for
parameter $2") so the customer acceptance endpoint returned HTTP 500. It was
never caught because unit tests use a *fake* repository (the SQL never executes)
and the dedicated integration database's schema is stale (its consultant suite
errors on ``can_extract`` before reaching the statement). This script runs the
real endpoint against a current schema, so a regression fails loudly.

Evidence produced per event: HTTP outcome, resulting entity state, the persisted
notification rows (event_key / type / recipients / title / link / actor_domain),
server-side recipient derivation, replay behaviour and a denied path.

State: the script CONSUMES lifecycle fixtures and RESTORES them at the end, so
the documented run order (fixtures -> this -> acceptance -> browser) is safe.

Writes: e2e/environment/.lifecycle_evidence_report.json  (gitignored)
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ENV_DIR = HERE.parent
REPO = ENV_DIR.parents[1]
E2E_ENV = ENV_DIR / ".env.e2e"
PERSONAS = REPO / "tests" / "e2e" / ".env.personas"
REPORT = ENV_DIR / ".lifecycle_evidence_report.json"

CHECKS: list[tuple[str, bool, str]] = []


def load(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"')
    return out


def check(name: str, ok: bool, detail: str = "") -> bool:
    CHECKS.append((name, bool(ok), detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
    return bool(ok)


env = load(E2E_ENV)
per = load(PERSONAS)
SUPA = env["E2E_SUPABASE_URL"]
if "55325" not in SUPA:
    raise SystemExit(f"REFUSING: target is not the isolated project: {SUPA}")
API = per.get("E2E_API_URL") or "http://127.0.0.1:8051"
SERVICE = env["E2E_SERVICE_ROLE_KEY"]
ANON = env["E2E_ANON_KEY"]
AH = {"apikey": SERVICE, "Authorization": f"Bearer {SERVICE}", "Accept": "application/json"}
WH = {**AH, "Content-Type": "application/json", "Prefer": "return=minimal"}


def rest(path: str):
    r = requests.get(f"{SUPA}/rest/v1/{path}", headers=AH, timeout=30)
    r.raise_for_status()
    return r.json()


def rest_write(path: str, rows):
    r = requests.post(f"{SUPA}/rest/v1/{path}", headers=WH, data=json.dumps(rows), timeout=60)
    return r.status_code


def rest_patch(path: str, body: dict) -> int:
    """Partial update — used to restore consumed fixture state (PATCH, so the
    NOT NULL columns of the row are not re-supplied)."""
    r = requests.patch(f"{SUPA}/rest/v1/{path}", headers=WH, data=json.dumps(body), timeout=60)
    return r.status_code


def token(email: str, password: str) -> str:
    r = requests.post(
        f"{SUPA}/auth/v1/token?grant_type=password",
        headers={"apikey": ANON, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=30,
    )
    if r.status_code != 200:
        raise SystemExit(f"REFUSING: sign-in failed for {email}: {r.status_code}")
    return r.json()["access_token"]


def jwt_sub(tok: str) -> str:
    payload = tok.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))["sub"]


def call(method: str, path: str, jwt: str, payload=None):
    r = requests.request(
        method,
        f"{API}{path}",
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
        data=json.dumps(payload) if payload is not None else None,
        timeout=60,
    )
    return r.status_code, r.text[:160]


def notifications(event_key: str) -> list[dict]:
    return rest(
        "notifications?event_key=eq." + event_key
        + "&select=event_key,notification_type,recipient_type,recipient_id,title,link,actor_domain"
        + "&order=created_at.asc"
    )


def item_status(item_id: str) -> str:
    rows = rest(f"manual_extraction_items?id=eq.{item_id}&select=status")
    return rows[0]["status"] if rows else "(missing)"


def client_status(client_id: str) -> str:
    rows = rest(f"consultant_clients?id=eq.{client_id}&select=status")
    return rows[0]["status"] if rows else "(missing)"


EVIDENCE: dict[str, dict] = {}


def record(section: str, key: str, value) -> None:
    EVIDENCE.setdefault(section, {})[key] = value


def main() -> int:
    print(f"target : {SUPA}  api={API}")
    org_b = per["E2E_ORG_B_ID"]
    client_a = per["E2E_CLIENT_A_ID"]
    engagement = per.get("E2E_ENGAGEMENT_PENDING_ID", "")
    item_a2 = per["E2E_ITEM_A2_ID"]   # consultant_reviewed -> submit -> qc_outcome approved
    item_a7 = per["E2E_ITEM_A7_ID"]   # consultant_reviewed -> qc_outcome rejected + rework
    if not engagement:
        raise SystemExit("REFUSING: run seed_lifecycle_fixtures.py first (engagement fixture missing)")

    firm_a = rest(f"consultant_clients?id=eq.{client_a}&select=consultant_id")[0]["consultant_id"]
    firm_members = sorted(
        r["user_id"]
        for r in rest(f"consultant_firm_members?firm_id=eq.{firm_a}&is_active=eq.true&select=user_id")
    )
    jwt_orgb = token(per["E2E_ORG_B_OWNER_EMAIL"], per["E2E_ORG_B_OWNER_PASSWORD"])
    jwt_qc = token(per["E2E_INTERNAL_QC_EMAIL"], per["E2E_INTERNAL_QC_PASSWORD"])
    jwt_cons = token(per["E2E_CONSULTANT_A_EMAIL"], per["E2E_CONSULTANT_A_PASSWORD"])
    print(f"firm A : {firm_a}  active members={len(firm_members)}")
    print("signed in: org B owner, internal QC, consultant A (real GoTrue JWTs)")

    # ------------------------------------------------------------------ #
    # event 1 — `accepted` (also the LT-1 regression guard: this is the
    # customer-acceptance endpoint whose repository SQL previously 500'd)
    # ------------------------------------------------------------------ #
    print("\n== D11 event 1: accepted (customer acceptance endpoint) ==")
    check("accepted: engagement starts pending", client_status(engagement) == "pending",
          client_status(engagement))
    key = f"consultant.lifecycle.accepted:engagement:{engagement}"
    before = len(notifications(key))
    code, body = call("POST",
                      f"/api/v3/organizations/{org_b}/consultant-engagements/{engagement}/accept",
                      jwt_orgb)
    record("accepted", "trigger_http", code)
    record("accepted", "trigger_body", body)
    check("accepted: LT-1 regression — 200 (was 500: ambiguous $2)", code == 200, body)
    check("accepted: engagement is now active", client_status(engagement) == "active",
          client_status(engagement))
    rows = notifications(key)
    record("accepted", "notifications", rows)
    # The event key is deterministic and uniqueness-guarded, so the trigger must
    # yield exactly one row per firm member — and a re-run must find that row
    # rather than adding a second (the replay check below asserts no growth).
    check("accepted: exactly one notification per active firm member (idempotent)",
          len(rows) == len(firm_members), f"rows={len(rows)} members={len(firm_members)}")
    check("accepted: recipients are the server-derived firm members",
          sorted({r["recipient_id"] for r in rows}) == firm_members)
    check("accepted: the accepting customer is not notified of its own decision",
          jwt_sub(jwt_orgb) not in {r["recipient_id"] for r in rows})
    check("accepted: event_key is the deterministic lifecycle key",
          all(r["event_key"] == key for r in rows), key)
    rcode, rbody = call("POST",
                        f"/api/v3/organizations/{org_b}/consultant-engagements/{engagement}/accept",
                        jwt_orgb)
    check("accepted: replay refused (409, no duplicate event)",
          rcode == 409 and len(notifications(key)) == len(rows), f"{rcode} {rbody}")
    dcode, _ = call("POST",
                    f"/api/v3/organizations/{org_b}/consultant-engagements/{engagement}/accept",
                    jwt_cons)
    check("accepted: consultant cannot accept its own engagement (403)", dcode == 403, str(dcode))
    record("accepted", "replay_http", rcode)
    record("accepted", "denied_consultant_http", dcode)

    # ------------------------------------------------------------------ #
    # event 3 — `qc_outcome` (approved / rejected) and event 5 — `rework`
    # ------------------------------------------------------------------ #
    print("\n== D11 event 3/5: qc_outcome and rework ==")
    scode, sbody = call("POST", f"/api/v3/processing/items/{item_a2}/consultant-submit", jwt_cons)
    check("qc_approved: consultant submission accepted (reviewed)",
          scode == 200 and item_status(item_a2) == "reviewed",
          f"{scode} status={item_status(item_a2)}")

    for label, item, approved in (("qc_approved", item_a2, True), ("qc_rejected", item_a7, False)):
        print(f"\n  -- {label} --")
        key_qc = (f"consultant.lifecycle.qc_outcome:item:{item}:"
                  + ("approved" if approved else "rejected"))
        key_rw = f"consultant.lifecycle.rework:item:{item}:ct_qc_rejected"
        check(f"{label}: item is in QC intake (reviewed)", item_status(item) == "reviewed",
              item_status(item))
        code, body = call("POST", f"/api/v3/ops/qc/items/{item}/decision", jwt_qc,
                          {"approved": approved, "quality_score": 88})
        record(label, "trigger_http", code)
        record(label, "trigger_body", body)
        check(f"{label}: QC decision applied", code == 200, body)
        expect = "ct_qc_approved" if approved else "ct_qc_rejected"
        check(f"{label}: item routed to {expect}", item_status(item) == expect, item_status(item))
        qc_rows = notifications(key_qc)
        record(label, "qc_outcome_notifications", qc_rows)
        check(f"{label}: qc_outcome notification persisted with the outcome discriminator",
              len(qc_rows) >= len(firm_members), f"rows={len(qc_rows)} key={key_qc}")
        check(f"{label}: qc_outcome recipients include the engaged firm",
              set(firm_members).issubset({r["recipient_id"] for r in qc_rows}))
        check(f"{label}: qc_outcome actor domain is internal_staff",
              all(r["actor_domain"] == "internal_staff" for r in qc_rows),
              str(sorted({r["actor_domain"] for r in qc_rows})))
        if not approved:
            rw_rows = notifications(key_rw)
            record(label, "rework_notifications", rw_rows)
            check("qc_rejected: rework event persisted with the ct_qc_rejected source",
                  len(rw_rows) >= len(firm_members), f"rows={len(rw_rows)} key={key_rw}")
            check("qc_rejected: rework recipients include the engaged firm",
                  set(firm_members).issubset({r["recipient_id"] for r in rw_rows}))
            check("qc_rejected: rework rows deep-link to the consultant item workspace",
                  all("/consultant/items/" in (r["link"] or "") for r in rw_rows),
                  str([r["link"] for r in rw_rows][:1]))
        rcode2, rbody2 = call("POST", f"/api/v3/ops/qc/items/{item}/decision", jwt_qc,
                              {"approved": approved, "quality_score": 88})
        check(f"{label}: replay refused (409, no duplicate events)",
              rcode2 == 409 and len(notifications(key_qc)) == len(qc_rows), f"{rcode2} {rbody2}")
        dcode2, _ = call("POST", f"/api/v3/ops/qc/items/{item}/decision", jwt_cons,
                         {"approved": True, "quality_score": 88})
        check(f"{label}: consultant cannot make a QC decision (403)", dcode2 == 403, str(dcode2))
        record(label, "replay_http", rcode2)
        record(label, "denied_consultant_http", dcode2)

    # ------------------------------------------------------------------ #
    # restore the fixtures consumed above so the documented run order
    # (fixtures -> this -> acceptance -> browser) stays safe
    # ------------------------------------------------------------------ #
    print("\n== restoring consumed fixtures ==")
    code_a = rest_patch(f"consultant_clients?id=eq.{engagement}", {"status": "pending"})
    code_b = rest_patch(f"manual_extraction_items?id=eq.{item_a2}",
                        {"status": "consultant_reviewed"})
    code_c = rest_patch(f"manual_extraction_items?id=eq.{item_a7}",
                        {"status": "consultant_reviewed"})
    check("fixtures restored (pending engagement + lifecycle item states)",
          all(c in (200, 204) for c in (code_a, code_b, code_c)),
          f"{code_a}/{code_b}/{code_c}")

    REPORT.write_text(json.dumps(EVIDENCE, indent=1, default=str))
    passed = sum(1 for _n, ok, _d in CHECKS if ok)
    failed = [n for n, ok, _d in CHECKS if not ok]
    print("\n" + "=" * 70)
    print(f"LIFECYCLE EVIDENCE: {passed}/{len(CHECKS)} checks passed; {len(failed)} failed")
    for n in failed:
        print(f"  FAILED: {n}")
    print(f"report: {REPORT}")
    print("=" * 70)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
