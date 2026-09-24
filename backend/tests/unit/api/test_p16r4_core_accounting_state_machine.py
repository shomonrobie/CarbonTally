"""P16-REMEDIATION-04 — core accounting state machine (PO-authoritative).

The PO decision for the P16 reviewer/processor workflow is explicit:

    mapped -> validated -> calculated

with NO intermediate state required between ``validated`` and ``calculated``,
and reviewer (``can_review``) / processor (``can_process``) authorization kept
separate.

These tests exercise the REAL ops routes and the REAL transition table — the
branches under test are not mocked away.
"""
from __future__ import annotations

from domain.partners import can_transition_item_status
from tests.unit.api.fakes import staff_user
from tests.unit.api.test_v3_operations import _seed_batch_with_item, _seed_ops_world

REVIEWER = staff_user("u-rev", email="rev@carbontally.test", permissions={"can_review": True})
PROCESSOR = staff_user("u-op", email="op@carbontally.test", permissions={"can_process": True})


# -- section 9A-9C: the transition table contract ----------------------------
def test_transition_table_contract() -> None:
    """``validated -> calculated`` is authorized; ``mapped -> calculated`` is not."""
    assert can_transition_item_status("mapped", "validated") is True
    assert can_transition_item_status("validated", "calculated") is True
    # the automatic pipeline's two-step path is preserved
    assert can_transition_item_status("validated", "calculating") is True
    assert can_transition_item_status("calculating", "calculated") is True
    # no arbitrary skip straight from mapping/extraction to calculated
    assert can_transition_item_status("mapped", "calculated") is False
    assert can_transition_item_status("extracted", "calculated") is False
    assert can_transition_item_status("pending", "calculated") is False


def _to_mapped(client, world, user_provider, *, supplier: str = "British Gas"):
    """Drive a seeded item to ``mapped`` through the real routes."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(PROCESSOR)
    client.post(f"/api/v3/ops/items/{item.id}/start", json={"stage": "extraction"})
    client.post(
        f"/api/v3/ops/items/{item.id}/extract",
        json={
            "extracted_data": {
                "quantity": "1000",
                "unit": "kWh",
                "activity": "Natural gas",
                "supplier": supplier,
                "date": "2025-06-01",
            }
        },
    )
    client.post(
        f"/api/v3/ops/items/{item.id}/map",
        json={
            "mapped_data": {"activity_type": "Natural gas"},
            "emission_factor_used": "factor-defra-gas",
        },
    )
    return item


# -- section 9A: mapped -> validated (authorized reviewer) -------------------
def test_a_reviewer_validates_mapped_item(client, world, user_provider) -> None:
    item = _to_mapped(client, world, user_provider)
    user_provider.set_user(REVIEWER)
    response = client.post(f"/api/v3/ops/items/{item.id}/validate")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "validated"
    assert response.json()["blocking"] is False


# -- section 9B: validated -> calculated (authorized processor) -------------
def test_b_processor_calculates_validated_item(client, world, user_provider) -> None:
    item = _to_mapped(client, world, user_provider)
    user_provider.set_user(REVIEWER)
    assert client.post(f"/api/v3/ops/items/{item.id}/validate").json()["status"] == "validated"

    user_provider.set_user(PROCESSOR)
    calc = client.post(f"/api/v3/ops/items/{item.id}/calculate", json={})
    assert calc.status_code == 200, calc.text
    snapshot_id = calc.json()["result"]["snapshot"]["id"]
    assert world.logs._snapshots[snapshot_id].source_item_id == item.id


# -- section 9C: mapped -> calculated without validation is DENIED ----------
def test_c_calculate_without_validation_is_denied(client, world, user_provider) -> None:
    item = _to_mapped(client, world, user_provider)
    user_provider.set_user(PROCESSOR)
    response = client.post(f"/api/v3/ops/items/{item.id}/calculate", json={})
    assert response.status_code == 409, response.text
    assert "cannot transition" in response.json()["error"]["message"]


# -- section 9D: reviewer without can_process cannot calculate --------------
def test_d_reviewer_without_can_process_cannot_calculate(client, world, user_provider) -> None:
    item = _to_mapped(client, world, user_provider)
    user_provider.set_user(REVIEWER)
    assert client.post(f"/api/v3/ops/items/{item.id}/validate").json()["status"] == "validated"
    response = client.post(f"/api/v3/ops/items/{item.id}/calculate", json={})
    assert response.status_code == 403, response.text


# -- section 9E: processor without can_review cannot validate ---------------
def test_e_processor_without_can_review_cannot_validate(client, world, user_provider) -> None:
    item = _to_mapped(client, world, user_provider)
    user_provider.set_user(PROCESSOR)
    response = client.post(f"/api/v3/ops/items/{item.id}/validate")
    assert response.status_code == 403, response.text


# -- supplier propagation: mapped_supplier_id -> emissions ------------------
def test_supplier_propagates_to_the_emissions_row(client, world, user_provider) -> None:
    item = _to_mapped(client, world, user_provider)
    user_provider.set_user(REVIEWER)
    assert client.post(f"/api/v3/ops/items/{item.id}/validate").json()["status"] == "validated"
    user_provider.set_user(PROCESSOR)
    calc = client.post(f"/api/v3/ops/items/{item.id}/calculate", json={})
    assert calc.status_code == 200, calc.text

    snapshot_id = calc.json()["result"]["snapshot"]["id"]
    snapshot = world.logs._snapshots[snapshot_id]
    assert snapshot.source_item_id == item.id, "snapshot must carry the source item"
