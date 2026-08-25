"""V3 QC surface (Phase 8) — the CarbonTally-staff QC gate over manual
extraction items (``/api/v3/qc/*``, admin-gated).

Covers the QC queue, stats and the item review decision (pass/fail + quality
score + notes). The ops-layer QC endpoints are covered in test_v3_operations.py.
"""
from __future__ import annotations

import asyncio

from tests.unit.api.fakes import admin_user
from tests.unit.api.route_paths import flatten_router_paths


def test_v3_qc_admin_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    for fragment in ("/api/v3/qc/queue", "/api/v3/qc/stats", "/api/v3/qc/items/{item_id}/review"):
        assert any(fragment in p for p in paths), f"missing V3 QC route: {fragment}"


def test_qc_queue_requires_admin(client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    user_provider.set_user(member_user("org-a", "user-a", "user.a@test"))
    assert client.get("/api/v3/qc/queue").status_code == 403


def test_qc_queue_and_stats(client, world, user_provider) -> None:
    _seed_extracted_item(world)
    user_provider.set_user(admin_user())
    queue = client.get("/api/v3/qc/queue")
    assert queue.status_code == 200
    assert len(queue.json()["items"]) == 1
    stats = client.get("/api/v3/qc/stats")
    assert stats.status_code == 200
    assert stats.json()["pending_qc"] == 1


def test_qc_review_item_pass(client, world, user_provider) -> None:
    item = _seed_extracted_item(world)
    user_provider.set_user(admin_user())
    response = client.post(
        f"/api/v3/qc/items/{item.id}/review",
        json={"quality_score": 90, "approved": True, "qc_notes": "verified"},
    )
    assert response.status_code == 200
    assert response.json()["status"] in ("qc_approved", "qc_rejected")
    assert response.json()["quality_score"] == 90


def test_qc_review_rejects_bad_score(client, world, user_provider) -> None:
    item = _seed_extracted_item(world)
    user_provider.set_user(admin_user())
    response = client.post(
        f"/api/v3/qc/items/{item.id}/review",
        json={"quality_score": 150, "approved": True},
    )
    assert response.status_code == 422


def _seed_extracted_item(world):
    async def _seed():
        batch = await world.manual_extraction.create_batch("org-a", "QC batch")
        item = await world.manual_extraction.create_item(
            batch.id, file_name="bill.pdf", file_url="s/bill.pdf", status="pending"
        )
        return await world.manual_extraction.set_item_status(item.id, "extracted")

    return asyncio.run(_seed())
