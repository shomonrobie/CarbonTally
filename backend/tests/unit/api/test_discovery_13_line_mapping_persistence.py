"""CT-CARBONTALLY-EMISSION-FACTOR-MAPPING-AND-PERSISTENCE-DISCOVERY-13 — P0.

Regression coverage for the multi-line mapping *write* contract.

Before this fix the mapping guard accepted only a **document-level** factor
(``emission_factor_used`` or ``mapped_data.factor_id``). The D23 multi-line
picker submits one factor per extracted line
(``mapped_data.line_items[].factor_id``), so a complete per-line selection
satisfied nothing and **every** multi-line save was rejected ``422`` before any
persistence was attempted — the item stayed ``status='extracted'`` with an empty
``mapped_data``.

These tests pin the corrected contract:

* a **complete** per-line factor set is accepted and persisted (T-1);
* a request selecting **no** factor anywhere is still refused ``422`` (T-2);
* an **invalid or inapplicable** per-line factor id is refused ``422`` (T-3) —
  widening the accepted shape must widen the validation with it, because
  ``mapped_data`` is persisted customer-visible provenance;
* the pre-existing **document-level** contract is unchanged (T-4).

The line ``activity``/``unit`` used for validation come from the **persisted**
extraction, never from the request, so a client cannot make an inapplicable
factor look applicable by echoing a different unit.
"""

from __future__ import annotations

import asyncio

from tests.unit.api.fakes import InMemoryWorld, member_user, seed_factor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

#: Printed invoice lines mirroring the reported document
#: (``border_double_fuel.pdf`` — diesel, litres).
DIESEL_UNIT = "litres"


def _seed_diesel_factors(world: InMemoryWorld, *factor_ids: str) -> None:
    """Seed one system diesel factor per supplied id (DEFRA-2025, GB, litres)."""
    for index, factor_id in enumerate(factor_ids):
        world.factors.add(
            seed_factor(
                factor_id=factor_id,
                year=2025,
                activity_type=f"Diesel supply variant {index + 1}",
                multiplier=f"2.{index}1",
                unit=DIESEL_UNIT,
                scope="Scope 1",
                factor_source="DEFRA-DESNZ",
                factor_set="DEFRA-2025",
                country="GB",
                provider_key="defra",
                import_batch_id="batch-defra-2025",
            )
        )


def _seed_kwh_gas_factor(world: InMemoryWorld, *, activity_type: str) -> None:
    """Seed a kWh factor — a valid system factor for a *different* activity/unit."""
    world.factors.add(
        seed_factor(
            factor_id="f-gas-kwh",
            year=2025,
            activity_type=activity_type,
            multiplier="0.183",
            unit="kWh",
            scope="Scope 1",
            factor_source="DEFRA-DESNZ",
            factor_set="DEFRA-2025",
            country="GB",
            provider_key="defra",
            import_batch_id="batch-defra-2025",
        )
    )


def _enable_manual_processing(world: InMemoryWorld) -> None:
    """FIN-06 precondition: manual processing is OFF for an organisation by default.

    The customer mapping route enforces it (``enforce_manual_processing=True``), so
    the manual pipeline is only reachable once the organisation holds BOTH the
    governance grant and the subscription entitlement (two separate gates, PO
    decision). Every test here is about the *mapping* contract, so the enable is
    expressed once, here, rather than repeated per assertion.
    """
    world.manual_processing.seed_grant("organization", "org-a")
    world.manual_processing.seed_entitlement("org-a")


def _seed_batch_with_item(world: InMemoryWorld):
    _enable_manual_processing(world)

    async def _seed():
        batch = await world.manual_extraction.create_batch(
            "org-a", "DISCOVERY-13 batch"
        )
        item = await world.manual_extraction.create_item(
            batch.id,
            file_name="border_double_fuel.pdf",
            file_url="storage/docs/border_double_fuel.pdf",
            document_type="invoice",
            status="pending",
        )
        return batch, item

    return asyncio.run(_seed())


def _seed_extracted(world: InMemoryWorld, item_id: str, data: dict) -> None:
    asyncio.run(world.manual_extraction.save_extracted_data(item_id, data, "member-1"))


