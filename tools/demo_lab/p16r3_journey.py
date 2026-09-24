#!/usr/bin/env python3
"""P16-R3 — fresh-document journey on the CURRENT code (canonical PDF).

Proves, through the real API only:
  upload -> enqueue -> extraction (line_items) -> map (+clarify, +supplier)
        -> validate (reviewer, line-aware) -> calculate (processor)
        -> snapshot -> emissions

A stale item created before the P12-IMPL-01 parser was loaded cannot be used for
this proof, so a NEW document is uploaded (new file id => new job).

argv: [pdf_name]
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab  # noqa: E402
from p16_journey import ORG_A, CORPUS_DOCS, call, login, upload  # noqa: E402

FACILITY = "e05b5cc8-4a6d-4ca1-9b62-8f2662ff4505"
SUPPLIER = "2fd4072c-0dfc-4c2b-86c6-59797f49898b"


def _psql(sql: str) -> str:
    return (lab.psql(sql).stdout or "").strip()


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "p12canon_waste_001.pdf"
    pdf = CORPUS_DOCS / name
    if not pdf.exists():
        print(f"missing {pdf}")
        return 1

    owner, _ = login("org_a_owner")
    op, _ = login("internal_operator")
    admin, _ = login("platform_admin")

    print(f"== 1. upload {name} (org_a_owner) ==")
    status, payload = upload(owner, pdf, ORG_A, "pdf")
    file_id = (payload or {}).get("id") if isinstance(payload, dict) else None
    print(f"   file_id={file_id}")
    if not file_id:
        return 1

    print("\n== 2. enqueue (operator) ==")
    _s, job = call(f"/api/v3/processing/documents/{file_id}/enqueue", op,
                   method="POST", body={"processing_type": "automatic"},
                   label="enqueue")
    job_id = (job or {}).get("id")
    item_id = (job or {}).get("source_item_id")
    print(f"   job={job_id} item={item_id} pv={(job or {}).get('pipeline_version')}")

    print("\n== 3. poll job ==")
    for _ in range(6):
        time.sleep(8)
        _s, job = call(f"/api/v3/processing/jobs/{job_id}?organization_id={ORG_A}", op,
                       label="job state")
        if (job or {}).get("stage") not in (None, "queued", "running"):
            break

    print("\n== 4. extracted line_items (read-only) ==")
    print(_psql(
        "SELECT 'extracted|' || coalesce(jsonb_array_length(extracted_data->'line_items')::text,'0')"
        f" || ' | status=' || status FROM manual_extraction_items WHERE id='{item_id}';"))

    print("\n== 5. map: clarify each 'Waste' line, then map factor + supplier ==")
    for _ in range(3):
        call("/api/v3/activity-clarifications/clarifications", op, method="POST",
             body={"organization_id": ORG_A, "activity": "Waste",
                   "clarification": "waste disposal|landfill|", "item_id": item_id},
             label="clarify")
    _s, _p = call(f"/api/v3/ops/items/{item_id}/map", op, method="POST",
                  body={"mapped_data": {"activity": "Waste", "activity_type": "Waste disposal",
                                        "factor_id": "33696860-fa7e-469b-970e-7ebc159afa6b",
                                        "unit": "tonnes", "factor_kind": "emission_factor",
                                        "methodology": "direct_multiply"},
                        "mapped_facility_id": FACILITY, "mapped_asset_id": None,
                        "mapped_supplier_id": SUPPLIER,
                        "emission_factor_used": "33696860-fa7e-469b-970e-7ebc159afa6b"},
                  label="map (+supplier)")

    print("\n== 6. validate as reviewer (admin, can_review) ==")
    _s, val = call(f"/api/v3/ops/items/{item_id}/validate", admin, method="POST", body={},
                   label="validate")
    print(f"   blocking={json.dumps(val)[:400] if val else None}")
    print("   state: " + _psql(
        f"SELECT status FROM manual_extraction_items WHERE id='{item_id}';"))

    print("\n== 7. calculate as processor (operator, can_process) ==")
    call(f"/api/v3/ops/items/{item_id}/calculate", op, method="POST",
         body={"date": "2025-03-31", "activity": "Waste",
               "activity_type": "Waste disposal", "scope": "Scope 3",
               "methodology": "direct_multiply", "facility_id": FACILITY},
         label="calculate")
    print("   state: " + _psql(
        f"SELECT status FROM manual_extraction_items WHERE id='{item_id}';"))

    print("\n== 8. persisted result ==")
    print(_psql(
        "SELECT 'snap|' || id::text || '|co2e=' || co2e_kg::text || '|factor=' || coalesce(factor_id::text,'-')"
        " || '|scope=' || coalesce(scope,'-') || '|item=' || coalesce(source_item_id::text,'-')"
        f" FROM calculation_snapshots WHERE source_item_id='{item_id}';\n"
        "SELECT 'log|' || id::text || '|co2e=' || calculated_kg_co2e::text || '|supplier='"
        f" || coalesce(supplier_id::text,'NULL') FROM emissions_logs WHERE snapshot_id IN"
        f" (SELECT id FROM calculation_snapshots WHERE source_item_id='{item_id}');"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
