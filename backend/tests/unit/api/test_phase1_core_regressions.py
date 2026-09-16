"""Phase 1 core-workflow regression tests (CL-1/ISC-1/ISC-2/ISC-10, PO D2).

Focused regressions for the restored customer core pipeline:

* CL-1 — the customer review queue lists calculated items (no ambiguous-id 500).
* ISC-1 — an ops calculation snapshot retains ``source_item_id`` (the D33
  document→emissions chain works after a pipeline run).
* PO Decision 2 / ISC-10 — ``system_admin`` passes the legacy admin authorizer.
"""

from __future__ import annotations

import asyncio

from tests.unit.api.fakes import (
    member_user,
    staff_user,
)
from tests.unit.api.test_v3_operations import _seed_batch_with_item, _seed_ops_world


# ---------------------------------------------------------------------------
# CL-1 — customer review queue lists calculated items
# ---------------------------------------------------------------------------


def test_customer_calculate_multiline_item_with_item_level_factor(client, world, user_provider) -> None:
    """Phase 2 close-out — the customer-facing ``calculate`` endpoint must handle
    multi-line (D23) items and honour the documented item-level factor contract.

    Live E2E: after the auto-processor mapped a multi-line CSV item and the map
    contract accepted ``emission_factor_used``, ``/calculate`` 422'd with
    ``extracted_data.quantity is required`` because the customer surface had no
    multi-line path (only the ops surface did). The customer surface now shares
    the D23 line-calculation used by ops, and the item-level factor applies to
    every line (matching the validation engine)."""
    _seed_ops_world(world)
    # FIN-06 precondition: customer manual processing requires the enable.
    world.manual_processing.seed_grant("organization", "org-a")
    _batch, item = _seed_batch_with_item(world)

    user_provider.set_user(member_user("org-a", "member-1", "m@test"))
    client.post(
        f"/api/v3/processing/items/{item.id}/extract",
        json={
            "extracted_data": {
                "supplier": "ACME Utilities",
                "invoice_date": "2026-01-10",
                "line_items": [
                    {"activity": "Electricity", "quantity": "1000", "unit": "kWh"},
                    {"activity": "Natural gas", "quantity": "500", "unit": "kWh"},
                ],
            }
        },
    )
    mapped = client.post(
        f"/api/v3/processing/items/{item.id}/map",
        json={
            "mapped_data": {"activity_type": "Natural gas"},
            "emission_factor_used": "factor-defra-gas",
        },
    )
    assert mapped.status_code == 200, mapped.text
    validated = client.post(f"/api/v3/processing/items/{item.id}/validate")
    assert validated.status_code == 200, validated.text
    assert validated.json()["blocking"] is False, validated.text

    assert (
        client.post(
            f"/api/v3/processing/items/{item.id}/start",
            json={"stage": "calculation"},
        ).status_code
        == 200
    )
    response = client.post(f"/api/v3/processing/items/{item.id}/calculate", json={})
    assert response.status_code == 200, response.text
    calc = response.json()["calculation"]
    assert calc["multi_line"] is True
    # 1000 kWh + 500 kWh × 0.183 kg/kWh = 274.5 kg CO2e.
    assert abs(float(calc["co2e_kg"]) - 274.5) < 0.01
    assert response.json()["item"]["status"] == "calculated"
    stored = world.manual_extraction._items[item.id]
    assert float(stored.calculated_emissions_kg_co2e) == 274.5
    assert len(stored.mapped_data["line_items"]) == 2

    """CL-1 — a calculated item appears in the customer review queue (the
    queue previously 500'd with ``column reference "id" is ambiguous``)."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    # Move the item to `calculated` (the state awaiting the customer gate).
    asyncio.run(world.manual_extraction.set_item_status(item.id, "calculated"))

    user_provider.set_user(member_user("org-a", "owner-1", "owner@test"))
    response = client.get(
        "/api/v3/processing/customer-review", params={"organization_id": "org-a"}
    )
    assert response.status_code == 200
    body = response.json()
    ids = [i["id"] for i in body.get("items", [])]
    assert item.id in ids, "calculated item must be listed in the customer review queue"


def test_customer_review_queue_rejects_cancelled_batch(client, world, user_provider) -> None:
    """CL-1 — items from cancelled batches are not offered for review."""
    _seed_ops_world(world)
    batch, item = _seed_batch_with_item(world)
    asyncio.run(world.manual_extraction.set_item_status(item.id, "calculated"))
    asyncio.run(world.manual_extraction.cancel_batch(batch.id, "u-op"))

    user_provider.set_user(member_user("org-a", "owner-1", "owner@test"))
    response = client.get(
        "/api/v3/processing/customer-review", params={"organization_id": "org-a"}
    )
    assert response.status_code == 200
    assert all(i["id"] != item.id for i in response.json().get("items", []))

# ---------------------------------------------------------------------------
# ISC-1 — ops calculate persists source_item_id on the snapshot
# ---------------------------------------------------------------------------


def test_validate_with_blocking_findings_creates_issues_without_500(client, world, user_provider) -> None:
    """Phase 2 close-out — validate with blocking findings must persist first-class
    issues without a 500.

    Previously ``_open_validation_issues`` wrote the manual-extraction batch id
    into ``issues.batch_id`` (FK -> ``upload_batches``) and the item id into
    ``issues.work_item_id`` (FK -> ``manual_review_queue``) — both violated FKs
    because a manual-extraction item has neither row, so every blocking
    validation run 500'd and the item could never advance.
    """
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)

    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"})
    # Extraction data with NO quantity/unit/activity -> blocking findings.
    client.post(
        f"/api/v3/ops/items/{item.id}/extract",
        json={"extracted_data": {"date": "2025-06-01"}},
    )
    client.post(
        f"/api/v3/ops/items/{item.id}/map",
        json={"mapped_data": {"activity_type": "Natural gas"}, "emission_factor_used": "factor-defra-gas"},
    )

    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    response = client.post(f"/api/v3/ops/items/{item.id}/validate")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["blocking"] is True, "missing extraction fields must block"
    assert body["status"] == "mapping", "blocked item routes back to mapping"

    # The issue row is persisted with the manual-extraction batch link (the
    # legacy defect wrote batch_id/work_item_id into FK columns that reference
    # other tables, which made every blocking validation run 500).
    issue = next(
        (i for i in world.issues._issues if i.manual_extraction_batch_id == _batch.id),
        None,
    )
    assert issue is not None, "blocking validation must persist a first-class issue"
    assert issue.batch_id is None
    assert issue.work_item_id is None



    """ISC-1 — ``/api/v3/ops/items/{id}/calculate`` persists ``source_item_id``
    on the calculation snapshot so the document->emissions reverse lookup works."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)

    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"})
    client.post(
        f"/api/v3/ops/items/{item.id}/extract",
        json={
            "extracted_data": {
                "quantity": "1000",
                "unit": "kWh",
                "activity": "Natural gas",
                "supplier": "British Gas",
                "date": "2025-06-01",
            }
        },
    )
    client.post(
        f"/api/v3/ops/items/{item.id}/map",
        json={"mapped_data": {"activity_type": "Natural gas"}, "emission_factor_used": "factor-defra-gas"},
    )
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    assert client.post(f"/api/v3/ops/items/{item.id}/validate").json()["status"] == "validated"

    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "calculation"})
    calc = client.post(f"/api/v3/ops/items/{item.id}/calculate", json={})
    assert calc.status_code == 200

    snapshot_id = calc.json()["result"]["snapshot"]["id"]
    snapshot = world.logs._snapshots[snapshot_id]
    # ISC-1 — the snapshot carries the extraction-item link (previously NULL).
    assert snapshot.source_item_id == item.id


