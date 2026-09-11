#!/usr/bin/env python3
"""P6-2F — deterministic LIFECYCLE-STATE fixtures for the browser acceptance suite.

Why this exists: the consultant lifecycle browser specs need items that are
legitimately in the lifecycle states the real UI gates on
(`calculated` → `consultant_reviewed` → `reviewed` → `ct_qc_approved`), and the
D11 notification deep-link spec needs a lifecycle notification that was produced
by the REAL workflow (not inserted directly).

This script is E2E-only:
  * refuses to run unless the target is the isolated project (port 55325);
  * inserts extra synthetic items into `manual_extraction_items` (same batch/org
    as the existing fixture, deterministic uuid5 ids, idempotent upsert);
  * drives ONE item forward through the real consultant endpoints
    (`/consultant-submit`) so that `submitted_to_qc` emits a durable,
    firm-centric D11 notification via the application itself;
  * appends the new ids to the gitignored tests/e2e/.env.personas.

No product code, schema, RLS, role, capability or recipient policy is changed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ENV_DIR = HERE.parent
REPO = ENV_DIR.parents[1]
sys.path.insert(0, str(HERE))
from seed_e2e import (  # noqa: E402
    BATCH_A, FIRM_A, ITEM_A, ITEM_PE_A, NS, ORG_A, ORG_B, PE_A, PERSONAS,
    PASSWORD, det, load_env, uid,
)

SUB_A = det("subscription:org-a")
SUB_B = det("subscription:org-b")
ALLOWANCE_ID = det("billingcfg:standard-allowance")
PE_ASSIGN_ID = det("workassign:pe-a")

ITEM_A2 = det("item:a2")   # consultant_reviewed  -> "Submit to CarbonTally QC" visible
ITEM_A3 = det("item:a3")   # ct_qc_approved       -> browser member-DENY
ITEM_A6 = det("item:a6")   # ct_qc_approved       -> (charge key burned by pre-009 500s)
ITEM_A7 = det("item:a7")   # consultant_reviewed  -> fixture drives submit -> notification
ITEM_A8 = det("item:a8")   # ct_qc_approved       -> FRESH, unused charge key (D6 approval)
ITEM_A9 = det("item:a9")   # calculated           -> browser pass-review (run-reset)
ITEM_A10 = det("item:a10")  # consultant_reviewed -> browser submit-to-QC (run-reset)
# D11 `accepted` — a PENDING engagement (origin `engagement_request`) that the
# ORG-B owner accepts through the real customer endpoint. ORG-B/FIRM-A is a pair
# no other P6-2F assertion depends on, so this cannot perturb existing evidence.
ENGAGEMENT_B_PENDING = det("engagement:org-b-firm-a")
EMAIL = {k: e for k, e, _r, _s in PERSONAS}
PERSONA_FILE = REPO / "tests" / "e2e" / ".env.personas"


def item(iid: str, status: str, name: str, firm: str | None = None) -> dict:
    return {"id": iid, "batch_id": BATCH_A, "file_name": name,
            "file_url": f"/uploads/{ORG_A}/{name}", "page_count": 1, "status": status,
            "processing_origin": "CARBONTALLY_INTERNAL", "processing_entity_id": None,
            "consultant_firm_id": firm, "processing_mode": "manual",
            "extracted_data": {"items": []}}


def main() -> int:
    env = load_env()
    url = env["E2E_SUPABASE_URL"]
    if "55325" not in url:
        raise SystemExit(f"REFUSING: target is not the isolated project: {url}")
    key, anon = env["E2E_SERVICE_ROLE_KEY"], env["E2E_ANON_KEY"]
    h = {"apikey": key, "Authorization": f"Bearer {key}",
         "Content-Type": "application/json", "Accept": "application/json",
         "Prefer": "return=minimal,resolution=merge-duplicates"}
    print(f"target : {env.get('E2E_ENV_ID')} {url}")

    # 1. lifecycle-state items (idempotent upsert on id)
    rows = [item(ITEM_A2, "consultant_reviewed", "p6f-org-a-a2.pdf", FIRM_A),
            item(ITEM_A3, "ct_qc_approved", "p6f-org-a-a3.pdf", FIRM_A),
            item(ITEM_A6, "ct_qc_approved", "p6f-org-a-a6.pdf", FIRM_A),
            item(ITEM_A7, "consultant_reviewed", "p6f-org-a-a7.pdf", FIRM_A),
            item(ITEM_A8, "ct_qc_approved", "p6f-org-a-a8.pdf", FIRM_A),
            item(ITEM_A9, "calculated", "p6f-org-a-a9.pdf", FIRM_A),
            item(ITEM_A10, "consultant_reviewed", "p6f-org-a-a10.pdf", FIRM_A)]
    r = requests.post(f"{url}/rest/v1/manual_extraction_items?on_conflict=id",
                      headers=h, data=json.dumps(rows), timeout=60)
    print(f"items  : {r.status_code} {r.text[:160]}")

    # 1a-R5 — the base item worked on by the consultant-surface browser specs
    # must legitimately belong to FIRM_A (consultant_firm_id), so the surface
    # presents its review/submit controls instead of the spec skipping.
    r = requests.post(f"{url}/rest/v1/manual_extraction_items?on_conflict=id",
                      headers=h, data=json.dumps([item(ITEM_A, "calculated",
                                                       "p6f-org-a.pdf", FIRM_A)]),
                      timeout=60)
    print(f"item A : {r.status_code} {r.text[:160]}")

    # 1c-R1 — canonical STANDARD allowance config: the approval-time gate reads
    #     billing_commercial_config['standard_allowance'].monthly_processing_units
    #     (backend/services/billing.py:113-126). Without it `remaining` is 0 and
    #     the canonical approval charge fails closed with 402.
    cfg = [{"id": ALLOWANCE_ID, "config_key": "standard_allowance",
            "config_value": {"monthly_processing_units": 100},
            "version": 2, "effective_from": "2026-01-01T00:00:00Z",
            "reason": "P6-2F isolated E2E allowance fixture"}]
    r = requests.post(f"{url}/rest/v1/billing_commercial_config?on_conflict=config_key,version",
                      headers=h, data=json.dumps(cfg), timeout=60)
    print(f"allow  : {r.status_code} {r.text[:200]}")

    # 1d-R4 — PE work assignment row (the table is empty in the seed, and the PE
    #     workspace handler re-validates item<->assignment via _ensure_assigned_item).
    asg = [{"id": PE_ASSIGN_ID, "manual_extraction_item_id": ITEM_PE_A,
            "processing_entity_id": PE_A, "assignee_kind": "processing_entity",
            "assigned_to": None, "action": "assign",
            "actor_domain": "processing_entity", "assigned_by": uid("pe_a_manager"),
            "status": "open"}]
    r = requests.post(f"{url}/rest/v1/work_item_assignments?on_conflict=id",
                      headers=h, data=json.dumps(asg), timeout=60)
    print(f"assign : {r.status_code} {r.text[:200]}")

    # 1b. D6 — active CLIENT-ORGANISATION subscription. The server gate is
    #     `customer_subscriptions.lifecycle_status IN (trial,active,past_due,suspended)`
    #     (backend/data/billing.py:get_active_for_org); without it the backend
    #     correctly fails closed with 403 "No active processing entitlement".
    #     Ownership stays with the client organisation — no consultant/PE owner.
    subs = [{"id": SUB_A, "organization_id": ORG_A, "plan": "pro", "plan_code": "pro",
             "lifecycle_status": "active", "status": "active", "billing_mode": "STANDARD",
             "currency": "GBP"},
            {"id": SUB_B, "organization_id": ORG_B, "plan": "pro", "plan_code": "pro",
             "lifecycle_status": "active", "status": "active", "billing_mode": "STANDARD",
             "currency": "GBP"}]
    r = requests.post(f"{url}/rest/v1/customer_subscriptions?on_conflict=id",
                      headers=h, data=json.dumps(subs), timeout=60)
    print(f"subs   : {r.status_code} {r.text[:160]}")

    # 1e. D11 `accepted` — reset the PENDING engagement to `pending` so the
    #     ORG-B owner can accept it through the real customer endpoint
    #     (acceptance is the ONLY pending -> active path, P6-1C). Idempotent:
    #     re-asserting `pending` makes the `accepted` event reproducible after a
    #     previous run already moved it to active (the event itself is
    #     uniqueness-guarded by its deterministic event_key).
    eng = [{"id": ENGAGEMENT_B_PENDING, "consultant_id": FIRM_A, "organization_id": ORG_B,
            "client_name": "P6F Org B (pending engagement)", "status": "pending",
            "relationship_origin": "engagement_request", "created_by": uid("consultant_a")}]
    r = requests.post(f"{url}/rest/v1/consultant_clients?on_conflict=id",
                      headers=h, data=json.dumps(eng), timeout=60)
    print(f"engage : {r.status_code} {r.text[:200]}")

    # 2. drive ITEM_A7 through the REAL workflow so submitted_to_qc emits a
    #    durable firm-centric notification (no direct notification insert).
    t = requests.post(f"{url}/auth/v1/token?grant_type=password",
                      headers={"apikey": anon, "Content-Type": "application/json"},
                      json={"email": EMAIL["consultant_a"], "password": PASSWORD}, timeout=30)
    jwt = t.json().get("access_token", "") if t.status_code == 200 else ""
    api = os.environ.get("E2E_API_URL", "http://127.0.0.1:8051")
    if jwt:
        r = requests.post(f"{api}/api/v3/processing/items/{ITEM_A7}/consultant-submit",
                          headers={"Authorization": f"Bearer {jwt}"}, timeout=60)
        print(f"submit : item A7 -> {r.status_code} {r.text[:160]}")
    else:
        print(f"submit : SKIPPED (sign-in {t.status_code})")

    # 3. expose the ids to Playwright (gitignored file)
    lines = [l for l in PERSONA_FILE.read_text().splitlines()
             if not l.startswith(("E2E_ITEM_A_ID=", "E2E_ITEM_A2_ID=", "E2E_ITEM_A3_ID=",
                                  "E2E_ITEM_A6_ID=", "E2E_ITEM_A7_ID=",
                                  "E2E_ENGAGEMENT_PENDING_ID=",
                                  "E2E_API_URL="))]
    # §4 — point the mutating browser specs at dedicated run-reset items so a
    # repeated run cannot consume the state they assert on.
    lines += [f"E2E_API_URL={api}", f"E2E_ITEM_A_ID={ITEM_A9}",
              f"E2E_ITEM_A2_ID={ITEM_A10}",
              f"E2E_ITEM_A3_ID={ITEM_A3}", f"E2E_ITEM_A6_ID={ITEM_A6}",
              f"E2E_ITEM_A7_ID={ITEM_A7}",
              f"E2E_ENGAGEMENT_PENDING_ID={ENGAGEMENT_B_PENDING}"]
    PERSONA_FILE.write_text("\n".join(lines) + "\n")
    print(f"personas: {PERSONA_FILE}")
    print("LIFECYCLE FIXTURES OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