def _extracted_three_diesel_lines() -> dict:
    """The reported document: three diesel lines, invoice dated 2025-10-04."""
    return {
        "supplier": "Pure Resources Group",
        "invoice_number": "INV-20279073",
        "date": "2025-10-04",
        "line_items": [
            {"activity": "Diesel supply", "quantity": 2200, "unit": DIESEL_UNIT},
            {"activity": "Diesel supply", "quantity": 1500, "unit": DIESEL_UNIT},
            {"activity": "Diesel supply", "quantity": 3400, "unit": DIESEL_UNIT},
        ],
    }


def _as_member(user_provider) -> None:
    user_provider.set_user(member_user("org-a", "member-1", "m@test"))


def _post_map(client, item_id: str, payload: dict):
    return client.post(f"/api/v3/processing/items/{item_id}/map", json=payload)


def _error_message(response) -> str:
    """The platform error envelope is ``{"error": {"code", "message", ...}}``."""
    body = response.json()
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        return str(body["error"].get("message", ""))
    return str(body.get("detail", "")) if isinstance(body, dict) else ""


def _stored(world: InMemoryWorld, item_id: str):
    """The persisted record behind the write (the in-memory write mirror)."""
    return world.manual_extraction._items[item_id]


def _three_line_payload(factor_ids) -> dict:
    """The shape ``onSaveMapping`` submits: one factor per extracted line."""
    return {
        "mapped_data": {
            "line_items": [
                {
                    "factor_id": factor_id,
                    "activity_type": "Diesel supply",
                    "unit": DIESEL_UNIT,
                }
                for factor_id in factor_ids
            ]
        }
    }


# ---------------------------------------------------------------------------
# T-1 — a complete per-line factor set is accepted and persisted
# ---------------------------------------------------------------------------


class TestCompleteLineFactorSetIsAccepted:
    def test_multi_line_mapping_persists_and_reaches_mapped(
        self, world, client, user_provider
    ) -> None:
        """T-1 — the exact shape ``onSaveMapping`` submits must succeed.

        This is the test that fails on the pre-fix guard with ``422``
        "an emission factor must be selected".
        """
        _seed_diesel_factors(world, "f-diesel-1", "f-diesel-2", "f-diesel-3")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, _extracted_three_diesel_lines())
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            _three_line_payload(["f-diesel-1", "f-diesel-2", "f-diesel-3"]),
        )

        assert resp.status_code == 200, resp.text
        stored = _stored(world, item.id)
        assert stored.status == "mapped"
        assert [entry["factor_id"] for entry in stored.mapped_data["line_items"]] == [
            "f-diesel-1",
            "f-diesel-2",
            "f-diesel-3",
        ]

    def test_multi_line_mapping_round_trips_the_selected_factor_ids(
        self, world, client, user_provider
    ) -> None:
        """T-1 (persistence) — the selected ids survive the write and read back."""
        _seed_diesel_factors(world, "f-diesel-1", "f-diesel-2", "f-diesel-3")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, _extracted_three_diesel_lines())
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            _three_line_payload(["f-diesel-1", "f-diesel-2", "f-diesel-3"]),
        )
        assert resp.status_code == 200, resp.text

        # Read back through the API the customer workspace actually renders.
        workspace = client.get(f"/api/v3/processing/items/{item.id}/workspace")
        assert workspace.status_code == 200, workspace.text
        body = workspace.json()
        assert body["status"]["status"] == "mapped"
        mapped_ids = [
            entry["factor_id"]
            for entry in (body["data"]["mapped_data"] or {}).get("line_items", [])
        ]
        assert mapped_ids == ["f-diesel-1", "f-diesel-2", "f-diesel-3"]

    def test_single_line_document_may_use_the_per_line_shape(
        self, world, client, user_provider
    ) -> None:
        """A one-line document submitted in the per-line shape is also accepted."""
        _seed_diesel_factors(world, "f-diesel-1")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(
            world,
            item.id,
            {
                "supplier": "Pure Resources Group",
                "date": "2025-10-04",
                "line_items": [
                    {"activity": "Diesel supply", "quantity": 2200, "unit": DIESEL_UNIT}
                ],
            },
        )
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            {"mapped_data": {"line_items": [{"factor_id": "f-diesel-1"}]}},
        )
        assert resp.status_code == 200, resp.text
        assert _stored(world, item.id).status == "mapped"


# ---------------------------------------------------------------------------
# T-2 — no factor selected anywhere is still refused
# ---------------------------------------------------------------------------


