#!/usr/bin/env python3
"""P16-R7 — live calculation idempotency proof.

Drive a FRESH item through the real API and calculate it TWICE with identical
inputs. The second execution must REUSE the immutable snapshots (no new
accounting rows, no doubled reportable total).

The activity text is deliberately one the automatic mapper cannot resolve, so the
job blocks at manual review and cannot race the two manual calculations.
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
CSV = pathlib.Path("/tmp/p16r7_idem.csv")
ACTIVITY = "Site diesel haulage"   # not auto-resolvable -> job blocks, no auto-calc


def sq(sql: str) -> str:
    return (lab.psql(sql).stdout or "").strip()


def census(item_id: str, label: str) -> str:
    out = sq(
        "SELECT count(*)::text||' snapshots, sum='||coalesce(sum(co2e_kg),0)::text"
        "||', reportable='||count(*) FILTER (WHERE reportability_status='reportable')::text"
        f" FROM calculation_snapshots WHERE source_item_id='{item_id}';")
    logs = sq("SELECT count(*)::text FROM emissions_logs WHERE snapshot_id IN "
              f"(SELECT id FROM calculation_snapshots WHERE source_item_id='{item_id}');")
    print(f"   [{label}] {out} | logs={logs}")
    return out


def main() -> int:
    owner, _ = login("org_a_owner")
    op, _ = login("internal_operator")
    admin, _ = login("platform_admin")

    CSV.write_text(
        "activity,quantity,unit,supplier,date\n"
        f"{ACTIVITY},12181.4,kWh,British Gas,2025-06-30\n"
        f"{ACTIVITY},8420.0,kWh,British Gas,2025-06-30\n"
    )
    st, doc = upload(owner, CSV, ORG_A, "csv")
    file_id = (doc or {}).get("id") if isinstance(doc, dict) else None
    print(f"== setup: upload=[{st}] file_id={file_id}")
    _s, job = call(f"/api/v3/processing/documents/{file_id}/enqueue", op,
                   method="POST", body={"processing_type": "automatic"}, label="enqueue")
    job_id, item_id = (job or {}).get("id"), (job or {}).get("source_item_id")
    print(f"   job={job_id} item={item_id}")
    for _ in range(5):
        time.sleep(7)
        _s, job = call(f"/api/v3/processing/jobs/{job_id}?organization_id={ORG_A}", op,
                       label="job")
        if (job or {}).get("stage") not in (None, "queued", "running"):
            break
    print(f"   job stage={ (job or {}).get('stage') } status={(job or {}).get('status')}")
    print("   lines: " + sq(
        "SELECT coalesce(jsonb_array_length(extracted_data->'line_items'),0)::text"
        f" FROM manual_extraction_items WHERE id='{item_id}';"))

    call(f"/api/v3/ops/items/{item_id}/map", op, method="POST",
         body={"mapped_data": {"activity": ACTIVITY, "activity_type": "Natural gas",
                               "factor_id": FACTOR, "unit": "kWh (Net CV)",
                               "factor_kind": "emission_factor",
                               "methodology": "direct_multiply"},
               "mapped_facility_id": FACILITY, "emission_factor_used": FACTOR},
         label="map")
    vs, val = call(f"/api/v3/ops/items/{item_id}/validate", admin, method="POST", body={},
                   label="validate")
    print(f"   validate=[{vs}] {json.dumps(val)[:100]}")

    body = {"date": "2025-06-30", "activity": ACTIVITY, "activity_type": "Natural gas",
            "scope": "Scope 1", "methodology": "direct_multiply", "facility_id": FACILITY}

    print("\n== CALCULATION #1 ==")
    print(f"   {census(item_id, 'before #1')}")
    c1, r1 = call(f"/api/v3/ops/items/{item_id}/calculate", op, method="POST", body=body,
                  label="calc1")
    total1 = ((r1 or {}).get("result") or {}).get("co2e_kg")
    print(f"   [{c1}] result.co2e_kg={total1}")
    print(f"   {census(item_id, 'after #1')}")

    print("\n== CALCULATION #2 (identical repeat) ==")
    c2, r2 = call(f"/api/v3/ops/items/{item_id}/calculate", op, method="POST", body=body,
                  label="calc2")
    total2 = ((r2 or {}).get("result") or {}).get("co2e_kg")
    print(f"   [{c2}] result.co2e_kg={total2} err={json.dumps((r2 or {}).get('error'))[:120]}")
    print(f"   {census(item_id, 'after #2')}")

    print("\n== independent inspection ==")
    print(sq("SELECT '     '||s.id::text||' qty='||s.quantity||' = '||s.co2e_kg"
             "||' status='||s.reportability_status||' req='||coalesce(left(s.request_id::text,18),'-')"
             f" FROM calculation_snapshots s WHERE s.source_item_id='{item_id}' ORDER BY s.calculated_at;"))
    print(f"   IDEMPOTENT={(total1 == total2)}  total1={total1} total2={total2} "
          f"(must NOT be 8351.807560)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
