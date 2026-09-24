#!/usr/bin/env python3
"""P16-REMEDIATION-02 — live acceptance for RD-1 (reviewer workflow) and RD-3
(pipeline-version response reconciliation).

RD-1: drive the real state machine.
    operator  -> map            (already done: item is 'mapped')
    admin     -> validate       (can_review)      <-- must now succeed
    operator  -> calculate      (can_process)     <-- must succeed after validation
plus negative tests for unauthorized actors.

RD-3: compare the enqueue HTTP response's pipeline_version against the stored
queue row for the same job.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lab  # noqa: E402
from p16_journey import ORG_A, call, login  # noqa: E402

ITEM = "9ef70492-1036-46b1-989e-b51b0a34c1ab"
FACILITY = "e05b5cc8-4a6d-4ca1-9b62-8f2662ff4505"


def _status(token: str) -> str:
    out = lab.psql(
        f"SELECT status FROM manual_extraction_items WHERE id = '{ITEM}';")
    return (out.stdout or "").strip()


def main() -> int:
    print("== RD-1: who holds what ==")
    roles = lab.psql("SELECT name || ' => ' || permissions::text FROM staff_roles ORDER BY name;")
    print(roles.stdout)

    op_token, how_op = login("internal_operator")
    admin_token, how_admin = login("platform_admin")
    owner_token, how_owner = login("org_a_owner")
    print(f"operator: {how_op}\nadmin:    {how_admin}\nowner:    {how_owner}\n")

    print(f"== item prior state: {_status(op_token)!r} ==")

    print("\n== RD-1-a: UNAUTHORIZED validate (operator lacks can_review) ==")
    call(f"/api/v3/ops/items/{ITEM}/validate", op_token, method="POST", body={},
         label="POST validate as operator (expect 403)")

    print("\n== RD-1-b: AUTHORIZED validate (admin holds can_review) ==")
    call(f"/api/v3/ops/items/{ITEM}/validate", admin_token, method="POST", body={},
         label="POST validate as admin (expect 2xx)")
    print(f"    state after validate: {_status(admin_token)!r}")

    print("\n== RD-1-c: AUTHORIZED calculate (operator holds can_process) ==")
    call(f"/api/v3/ops/items/{ITEM}/calculate", op_token, method="POST",
         body={"date": "2025-03-31", "activity": "Waste",
               "activity_type": "Waste disposal", "scope": "Scope 3",
               "methodology": "direct_multiply", "facility_id": FACILITY},
         label="POST calculate as operator (expect 2xx)")
    print(f"    state after calculate: {_status(op_token)!r}")

    print("\n== RD-1-d: UNAUTHORIZED calculate (admin lacks can_process) ==")
    call(f"/api/v3/ops/items/{ITEM}/calculate", admin_token, method="POST",
         body={"date": "2025-03-31", "activity": "Waste",
               "activity_type": "Waste disposal", "scope": "Scope 3"},
         label="POST calculate as admin (expect 403)")

    print("\n== RD-3: enqueue response vs stored row ==")
    jobs = lab.psql(
        "SELECT id || ' | ' || file_name || ' | ' || coalesce(pipeline_version,'NULL') "
        "|| ' | ' || status FROM document_processing_queue "
        "WHERE file_name = 'p12canon_waste_001.pdf' ORDER BY created_at DESC LIMIT 2;")
    print("stored rows:\n" + jobs.stdout)

    print("\n== persisted calculation state ==")
    out = lab.psql(
        "SELECT 'item|' || status || '|co2e=' || coalesce(calculated_emissions_kg_co2e::text,'-') "
        "|| '|supplier=' || coalesce(mapped_supplier_id::text,'-') "
        f"FROM manual_extraction_items WHERE id = '{ITEM}';\n"
        "SELECT 'snap|' || id::text || '|co2e=' || co2e_kg::text || '|factor=' "
        "|| coalesce(factor_id::text,'-') || '|scope=' || coalesce(scope,'-') "
        "|| '|supplier=' FROM calculation_snapshots ORDER BY created_at DESC LIMIT 2;\n"
        "SELECT 'log|' || id::text || '|co2e=' || calculated_kg_co2e::text || '|supplier=' "
        "|| coalesce(supplier_id::text,'NULL') FROM emissions_logs ORDER BY created_at DESC LIMIT 2;\n")
    print(out.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