class TestNoFactorSelectedIsStillRefused:
    def test_empty_mapped_data_is_422(self, world, client, user_provider) -> None:
        """T-2 — a bare save with no factor is not a mapping decision."""
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, _extracted_three_diesel_lines())
        _as_member(user_provider)

        resp = _post_map(client, item.id, {"mapped_data": {}})

        assert resp.status_code == 422, resp.text
        assert "emission factor" in _error_message(resp)
        assert _stored(world, item.id).status == "extracted"

    def test_partial_line_selection_is_422(self, world, client, user_provider) -> None:
        """T-2 — an incomplete per-line set fails closed (never a silent partial save)."""
        _seed_diesel_factors(world, "f-diesel-1", "f-diesel-2")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, _extracted_three_diesel_lines())
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            {
                "mapped_data": {
                    "line_items": [
                        {"factor_id": "f-diesel-1"},
                        {"factor_id": None},
                        {"factor_id": "f-diesel-2"},
                    ]
                }
            },
        )

        assert resp.status_code == 422, resp.text
        assert _stored(world, item.id).status == "extracted"

    def test_blank_factor_id_is_422(self, world, client, user_provider) -> None:
        """T-2 — an empty-string selection is not a selection."""
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, _extracted_three_diesel_lines())
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            {
                "mapped_data": {
                    "line_items": [
                        {"factor_id": ""},
                        {"factor_id": ""},
                        {"factor_id": ""},
                    ]
                }
            },
        )
        assert resp.status_code == 422, resp.text

    def test_line_count_mismatch_is_422(self, world, client, user_provider) -> None:
        """T-2 — a per-line mapping must cover every extracted line."""
        _seed_diesel_factors(world, "f-diesel-1")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, _extracted_three_diesel_lines())
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            {"mapped_data": {"line_items": [{"factor_id": "f-diesel-1"}]}},
        )

        assert resp.status_code == 422, resp.text
        assert "line" in _error_message(resp)


# ---------------------------------------------------------------------------
# T-3 — invalid / inapplicable per-line factor ids are refused
# ---------------------------------------------------------------------------


class TestPerLineFactorValidation:
    def test_unknown_factor_id_is_422(self, world, client, user_provider) -> None:
        """T-3 — an arbitrary string is never accepted into ``mapped_data``."""
        _seed_diesel_factors(world, "f-diesel-1", "f-diesel-2", "f-diesel-3")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, _extracted_three_diesel_lines())
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            _three_line_payload(["f-diesel-1", "not-a-real-factor", "f-diesel-3"]),
        )

        assert resp.status_code == 422, resp.text
        assert "not-a-real-factor" in _error_message(resp)
        assert _stored(world, item.id).status == "extracted"

    def test_factor_inapplicable_to_the_line_is_422(
        self, world, client, user_provider
    ) -> None:
        """T-3 — an existing factor for a different activity is not applicable.

        The gas factor exists and is a valid system factor, but it is not a
        candidate for a *diesel/litres* line, so it must be refused. This is the
        check that stops the widening from becoming an unvalidated write path.
        """
        _seed_diesel_factors(world, "f-diesel-1")
        _seed_kwh_gas_factor(world, activity_type="Natural gas")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(world, item.id, _extracted_three_diesel_lines())
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            _three_line_payload(["f-diesel-1", "f-gas-kwh", "f-diesel-1"]),
        )

        assert resp.status_code == 422, resp.text
        assert "f-gas-kwh" in _error_message(resp)

    def test_unit_is_validated_from_the_persisted_line_not_the_request(
        self, world, client, user_provider
    ) -> None:
        """T-3 — echoing a different unit in the request cannot legitimise a factor.

        The persisted line is ``litres``; the request claims ``kWh``. The
        kWh-only factor must still be refused, because applicability is judged
        against the persisted extraction, not client-supplied text — and the
        refusal names the *persisted* unit.
        """
        _seed_kwh_gas_factor(world, activity_type="Diesel supply")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(
            world,
            item.id,
            {
                "date": "2025-10-04",
                "line_items": [
                    {"activity": "Diesel supply", "quantity": 2200, "unit": "litres"}
                ],
            },
        )
        _as_member(user_provider)

        resp = _post_map(
            client,
            item.id,
            {
                "mapped_data": {
                    "line_items": [
                        {
                            "factor_id": "f-gas-kwh",
                            "activity_type": "Diesel supply",
                            "unit": "kWh",  # a lie: the persisted line is litres
                        }
                    ]
                }
            },
        )

        assert resp.status_code == 422, resp.text
        message = _error_message(resp)
        assert "litres" in message
        assert "kWh" not in message


