"""WS4 Gate 4 remediation F1/F2 — actor/entity attribution regression tests.

Verifies, over the real FastAPI surface with the in-memory world (the standard
unit/API harness — real authorization guards + real calculation/validation
engines over fake repositories):

* internal-origin map/validate/calculate persist the responsible actor as
  canonical audit events (``ops_map:applied``, ``ops_validate:validated``,
  ``ops_calculate:applied``);
* PE-origin map/calculate persist the responsible PE actor
  (``pe_map:applied``, ``pe_calculate:applied``);
* calculation snapshots carry the actual human actor
  (``calculation_snapshots.performed_by``) — never the organisation id alone;
* PE-origin calculation snapshots are linked to their source work item
  (``source_item_id``) — F2 — and the internal-origin link stays intact.
"""
from __future__ import annotations

import asyncio

from domain.entity import ProcessingEntity
from domain.staff import StaffProfile, StaffRole
from tests.unit.api.fakes import entity_operator_user, staff_user


def _seed_world(world) -> None:
    world.staff.seed_role(
        StaffRole(id="role-op", name="operator", permissions={"can_process": True})
    )
    world.staff.seed_role(
        StaffRole(id="role-rev", name="reviewer", permissions={"can_review": True})
    )
    world.staff.seed_role(
        StaffRole(
            id="role-entity-op",
            name="entity_operator",
            permissions={"can_process": True},
        )
    )
    asyncio.run(
        world.entities.save(
            ProcessingEntity(id="entity-1", name="Entity Alpha", status="active")
        )
    )
    profiles = [
        StaffProfile(
            id="sp-op", user_id="u-op", first_name="Op", last_name="One",
            email="op@carbontally.test", role_id="role-op", entity_id=None,
        ),
        StaffProfile(
            id="sp-rev", user_id="u-rev", first_name="Rev", last_name="One",
            email="rev@carbontally.test", role_id="role-rev", entity_id=None,
        ),
        StaffProfile(
            id="sp-ent", user_id="u-ent", first_name="Ent", last_name="Alpha",
            email="ent@entity.test", role_id="role-entity-op", entity_id="entity-1",
        ),
    ]
    for profile in profiles:
        world.staff.seed_profile(profile)


def _seed_internal_batch_with_item(world):
    batch = asyncio.run(
        world.manual_extraction.create_batch("org-a", "G4R internal batch")
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id,
            file_name="g4r-internal.csv",
            file_url="storage/docs/g4r-internal.csv",
            document_type="invoice",
            status="pending",
        )
    )
    return batch, item


def _seed_entity_batch_with_item(world):
    batch = asyncio.run(
        world.manual_extraction.create_batch("org-a", "G4R entity batch")
    )
    asyncio.run(
        world.manual_extraction.update_batch(
            batch.id,
            status="in_progress",
            assigned_to=None,
            assigned_by="u-rev",
            entity_id="entity-1",
        )
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id,
            file_name="g4r-pe.csv",
            file_url="storage/docs/g4r-pe.csv",
            document_type="invoice",
            status="pending",
        )
    )
    return batch, item


def _audit_entries(world, action: str):
    return [e for e in world.audit._entries if e.action == action]


def _internal_operator(user_provider) -> None:
    user_provider.set_user(staff_user("u-op", email="op@carbontally.test"))


def _reviewer(user_provider) -> None:
    user_provider.set_user(staff_user("u-rev", email="rev@carbontally.test"))


def _pe_operator(user_provider) -> None:
    user_provider.set_user(entity_operator_user("entity-1", "u-ent"))


