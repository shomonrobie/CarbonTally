#!/usr/bin/env python3
"""P16-REMEDIATION-01 — live verification of D-1, D-2, D-3 and the FY policy.

Four real API calls against the release backend:

  A  D-1 + D-3 : calculate with source_item_id -> must use the operator-selected
                 factor (33696860, Waste disposal Landfill) and carry supplier
                 2fd4072c into emissions_logs.supplier_id.
  B  D-2.1     : explicitly request the P16-invalid CH4 component factor
                 (65ccf7ec) -> must be refused (422), never calculated.
  C  D-2.2     : request the correct Scope 3 factor under scope="Scope 1"
                 -> must be refused (422 scope mismatch).
  D  FY policy : request reporting_year=2026 with a 2025 factor
                 -> must be refused (422, no silent year substitution).
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab  # noqa: E402
from p16_journey import ORG_A, call, login  # noqa: E402

ITEM = "9ef70492-1036-46b1-989e-b51b0a34c1ab"
OPERATOR_FACTOR = "33696860-fa7e-469b-970e-7ebc159afa6b"   # Waste disposal > ... Landfill, Scope 3
P16_INVALID = "65ccf7ec-d66b-4af3-b834-5a245174d74d"       # Waste oils ... of CH4 per unit, Scope 1
SUPPLIER = "2fd4072c-0dfc-4c2b-86c6-59797f49898b"

BASE = {"organization_id": ORG_A, "activity": "Waste", "activity_type": "Waste disposal",
        "quantity": "90.0", "quantity_unit": "tonnes", "date": "2025-03-31"}


def main() -> int:
    token, how = login("org_a_owner")
    print(f"actor: {how}\n")

    print("== A: D-1 precedence + D-3 supplier (source_item_id, no explicit factor) ==")
    status, payload = call("/api/v3/emissions/calculate", token, method="POST",
                           body={**BASE, "reporting_year": 2025, "scope": "Scope 3",
                                 "source_item_id": ITEM},
                           label="A POST calculate (item-driven)")
    snap = (payload or {}).get("snapshot") or {}
    print(f"    -> factor_id={snap.get('factor_id')}")
    print(f"    -> D-1 {'PASS' if snap.get('factor_id') == OPERATOR_FACTOR else 'FAIL'}"
          f"  (operator factor used: {snap.get('factor_id') == OPERATOR_FACTOR})")
    print(f"    -> must not be P16-invalid: {snap.get('factor_id') != P16_INVALID}")
    print(f"    -> snapshot id = {snap.get('id')}")

    print("\n== B: D-2.1 component factor must be refused ==")
    call("/api/v3/emissions/calculate", token, method="POST",
         body={**BASE, "reporting_year": 2025, "scope": "Scope 3", "factor_id": P16_INVALID},
         label="B POST calculate (CH4 component)")

    print("\n== C: D-2.2 factor scope must match requested scope ==")
    call("/api/v3/emissions/calculate", token, method="POST",
         body={**BASE, "reporting_year": 2025, "scope": "Scope 1", "factor_id": OPERATOR_FACTOR},
         label="C POST calculate (scope mismatch)")

    print("\n== D: FY policy — no silent reporting-year substitution ==")
    call("/api/v3/emissions/calculate", token, method="POST",
         body={**BASE, "reporting_year": 2026, "scope": "Scope 3", "factor_id": OPERATOR_FACTOR},
         label="D POST calculate (2026 request vs 2025 factor)")

    print("\n== persisted check (read-only) ==")
    out = lab.psql(
        "SELECT 'log|'||id::text||'|scope='||coalesce(scope,'-')||'|co2e='||calculated_kg_co2e::text"
        "||'|supplier='||coalesce(supplier_id::text,'NULL')||'|snap='||coalesce(snapshot_id::text,'-')"
        " FROM emissions_logs ORDER BY created_at DESC LIMIT 3;\n"
        "SELECT 'snap|'||id::text||'|factor='||coalesce(factor_id::text,'-')||'|co2e='||co2e_kg::text"
        "||'|mult='||co2e_multiplier::text||'|scope='||coalesce(scope,'-')"
        " FROM calculation_snapshots ORDER BY created_at DESC LIMIT 3;\n")
    print(out.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