# ---------------------------------------------------------------------------
# T-4 — the pre-existing document-level contract is unchanged
# ---------------------------------------------------------------------------


class TestDocumentLevelContractUnchanged:
    def test_document_level_factor_is_still_accepted(
        self, world, client, user_provider
    ) -> None:
        """T-4 — single-line documents may still map at the document level."""
        _seed_diesel_factors(world, "f-diesel-1")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(
            world,
            item.id,
            {"activity": "Diesel supply", "quantity": 2200, "unit": DIESEL_UNIT},
        )
        _as_member(user_provider)

        resp = _post_map(client, item.id, {"emission_factor_used": "f-diesel-1"})

        assert resp.status_code == 200, resp.text
        assert _stored(world, item.id).status == "mapped"

    def test_mapped_data_factor_id_is_still_accepted(
        self, world, client, user_provider
    ) -> None:
        """T-4 — the ``mapped_data.factor_id`` spelling keeps working."""
        _seed_diesel_factors(world, "f-diesel-1")
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(
            world,
            item.id,
            {"activity": "Diesel supply", "quantity": 2200, "unit": DIESEL_UNIT},
        )
        _as_member(user_provider)

        resp = _post_map(client, item.id, {"mapped_data": {"factor_id": "f-diesel-1"}})

        assert resp.status_code == 200, resp.text
        assert _stored(world, item.id).status == "mapped"

    def test_document_level_guard_still_refuses_a_blank_factor(
        self, world, client, user_provider
    ) -> None:
        """T-4 — the original refusal is unchanged for a blank document factor."""
        _batch, item = _seed_batch_with_item(world)
        _seed_extracted(
            world,
            item.id,
            {"activity": "Diesel supply", "quantity": 2200, "unit": DIESEL_UNIT},
        )
        _as_member(user_provider)

        resp = _post_map(client, item.id, {"emission_factor_used": "   "})

        assert resp.status_code == 422, resp.text
        assert "emission factor" in _error_message(resp)


# ---------------------------------------------------------------------------
# Guard helpers (unit level — the predicates themselves)
# ---------------------------------------------------------------------------


class TestSelectionPredicates:
    def test_complete_line_factor_set_requires_every_entry(self) -> None:
        from api.v3_processing_workflow import _complete_line_factor_set

        assert _complete_line_factor_set({}) is None
        assert _complete_line_factor_set({"line_items": []}) is None
        assert _complete_line_factor_set({"line_items": "not-a-list"}) is None
        assert _complete_line_factor_set({"line_items": [{"factor_id": None}]}) is None
        assert _complete_line_factor_set({"line_items": [{"factor_id": "  "}]}) is None
        assert (
            _complete_line_factor_set(
                {"line_items": [{"factor_id": "a"}, {"factor_id": None}]}
            )
            is None
        )
        # complete
        complete = [{"factor_id": "a"}, {"factor_id": "b"}]
        assert _complete_line_factor_set({"line_items": complete}) == complete

    def test_document_level_predicate(self) -> None:
        from api.v3_processing_workflow import (
            MapPayload,
            _complete_line_factor_set,
            _document_level_factor_selected,
        )

        assert not _document_level_factor_selected(MapPayload())
        assert not _document_level_factor_selected(
            MapPayload(emission_factor_used="  ")
        )
        assert not _document_level_factor_selected(
            MapPayload(mapped_data={"factor_id": None})
        )
        assert _document_level_factor_selected(MapPayload(emission_factor_used="f-1"))
        assert _document_level_factor_selected(
            MapPayload(mapped_data={"factor_id": "f-1"})
        )

        # The regression this fix addresses: a per-line-only payload satisfies
        # NEITHER document-level spelling, so the pre-fix guard refused it 422
        # even though the picker had supplied a complete, valid selection.
        line_only = MapPayload(
            mapped_data={"line_items": [{"factor_id": "a"}, {"factor_id": "b"}]}
        )
        assert not _document_level_factor_selected(line_only)
        assert _complete_line_factor_set(line_only.mapped_data) is not None
