"""V3 operations surface (Phase 8) — route registration + authorization + workflow.

Covers the CarbonTally-internal workforce layer over ``/api/v3/ops/*``:
staff identity + role gating (server-side), operator/review/QC queues, the item
workflow (start/extract/map/validate/calculate/QC), batch/review assignment,
SLA settings and the shared split-screen workspace. All authorization is
server-side (frontend visibility is never the barrier).
"""
from __future__ import annotations

import asyncio

from domain.entity import ProcessingEntity
from domain.partners import ManualExtractionBatch, ManualExtractionItem
from domain.staff import StaffProfile, StaffRole
from tests.unit.api.fakes import (
    entity_operator_user,
    member_user,
    staff_user,
)
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/ops/me",
    "/api/v3/ops/dashboard",
    "/api/v3/ops/staff",
    "/api/v3/ops/staff-roles",
    "/api/v3/ops/entities",
    "/api/v3/ops/entities/{entity_id}/dashboard",
    "/api/v3/ops/entities/{entity_id}/extraction/batches",
    "/api/v3/ops/entities/{entity_id}/extraction/batches/{batch_id}",
    "/api/v3/ops/entities/{entity_id}/extraction/batches/{batch_id}/items",
    "/api/v3/ops/entities/{entity_id}/extraction/items/{item_id}",
    "/api/v3/ops/entities/{entity_id}/extraction/next-item",
    "/api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/start",
    "/api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/extract",
    "/api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/map",
    "/api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/calculate",
    "/api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/status",
    "/api/v3/ops/entities/{entity_id}/extraction/items/{item_id}/clarify",
    "/api/v3/ops/queues/operator",
    "/api/v3/ops/queues/review",
    "/api/v3/ops/queues/qc",
    "/api/v3/ops/items/{item_id}/workspace",
    "/api/v3/ops/items/{item_id}/mapping-options",
    "/api/v3/ops/items/{item_id}/start",
    "/api/v3/ops/items/{item_id}/extract",
    "/api/v3/ops/items/{item_id}/map",
    "/api/v3/ops/items/{item_id}/validate",
    "/api/v3/ops/items/{item_id}/calculate",
    "/api/v3/ops/items/{item_id}/qc",
    "/api/v3/ops/batches/{batch_id}/assign",
    "/api/v3/ops/review/{review_id}/assign",
    "/api/v3/ops/review/{review_id}/complete",
    "/api/v3/ops/sla/settings",
    "/api/v3/ops/next-item",
)


def _seed_ops_world(world) -> None:
    """Seed staff roles + staff profiles the ops guards resolve (server-side).

    Permissions live on ``staff_roles`` (``staff_profiles.role_id`` →
    ``staff_roles.id``) — the authoritative staff-role model.
    """
    world.staff.seed_role(
        StaffRole(id="role-operator", name="operator", permissions={"can_process": True})
    )
    world.staff.seed_role(
        StaffRole(id="role-reviewer", name="reviewer", permissions={"can_review": True})
    )
    # Supervisor = manager with the full ops permission set (review + process +
    # manage staff + view-all). This matches the batch/review assignment gates,
    # which require two permissions at once.
    world.staff.seed_role(
        StaffRole(
            id="role-manager",
            name="manager",
            permissions={
                "can_manage_staff": True,
                "can_view_all": True,
                "can_review": True,
                "can_process": True,
            },
        )
    )
    asyncio.run(world.entities.save(ProcessingEntity(id="entity-1", name="Entity Beta", status="active")))
    profiles = [
        StaffProfile(
            id="sp-op",
            user_id="u-op",
            first_name="Op",
            last_name="One",
            email="op@carbontally.test",
            role_id="role-operator",
            entity_id=None,
        ),
        StaffProfile(
            id="sp-rev",
            user_id="u-rev",
            first_name="Rev",
            last_name="One",
            email="rev@carbontally.test",
            role_id="role-reviewer",
            entity_id=None,
        ),
        StaffProfile(
            id="sp-mgr",
            user_id="u-mgr",
            first_name="Mgr",
            last_name="One",
            email="mgr@carbontally.test",
            role_id="role-manager",
            entity_id=None,
        ),
        StaffProfile(
            id="sp-ent",
            user_id="u-ent",
            first_name="Ent",
            last_name="One",
            email="ent@carbontally.test",
            role_id="role-reviewer",
            entity_id="entity-1",
        ),
    ]
    for profile in profiles:
        world.staff.seed_profile(profile)

