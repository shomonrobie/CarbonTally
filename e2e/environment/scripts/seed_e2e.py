#!/usr/bin/env python3
"""P6-2F — seed the ISOLATED E2E database with deterministic synthetic fixtures.

Safety: refuses to run unless the target is the isolated project
(`carbontally_e2e`, port 55326). Never touches the demo instance.

Design: rows are declared as dicts and filtered against the *live* column set
(introspected from the isolated DB), so the seeder is robust to schema detail.
All ids are deterministic; all inserts are idempotent upserts on `id`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

HERE = Path(__file__).resolve().parent
ENV_DIR = HERE.parent
REPO = ENV_DIR.parents[1]
ENV_FILE = ENV_DIR / ".env.e2e"
PERSONA_FILE = REPO / "tests" / "e2e" / ".env.personas"

NS = "carbontally-e2e-p6f"
PASSWORD = "CarbonTally-E2E-Local-2026!"


def det(key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{NS}:{key}"))


def load_env() -> dict:
    out = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip('"')
    return out


class Db:
    def __init__(self, env: dict):
        self.url = env["E2E_SUPABASE_URL"]
        # DB port comes from the DB URL (the API URL port is different).
        import re as _re
        m = _re.search(r":(\d+)/", env.get("E2E_DB_URL", ""))
        self.db_port = m.group(1) if m else "55326"
        self.key = env["E2E_SERVICE_ROLE_KEY"]
        self.anon = env["E2E_ANON_KEY"]
        self.h = {"apikey": self.key, "Authorization": f"Bearer {self.key}",
                  "Content-Type": "application/json", "Accept": "application/json"}
        self.s = requests.Session()

    # -- target proof -------------------------------------------------------
    def assert_isolated(self) -> None:
        if "55325" not in self.url:
            raise SystemExit(f"REFUSING: target is not the isolated project: {self.url}")

    # -- introspection ------------------------------------------------------
    def columns(self, table: str) -> set[str]:
        cmd = ["psql", "-h", "127.0.0.1", "-p", self.db_port, "-U", "postgres",
               "-d", "postgres", "-tAc",
               f"select column_name from information_schema.columns "
               f"where table_schema='public' and table_name='{table}'"]
        env = dict(os.environ, PGPASSWORD="postgres")
        out = subprocess.run(cmd, capture_output=True, text=True, env=env).stdout
        return {l.strip() for l in out.splitlines() if l.strip()}

    def insert(self, table: str, rows: list[dict]) -> tuple[int, Optional[str]]:
        if not rows:
            return 0, None
        cols = self.columns(table)
        if not cols:
            return 0, f"table {table} has no columns (missing?)"
        payload = [{k: v for k, v in r.items() if k in cols} for r in rows]
        url = f"{self.url}/rest/v1/{table}?on_conflict=id"
        h = dict(self.h, Prefer="return=minimal,resolution=merge-duplicates")
        r = self.s.post(url, headers=h, data=json.dumps(payload), timeout=60)
        if r.status_code not in (200, 201, 204):
            return 0, f"{r.status_code} {r.text[:220]}"
        return len(payload), None

    # -- auth ---------------------------------------------------------------
    def ensure_user(self, email: str, uid: str, metadata: dict) -> str:
        r = self.s.post(
            f"{self.url}/auth/v1/admin/users",
            headers={"apikey": self.anon, "Authorization": f"Bearer {self.key}",
                     "Content-Type": "application/json"},
            data=json.dumps({"email": email, "password": PASSWORD, "email_confirm": True,
                             "id": uid, "user_metadata": metadata}),
            timeout=30,
        )
        if r.status_code in (200, 201):
            return "created"
        if r.status_code in (409, 422):
            return "exists"
        return f"ERR {r.status_code} {r.text[:140]}"

    def sign_in(self, email: str) -> tuple[int, str]:
        r = self.s.post(
            f"{self.url}/auth/v1/token?grant_type=password",
            headers={"apikey": self.anon, "Content-Type": "application/json"},
            data=json.dumps({"email": email, "password": PASSWORD}), timeout=30,
        )
        if r.status_code == 200:
            return 200, r.json().get("access_token", "")
        return r.status_code, r.text[:140]


PERSONAS = [
    ("org_a_owner",  "org.a.owner@p6f.carbontally.local",    "org_owner",  "org-a"),
    ("org_a_admin",  "org.a.admin@p6f.carbontally.local",    "org_admin",  "org-a"),
    ("org_a_member", "org.a.member@p6f.carbontally.local",   "member",     "org-a"),
    ("org_a_viewer", "org.a.viewer@p6f.carbontally.local",   "viewer",     "org-a"),
    ("org_b_owner",  "org.b.owner@p6f.carbontally.local",    "org_owner",  "org-b"),
    ("org_b_member", "org.b.member@p6f.carbontally.local",   "member",     "org-b"),
    ("consultant_a", "consultant.a@p6f.carbontally.local",   "consultant", "firm-a"),
    ("consultant_b", "consultant.b@p6f.carbontally.local",   "consultant", "firm-b"),
    ("pe_a_manager", "pe.a.manager@p6f.carbontally.local",   "pe_manager", "pe-a"),
    ("pe_a_staff",   "pe.a.staff@p6f.carbontally.local",     "pe_staff",   "pe-a"),
    ("pe_b_manager", "pe.b.manager@p6f.carbontally.local",   "pe_manager", "pe-b"),
    ("internal_qc",  "internal.qc@p6f.carbontally.local",    "qc",         "internal"),
    ("internal_ops", "internal.ops@p6f.carbontally.local",   "ops",        "internal"),
]
SCOPES = {k: sc for k, _e, _r, sc in PERSONAS}

ORG_A, ORG_B = det("org:a"), det("org:b")
PE_A, PE_B = det("entity:a"), det("entity:b")
FIRM_A, FIRM_B = det("firm:a"), det("firm:b")
CLIENT_A, CLIENT_B = det("client:a"), det("client:b")
CLIENT_A_SUSP = det("client:a-suspended")
BATCH_A, BATCH_B, BATCH_PE_A = det("batch:a"), det("batch:b"), det("batch:pe-a")
ITEM_A, ITEM_B, ITEM_PE_A = det("item:a"), det("item:b"), det("item:pe-a")
ROLE_QC, ROLE_OPS = det("staffrole:qc"), det("staffrole:ops")


def uid(p: str) -> str:
    return det(f"user:{p}")


def _org(oid: str, name: str) -> dict:
    return {"id": oid, "name": name, "industry": "Manufacturing", "sector": "Industry",
            "company_size": "51-200", "country": "GB", "currency": "GBP",
            "timezone": "Europe/London", "financial_year_end": "2025-12-31",
            "reporting_standard": "GHG Protocol", "secr_enabled": True, "esrs_enabled": False,
            "issb_enabled": False, "default_factor_year": 2025, "preferred_units": "kWh",
            "primary_contact_email": "owner@p6f.test", "primary_contact_name": "Owner",
            "billing_contact_email": "admin@p6f.test", "billing_contact_name": "Admin",
            "subscription_status": "active", "subscription_tier": "pro",
            "city": "Manchester", "county": "Greater Manchester", "postcode": "M1 1AA",
            "address_line1": "1 Test Street", "is_public": False, "reporting_frequency": "annual",
            "is_active": True, "metadata": {"e2e": True, "namespace": NS}}


NOW = "2026-01-01T00:00:00Z"


def rows() -> dict[str, list[dict]]:
    return {
        "organizations": [_org(ORG_A, "P6F Organisation A"), _org(ORG_B, "P6F Organisation B")],
        "organization_metadata": [
            {"id": det("orgmeta:a"), "organization_id": ORG_A, "total_employees": 120,
             "full_time_employees": 100, "annual_revenue": 15000000,
             "reporting_standard": "GHG Protocol", "industry_sector": "Manufacturing",
             "custom_metrics": {"e2e": True}},
            {"id": det("orgmeta:b"), "organization_id": ORG_B, "total_employees": 60,
             "full_time_employees": 50, "annual_revenue": 7000000,
             "reporting_standard": "GHG Protocol", "industry_sector": "Logistics",
             "custom_metrics": {"e2e": True}},
        ],
        "users": [
            {"id": uid(k), "email": e, "first_name": k.split("_")[-1].title(), "last_name": "P6F",
             "user_type": "staff" if sc in ("internal", "pe-a", "pe-b") else "customer",
             "is_active": True, "email_verified": True, "created_at": NOW}
            for k, e, _r, sc in PERSONAS
        ],
        "organization_members": [
            {"organization_id": ORG_A, "user_id": uid("org_a_owner"), "role": "owner", "is_active": True, "created_at": NOW},
            {"organization_id": ORG_A, "user_id": uid("org_a_admin"), "role": "admin", "is_active": True, "created_at": NOW},
            {"organization_id": ORG_A, "user_id": uid("org_a_member"), "role": "member", "is_active": True, "created_at": NOW},
            {"organization_id": ORG_A, "user_id": uid("org_a_viewer"), "role": "viewer", "is_active": True, "created_at": NOW},
            {"organization_id": ORG_B, "user_id": uid("org_b_owner"), "role": "owner", "is_active": True, "created_at": NOW},
            {"organization_id": ORG_B, "user_id": uid("org_b_member"), "role": "member", "is_active": True, "created_at": NOW},
        ],
        "staff_roles": [
            {"id": ROLE_QC, "name": "qc_specialist", "description": "P6F QC",
             "permissions": {"can_qc": True, "can_review": True}, "is_active": True},
            {"id": ROLE_OPS, "name": "p6f_ops", "description": "P6F Ops",
             "permissions": {"can_manage_staff": True, "can_view_all": True}, "is_active": True},
        ],
        "processing_entities": [
            {"id": PE_A, "name": "P6F Processing Entity A Ltd", "status": "active",
             "description": "Synthetic PE A", "metadata": {"e2e": True}},
            {"id": PE_B, "name": "P6F Processing Entity B Ltd", "status": "active",
             "description": "Synthetic PE B", "metadata": {"e2e": True}},
        ],
        "staff_profiles": [
            {"id": det("sp:qc"), "user_id": uid("internal_qc"), "first_name": "Internal",
             "last_name": "QC", "email": "internal.qc@p6f.carbontally.local", "role_id": ROLE_QC,
             "entity_id": None, "is_active": True},
            {"id": det("sp:ops"), "user_id": uid("internal_ops"), "first_name": "Internal",
             "last_name": "Ops", "email": "internal.ops@p6f.carbontally.local", "role_id": ROLE_OPS,
             "entity_id": None, "is_active": True},
            {"id": det("sp:pe-a-mgr"), "user_id": uid("pe_a_manager"), "first_name": "PEA",
             "last_name": "Manager", "email": "pe.a.manager@p6f.carbontally.local",
             "role_id": ROLE_QC, "entity_id": PE_A, "is_active": True},
            {"id": det("sp:pe-a-staff"), "user_id": uid("pe_a_staff"), "first_name": "PEA",
             "last_name": "Staff", "email": "pe.a.staff@p6f.carbontally.local",
             "role_id": ROLE_OPS, "entity_id": PE_A, "is_active": True},
            {"id": det("sp:pe-b-mgr"), "user_id": uid("pe_b_manager"), "first_name": "PEB",
             "last_name": "Manager", "email": "pe.b.manager@p6f.carbontally.local",
             "role_id": ROLE_QC, "entity_id": PE_B, "is_active": True},
        ],
        "consultant_profiles": [
            {"id": FIRM_A, "user_id": uid("consultant_a"), "company_name": "P6F Firm A", "is_active": True},
            {"id": FIRM_B, "user_id": uid("consultant_b"), "company_name": "P6F Firm B", "is_active": True},
        ],
        "consultant_firm_members": [
            {"id": det("fm:a"), "firm_id": FIRM_A, "user_id": uid("consultant_a"), "role": "manager",
             "is_active": True, "can_manage_clients": True, "can_submit": True, "can_extract": True,
             "can_map": True, "can_validate": True, "can_calculate": True},
            {"id": det("fm:b"), "firm_id": FIRM_B, "user_id": uid("consultant_b"), "role": "manager",
             "is_active": True, "can_manage_clients": True, "can_submit": True, "can_extract": True,
             "can_map": True, "can_validate": True, "can_calculate": True},
        ],
        "consultant_clients": [
            {"id": CLIENT_A, "consultant_id": FIRM_A, "organization_id": ORG_A,
             "client_name": "P6F Org A", "status": "active",
             "relationship_origin": "consultant_created_customer", "created_by": uid("consultant_a")},
            {"id": CLIENT_B, "consultant_id": FIRM_B, "organization_id": ORG_B,
             "client_name": "P6F Org B", "status": "active",
             "relationship_origin": "consultant_created_customer", "created_by": uid("consultant_b")},
            {"id": CLIENT_A_SUSP, "consultant_id": FIRM_B, "organization_id": ORG_A,
             "client_name": "P6F Org A (suspended)", "status": "suspended",
             "relationship_origin": "consultant_created_customer", "created_by": uid("consultant_b")},
        ],
        "manual_extraction_batches": [
            {"id": BATCH_A, "organization_id": ORG_A, "entity_id": None, "batch_name": "P6F Org A uploads",
             "status": "open", "total_documents": 1, "total_pages": 1, "total_cost": 0,
             "currency": "GBP", "created_at": NOW},
            {"id": BATCH_B, "organization_id": ORG_B, "entity_id": None, "batch_name": "P6F Org B uploads",
             "status": "open", "total_documents": 1, "total_pages": 1, "total_cost": 0,
             "currency": "GBP", "created_at": NOW},
            {"id": BATCH_PE_A, "organization_id": ORG_A, "entity_id": PE_A,
             "batch_name": "P6F PE-A assigned work", "status": "open", "total_documents": 1,
             "total_pages": 1, "total_cost": 0, "currency": "GBP", "created_at": NOW},
        ],
        "manual_extraction_items": [
            {"id": ITEM_A, "batch_id": BATCH_A, "file_name": "p6f-org-a.pdf",
             "file_url": f"/uploads/{ORG_A}/p6f-org-a.pdf", "page_count": 1, "status": "calculated",
             "created_at": NOW, "processing_origin": "CARBONTALLY_INTERNAL",
             "processing_entity_id": None, "consultant_firm_id": None, "processing_mode": "manual",
             "extracted_data": {"items": []}},
            {"id": ITEM_B, "batch_id": BATCH_B, "file_name": "p6f-org-b.pdf",
             "file_url": f"/uploads/{ORG_B}/p6f-org-b.pdf", "page_count": 1, "status": "calculated",
             "created_at": NOW, "processing_origin": "CARBONTALLY_INTERNAL",
             "processing_entity_id": None, "consultant_firm_id": None, "processing_mode": "manual",
             "extracted_data": {"items": []}},
            {"id": ITEM_PE_A, "batch_id": BATCH_PE_A, "file_name": "p6f-pe-a.pdf",
             "file_url": f"/uploads/{ORG_A}/p6f-pe-a.pdf", "page_count": 1, "status": "pe_qc_approved",
             "created_at": NOW, "processing_origin": "PROCESSING_ENTITY", "processing_entity_id": PE_A,
             "consultant_firm_id": None, "processing_mode": "manual",
             "extracted_data": {"items": []}},
        ],
    }


def main() -> int:
    env = load_env()
    db = Db(env)
    db.assert_isolated()
    report: dict[str, Any] = {"environment": env.get("E2E_ENV_ID"), "url": db.url,
                              "tables": {}, "auth": {}, "signin": {}, "errors": []}
    print(f"target : {env.get('E2E_ENV_ID')} {db.url}")

    # 1. auth users (must exist before public.users FK)
    for key, email, role, scope in PERSONAS:
        status = db.ensure_user(email, uid(key), {"e2e": True, "namespace": NS,
                                                  "persona": key, "role": role, "scope": scope})
        report["auth"][key] = status
        if str(status).startswith("ERR"):
            report["errors"].append(f"auth {key}: {status}")

    # 2. fixture graph
    for table, rows_ in rows().items():
        n, err = db.insert(table, rows_)
        report["tables"][table] = {"rows": n, "error": err}
        if err:
            report["errors"].append(f"{table}: {err}")
        print(f"  {table:32s} rows={n} {'OK' if not err else 'ERR: ' + err}")

    # 3. verify real sign-in for every persona
    for key, email, _role, _scope in PERSONAS:
        code, token = db.sign_in(email)
        report["signin"][key] = {"status": code, "token": bool(token)}
        if code != 200:
            report["errors"].append(f"signin {key}: {code}")
    ok = sum(1 for v in report["signin"].values() if v["status"] == 200)
    print(f"sign-in    : {ok}/{len(PERSONAS)} personas authenticated")

    # 4. persona env file for Playwright / API clients (gitignored)
    lines = ["# P6-2F isolated E2E personas (synthetic; gitignored)", f"E2E_BASE_URL=http://127.0.0.1:3001",
             f"E2E_SUPABASE_URL={db.url}", f"E2E_ANON_KEY={env['E2E_ANON_KEY']}",
             f"E2E_SERVICE_ROLE_KEY={env['E2E_SERVICE_ROLE_KEY']}", f"E2E_PASSWORD={PASSWORD}",
             f"E2E_CLIENT_A_ID={CLIENT_A}", f"E2E_CLIENT_B_ID={CLIENT_B}",
             f"E2E_ITEM_A_ID={ITEM_A}", f"E2E_ITEM_B_ID={ITEM_B}", f"E2E_ITEM_PE_A_ID={ITEM_PE_A}",
             f"E2E_ORG_A_ID={ORG_A}", f"E2E_ORG_B_ID={ORG_B}",
             f"E2E_FIRM_A_ID={FIRM_A}", f"E2E_FIRM_B_ID={FIRM_B}",
             f"E2E_PE_A_ID={PE_A}", f"E2E_PE_B_ID={PE_B}"]
    var = {"org_a_owner": "E2E_ORG_OWNER_EMAIL", "org_a_admin": "E2E_ORG_ADMIN_EMAIL",
           "org_a_member": "E2E_ORG_MEMBER_EMAIL", "org_a_viewer": "E2E_ORG_VIEWER_EMAIL",
           "org_b_owner": "E2E_ORG_B_OWNER_EMAIL", "org_b_member": "E2E_ORG_B_MEMBER_EMAIL",
           "consultant_a": "E2E_CONSULTANT_A_EMAIL", "consultant_b": "E2E_CONSULTANT_B_EMAIL",
           "pe_a_manager": "E2E_PE_A_EMAIL", "pe_a_staff": "E2E_PE_A_STAFF_EMAIL",
           "pe_b_manager": "E2E_PE_B_EMAIL", "internal_qc": "E2E_INTERNAL_QC_EMAIL",
           "internal_ops": "E2E_INTERNAL_OPS_EMAIL"}
    for key, email, _r, _s in PERSONAS:
        if key in var:
            lines.append(f"{var[key]}={email}")
            lines.append(f"{var[key].removesuffix('_EMAIL')}_PASSWORD={PASSWORD}")
    PERSONA_FILE.parent.mkdir(parents=True, exist_ok=True)
    PERSONA_FILE.write_text("\n".join(lines) + "\n")
    print(f"personas   : {PERSONA_FILE}")

    (ENV_DIR / ".seed_report.json").write_text(json.dumps(report, indent=2))
    print(f"errors     : {len(report['errors'])}")
    print("SEED " + ("OK" if not report["errors"] else "WITH_ERRORS"))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())



