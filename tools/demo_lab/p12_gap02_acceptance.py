#!/usr/bin/env python3
"""P12-GAP-02 — canonical PDF extraction / supplier attribution acceptance runner.

Task: ``P12-GAP-02-20260924-CANONICAL-PDF-SUPPLIER-REUSE``

What it does (all against the REAL product path — no direct table inserts):

  1. reads the immutable oracle ``tools/demo_lab/p12_canonical_manifest.json``;
  2. uploads each canonical PDF through ``POST /api/v3/uploads`` (the product
     ingestion API) into Demo Lab Organisation A;
  3. observes the persisted queue row and extraction payload from PostgreSQL;
  4. measures the P1 extraction-fidelity hook OFFLINE, twice, in isolated
     subprocesses: default (``shadow``, the running mode) and ``enabled`` with a
     global allowlist, to establish what the shadow shaper would emit WITHOUT
     promoting P1 in the environment;
  5. writes an evidence JSON.

It never inserts extracted payloads directly, never edits the oracle, and never
changes product code or the running backend's environment configuration.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

REPO = pathlib.Path("/home/shomonrobie/ct_93d5cdd")
sys.path.insert(0, str(REPO / "tools/demo_lab"))

import lab  # noqa: E402
import t3_scenarios as t3  # noqa: E402

ORACLE_PATH = REPO / "tools/demo_lab/p12_canonical_manifest.json"
TARGET_ORGANIZATION = "Demo Lab Organisation A"
ACTOR = "org_a_owner"
EVIDENCE = lab.EVIDENCE_DIR / "p12_gap02_acceptance.json"


def _queue_row(file_name: str) -> dict:
    out = lab.psql(
        "SELECT coalesce(row_to_json(q)::text,'{}') FROM document_processing_queue q "
        f"WHERE q.file_name = '{file_name}' ORDER BY q.created_at DESC LIMIT 1"
    ).stdout.strip()
    return json.loads(out) if out else {}


_P1_PROBE = r'''
import json, pathlib, sys
sys.path.insert(0, "/home/shomonrobie/ct_93d5cdd/backend")
from services import automatic_extraction as ax
pdf = pathlib.Path(sys.argv[1])
res = ax.extract_document(pdf.read_bytes(), pdf.name, "application/pdf",
                          organization_id=sys.argv[2])
ex = res.get("extracted_data") or {}
print(json.dumps({
    "status": res.get("status"), "method": res.get("method"),
    "confidence": res.get("confidence"),
    "keys": sorted(ex.keys()),
    "line_item_count": len(ex.get("line_items") or []),
    "line_items": ex.get("line_items"),
    "supplier": ex.get("supplier"), "customer": ex.get("customer"),
    "invoice_number": ex.get("invoice_number"), "date": ex.get("date"),
    "quantity": ex.get("quantity"), "unit": ex.get("unit"),
    "activity": ex.get("activity"),
    "unresolved": res.get("unresolved"), "coverage": res.get("coverage"),
}))
'''


def probe(pdf_path: str, org_id: str, enabled: bool) -> dict:
    env = dict(os.environ)
    if enabled:
        env["CARBONTALLY_P1_EXTRACTION_SHAPE"] = "enabled"
        env["CARBONTALLY_P1_ORGANIZATION_ALLOWLIST"] = "*"
    proc = subprocess.run(
        [sys.executable, "-c", _P1_PROBE, pdf_path, org_id],
        capture_output=True, text=True, env=env,
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    if not lines:
        return {"error": (proc.stderr or "")[-500:]}
    return json.loads(lines[-1])


def main() -> int:
    oracle = json.loads(ORACLE_PATH.read_text())
    state = lab.load_state()
    spec = json.loads((REPO / "tools/demo_lab/manifest.json").read_text())
    org_id = t3.org_id_by_name(TARGET_ORGANIZATION)
    token = t3.login(ACTOR, state, spec)

    evidence: dict = {
        "task": "P12-GAP-02-20260924-CANONICAL-PDF-SUPPLIER-REUSE",
        "oracle": str(ORACLE_PATH),
        "target_organization": TARGET_ORGANIZATION,
        "target_organization_id": org_id,
        "documents": {},
    }

    for doc in oracle["documents"]:
        did = doc["document_id"]
        pdf = pathlib.Path(doc["pdf"])
        rec: dict = {
            "oracle": {
                "pdf_sha256": doc["pdf_sha256"],
                "supplier": doc["supplier"],
                "customer": doc["customer"],
                "invoice_number": doc["invoice_number"],
                "invoice_date": doc["invoice_date"],
                "billing_period": [doc["billing_period_start"], doc["billing_period_end"]],
                "reporting_year": doc["reporting_year"],
                "line_item_count": doc["line_item_count"],
                "line_items": doc["line_items"],
                "net_total": doc["net_total"],
                "vat_total": doc["vat_total"],
                "gross_total": doc["gross_total"],
            },
            "actual_pdf_sha256": __import__("hashlib").sha256(pdf.read_bytes()).hexdigest(),
        }
        body, ctype = t3._multipart(
            {"organization_id": org_id, "data_type": "utility"},
            pdf.name, pdf.read_bytes(),
        )
        code, payload = t3.api("POST", "/api/v3/uploads", token,
                               body=body, headers={"Content-Type": ctype})
        rec["upload_status"] = code
        rec["upload_response"] = payload
        document_id = None
        if isinstance(payload, dict):
            inner = payload.get("document")
            document_id = (inner or {}).get("id") if isinstance(inner, dict) else payload.get("id")
        rec["document_id"] = document_id
        print(f"{did}: upload={code} document_id={document_id}")
        evidence["documents"][did] = rec

    time.sleep(20)  # let the durable worker progress

    docs_dir = pathlib.Path(oracle["documents"][0]["pdf"]).parent
    for did, rec in evidence["documents"].items():
        row = _queue_row(f"{did}.pdf")
        rec["queue_row"] = row
        ex = row.get("extracted_data") or {}
        rec["queue_extraction"] = {
            "status": row.get("status"),
            "file_type": row.get("file_type"),
            "keys": sorted(ex.keys()) if isinstance(ex, dict) else None,
            "line_item_count": len(ex.get("line_items") or []) if isinstance(ex, dict) else None,
            "supplier": ex.get("supplier") if isinstance(ex, dict) else None,
            "customer": ex.get("customer") if isinstance(ex, dict) else None,
            "invoice_number": ex.get("invoice_number") if isinstance(ex, dict) else None,
            "date": ex.get("date") if isinstance(ex, dict) else None,
            "quantity": ex.get("quantity") if isinstance(ex, dict) else None,
            "unit": ex.get("unit") if isinstance(ex, dict) else None,
            "activity": ex.get("activity") if isinstance(ex, dict) else None,
        }
        target = str(docs_dir / f"{did}.pdf")
        rec["p1_shadow_default"] = probe(target, org_id, enabled=False)
        rec["p1_enabled_probe"] = probe(target, org_id, enabled=True)
        print(f"  {did}: queue={rec['queue_extraction']['status']} "
              f"keys={rec['queue_extraction']['keys']} "
              f"shadow_items={rec['p1_shadow_default'].get('line_item_count')} "
              f"enabled_items={rec['p1_enabled_probe'].get('line_item_count')}")

    EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n")
    print("evidence:", EVIDENCE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
