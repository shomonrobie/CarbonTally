"""API contract tests for the V3 Processing Entity admin surface (ADR-V3-001)."""

from __future__ import annotations

import asyncio

from tests.unit.api.fakes import InMemoryWorld, ProcessingEntity


def _await(coro) -> None:
    asyncio.run(coro)


def _seed_world() -> InMemoryWorld:
    return InMemoryWorld(
        entities=[
            ProcessingEntity(id="pe-1", name="Babui Limited", status="active"),
            ProcessingEntity(id="pe-2", name="Entity Two", status="suspended"),
        ]
    )


class TestV3EntitiesAdmin:
    def test_list_entities(self, world: InMemoryWorld, client) -> None:
        world2 = _seed_world()
        world.entities = world2.entities
        resp = client.get("/api/v3/admin/entities")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2

    def test_list_entities_by_status(self, world: InMemoryWorld, client) -> None:
        world2 = _seed_world()
        world.entities = world2.entities
        resp = client.get("/api/v3/admin/entities", params={"status": "suspended"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["entities"][0]["id"] == "pe-2"

    def test_create_entity(self, client) -> None:
        resp = client.post(
            "/api/v3/admin/entities",
            json={"name": "Provider C", "description": "Third provider"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Provider C"
        assert body["status"] == "active"

    def test_update_entity_lifecycle_transition(self, world: InMemoryWorld, client) -> None:
        world2 = _seed_world()
        world.entities = world2.entities
        resp = client.put(
            "/api/v3/admin/entities/pe-1",
            json={"status": "suspended"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "suspended"

    def test_update_entity_rejects_invalid_transition(
        self, world: InMemoryWorld, client
    ) -> None:
        world2 = _seed_world()
        world.entities = world2.entities
        # pe-2 is terminated-equivalent? suspended -> terminated is valid, so use
        # a terminated entity created inline: terminated -> active is invalid.
        from domain.entity import ProcessingEntity
        _await(world.entities.save(ProcessingEntity(id="pe-3", name="Done", status="terminated")))
        resp = client.put("/api/v3/admin/entities/pe-3", json={"status": "active"})
        assert resp.status_code == 409

    def test_get_entity_404(self, client) -> None:
        resp = client.get("/api/v3/admin/entities/does-not-exist")
        assert resp.status_code == 404
