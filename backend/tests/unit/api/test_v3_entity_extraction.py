"""V3 D22 — Processing work assignment + entity extraction workspace.

Covers the Processing Entity work-assignment model end-to-end:

* batch-level ``entity_id`` assignment (CarbonTally -> Processing Entity),
  reassignment Entity A -> Entity B -> CarbonTally, single-active-assignment
* the entity extraction workspace: entity staff process ONLY their entity's
  assigned work (list/workspace/start/extract/map/calculate/status)
* strict bidirectional isolation: entity staff never see internal or
  cross-entity work or any customer-org surface; internal staff never process
  entity-assigned batches
* mediated clarification (entity-scoped issues: entity -> CarbonTally ->
  customer; the customer NEVER sees the entity issue)
* assignment/reassignment recorded through the existing V3 audit trail
* D20/D21 hardening intact: entity staff never pass internal-admin/role-name
  guards; no broad customer-org access ever granted
"""
from __future__ import annotations

import asyncio

from domain.entity import ProcessingEntity
from domain.partners import ManualExtractionBatch, ManualExtractionItem
from domain.staff import StaffProfile, StaffRole
from tests.unit.api.fakes import admin_user, entity_operator_user, member_user, staff_user

# ---------------------------------------------------------------------------
# Seeding helpers
# ---------------------------------------------------------------------------


def _seed_world(world) -> None:
    """Seed roles, entities, staff profiles (internal + two entities)."""
    world.staff.seed_role(
        StaffRole(id="role-operator", name="operator", permissions={"can_process": True})
    )
    world.staff.seed_role(
        StaffRole(
            id="role-manager",
            name="manager",
            permissions={
                "can_manage_staff": True,
                "can_process": True,
                "can_review": True,
                "can_view_all": True,
            },
        )
    )
    world.staff.seed_role(
        StaffRole(
            id="role-reviewer", name="reviewer", permissions={"can_review": True}
        )
    )
    asyncio.run(world.entities.save(ProcessingEntity(id="entity-1", name="Processing Entity A", status="active")))
    asyncio.run(world.entities.save(ProcessingEntity(id="entity-2", name="Processing Entity B", status="active")))
    asyncio.run(world.entities.save(ProcessingEntity(id="entity-3", name="Processing Entity C", status="suspended")))
    profiles = [
        StaffProfile(
            id="sp-op", user_id="u-op", first_name="Op", last_name="One",
            email="op@carbontally.test", role_id="role-operator", entity_id=None,
        ),
        StaffProfile(
            id="sp-rev", user_id="u-rev", first_name="Rev", last_name="One",
            email="rev@carbontally.test", role_id="role-reviewer", entity_id=None,
        ),
        StaffProfile(
            id="sp-mgr", user_id="u-mgr", first_name="Mgr", last_name="One",
            email="mgr@carbontally.test", role_id="role-manager", entity_id=None,
        ),
        StaffProfile(
            id="sp-ent1", user_id="u-ent1", first_name="Ent", last_name="A",
            email="enta@entity.test", role_id="role-operator", entity_id="entity-1",
        ),
        StaffProfile(
            id="sp-ent2", user_id="u-ent2", first_name="Ent", last_name="B",
            email="entb@entity.test", role_id="role-operator", entity_id="entity-2",
        ),
    ]
    for profile in profiles:
        world.staff.seed_profile(profile)


def _seed_work(world) -> tuple[ManualExtractionBatch, ManualExtractionItem, ManualExtractionItem]:
    """Seed one internal batch (org-a, u-op), one Entity-A batch (org-a) with a
    pending item, and one Entity-B batch (org-b) with a pending item."""
    internal_batch = asyncio.run(
        world.manual_extraction.create_batch("org-a", "Internal B1", created_by="u-mgr")
    )
    asyncio.run(
        world.manual_extraction.update_batch(
            internal_batch.id, status="in_progress", assigned_to="u-op", assigned_by="u-mgr"
        )
    )
    entity_a_batch = asyncio.run(
        world.manual_extraction.create_batch("org-a", "Entity A B1", created_by="u-mgr")
    )
    asyncio.run(
        world.manual_extraction.update_batch(
            entity_a_batch.id,
            status="in_progress",
            assigned_to=None,
            assigned_by="u-mgr",
            entity_id="entity-1",
        )
    )
    entity_b_batch = asyncio.run(
        world.manual_extraction.create_batch("org-b", "Entity B B1", created_by="u-mgr")
    )
    asyncio.run(
        world.manual_extraction.update_batch(
            entity_b_batch.id,
            status="in_progress",
            assigned_to=None,
            assigned_by="u-mgr",
            entity_id="entity-2",
        )
    )
    item_a = asyncio.run(
        world.manual_extraction.create_item(
            entity_a_batch.id, "invoice-a.pdf", "https://files.test/a.pdf", 2
        )
    )
    item_b = asyncio.run(
        world.manual_extraction.create_item(
            entity_b_batch.id, "invoice-b.pdf", "https://files.test/b.pdf", 2
        )
    )
    return internal_batch, item_a, item_b

