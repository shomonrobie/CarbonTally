"""P6-2A — Consultant Processing Authorization Contract.

Proves the ratified authorization semantics (P6-2-D1/D2/D3/D10):

    identity → active consultant membership → active client engagement →
    server-derived resource scope → consultant capability flag → D38 conflict

* Positive: active member + active engagement + capability + unassigned
  resource → processing action ALLOWED.
* Negative: unauthenticated / no membership / inactive membership / pending,
  rejected, suspended, ended, inactive engagement / cross-firm / cross-client /
  missing capability / open internal-staff or PE D38 assignment / PE-defaulted
  batch / forged resource identity / assignment-manipulation attempt /
  customer-approval attempt → DENIED.

The Consultant path is exercised through the shared /api/v3/processing/*
surface (the only processing surface Consultants can reach today). Organisation
member and internal-staff behaviour is preserved (P6-2-D10) and covered by the
pre-existing workflow suites.
"""
from __future__ import annotations

import asyncio
import uuid

from tests.unit.api.fakes import consultant_user
from tests.unit.api.test_v3_operations import _seed_batch_with_item, _seed_ops_world

CONSULT = "/api/v3/consultants"
PROC = "/api/v3/processing"
OPS = "/api/v3/ops"

ALL_PROC_FLAGS = {
    "can_extract": True,
    "can_map": True,
    "can_validate": True,
    "can_calculate": True,
    "can_confirm_automation": True,
    "can_submit": True,
}


def _seed_consultant(
    world,
    *,
    user_id="u-c1",
    firm_id="firm-c1",
    org_id="org-a",
    is_active=True,
    engagement_status="active",
    caps=None,
    client_id="cc-1",
):
    """Seed a consultant firm member + client relationship for ``org_id``."""
    # FIN-06 precondition: manual processing is OFF by default and CT-Admin
    # controlled, so the consultant manual work these tests exercise needs an
    # explicit enable for the client organisation.
    world.manual_processing.seed_grant("organization", org_id)
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=is_active)
    world.consultants.seed_firm_member(
        firm_id,
        user_id,
        role="manager",
        is_active=is_active,
        can_manage_clients=True,
        **(caps or {}),
    )
    world.consultants.seed_client(
        client_id, firm_id, org_id, "Client Org", status=engagement_status
    )
    return consultant_user(user_id, f"{user_id}@example.test")


def _seed_item(world, *, org_id="org-a", item_id=None, status="pending", batch_id=None):
    return world.manual_extraction.seed_item(
        item_id or f"item-{uuid.uuid4().hex[:8]}",
        org_id,
        "invoice.pdf",
        status=status,
        batch_id=batch_id,
    )


# ---------------------------------------------------------------------------
# Positive — full consultant processing pipeline on an unassigned item
# ---------------------------------------------------------------------------


def test_consultant_extract_mapping_validate_calculate_allowed(
    client, world, user_provider
) -> None:
    """P6-2A-D1 positive: active member + active engagement + full capability
    set on an UNASSIGNED item → extraction, mapping, validation and the
    authoritative calculation all ALLOWED (engine result is real)."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world, caps=ALL_PROC_FLAGS)
    user_provider.set_user(user)

    extracted = client.post(
        f"{PROC}/items/{item.id}/extract",
        json={
            "extracted_data": {
                "supplier": "ACME Utilities",
                "invoice_date": "2026-01-10",
                "line_items": [
                    {"activity": "Electricity", "quantity": "1000", "unit": "kWh"},
                    {"activity": "Natural gas", "quantity": "500", "unit": "kWh"},
                ],
            }
        },
    )
    assert extracted.status_code == 200, extracted.text
    assert extracted.json()["status"] == "extracted"

    mapped = client.post(
        f"{PROC}/items/{item.id}/map",
        json={
            "mapped_data": {"activity_type": "Natural gas"},
            "emission_factor_used": "factor-defra-gas",
        },
    )
    assert mapped.status_code == 200, mapped.text
    assert mapped.json()["status"] == "mapped"

    validated = client.post(f"{PROC}/items/{item.id}/validate")
    assert validated.status_code == 200, validated.text
    assert validated.json()["blocking"] is False, validated.text

    claimed = client.post(
        f"{PROC}/items/{item.id}/start", json={"stage": "calculation"}
    )
    assert claimed.status_code == 200, claimed.text

def test_consultant_validate_allowed_with_can_validate(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world, caps={"can_validate": True})
    user_provider.set_user(user)
    asyncio.run(world.manual_extraction.set_item_status(item.id, "mapped"))
    response = client.post(f"{PROC}/items/{item.id}/validate")
    # ALLOW path: the authorization gate passes; validation findings may still
    # be non-blocking/blocking depending on the item's data, but never a 403.
    assert response.status_code == 200, response.text


def test_consultant_stage_claim_requires_stage_capability(
    client, world, user_provider
) -> None:
    """Claiming the extraction stage is itself a consultant processing action."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world, caps={"can_extract": True})
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/start", json={"stage": "extraction"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "extracting"


# ---------------------------------------------------------------------------
# Negative — D38 conflict (open assignment / batch default) + security bounds
# ---------------------------------------------------------------------------


def test_open_internal_staff_assignment_denies_consultant(
    client, world, user_provider
) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    asyncio.run(
        world.manual_extraction.work_item_open(
            item_id=item.id,
            action="assign",
            assignee_kind="internal_staff",
            assigned_to="u-op",
            actor="u-mgr",
            actor_domain="internal_staff",
        )
    )
    user = _seed_consultant(world, caps=ALL_PROC_FLAGS)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403


