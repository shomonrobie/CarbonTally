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


def test_customer_review_queue_lists_calculated_item(client, world, user_provider) -> None:
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


def test_ops_calculate_snapshot_retains_source_item_id(client, world, user_provider) -> None:
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

