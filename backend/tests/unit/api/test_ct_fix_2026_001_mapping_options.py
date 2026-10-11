"""CARBONTALLY-FIX-2026-001 — mapping-options wiring (GAP-2 / GAP-3).

Regression coverage for the two *additive* backend fixes in this batch:

* **GAP-3** — the supplier-resolution engine (``engines/supplier_resolution.py``,
  P12-IMPL-02) is actually invoked by
  ``GET /api/v3/processing/items/{id}/mapping-options`` and its verdict reaches
  the response. The engine stays org-scoped: org A can never be resolved to
  org B's supplier, and a blank extraction is ``unresolved`` rather than a guess.
* **GAP-2 / B4a** — the response carries ``line_mapping_options`` (one entry per
  extracted line, each with that line's own activity/unit, candidates, reason and
  spend guidance) plus the ``reporting_year`` those candidates were looked up for.

Nothing here writes: mapping-options is a read surface.
"""
from __future__ import annotations

import asyncio
import json

from tests.unit.api.fakes import InMemoryWorld, member_user


def _seed_batch_with_item(world: InMemoryWorld):
    async def _seed():
        batch = await world.manual_extraction.create_batch("org-a", "FIX-2026-001 batch")
        item = await world.manual_extraction.create_item(
            batch.id,
            file_name="diesel-invoice-2025.pdf",
            file_url="storage/docs/diesel-invoice-2025.pdf",
            document_type="invoice",
            status="pending",
        )
        return batch, item

    return asyncio.run(_seed())


def _seed_extracted(world: InMemoryWorld, item_id: str, data: dict) -> None:
    asyncio.run(world.manual_extraction.save_extracted_data(item_id, data, "member-1"))


def _supplier(supplier_id: str, org_id: str, name: str, postcode: str = "") -> dict:
    return {
        "id": supplier_id,
        "organization_id": org_id,
        "name": name,
        "is_active": True,
        "metadata": {"postcode": postcode} if postcode else {},
    }


class TestSupplierResolutionWiring:
    def test_blank_supplier_is_unresolved_and_never_invented(
        self, world, client, user_provider
    ) -> None:
        """No extracted supplier -> ``unresolved`` + manual review (never a guess)."""
        world.suppliers.seed(_supplier("sup-a", "org-a", "Robinsons Recycling Services Ltd"))
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, {"activity": "Diesel", "unit": "litres"})
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))

        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        resolution = resp.json()["supplier_resolution"]
        assert resolution["verdict"] == "unresolved"
        assert resolution["action"] == "manual_review"
        assert resolution["selected_supplier_id"] is None
        assert resolution["auto_persist"] is False

    def test_exact_supplier_name_plus_postcode_is_resolved_and_auto_persistable(
        self, world, client, user_provider
    ) -> None:
        """The engine's verdict now reaches the API response (GAP-3)."""
        world.suppliers.seed(
            _supplier("sup-a", "org-a", "Robinsons Recycling Services Ltd", "QI14 5ZD")
        )
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(
            world,
            item.id,
            {
                "supplier": "Robinsons Recycling Services Ltd",
                "supplier_postcode": "QI14 5ZD",
                "date": "2025-04-02",
                "activity": "Diesel",
                "unit": "litres",
            },
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))

        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        resolution = resp.json()["supplier_resolution"]
        assert resolution["verdict"] == "exact"
        assert resolution["action"] == "reuse"
        assert resolution["selected_supplier_id"] == "sup-a"
        assert resolution["auto_persist"] is True

    def test_another_organisations_supplier_is_never_resolved(
        self, world, client, user_provider
    ) -> None:
        """Tenant isolation: org A's item can never resolve to org B's supplier."""
        world.suppliers.seed(
            _supplier("sup-orgb", "org-b", "Robinsons Recycling Services Ltd", "QI14 5ZD")
        )
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(
            world,
            item.id,
            {
                "supplier": "Robinsons Recycling Services Ltd",
                "supplier_postcode": "QI14 5ZD",
                "activity": "Diesel",
                "unit": "litres",
            },
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))

        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        resolution = resp.json()["supplier_resolution"]
        # No org-a candidate exists, so creation must be confirmed — org-b's
        # supplier is not even offered, let alone selected.
        assert resolution["verdict"] == "none"
        assert resolution["action"] == "confirm_creation"
        assert resolution["selected_supplier_id"] is None
        assert "sup-orgb" not in json.dumps(resolution)


class TestPerLineMappingOptions:
    def test_line_mapping_options_are_per_line_and_carry_reporting_year(
        self, world, client, user_provider
    ) -> None:
        """GAP-2 / B4a — one candidate block per extracted line, not one per doc."""
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(
            world,
            item.id,
            {
                "supplier": "Robinsons Recycling Services Ltd",
                "date": "2025-04-02",
                "line_items": [
                    {"activity": "Diesel", "unit": "litres", "quantity": "2200"},
                    {"activity": "Purchased goods", "unit": "GBP", "quantity": "12500"},
                ],
            },
        )
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))

        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        body = resp.json()

        options = body["line_mapping_options"]
        assert [o["line_number"] for o in options] == [1, 2]
        assert [o["activity"] for o in options] == ["Diesel", "Purchased goods"]
        assert [o["unit"] for o in options] == ["litres", "GBP"]
        for option in options:
            assert set(option) >= {
                "factors",
                "customer_factors",
                "no_factors_reason",
                "spend_suggestion",
            }
        # The currency line is a spend dead-end and says so per line (CL-47).
        assert options[1]["spend_suggestion"] is not None
        assert options[1]["spend_suggestion"]["kind"] == "spend_based"
        # The year the per-line candidates were looked up for is echoed back.
        assert body["reporting_year"] == 2025

    def test_no_line_items_yields_an_empty_per_line_list(
        self, world, client, user_provider
    ) -> None:
        """Single-activity documents keep the document-level contract intact."""
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, {"activity": "Diesel", "unit": "litres"})
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))

        resp = client.get(f"/api/v3/processing/items/{item.id}/mapping-options")
        assert resp.status_code == 200
        body = resp.json()
        assert body["line_mapping_options"] == []
        assert body["reporting_year"] is None
        # The pre-existing document-level fields are unchanged.
        assert "factors" in body and "no_factors_reason" in body