# ---------------------------------------------------------------------------
# A/B/C — Entity staff see ONLY their entity's assigned work
# ---------------------------------------------------------------------------


def test_a_entity_staff_list_own_entity_batches(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    response = client.get("/api/v3/ops/entities/entity-1/extraction/batches")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["batches"][0]["entity_id"] == "entity-1"
    assert body["batches"][0]["assigned_to"] is None


def test_b_entity_staff_cannot_touch_another_entitys_workspace(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    # Cross-entity workspace is denied outright (403), even before row checks.
    assert client.get("/api/v3/ops/entities/entity-2/extraction/batches").status_code == 403
    assert client.get("/api/v3/ops/entities/entity-2/dashboard").status_code == 403


def test_c_entity_staff_never_see_internal_batches(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    batches = client.get("/api/v3/ops/entities/entity-1/extraction/batches").json()
    # Only the Entity-A batch; the internal batch (entity_id NULL) never appears.
    assert batches["total"] == 1
    assert all(b["entity_id"] == "entity-1" for b in batches["batches"])


# ---------------------------------------------------------------------------
# D — Entity staff have NO customer-org access (D20 intact)
# ---------------------------------------------------------------------------


def test_d_entity_staff_denied_customer_org_surface(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    assert (
        client.get("/api/v3/manual-extraction/batches?organization_id=org-a").status_code
        == 403
    )
    assert (
        client.get("/api/v3/ops/queues/operator").status_code == 403
    )  # internal queue requires internal staff
    assert client.get("/api/v3/ops/dashboard").status_code == 403


# ---------------------------------------------------------------------------
# E — Internal operator queue excludes entity-assigned work (single active party)
# ---------------------------------------------------------------------------


def test_e_internal_operator_queue_excludes_entity_work(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    response = client.get("/api/v3/ops/queues/operator")
    assert response.status_code == 200
    # Only the internal batch — the entity-assigned batches never appear.
    assert response.json()["queued"] == 1
    assert response.json()["batches"][0]["batch"]["entity_id"] is None


# ---------------------------------------------------------------------------
# F — Entity staff process their entity's assigned work end-to-end
# ---------------------------------------------------------------------------


def _entity_item(world, entity_id: str):
    batch = next(
        b for b in world.manual_extraction._batches.values() if b.entity_id == entity_id
    )
    return next(i for i in world.manual_extraction._items.values() if i.batch_id == batch.id)


def test_f_entity_staff_process_own_entity_work(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    ea_item = _entity_item(world, "entity-1")

    # workspace
    ws = client.get(f"/api/v3/ops/entities/entity-1/extraction/items/{ea_item.id}")
    assert ws.status_code == 200
    assert ws.json()["item"]["id"] == ea_item.id
    assert ws.json()["batch"]["entity_id"] == "entity-1"

    # start + extract + map
    started = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{ea_item.id}/start",
        json={"stage": "extraction"},
    )
    assert started.status_code == 200
    assert started.json()["working_status"] == "extracting"

    extracted = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{ea_item.id}/extract",
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
    assert extracted.status_code == 200
    assert extracted.json()["item"]["status"] == "extracted"

    mapped = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{ea_item.id}/map",
        json={
            "mapped_data": {"activity_type": "Natural gas"},
            "emission_factor_used": "factor-defra-gas",
        },
    )
    assert mapped.status_code == 200
    assert mapped.json()["item"]["status"] == "mapped"

    # CarbonTally's validation gate reviews the entity's output, then the
    # entity calculates.
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    validated = client.post(f"/api/v3/ops/items/{ea_item.id}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "validated"

    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    # calculation requires the 'calculating' working status first
    calc_start = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{ea_item.id}/start",
        json={"stage": "calculation"},
    )
    assert calc_start.status_code == 200
    assert calc_start.json()["working_status"] == "calculating"

    calculated = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{ea_item.id}/calculate",
        json={},
    )
    assert calculated.status_code == 200
    assert calculated.json()["item"]["status"] == "calculated"
    assert float(calculated.json()["result"]["co2e_kg"]) >= 0

    # next-item returns nothing new at the extraction stage (item already worked)
    nxt = client.get(
        "/api/v3/ops/entities/entity-1/extraction/next-item",
        params={"stage": "source"},
    )
    assert nxt.status_code == 404


# ---------------------------------------------------------------------------
# G/H — Entity staff cannot touch another entity's item or CarbonTally gates
# ---------------------------------------------------------------------------


def test_g_entity_staff_cannot_process_another_entitys_item(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    eb_item = _entity_item(world, "entity-2")
    response = client.get(f"/api/v3/ops/entities/entity-1/extraction/items/{eb_item.id}")
    assert response.status_code == 403  # batch belongs to entity-2
    # next-item for entity-1 returns only entity-1's own items (never entity-2's).
    nxt = client.get(
        "/api/v3/ops/entities/entity-1/extraction/next-item",
        params={"stage": "source"},
    )
    assert nxt.status_code == 200
    nxt_item = nxt.json()["item"]
    nxt_batch = world.manual_extraction._batches[nxt_item["batch_id"]]
    assert nxt_batch.entity_id == "entity-1"


def test_h_entity_staff_denied_internal_gates(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    assert client.get("/api/v3/ops/queues/qc").status_code == 403
    assert client.get("/api/v3/ops/staff").status_code == 403
    assert client.get("/api/v3/ops/queues/operator").status_code == 403
    ea_item = _entity_item(world, "entity-1")
    # status endpoint rejects CarbonTally-gated statuses even on own entity work
    assert (
        client.post(
            f"/api/v3/ops/entities/entity-1/extraction/items/{ea_item.id}/status",
            json={"status": "validated"},
        ).status_code
        == 403
    )


# ---------------------------------------------------------------------------
# I/J/K/N/O — Assignment administration (CarbonTally controls the assignment)
# ---------------------------------------------------------------------------


def test_i_assign_batch_to_entity_by_internal_manager(client, world, user_provider) -> None:
    _seed_world(world)
    internal_batch, _item_a, _item_b = _seed_work(world)
    # Entity staff cannot assign.
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    assert (
        client.post(
            f"/api/v3/ops/batches/{internal_batch.id}/assign",
            json={"entity_id": "entity-1"},
        ).status_code
        == 403
    )
    # Internal manager assigns the internal batch to Entity A.
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    response = client.post(
        f"/api/v3/ops/batches/{internal_batch.id}/assign",
        json={"entity_id": "entity-1", "reason": "capacity"},
    )
    assert response.status_code == 200
    batch = response.json()["batch"]
    assert batch["entity_id"] == "entity-1"
    assert batch["assigned_to"] is None
    assert batch["assigned_by"] == "u-mgr"
    # Audit trail records the assignment.
    assert any(e.entity_id == internal_batch.id for e in world.audit._entries)


def test_j_reassign_entity_a_to_entity_b_records_history(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    ea_batch = next(
        b for b in world.manual_extraction._batches.values() if b.entity_id == "entity-1"
    )
    response = client.post(
        f"/api/v3/ops/batches/{ea_batch.id}/assign",
        json={"entity_id": "entity-2", "reason": "rebalance"},
    )
    assert response.status_code == 200
    assert response.json()["batch"]["entity_id"] == "entity-2"
    audit = [e for e in world.audit._entries if e.entity_id == ea_batch.id]
    assert any(e.action == "reassigned" for e in audit)
    assert any((e.reason or "") == "rebalance" for e in audit)


def test_k_assign_to_inactive_entity_rejected(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    ea_batch = next(
        b for b in world.manual_extraction._batches.values() if b.entity_id == "entity-1"
    )
    response = client.post(
        f"/api/v3/ops/batches/{ea_batch.id}/assign",
        json={"entity_id": "entity-3"},
    )
    assert response.status_code == 422


def test_n_assign_requires_exactly_one_party(client, world, user_provider) -> None:
    _seed_world(world)
    internal_batch, _item_a, _item_b = _seed_work(world)
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    both = client.post(
        f"/api/v3/ops/batches/{internal_batch.id}/assign",
        json={"assigned_to": "u-op", "entity_id": "entity-1"},
    )
    assert both.status_code == 422
    neither = client.post(
        f"/api/v3/ops/batches/{internal_batch.id}/assign",
        json={"reason": "empty"},
    )
    assert neither.status_code == 422


def test_o_reassign_entity_back_to_internal_operator(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    ea_batch = next(
        b for b in world.manual_extraction._batches.values() if b.entity_id == "entity-1"
    )
    response = client.post(
        f"/api/v3/ops/batches/{ea_batch.id}/assign",
        json={"assigned_to": "u-op", "reason": "return to CarbonTally"},
    )
    assert response.status_code == 200
    batch = response.json()["batch"]
    assert batch["entity_id"] is None
    assert batch["assigned_to"] == "u-op"
    assert any(
        e.action == "reassigned"
        for e in world.audit._entries
        if e.entity_id == ea_batch.id
    )


# ---------------------------------------------------------------------------
# M — Internal staff blocked from entity-assigned work (bidirectional isolation)
# ---------------------------------------------------------------------------


def test_m_internal_operator_blocked_from_entity_batch(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    ea_item = _entity_item(world, "entity-1")
    # Internal pipeline rejects the entity-assigned item outright.
    assert (
        client.post(
            f"/api/v3/ops/items/{ea_item.id}/start", json={"stage": "extraction"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v3/ops/items/{ea_item.id}/extract", json={"extracted_data": {}}
        ).status_code
        == 403
    )

# ---------------------------------------------------------------------------
# L — Mediated clarification (entity -> CarbonTally; NEVER customer-facing)
# ---------------------------------------------------------------------------


def test_l_mediated_clarification_issue(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    ea_item = _entity_item(world, "entity-1")
    ea_batch = next(
        b for b in world.manual_extraction._batches.values() if b.id == ea_item.batch_id
    )
    response = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{ea_item.id}/clarify",
        json={"title": "Invoice supplier unclear", "description": "Two supplier names"},
    )
    assert response.status_code == 200
    issue = response.json()["issue"]
    assert issue["entity_id"] == "entity-1"
    assert issue["organization_id"] == "org-a"
    assert issue["manual_extraction_batch_id"] == ea_batch.id
    # CarbonTally internal triage sees it (mediated leg).
    user_provider.set_user(admin_user())
    triage = client.get("/api/v3/issues/admin/open")
    assert triage.status_code == 200
    assert any(i["id"] == issue["id"] for i in triage.json()["issues"])
    # The customer NEVER sees the entity-scoped issue.
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    customer_issues = client.get("/api/v3/issues", params={"organization_id": "org-a"})
    assert customer_issues.status_code == 200
    assert all(i["id"] != issue["id"] for i in customer_issues.json()["issues"])


# ---------------------------------------------------------------------------
# P/Q — Dashboard extraction block + the server never trusts path entity_id
# ---------------------------------------------------------------------------


def test_p_entity_dashboard_includes_extraction_block(client, world, user_provider) -> None:
    _seed_world(world)
    _seed_work(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent1"))
    response = client.get("/api/v3/ops/entities/entity-1/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["extraction"]["batches"]["total"] == 1
    assert body["extraction"]["items"]["total"] == 1


def test_q_entity_staff_cannot_fake_entity_id_parameter(client, world, user_provider) -> None:
    """The server derives scope from the caller's profile, never the path."""
    _seed_world(world)
    _seed_work(world)
    # Entity-2 staff pass entity-1's entity_id in the path -> 403 (require_entity_scope).
    user_provider.set_user(entity_operator_user("entity-2", "u-ent2"))
    assert client.get("/api/v3/ops/entities/entity-1/extraction/batches").status_code == 403


