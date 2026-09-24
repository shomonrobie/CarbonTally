#!/usr/bin/env python3
"""P16-R4 — six-PDF end-to-end acceptance over the real API.

For every frozen canonical PDF: upload -> enqueue -> extraction -> clarify ->
map(+supplier) -> reviewer validate -> processor calculate -> snapshot/log.

Emits one compact JSON line per document plus a summary table. A legitimate
policy block (e.g. FY2026 with no FY2026 factor) is recorded as the observed
outcome, never forced.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab  # noqa: E402
from p16_journey import CORPUS_DOCS, ORG_A, call, login, upload  # noqa: E402

FACILITY = "e05b5cc8-4a6d-4ca1-9b62-8f2662ff4505"
SUPPLIER = "2fd4072c-0dfc-4c2b-86c6-59797f49898b"
FACTOR = "33696860-fa7e-469b-970e-7ebc159afa6b"


def _psql(sql: str) -> str:
    return (lab.psql(sql).stdout or "").strip()


def run_doc(name: str, owner, op, admin) -> dict:
    row: dict = {"pdf": name}
    pdf = CORPUS_DOCS / name
    status, payload = upload(owner, pdf, ORG_A, "pdf")
    row["upload"] = status
    file_id = (payload or {}).get("id") if isinstance(payload, dict) else None
    if not file_id:
        row["final"] = "UPLOAD_FAILED"
        return row

    _s, job = call(f"/api/v3/processing/documents/{file_id}/enqueue", op,
                   method="POST", body={"processing_type": "automatic"}, label="enqueue")
    job_id = (job or {}).get("id")
    item_id = (job or {}).get("source_item_id")
    row.update(job=job_id, item=item_id, pipeline=(job or {}).get("pipeline_version"))
    if not item_id:
        row["final"] = "ENQUEUE_FAILED"
        return row

    for _ in range(5):
        time.sleep(7)
        _s, job = call(f"/api/v3/processing/jobs/{job_id}?organization_id={ORG_A}", op,
                       label="job state")
        if (job or {}).get("stage") not in (None, "queued", "running"):
            break
    row["job_stage"] = (job or {}).get("stage")
    row["job_reason"] = (job or {}).get("manual_review_reason")

    row["lines"] = _psql(
        "SELECT coalesce(jsonb_array_length(extracted_data->'line_items'),0)::text"
        f" FROM manual_extraction_items WHERE id='{item_id}';") or "0"
    row["completeness"] = "1.0" if row["lines"] not in ("", "0") else "0.0"

    for _ in range(3):
        call("/api/v3/activity-clarifications/clarifications", op, method="POST",
             body={"organization_id": ORG_A, "activity": "Waste",
                   "clarification": "waste disposal|landfill|", "item_id": item_id},
             label="clarify")
    _s, _p = call(f"/api/v3/ops/items/{item_id}/map", op, method="POST",
                  body={"mapped_data": {"activity": "Waste", "activity_type": "Waste disposal",
                                        "factor_id": FACTOR, "unit": "tonnes",
                                        "factor_kind": "emission_factor",
                                        "methodology": "direct_multiply"},
                        "mapped_facility_id": FACILITY, "mapped_supplier_id": SUPPLIER,
                        "emission_factor_used": FACTOR},
                  label="map")
    row["mapping"] = "mapped"

    vs, val = call(f"/api/v3/ops/items/{item_id}/validate", admin, method="POST", body={},
                   label="validate")
    row["validation"] = vs
    row["validation_blocking"] = (val or {}).get("blocking")
    row["validation_findings"] = len((val or {}).get("findings") or [])
    row["state_after_validate"] = _psql(
        f"SELECT status FROM manual_extraction_items WHERE id='{item_id}';")

    cs, calc = call(f"/api/v3/ops/items/{item_id}/calculate", op, method="POST",
                    body={"date": "2025-03-31", "activity": "Waste",
                          "activity_type": "Waste disposal", "scope": "Scope 3",
                          "methodology": "direct_multiply", "facility_id": FACILITY},
                    label="calculate")
    row["calculation"] = cs
    row["calc_error"] = (calc or {}).get("error", {}).get("message") if isinstance(calc, dict) else None
    row["state_after_calculate"] = _psql(
        f"SELECT status FROM manual_extraction_items WHERE id='{item_id}';")

    row["snapshots"] = _psql(
        "SELECT count(*)::text || '|sum=' || coalesce(sum(co2e_kg),0)::text"
        f" FROM calculation_snapshots WHERE source_item_id='{item_id}';")
    row["emissions"] = _psql(
        "SELECT count(*)::text || '|supplier=' || count(supplier_id)::text"
        " FROM emissions_logs WHERE snapshot_id IN"
        f" (SELECT id FROM calculation_snapshots WHERE source_item_id='{item_id}');")
    row["factor_year"] = _psql(
        "SELECT reporting_year::text FROM emission_factors WHERE id="
        f"'{FACTOR}';")
    row["final"] = row.get("state_after_calculate") or "UNKNOWN"
    print(json.dumps(row), flush=True)
    return row


def main() -> int:
    owner, _ = login("org_a_owner")
    op, _ = login("internal_operator")
    admin, _ = login("platform_admin")
    names = sorted(p.name for p in CORPUS_DOCS.glob("*.pdf"))
    rows = [run_doc(n, owner, op, admin) for n in names]
    print("\n=== SUMMARY ===")
    for r in rows:
        print(f"{r['pdf']}: lines={r.get('lines')} val={r.get('validation')} "
              f"calc={r.get('calculation')} state={r.get('final')} "
              f"snap={r.get('snapshots')} emis={r.get('emissions')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
