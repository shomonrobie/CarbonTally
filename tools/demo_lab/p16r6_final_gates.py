#!/usr/bin/env python3
"""P16-R6 — combined live acceptance: R11 (EV-01 fresh redrive), R8 (FY2026
fail-closed), R12/RD-8 (live cross-tenant denial).

All state changes go through authenticated application routes. The cross-tenant
proof uses EXISTING organisations/items (no fabricated tenant or accounting rows).
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab  # noqa: E402
from p16_journey import ORG_A, call, login, upload  # noqa: E402

FACTOR = "aef1f0bb-4e48-4e4b-a079-c1e827964d07"   # Natural gas [kWh (Net CV)] 0.2027
FACILITY = "e05b5cc8-4a6d-4ca1-9b62-8f2662ff4505"
EV01_CSV = pathlib.Path("/tmp/p16r6_ev01.csv")


def sq(sql: str) -> str:
    return (lab.psql(sql).stdout or "").strip()


def main() -> int:
    owner, _ = login("org_a_owner")
    op, _ = login("internal_operator")
    admin, _ = login("platform_admin")

    print("== R11: EV-01 fresh redrive ==")
    EV01_CSV.write_text(
        "activity,quantity,unit,supplier,date\n"
        "Natural gas,12181.4,kWh,British Gas,2025-06-30\n"
        "Natural gas,8420.0,kWh,British Gas,2025-06-30\n"
    )
    st, doc = upload(owner, EV01_CSV, ORG_A, "csv")
    file_id = (doc or {}).get("id") if isinstance(doc, dict) else None
    print(f"   upload=[{st}] file_id={file_id}")
    _s, job = call(f"/api/v3/processing/documents/{file_id}/enqueue", op,
                   method="POST", body={"processing_type": "automatic"}, label="enqueue")
    job_id, item_id = (job or {}).get("id"), (job or {}).get("source_item_id")
    print(f"   job={job_id} item={item_id} pipeline={(job or {}).get('pipeline_version')}")
    for _ in range(5):
        time.sleep(7)
        _s, job = call(f"/api/v3/processing/jobs/{job_id}?organization_id={ORG_A}", op,
                       label="job")
        if (job or {}).get("stage") not in (None, "queued", "running"):
            break
    print("   extracted: " + sq(
        "SELECT coalesce(jsonb_array_length(extracted_data->'line_items'),0)::text||' lines'"
        f" FROM manual_extraction_items WHERE id='{item_id}';"))

    for i in range(2):
        call(f"/api/v3/ops/items/{item_id}/map", op, method="POST",
             body={"mapped_data": {"activity": "Natural gas", "activity_type": "Natural gas",
                                   "factor_id": FACTOR, "unit": "kWh (Net CV)",
                                   "factor_kind": "emission_factor",
                                   "methodology": "direct_multiply"},
                   "mapped_facility_id": FACILITY, "emission_factor_used": FACTOR},
             label=f"map {i+1}")
    vs, val = call(f"/api/v3/ops/items/{item_id}/validate", admin, method="POST", body={},
                   label="validate")
    print(f"   validate=[{vs}] {json.dumps(val)[:110]}")
    cs, calc = call(f"/api/v3/ops/items/{item_id}/calculate", op, method="POST",
                    body={"date": "2025-06-30", "activity": "Natural gas",
                          "activity_type": "Natural gas", "scope": "Scope 1",
                          "methodology": "direct_multiply", "facility_id": FACILITY},
                    label="calculate")
    print(f"   calculate=[{cs}] state=" + sq(
        f"SELECT status FROM manual_extraction_items WHERE id='{item_id}';"))
    print("   FRESH EV-01 rows:")
    print(sq(
        "SELECT '     qty='||s.quantity||' '||s.quantity_unit||' x '||s.co2e_multiplier"
        "||' = '||s.co2e_kg||' | snap='||s.id::text||' | log='||coalesce(l.id::text,'-')"
        "||' | factor='||s.factor_id::text||' yr='||s.reporting_year||' | supplier='"
        "||coalesce(l.supplier_id::text,'NULL')"
        " FROM calculation_snapshots s LEFT JOIN emissions_logs l ON l.snapshot_id=s.id"
        f" WHERE s.source_item_id='{item_id}' ORDER BY s.quantity DESC;"))
    print("   SUM: " + sq(
        "SELECT coalesce(sum(co2e_kg),0)::text||' kg CO2e (expect 4175.903780)'"
        f" FROM calculation_snapshots WHERE source_item_id='{item_id}';"))

    print("\n== R8: FY2026 no-silent-fallback (live API) ==")
    st8, b8 = call("/api/v3/emissions/calculate", owner, method="POST",
                   body={"organization_id": ORG_A, "activity": "Natural gas",
                         "quantity": "1000", "quantity_unit": "kWh (Net CV)",
                         "date": "2026-06-30", "reporting_year": 2026, "country": "GB",
                         "scope": "Scope 1"},
                   label="calculate 2026")
    print(f"   requested_year=2026 factor_year=2025 -> [{st8}] {json.dumps(b8)[:280]}")

    print("\n== R12/RD-8: live cross-tenant denial (existing data, no fabrication) ==")
    own_snap = sq(f"SELECT id::text FROM calculation_snapshots WHERE organization_id='{ORG_A}'"
                  " ORDER BY calculated_at DESC NULLS LAST LIMIT 1;")
    other_snap = sq("SELECT id::text FROM calculation_snapshots "
                    f"WHERE organization_id <> '{ORG_A}' LIMIT 1;")
    other_org = sq("SELECT organization_id::text FROM calculation_snapshots "
                   f"WHERE organization_id <> '{ORG_A}' LIMIT 1;")
    print(f"   orgA={ORG_A}  orgB={other_org}")
    if own_snap:
        s1, _ = call(f"/api/v3/emissions/calculations/{own_snap}", owner, label="own")
        print(f"   own-org snapshot read          -> [{s1}] (expect 200)")
    if other_snap:
        s2, b2 = call(f"/api/v3/emissions/calculations/{other_snap}", owner, label="foreign")
        print(f"   foreign-org snapshot read      -> [{s2}] {json.dumps(b2)[:140]} (expect 403)")
        s3, b3 = call(f"/api/v3/emissions/calculations/{other_snap}/invalidate", admin,
                      method="POST", body={"reason": "cross-tenant probe"}, label="foreign-inv")
        print(f"   foreign-org invalidate (admin)-> [{s3}] {json.dumps(b3)[:140]} (expect 404/403)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
