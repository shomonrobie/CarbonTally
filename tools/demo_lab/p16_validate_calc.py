#!/usr/bin/env python3
"""P16 — complete the mapped item: validate then calculate, then report persisted state."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab  # noqa: E402
from p16_journey import ORG_A, call, login  # noqa: E402

ITEM = sys.argv[1] if len(sys.argv) > 1 else "9ef70492-1036-46b1-989e-b51b0a34c1ab"
ACTOR = sys.argv[2] if len(sys.argv) > 2 else "internal_operator"
FACILITY = "e05b5cc8-4a6d-4ca1-9b62-8f2662ff4505"


def main() -> int:
    token, how = login(ACTOR)
    print(f"== actor: {how} ==")

    print("\n== validate ==")
    call(f"/api/v3/ops/items/{ITEM}/validate", token, method="POST", body={},
         label="POST validate")

    print("\n== calculate ==")
    call(f"/api/v3/ops/items/{ITEM}/calculate", token, method="POST",
         body={"date": "2025-03-31", "activity": "Waste",
               "activity_type": "Waste disposal", "scope": "Scope 3",
               "methodology": "direct_multiply", "facility_id": FACILITY},
         label="POST calculate")

    print("\n== persisted state (read-only SQL) ==")
    sql = (
        "SELECT 'clarification|'||original_activity||'|'||clarification||'|'||outcome_status"
        "||'|factor='||coalesce(selected_factor_id::text,'-')||'|actor='||coalesce(actor_id::text,'-')"
        "||'|scope='||coalesce(actor_scope,'-') FROM activity_clarifications;\n"
        "SELECT 'item|'||id::text||'|'||status||'|co2e='||coalesce(calculated_emissions_kg_co2e::text,'-')"
        "||'|factor='||coalesce(emission_factor_used::text,'-')||'|supplier='"
        "||coalesce(mapped_supplier_id::text,'-') FROM manual_extraction_items WHERE id='" + ITEM + "';\n"
        "SELECT 'snapshot|'||id::text||'|scope='||coalesce(scope,'-')||'|co2e='||co2e_kg::text"
        "||'|factor='||coalesce(factor_id::text,'-')||'|src='||coalesce(factor_source,'-')"
        "||'|set='||coalesce(factor_set,'-')||'|item='||coalesce(source_item_id::text,'-')"
        "||'|hash='||left(content_hash,10) FROM calculation_snapshots ORDER BY calculated_at DESC LIMIT 3;\n"
        "SELECT 'log|'||id::text||'|scope='||coalesce(scope,'-')||'|co2e='||calculated_kg_co2e::text"
        "||'|snap='||coalesce(snapshot_id::text,'-')||'|supplier='||coalesce(supplier_id::text,'-')"
        "||'|unit='||coalesce(unit,'-') FROM emissions_logs ORDER BY created_at DESC LIMIT 4;\n"
    )
    out = lab.psql(sql)
    print(out.stdout)
    print(out.stderr[:400] if out.stderr else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
