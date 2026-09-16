"""P6-2B-1 — Consultant Review state & authorization.

Consultant Review (item-level readiness control):

  * Active member + active engagement + item at `calculated` + no open D38
    assignment → review succeeds (`consultant_reviewed`) or routes to `mapping`
    rework.
  * Self-review is ratified (P6-2B-D1).
  * Review does NOT require `can_submit` (nor any of the six flags) and never
    grants CarbonTally QC or Customer Approval authority.
  * Membership/engagement/D38/scope/state failures DENY with zero mutation.
"""
from __future__ import annotations

import asyncio
import dataclasses
import uuid

from tests.unit.api.fakes import consultant_user, member_user

PROC = "/api/v3/processing"
OPS = "/api/v3/ops"


def _seed_consultant(
    world,
    *,
    user_id="u-c1",
    firm_id="firm-c1",
    org_id="org-a",
    is_active=True,
    engagement_status="active",
    client_id="cc-1",
):
    # FIN-06 precondition: the consultant manual work under test requires the
    # organisation to have Manual Processing enabled (OFF by default).
    world.manual_processing.seed_grant("organization", org_id)
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=is_active)
    world.consultants.seed_firm_member(
        firm_id, user_id, role="manager", is_active=is_active, can_manage_clients=True
    )
    world.consultants.seed_client(
        client_id, firm_id, org_id, "Client Org", status=engagement_status
    )
    return consultant_user(user_id, f"{user_id}@example.test")


def _seed_calculated_item(world, *, org_id="org-a", item_id=None):
    return world.manual_extraction.seed_item(
        item_id or f"item-{uuid.uuid4().hex[:8]}", org_id, "invoice.pdf",
        status="calculated",
    )


def _actions(world, item_id):
    return [e.action for e in world.audit._entries if getattr(e, "entity_id", None) == item_id]


# ---------------------------------------------------------------------------
# Positive
# ---------------------------------------------------------------------------


def test_consultant_review_pass_does_not_require_can_submit(
    client, world, user_provider
) -> None:
    item = _seed_calculated_item(world)
    user = _seed_consultant(world)  # all six processing flags default False
    user_provider.set_user(user)
    assert world.consultants._members[-1].can_submit is False
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
    )
    assert response.status_code == 200, response.text
    assert response.json()["item"]["status"] == "consultant_reviewed"
    assert "consultant.review:passed" in _actions(world, item.id)


def test_consultant_self_review_allowed(client, world, user_provider) -> None:
    """P6-2B-D1 — the processing consultant may review their own item."""
    item = _seed_calculated_item(world)
    world.manual_extraction._items[item.id] = dataclasses.replace(
        world.manual_extraction._items[item.id], extracted_by="u-c1"
    )
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
    )
    assert response.status_code == 200, response.text


def test_consultant_review_rework_returns_to_mapping(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-review",
        json={"passed": False, "rejection_reason": "quantity looks wrong"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["item"]["status"] == "mapping"
    assert "consultant.review:rework" in _actions(world, item.id)


def test_review_without_reason_when_failing_is_422(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-review", json={"passed": False}
    )
    assert response.status_code == 422
    # Zero mutation.
    assert world.manual_extraction._items[item.id].status == "calculated"


# ---------------------------------------------------------------------------
# Capacity / membership / engagement negatives (zero mutation asserted)
# ---------------------------------------------------------------------------


def test_non_consultant_org_member_denied(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)
    user_provider.set_user(member_user("org-a", "user-a", "a@example.test"))
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
    )
    assert response.status_code == 403
    assert world.manual_extraction._items[item.id].status == "calculated"


def test_inactive_membership_denied(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)
    user = _seed_consultant(world, is_active=False)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
    )
    assert response.status_code == 403


def test_non_active_engagements_deny_review(client, world, user_provider) -> None:
    for status in ("pending", "rejected", "suspended", "ended", "inactive"):
        item = _seed_calculated_item(world, item_id=f"item-{status}")
        user = _seed_consultant(
            world, user_id=f"u-{status}", client_id=f"cc-{status}",
            engagement_status=status,
        )
        user_provider.set_user(user)
        response = client.post(
            f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
        )
        assert response.status_code == 403, f"{status}: {response.text}"
        assert world.manual_extraction._items[item.id].status == "calculated"


