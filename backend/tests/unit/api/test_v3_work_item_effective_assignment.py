"""WS4 Gate 3 / Workstream 4B — item-level effective-assignment service tests.

Covers the required service-layer ALLOW/DENY cases (1-10) against the in-memory
world: batch default, item override, internal override, unassigned, historical
assignment, mixed one-batch, Alpha->Beta reassignment, single-open invariant,
PE cannot reassign, and origin immutability (item untouched by D38 service).
"""
from __future__ import annotations

import asyncio

import pytest

from domain.entity import ProcessingEntity
from services.work_items import (
    WorkItemError,
    ops_assign_item,
    ops_reassign_item,
    work_item_effective,
)
from tests.unit.api.fakes import InMemoryWorld

ALPHA = "entity-alpha"
BETA = "entity-beta"
CT_USER = "ct-user-1"
OPS_ACTOR = "ct-admin-1"


def _world() -> InMemoryWorld:
    world = InMemoryWorld()

    async def _seed_entities():
        await world.entities.save(
            ProcessingEntity(id=ALPHA, name="Alpha", status="active"))
        await world.entities.save(
            ProcessingEntity(id=BETA, name="Beta", status="active"))
    asyncio.run(_seed_entities())
    world.manual_extraction.seed_internal_staff(CT_USER)
    world.manual_extraction.seed_internal_staff(OPS_ACTOR)
    return world


def _seed(world: InMemoryWorld, *, batch_entity, items):
    """Create one batch (optional default entity) and seed named items.

    Returns ``(batch_id, {name: item_id})``.
    """
    async def _run():
        batch = await world.manual_extraction.create_batch(
            org_id="org-a",
            batch_name="4B-test",
            total_documents=1,
            total_pages=1,
            total_cost=0.0,
            entity_id=batch_entity,
        )
        ids = {}
        for name in items:
            item = world.manual_extraction.seed_item(
                name, "org-a", f"{name}.csv", batch_id=batch.id
            )
            ids[name] = item.id
        return batch.id, ids
    return asyncio.run(_run())


def _assign_item(world, item_id, *, entity=None, user=None):
    async def _run():
        return await ops_assign_item(
            world.bundle(), item_id=item_id, actor_user_id=OPS_ACTOR,
            target_user_id=user, target_entity_id=entity,
            reason="4B test", action="assign", close_action="superseded",
        )
    return asyncio.run(_run())


def _effective(world, item_id):
    async def _run():
        return await work_item_effective(world.bundle(), item_id)
    return asyncio.run(_run())


def _pe_claim(world, item_id, entity):
    """Return (ok, err) for a PE claim attempt."""
    from services.work_items import pe_claim_item

    async def _run():
        try:
            await pe_claim_item(
                world.bundle(), item_id=item_id, entity_id=entity,
                actor_user_id="pe-user", reason="4B claim",
            )
            return True, None
        except WorkItemError as exc:
            return False, exc.detail
    return asyncio.run(_run())


def _open_count(world, item_id) -> int:
    async def _run():
        rows = await world.manual_extraction.work_item_history(item_id)
        return sum(1 for r in rows if r.get("status") == "open")
    return asyncio.run(_run())


def test_1_batch_default_alpha_only():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["a"])
    ok_a, err_a = _pe_claim(world, ids["a"], ALPHA)
    ok_b, err_b = _pe_claim(world, ids["a"], BETA)
    assert ok_a is True
    assert ok_b is False
    assert "effectively assigned" in (err_b or "")


def test_2_item_override_beta_in_alpha_batch():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["b"])
    _assign_item(world, ids["b"], entity=BETA)
    eff = _effective(world, ids["b"])
    assert eff == {"kind": "processing_entity", "assignee": BETA, "source": "item"}
    ok_a, _ = _pe_claim(world, ids["b"], ALPHA)
    ok_b, _ = _pe_claim(world, ids["b"], BETA)
    assert ok_a is False and ok_b is True


def test_3_internal_override_in_alpha_batch():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["d"])
    _assign_item(world, ids["d"], user=CT_USER)
    eff = _effective(world, ids["d"])
    assert eff == {"kind": "internal_staff", "assignee": CT_USER, "source": "item"}
    ok_a, _ = _pe_claim(world, ids["d"], ALPHA)
    ok_b, _ = _pe_claim(world, ids["d"], BETA)
    assert ok_a is False and ok_b is False