def test_internal_map_validate_calculate_persist_actor(client, world, user_provider):
    """F1 — internal-origin map/validate/calculate record the human actor."""
    _seed_world(world)
    _batch, item = _seed_internal_batch_with_item(world)

    _internal_operator(user_provider)
    assert client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"}).status_code == 200
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
    assert extract.status_code == 200
    mapped = client.post(
        f"/api/v3/ops/items/{item.id}/map",
        json={
            "mapped_data": {"activity_type": "Natural gas"},
            "emission_factor_used": "factor-defra-gas",
        },
    )
    assert mapped.status_code == 200
    assert mapped.json()["item"]["status"] == "mapped"

    _reviewer(user_provider)
    validated = client.post(f"/api/v3/ops/items/{item.id}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "validated"

    _internal_operator(user_provider)
    assert client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "calculation"}).status_code == 200
    calculated = client.post(f"/api/v3/ops/items/{item.id}/calculate", json={})
    assert calculated.status_code == 200

    map_audits = _audit_entries(world, "ops_map:applied")
    assert len(map_audits) == 1
    assert map_audits[0].actor == "u-op"
    assert map_audits[0].entity_id == item.id
    assert map_audits[0].changed_fields.get("status_to") == "mapped"

    validate_audits = _audit_entries(world, "ops_validate:validated")
    assert len(validate_audits) == 1
    assert validate_audits[0].actor == "u-rev"
    assert validate_audits[0].changed_fields.get("status_to") == "validated"

    calc_audits = _audit_entries(world, "ops_calculate:applied")
    assert len(calc_audits) == 1
    assert calc_audits[0].actor == "u-op"
    assert calc_audits[0].changed_fields.get("status_to") == "calculated"
    snapshot_id = calc_audits[0].changed_fields.get("snapshot_id")
    assert snapshot_id

    # Snapshot actor = the human operator (never the org id); snapshot remains
    # linked to its source work item (internal-origin linkage intact).
    snapshot = world.logs._snapshots[snapshot_id]
    assert world.logs._snapshot_actors[snapshot_id] == "u-op"
    assert world.logs._snapshot_actors[snapshot_id] != "org-a"
    assert snapshot.source_item_id == item.id


def test_pe_map_calculate_persist_actor_and_link_snapshot(client, world, user_provider):
    """F1 + F2 — PE-origin map/calculate record the PE actor and link the snapshot."""
    _seed_world(world)
    _batch, item = _seed_entity_batch_with_item(world)

    _pe_operator(user_provider)
    assert client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/start",
        json={"stage": "extraction"},
    ).status_code == 200
    extract = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/extract",
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
    assert extract.status_code == 200
    mapped = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/map",
        json={
            "mapped_data": {"activity_type": "Natural gas"},
            "emission_factor_used": "factor-defra-gas",
        },
    )
    assert mapped.status_code == 200
    assert mapped.json()["item"]["status"] == "mapped"

    # CarbonTally validation gate (internal reviewer) approves the PE output.
    _reviewer(user_provider)
    validated = client.post(f"/api/v3/ops/items/{item.id}/validate")
    assert validated.status_code == 200
    assert validated.json()["status"] == "validated"

    # PE operator calculates through the PE-origin surface.
    _pe_operator(user_provider)
    assert client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/start",
        json={"stage": "calculation"},
    ).status_code == 200
    calculated = client.post(
        f"/api/v3/ops/entities/entity-1/extraction/items/{item.id}/calculate",
        json={},
    )
    assert calculated.status_code == 200

    map_audits = _audit_entries(world, "pe_map:applied")
    assert len(map_audits) == 1
    assert map_audits[0].actor == "u-ent"
    assert map_audits[0].changed_fields.get("entity_id") == "entity-1"
    assert map_audits[0].changed_fields.get("status_to") == "mapped"

    calc_audits = _audit_entries(world, "pe_calculate:applied")
    assert len(calc_audits) == 1
    assert calc_audits[0].actor == "u-ent"
    assert calc_audits[0].changed_fields.get("entity_id") == "entity-1"
    assert calc_audits[0].changed_fields.get("status_to") == "calculated"
    snapshot_id = calc_audits[0].changed_fields.get("snapshot_id")
    assert snapshot_id

    # F1: snapshot actor is the PE human operator (never the org id).
    snapshot = world.logs._snapshots[snapshot_id]
    assert world.logs._snapshot_actors[snapshot_id] == "u-ent"
    assert world.logs._snapshot_actors[snapshot_id] != "org-a"
    # F2: the PE-origin snapshot links to its source work item.
    assert snapshot.source_item_id == item.id