def test_cross_firm_and_cross_client_denied(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)  # org-a
    user = _seed_consultant(world, firm_id="firm-other", org_id="org-b")
    user_provider.set_user(user)
    assert (
        client.post(f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}).status_code
        == 403
    )
    item_b = _seed_calculated_item(world, org_id="org-b", item_id="item-crossb")
    user2 = _seed_consultant(world, user_id="u-c2", client_id="cc-2")
    user_provider.set_user(user2)
    assert (
        client.post(f"{PROC}/items/{item_b.id}/consultant-review", json={"passed": True}).status_code
        == 403
    )


def test_unknown_item_404(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/does-not-exist/consultant-review", json={"passed": True}
    )
    assert response.status_code == 404


def test_unauthenticated_denied(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)
    user_provider.set_unauthenticated()
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# D38 conflict
# ---------------------------------------------------------------------------


def _open_assignment(world, item_id, kind, **kw):
    asyncio.run(
        world.manual_extraction.work_item_open(
            item_id=item_id, action="assign", assignee_kind=kind,
            actor="u-mgr", actor_domain="internal_staff", **kw,
        )
    )


def test_open_internal_and_pe_assignment_deny_review(client, world, user_provider) -> None:
    for kind, kw, uid in (
        ("internal_staff", {"assigned_to": "u-op"}, "u-i1"),
        ("processing_entity", {"processing_entity_id": "entity-1"}, "u-i2"),
    ):
        item = _seed_calculated_item(world, item_id=f"item-{kind}")
        _open_assignment(world, item.id, kind, **kw)
        user = _seed_consultant(world, user_id=uid, client_id=f"cc-{uid}")
        user_provider.set_user(user)
        response = client.post(
            f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
        )
        assert response.status_code == 403, f"{kind}: {response.text}"
        assert world.manual_extraction._items[item.id].status == "calculated"


def test_batch_default_assignment_denies_review(client, world, user_provider) -> None:
    for carrier, kw in (("pe", {"entity_id": "entity-1"}), ("internal", None)):
        batch = asyncio.run(
            world.manual_extraction.create_batch("org-a", f"batch-{carrier}", **(kw or {}))
        )
        if carrier == "internal":
            asyncio.run(
                world.manual_extraction.update_batch(
                    batch.id, status="in_progress", assigned_to="u-op"
                )
            )
        item = world.manual_extraction.seed_item(
            f"item-{carrier}-{uuid.uuid4().hex[:4]}", "org-a", "f.pdf",
            status="calculated", batch_id=batch.id,
        )
        user = _seed_consultant(world, user_id=f"u-{carrier}", client_id=f"cc-{carrier}")
        user_provider.set_user(user)
        response = client.post(
            f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
        )
        assert response.status_code == 403, f"{carrier}: {response.text}"


# ---------------------------------------------------------------------------
# Workflow-state eligibility / QC / approval boundaries
# ---------------------------------------------------------------------------


def test_invalid_workflow_state_denied(client, world, user_provider) -> None:
    for status, uid in (("extracting", "u-x1"), ("mapped", "u-x2"), ("validated", "u-x3")):
        item = world.manual_extraction.seed_item(
            f"item-{uid}", "org-a", "f.pdf", status=status
        )
        user = _seed_consultant(world, user_id=uid, client_id=f"cc-{uid}")
        user_provider.set_user(user)
        response = client.post(
            f"{PROC}/items/{item.id}/consultant-review", json={"passed": True}
        )
        assert response.status_code == 409, f"{status}: {response.text}"
        assert world.manual_extraction._items[item.id].status == status


def test_already_reviewed_item_cannot_be_reviewed_again(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)
    user = _seed_consultant(world)
    user_provider.set_user(user)
    first = client.post(f"{PROC}/items/{item.id}/consultant-review", json={"passed": True})
    assert first.status_code == 200
    second = client.post(f"{PROC}/items/{item.id}/consultant-review", json={"passed": True})
    assert second.status_code == 409
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"


def test_consultant_cannot_reach_ct_qc(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert response.status_code == 403


def test_consultant_cannot_reach_customer_approval(client, world, user_provider) -> None:
    item = _seed_calculated_item(world)
    asyncio.run(world.manual_extraction.set_item_status(item.id, "customer_review"))
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "force"},
    )
    assert response.status_code == 403