def test_4_unassigned_no_default():
    world = _world()
    _, ids = _seed(world, batch_entity=None, items=["u"])
    eff = _effective(world, ids["u"])
    assert eff == {"kind": "unassigned", "assignee": None, "source": None}
    ok_a, _ = _pe_claim(world, ids["u"], ALPHA)
    ok_b, _ = _pe_claim(world, ids["u"], BETA)
    assert ok_a is False and ok_b is False


def test_5_historical_alpha_closed_open_beta():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["h"])
    _assign_item(world, ids["h"], entity=ALPHA)

    async def _reassign():
        await ops_reassign_item(
            world.bundle(), item_id=ids["h"], actor_user_id=OPS_ACTOR,
            target_entity_id=BETA, reason="4B history",
        )
    asyncio.run(_reassign())
    eff = _effective(world, ids["h"])
    assert eff == {"kind": "processing_entity", "assignee": BETA, "source": "item"}
    ok_a, _ = _pe_claim(world, ids["h"], ALPHA)
    ok_b, _ = _pe_claim(world, ids["h"], BETA)
    assert ok_a is False and ok_b is True
    assert _open_count(world, ids["h"]) == 1


def test_6_mixed_one_batch_isolation():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["a", "b", "c", "d"])
    _assign_item(world, ids["b"], entity=BETA)
    _assign_item(world, ids["d"], user=CT_USER)
    for name, entity, expected in [
        ("a", ALPHA, True), ("a", BETA, False),
        ("b", ALPHA, False), ("b", BETA, True),
        ("c", ALPHA, True), ("c", BETA, False),
        ("d", ALPHA, False), ("d", BETA, False),
    ]:
        ok, _ = _pe_claim(world, ids[name], entity)
        assert ok is expected, f"item {name} on {entity}"


def test_7_reassign_alpha_to_beta_updates_current_history():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["x"])
    _assign_item(world, ids["x"], entity=ALPHA)

    async def _reassign():
        return await ops_reassign_item(
            world.bundle(), item_id=ids["x"], actor_user_id=OPS_ACTOR,
            target_entity_id=BETA, reason="4B reassign",
        )
    result = asyncio.run(_reassign())
    assert result["changed"] is True
    current = result["current"]
    assert current["assignee_kind"] == "processing_entity"
    assert current["processing_entity_id"] == BETA
    assert current["previous_processing_entity_id"] == ALPHA
    ok_a, _ = _pe_claim(world, ids["x"], ALPHA)
    ok_b, _ = _pe_claim(world, ids["x"], BETA)
    assert ok_a is False and ok_b is True

    async def _hist():
        return await world.manual_extraction.work_item_history(ids["x"])
    hist = asyncio.run(_hist())
    closed = [r for r in hist if r.get("status") == "closed"]
    assert any(r.get("processing_entity_id") == ALPHA
               and r.get("close_action") == "reassigned" for r in closed)


def test_8_single_open_invariant_after_reassign():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["s"])
    _assign_item(world, ids["s"], entity=ALPHA)

    async def _reassign():
        await ops_reassign_item(
            world.bundle(), item_id=ids["s"], actor_user_id=OPS_ACTOR,
            target_entity_id=BETA, reason="4B single-open",
        )
    asyncio.run(_reassign())
    assert _open_count(world, ids["s"]) == 1


def test_9_pe_cannot_reassign_or_reach_other_entity_assignment():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["q"])
    _assign_item(world, ids["q"], entity=BETA)
    ok_alpha, err_alpha = _pe_claim(world, ids["q"], ALPHA)
    assert ok_alpha is False and "effectively assigned" in (err_alpha or "")
    import inspect
    from services import work_items
    sig = inspect.signature(work_items.pe_claim_item)
    assert "target" not in str(sig.parameters)


def test_10_origin_unchanged_by_assignment_service():
    world = _world()
    _, ids = _seed(world, batch_entity=ALPHA, items=["o"])
    before = world.manual_extraction._items[ids["o"]]
    _assign_item(world, ids["o"], entity=ALPHA)

    async def _reassign():
        await ops_reassign_item(
            world.bundle(), item_id=ids["o"], actor_user_id=OPS_ACTOR,
            target_entity_id=BETA, reason="4B origin",
        )
    asyncio.run(_reassign())
    after = world.manual_extraction._items[ids["o"]]
    assert after == before