# ---------------------------------------------------------------------------
# Authorization (server-side)
# ---------------------------------------------------------------------------


def test_ops_requires_staff(client, user_provider) -> None:
    # A non-staff org member is not an active staff profile -> 403.
    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/ops/me").status_code == 403


def test_ops_requires_staff_profile(client, world, user_provider) -> None:
    _seed_ops_world(world)
    # Authenticated but with no staff profile -> 403.
    user_provider.set_user(staff_user("u-nobody", email="nobody@carbontally.test"))
    assert client.get("/api/v3/ops/me").status_code == 403


def test_operator_queue_requires_can_process(client, world, user_provider) -> None:
    _seed_ops_world(world)
    # Reviewer role has can_review but not can_process -> 403.
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    assert client.get("/api/v3/ops/queues/operator").status_code == 403


def test_internal_operator_accesses_operator_queue(client, world, user_provider) -> None:
    _seed_ops_world(world)
    batch, _item = _seed_batch_with_item(world)
    asyncio.run(_assign_batch_to(world, batch, "u-op"))
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    response = client.get("/api/v3/ops/queues/operator")
    assert response.status_code == 200
    assert response.json()["queued"] == 1


def test_entity_staff_denied_internal_dashboard(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent"))
    assert client.get("/api/v3/ops/dashboard").status_code == 403
    assert client.get("/api/v3/ops/queues/operator").status_code == 403


def test_entity_staff_entity_dashboard_allowed_for_own_entity(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent"))
    response = client.get("/api/v3/ops/entities/entity-1/dashboard")
    assert response.status_code == 200


def test_entity_staff_entity_dashboard_denied_cross_entity(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent"))
    assert client.get("/api/v3/ops/entities/entity-2/dashboard").status_code == 403


# ---------------------------------------------------------------------------
# Ops dashboard + staff roster (manager role)
# ---------------------------------------------------------------------------


def test_ops_dashboard_internal_manager(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    response = client.get("/api/v3/ops/dashboard")
    assert response.status_code == 200
    assert "scope" in response.json()
    assert "pipeline" in response.json()


def test_staff_list_requires_permission(client, world, user_provider) -> None:
    _seed_ops_world(world)
    # Operator has neither can_view_all nor can_manage_staff -> 403.
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    assert client.get("/api/v3/ops/staff").status_code == 403


def test_staff_list_manager(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    response = client.get("/api/v3/ops/staff")
    assert response.status_code == 200
    assert response.json()["total"] == 4


def test_staff_roles_catalog(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    response = client.get("/api/v3/ops/staff-roles")
    assert response.status_code == 200
    assert "staff_roles" in response.json()


def _seed_batch_with_item(world) -> tuple[ManualExtractionBatch, ManualExtractionItem]:
    """Synchronously seed a batch + one pending item in the in-memory world."""
    return asyncio.run(_seed_batch_with_item_async(world))


async def _seed_batch_with_item_async(world):
    batch = await world.manual_extraction.create_batch("org-a", "Phase 8 batch")
    item = await world.manual_extraction.create_item(
        batch.id,
        file_name="invoice-2025.pdf",
        file_url="storage/docs/invoice-2025.pdf",
        document_type="invoice",
        status="pending",
    )
    return batch, item


async def _assign_batch_to(world, batch, user_id: str) -> None:
    await world.manual_extraction.update_batch(
        batch.id, status="in_progress", assigned_to=user_id
    )


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def test_v3_ops_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 ops routes: {missing}"


def test_v3_qc_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    for fragment in ("/api/v3/qc/queue", "/api/v3/qc/stats", "/api/v3/qc/items/{item_id}/review"):
        assert any(fragment in p for p in paths), f"missing V3 QC route: {fragment}"

# ---------------------------------------------------------------------------
# Item workflow (operator pipeline)
# ---------------------------------------------------------------------------


def test_item_workflow_start_and_extract(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))

    start = client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"})
    assert start.status_code == 200
    assert start.json()["working_status"] == "extracting"

    extract = client.post(
        f"/api/v3/ops/items/{item.id}/extract",
        json={"extracted_data": {"quantity": "1000", "unit": "kWh", "activity": "Natural gas"}},
    )
    assert extract.status_code == 200
    assert extract.json()["item"]["status"] == "extracted"


def test_item_workflow_full_pipeline_operator(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)

    # Data entry (can_process): start/extract/map.
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"})
    extract = client.post(
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
    assert extract.json()["item"]["status"] == "extracted"

    mapped = client.post(
        f"/api/v3/ops/items/{item.id}/map",
        json={
            "mapped_data": {"activity_type": "Natural gas"},
            "emission_factor_used": "factor-defra-gas",
        },
    )
    assert mapped.status_code == 200
    assert mapped.json()["item"]["status"] == "mapped"

    # Validation is a reviewer action (can_review).
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    validated = client.post(f"/api/v3/ops/items/{item.id}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "validated"

    # Calculation returns to the operator (can_process).
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    calc_start = client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "calculation"})
    assert calc_start.status_code == 200
    assert calc_start.json()["working_status"] == "calculating"

    calculated = client.post(f"/api/v3/ops/items/{item.id}/calculate", json={})
    assert calculated.status_code == 200
    assert float(calculated.json()["result"]["co2e_kg"]) == 183.0


def test_validate_returns_blocking_findings(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"})
    # Missing quantity/unit -> blocking findings route the item back to mapping.
    client.post(f"/api/v3/ops/items/{item.id}/extract", json={"extracted_data": {"activity": "X"}})
    client.post(
        f"/api/v3/ops/items/{item.id}/map",
        json={"mapped_data": {}, "emission_factor_used": "factor-defra-gas"},
    )
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    response = client.post(f"/api/v3/ops/items/{item.id}/validate")
    assert response.status_code == 200
    assert response.json()["blocking"] is True
    assert response.json()["status"] == "mapping"


# ---------------------------------------------------------------------------
# QC (CarbonTally-staff gate over extracted items)
# ---------------------------------------------------------------------------


def test_qc_review_extracted_item(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    asyncio.run(world.manual_extraction.set_item_status(item.id, "extracted"))
    response = client.post(
        f"/api/v3/ops/items/{item.id}/qc",
        json={"quality_score": 88, "approved": True, "qc_notes": "clean"},
    )
    assert response.status_code == 200
    assert response.json()["item"]["status"] in ("qc_approved", "qc_rejected")


def test_qc_rejects_non_extracted_item(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    response = client.post(
        f"/api/v3/ops/items/{item.id}/qc",
        json={"quality_score": 88, "approved": True},
    )
    assert response.status_code == 409


def test_qc_queue_lists_pending(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    asyncio.run(world.manual_extraction.set_item_status(item.id, "extracted"))
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    response = client.get("/api/v3/ops/queues/qc")
    assert response.status_code == 200
    assert response.json()["queued"] == 1


# ---------------------------------------------------------------------------
# Review queue + assignment
# ---------------------------------------------------------------------------


def test_review_queue_requires_can_review(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    assert client.get("/api/v3/ops/queues/review").status_code == 403


def test_review_assign_and_complete(client, world, user_provider) -> None:
    _seed_ops_world(world)
    review = await_review_item(world)
    # Assignment requires can_review + can_manage_staff (supervisor); completing
    # requires can_review (reviewer).
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    assign = client.post(
        f"/api/v3/ops/review/{review.id}/assign",
        json={"assigned_to": "u-rev"},
    )
    assert assign.status_code == 200
    assert assign.json()["item"]["status"] == "assigned"
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))
    complete = client.post(
        f"/api/v3/ops/review/{review.id}/complete",
        json={"manual_extraction_result": {"ok": True}, "review_time_seconds": 42},
    )
    assert complete.status_code == 200
    assert complete.json()["item"]["status"] == "completed"


def test_batch_assign_requires_manager(client, world, user_provider) -> None:
    _seed_ops_world(world)
    batch, _item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    response = client.post(
        f"/api/v3/ops/batches/{batch.id}/assign",
        json={"assigned_to": "u-op"},
    )
    assert response.status_code == 403


def test_batch_assign_by_manager(client, world, user_provider) -> None:
    _seed_ops_world(world)
    batch, _item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))
    response = client.post(
        f"/api/v3/ops/batches/{batch.id}/assign",
        json={"assigned_to": "u-op"},
    )
    assert response.status_code == 200
    assert response.json()["batch"]["assigned_to"] == "u-op"


# ---------------------------------------------------------------------------
# SLA settings + workspace + mapping options + next-item
# ---------------------------------------------------------------------------


def test_sla_settings_read(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    response = client.get("/api/v3/ops/sla/settings")
    assert response.status_code == 200
    assert "sla_hours" in response.json()


def test_item_workspace_shared(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    response = client.get(f"/api/v3/ops/items/{item.id}/workspace")
    assert response.status_code == 200
    body = response.json()
    assert "source" in body
    assert "data" in body
    assert "workflow" in body


def test_mapping_options(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    response = client.get(f"/api/v3/ops/items/{item.id}/mapping-options")
    assert response.status_code == 200
    assert "facilities" in response.json()
    assert "factors" in response.json()


def test_next_item_flow(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    response = client.get("/api/v3/ops/next-item", params={"stage": "extraction"})
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert response.json()["id"] == item.id


def await_review_item(world):
    import asyncio as _asyncio

    return _asyncio.run(_create_review_item(world))


async def _create_review_item(world):
    return await world.review_queue.create_item(
        org_id="org-a", file_name="invoice.pdf", status="pending", priority=2
    )


# ---------------------------------------------------------------------------
# STEP 10 — server-side security: manipulated IDs / cross-company denial
# ---------------------------------------------------------------------------


def test_operator_cannot_touch_batch_assigned_to_another_operator(client, world, user_provider) -> None:
    _seed_ops_world(world)
    batch, item = _seed_batch_with_item(world)
    asyncio.run(_assign_batch_to(world, batch, "u-other"))
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    # The item belongs to a batch assigned to another operator -> 403 (the
    # operator may only touch batches assigned to them, or open self-serve ones).
    response = client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"})
    assert response.status_code == 403


def test_missing_item_id_returns_404(client, world, user_provider) -> None:
    _seed_ops_world(world)
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))
    assert client.get("/api/v3/ops/items/does-not-exist/workspace").status_code == 404


def test_entity_staff_cannot_access_manual_extraction_items(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(entity_operator_user("entity-1", "u-ent"))
    # Processing-entity staff are structurally denied from the manual-extraction
    # pipeline (batches/items carry no entity column).
    assert client.get(f"/api/v3/ops/items/{item.id}/workspace").status_code == 403


def test_entity_staff_cannot_review_other_entity_item(client, world, user_provider) -> None:
    _seed_ops_world(world)
    review = _seed_review_item(world, entity_id="entity-2")
    user_provider.set_user(entity_operator_user("entity-1", "u-ent"))
    assign = client.post(
        f"/api/v3/ops/review/{review.id}/assign",
        json={"assigned_to": "u-rev"},
    )
    # u-ent belongs to entity-1; the review item is entity-2 -> denied.
    assert assign.status_code == 403


def _seed_review_item(world, entity_id):
    async def _seed():
        return await world.review_queue.create_item(
            org_id="org-a", file_name="other.pdf", status="pending", priority=1, entity_id=entity_id
        )

    return asyncio.run(_seed())