# ---------------------------------------------------------------------------
# PO Decision 2 / ISC-10 — system_admin passes the legacy admin authorizer
# ---------------------------------------------------------------------------


def test_system_admin_can_read_legacy_audit(client, world, user_provider) -> None:
    """ISC-10 — ``system_admin`` is a full system-administration role and must
    pass the legacy ``/api/v2/admin/*`` authorizer (previously 403)."""
    _seed_ops_world(world)
    user_provider.set_user(
        staff_user("u-sysadmin", email="sysadmin@carbontally.test", role_name="system_admin")
    )
    response = client.get("/api/v2/admin/audit")
    assert response.status_code == 200


def test_non_admin_staff_still_denied_legacy_audit(client, world, user_provider) -> None:
    """Least privilege preserved — an operator is still denied the admin audit."""
    _seed_ops_world(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    assert client.get("/api/v2/admin/audit").status_code == 403


def test_entity_staff_system_admin_denied_legacy_audit(client, world, user_provider) -> None:
    """D20 — entity staff with an admin-named role never pass the legacy gate."""
    _seed_ops_world(world)
    user_provider.set_user(
        staff_user(
            "u-ent-sysadmin",
            email="entsysadmin@entity.test",
            role_name="system_admin",
            entity_id="entity-1",
        )
    )
    assert client.get("/api/v2/admin/audit").status_code == 403