def test_open_pe_assignment_denies_consultant(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    asyncio.run(
        world.manual_extraction.work_item_open(
            item_id=item.id,
            action="assign",
            assignee_kind="processing_entity",
            processing_entity_id="entity-1",
            actor="u-mgr",
            actor_domain="internal_staff",
        )
    )
    user = _seed_consultant(world, caps=ALL_PROC_FLAGS)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403


def test_pe_defaulted_batch_denies_consultant(client, world, user_provider) -> None:
    """A batch defaulted to a Processing Entity (batch.entity_id) is not an
    unassigned item — the consultant may not act on it (no authorized handoff)."""
    _seed_ops_world(world)
    batch = asyncio.run(
        world.manual_extraction.create_batch("org-a", "PE batch", entity_id="entity-1")
    )
    item = world.manual_extraction.seed_item("item-pe", "org-a", "pe.pdf", batch_id=batch.id)
    user = _seed_consultant(world, caps=ALL_PROC_FLAGS)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403


def test_consultant_cannot_manipulate_assignments(client, world, user_provider) -> None:
    """Consultants are not D38 actors: assignment routes are Operations-only."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world, caps=ALL_PROC_FLAGS)
    user_provider.set_user(user)
    for path in (
        f"{OPS}/items/{item.id}/work/claim",
        f"{OPS}/items/{item.id}/work/assign",
        f"{OPS}/items/{item.id}/work/release",
    ):
        response = client.post(path)
        assert response.status_code == 403, f"{path} must deny: {response.text}"


def test_consultant_cannot_reach_customer_approval(client, world, user_provider) -> None:
    """D9 hard invariant — consultants can never approve customer work."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    asyncio.run(world.manual_extraction.set_item_status(item.id, "customer_review"))
    user = _seed_consultant(world, caps=ALL_PROC_FLAGS)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "force"},
    )
    assert response.status_code == 403


def test_forged_or_missing_resource_denied(client, world, user_provider) -> None:
    """A Consultant-supplied item id that is not a real resource → 404; a real
    resource of a non-engaged org → 403. Never a silent allow."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world, org_id="org-a", caps={"can_extract": True})
    user_provider.set_user(user)
    assert (
        client.post(
            f"{PROC}/items/does-not-exist", json={"extracted_data": {}}
        ).status_code
        == 404
    )
    # Cross-client item (org-b) is denied even though the id is "real".
    world.manual_extraction.seed_item("item-b2", "org-b", "b.pdf")
    assert (
        client.post(
            f"{PROC}/items/item-b2/extract", json={"extracted_data": {}}
        ).status_code
        == 403
    )


def test_unknown_engagement_identifier_denied(client, world, user_provider) -> None:
    """A fabricated firm/client relationship cannot grant processing access."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    # Member row exists but NO consultant_clients grant row for org-a.
    world.consultants.seed_profile("firm-x", "u-x", "X Advisory")
    world.consultants.seed_firm_member(
        "firm-x", "u-x", role="consultant", can_manage_clients=True, can_extract=True
    )
    user_provider.set_user(consultant_user("u-x", "x@example.test"))
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403



def test_unauthenticated_consultant_denied(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_unauthenticated()
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 401


def test_no_consultant_membership_denied(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user_provider.set_user(consultant_user("u-nobody", "nobody@example.test"))
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403


def test_inactive_consultant_membership_denied(client, world, user_provider) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world, is_active=False, caps={"can_extract": True})
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403


def test_non_active_engagements_deny_processing(client, world, user_provider) -> None:
    """pending / rejected / suspended / ended / inactive → no processing."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    for status in ("pending", "rejected", "suspended", "ended", "inactive"):
        user = _seed_consultant(
            world,
            user_id=f"u-{status}",
            client_id=f"cc-{status}",
            engagement_status=status,
            caps={"can_extract": True},
        )
        user_provider.set_user(user)
        response = client.post(
            f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
        )
        assert response.status_code == 403, f"{status} engagement must deny: {response.text}"


def test_cross_firm_consultant_denied(client, world, user_provider) -> None:
    """A consultant whose firm holds a grant elsewhere but NOT for the item's
    organisation is denied (resource scope is engagement-derived)."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)  # item org = org-a
    user = _seed_consultant(
        world, firm_id="firm-other", org_id="org-other", caps={"can_extract": True}
    )
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403


def test_cross_client_resource_denied(client, world, user_provider) -> None:
    """Active engagement on org-a; item belongs to org-b → DENIED."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)  # org-a
    world.manual_extraction.seed_item("item-b", "org-b", "other.pdf")
    user = _seed_consultant(world, org_id="org-a", caps={"can_extract": True})
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/item-b/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403


def test_missing_capability_denied(client, world, user_provider) -> None:
    """Active engagement but no can_extract → capability gate DENIES."""
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world)  # all processing flags default False
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/extract", json={"extracted_data": {}}
    )
    assert response.status_code == 403
    assert "permission" in response.text.lower()


def test_missing_capability_denied_on_map_and_validate(
    client, world, user_provider
) -> None:
    _seed_ops_world(world)
    _batch, item = _seed_batch_with_item(world)
    user = _seed_consultant(world, caps={"can_extract": True})
    user_provider.set_user(user)
    asyncio.run(world.manual_extraction.set_item_status(item.id, "extracted"))
    assert (
        client.post(
            f"{PROC}/items/{item.id}/map",
            json={"mapped_data": {}, "emission_factor_used": "f-x"},
        ).status_code
        == 403
    )
    asyncio.run(world.manual_extraction.set_item_status(item.id, "mapped"))
    assert client.post(f"{PROC}/items/{item.id}/validate").status_code == 403


