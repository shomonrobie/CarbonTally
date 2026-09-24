#!/usr/bin/env python3
"""P12-IMPL-01 — canonical six-PDF extraction acceptance through the REAL product path.

Task: ``P12-IMPL-01-20260924-PDF-EXTRACTION-FOUNDATION``

Flow (no SQL writes anywhere):

  1. load the frozen oracle ``tools/demo_lab/p12_canonical_manifest.json``;
  2. upload each canonical PDF via the product ingestion API ``POST /api/v3/uploads``;
  3. let the real extraction workflow run;
  4. **observe** the product-owned persisted extraction record (the extraction item
     the workbench reads), with an application-API read attempted alongside;
  5. compare against the oracle and write the machine-readable artifact.

It never inserts, updates or repairs extraction rows, and product code never reads
the oracle.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import time

REPO = pathlib.Path("/home/shomonrobie/ct_93d5cdd")
sys.path.insert(0, str(REPO / "tools/demo_lab"))

import lab  # noqa: E402
import t3_scenarios as t3  # noqa: E402

ORACLE_PATH = REPO / "tools/demo_lab/p12_canonical_manifest.json"
ARTIFACT = (REPO / "docs/architecture/artifacts"
            / "p12_impl_01_extracted_data_20260924.json")
TARGET_ORGANIZATION = "Demo Lab Organisation A"
ACTOR = "org_a_owner"


def _json(sql: str) -> dict:
    out = lab.psql(sql).stdout.strip()
    return json.loads(out) if out else {}


def _latest_item(file_name: str) -> dict:
    return _json(
        "SELECT row_to_json(t)::text FROM (SELECT id, status, extracted_data, "
        "mapped_supplier_id, emission_factor_used, created_at "
        "FROM manual_extraction_items WHERE file_name = "
        f"'{file_name}' ORDER BY created_at DESC LIMIT 1) t"
    )


def _latest_queue(file_name: str) -> dict:
    return _json(
        "SELECT row_to_json(t)::text FROM (SELECT id, status, stage, "
        "pipeline_version, manual_review_reason, extracted_data, created_at "
        "FROM document_processing_queue "
        f"WHERE file_name = '{file_name}' ORDER BY created_at DESC LIMIT 1) t"
    )


def _norm(value):
    """Numeric-normalising comparison helper (handles '£1,234.5' and floats)."""
    if value is None:
        return None
    text = str(value).strip()
    if text.startswith("£"):
        text = text[1:]
    text = text.replace(",", "")
    try:
        return round(float(text), 4)
    except ValueError:
        return str(value).strip()


def _document_comparison(oracle: dict, extracted: dict) -> dict:
    pairs = [
        ("supplier", oracle["supplier"], extracted.get("supplier"), "text"),
        ("customer", oracle["customer"], extracted.get("customer"), "text"),
        ("invoice_ref", oracle["invoice_number"], extracted.get("invoice_number"), "text"),
        ("invoice_date", oracle["invoice_date"], extracted.get("date"), "text"),
        ("period_start", oracle["billing_period_start"],
         extracted.get("billing_period_start"), "text"),
        ("period_end", oracle["billing_period_end"],
         extracted.get("billing_period_end"), "text"),
        ("subtotal", oracle["net_total"], extracted.get("net_amount"), "number"),
        ("vat", oracle["vat_total"], extracted.get("vat_amount"), "number"),
        ("total", oracle["gross_total"], extracted.get("gross_amount"), "number"),
    ]
    result = {}
    for field, expected, actual, kind in pairs:
        match = (_norm(expected) == _norm(actual) if kind == "number"
                 else str(expected) == str(actual))
        result[field] = {"oracle": expected, "extracted": actual,
                         "result": "PASS" if match else "FAIL"}
    return result


def _line_comparison(oracle: dict, extracted: dict) -> dict:
    expected = oracle["line_items"]
    actual = extracted.get("line_items") or []
    rows = []
    for index in range(max(len(expected), len(actual))):
        exp = expected[index] if index < len(expected) else {}
        act = actual[index] if index < len(actual) else {}
        rows.append({
            "line": index + 1,
            "expected_description": exp.get("description"),
            "actual_description": act.get("description"),
            "expected_qty": exp.get("quantity"), "actual_qty": act.get("quantity"),
            "expected_unit": exp.get("unit"), "actual_unit": act.get("unit"),
            "expected_rate": exp.get("unit_price"), "actual_rate": act.get("unit_price"),
            "expected_net": exp.get("net_amount"), "actual_net": act.get("net_amount"),
            "qty_result": "PASS" if _norm(exp.get("quantity")) == _norm(act.get("quantity")) else "FAIL",
            "unit_result": "PASS" if str(act.get("unit") or "").startswith(
                str(exp.get("unit") or "")[:4]) else "FAIL",
            "rate_result": "PASS" if _norm(exp.get("unit_price")) == _norm(act.get("unit_price")) else "FAIL",
            "net_result": "PASS" if _norm(exp.get("net_amount")) == _norm(act.get("net_amount")) else "FAIL",
            "arithmetic_ok": act.get("arithmetic_ok"),
            "source_line": act.get("source_line"),
        })
    return {"expected_line_count": len(expected), "actual_line_count": len(actual),
            "rows": rows}


def main() -> int:
    oracle = json.loads(ORACLE_PATH.read_text())
    state = lab.load_state()
    spec = json.loads((REPO / "tools/demo_lab/manifest.json").read_text())
    org_id = t3.org_id_by_name(TARGET_ORGANIZATION)
    token = t3.login(ACTOR, state, spec)
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                            capture_output=True, text=True).stdout.strip()

    artifact = {
        "task_id": "P12-IMPL-01-20260924-PDF-EXTRACTION-FOUNDATION",
        "corpus": "p12-canonical-demo-v1",
        "commit_sha": commit,
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_organization": TARGET_ORGANIZATION,
        "target_organization_id": org_id,
        "observation_method": (
            "real product upload (POST /api/v3/uploads) then read of the "
            "product-owned persisted extraction item "
            "(manual_extraction_items.extracted_data); no SQL writes"
        ),
        "documents": [],
    }

    for doc in oracle["documents"]:
        pdf = pathlib.Path(doc["pdf"])
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        body, ctype = t3._multipart(
            {"organization_id": org_id, "data_type": "utility"},
            pdf.name, pdf.read_bytes(),
        )
        code, payload = t3.api("POST", "/api/v3/uploads", token,
                               body=body, headers={"Content-Type": ctype})
        artifact["documents"].append({
            "document_id": doc["document_id"],
            "source_filename": pdf.name,
            "pdf_sha256": sha,
            "pdf_sha256_matches_oracle": sha == doc["pdf_sha256"],
            "upload_status": code,
            "upload_response": payload,
        })
        print(f"{doc['document_id']}: upload={code}")

    time.sleep(25)  # allow the durable worker to extract

    for entry, doc in zip(artifact["documents"], oracle["documents"]):
        item = _latest_item(entry["source_filename"])
        queue = _latest_queue(entry["source_filename"])
        extracted = item.get("extracted_data") or {}
        app_status, _ = t3.api(
            "GET", f"/api/v3/customer-documents/{item.get('id')}/extraction", token
        )
        entry.update({
            "extraction_item_id": item.get("id"),
            "extraction_item_status": item.get("status"),
            "queue_status": queue.get("status"),
            "queue_stage": queue.get("stage"),
            "queue_pipeline_version": queue.get("pipeline_version"),
            "manual_review_reason": queue.get("manual_review_reason"),
            "actual_extracted_data": extracted,
            "application_read_status": app_status,
            "document_comparison": _document_comparison(doc, extracted),
            "line_comparison": _line_comparison(doc, extracted),
        })
        dc = entry["document_comparison"]
        lc = entry["line_comparison"]
        print(f"  {doc['document_id']}: supplier={dc['supplier']['result']} "
              f"customer={dc['customer']['result']} ref={dc['invoice_ref']['result']} "
              f"date={dc['invoice_date']['result']} period={dc['period_start']['result']} "
              f"lines={lc['actual_line_count']}/{lc['expected_line_count']} "
              f"qty_pass={sum(r['qty_result'] == 'PASS' for r in lc['rows'])} "
              f"rate_pass={sum(r['rate_result'] == 'PASS' for r in lc['rows'])} "
              f"net_pass={sum(r['net_result'] == 'PASS' for r in lc['rows'])}")

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact, indent=2, default=str) + "\n")
    print("artifact:", ARTIFACT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
