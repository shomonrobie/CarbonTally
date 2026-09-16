"""P6-2B-3 — CarbonTally QC decision boundary for Consultant-submitted work.

Proves the EXISTING CarbonTally QC machinery correctly handles items that a
Consultant submitted (`consultant_reviewed → reviewed`):

  * Internal ``can_qc`` staff may approve/reject `reviewed` items
    (`ct_qc_approved` / `ct_qc_rejected`) — the intake works for Consultant-
    submitted items with no Consultant-specific QC system.
  * Consultants / PE staff / non-QC internal staff / customers can NEVER make a
    CT-QC decision; CT-QC approval is not Customer Approval.
  * `ct_qc_approved` proceeds only through the org Owner/Admin customer-review
    surface; `ct_qc_rejected` routes only through the existing rework states
    (`mapping`/`extracting`) and can never reach Customer Review/Approval.
  * No billing charge occurs at CT-QC; the charge remains at Customer Approval.
  * Unauthorized/invalid/duplicate decisions produce zero mutation and no
    success audit.
"""
from __future__ import annotations

import asyncio
import uuid

from datetime import datetime, timezone

from domain.billing import BillingPlan, Subscription
from domain.partners import ITEM_STATUS_FLOW, can_transition_item_status
from domain.staff import StaffProfile, StaffRole
from services.billing import BillingService
from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    org_owner_user,
    staff_user,
)

PROC = "/api/v3/processing"
OPS = "/api/v3/ops"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_role(world, *, role_id="role-qc", name="qc_specialist", perms=None) -> None:
    world.staff.seed_role(
        StaffRole(
            id=role_id,
            name=name,
            permissions=perms if perms is not None else {"can_qc": True},
        )
    )


def _seed_staff(world, *, user_id: str, role_id: str, entity_id=None) -> None:
    world.staff.seed_profile(
        StaffProfile(
            id=f"sp-{user_id}",
            user_id=user_id,
            first_name=user_id,
            last_name="One",
            email=f"{user_id}@test",
            role_id=role_id,
            entity_id=entity_id,
        )
    )


def _seed_commercial(world, org="org-a", *, key="sub-p62b3") -> None:
    """Active professional subscription + 500 CREDIT-mode credits (org-scoped)."""
    asyncio.run(
        world.billing_plans.create(
            BillingPlan(
                id=str(uuid.uuid4()),
                plan_code="professional",
                name="Professional",
                price=149,
                currency="GBP",
                included_credits=500,
                version=1,
                is_active=True,
                features={},
                effective_from=datetime.now(timezone.utc),
            ),
            created_by="admin-1",
        )
    )
    asyncio.run(
        world.billing_subscriptions.upsert_active(
            Subscription(
                id=str(uuid.uuid4()),
                organization_id=org,
                plan_code="professional",
                plan_version=1,
                billing_mode="CREDIT",
                lifecycle_status="active",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc),
                idempotency_key=key,
            ),
            created_by="admin-1",
        )
    )
    asyncio.run(
        BillingService(world.bundle()).grant_credits(
            org,
            500,
            source="plan_included",
            reason="monthly",
            idempotency_key=f"{key}-grant",
        )
    )

def _seed_consultant_submission(client, world, user_provider):
    """Consultant submits a `consultant_reviewed` item -> `reviewed` (P6-2B-2)."""
    # FIN-06 precondition: manual processing must be enabled for the client org.
    world.manual_processing.seed_grant("organization", "org-a")
    world.consultants.seed_profile("firm-c1", "u-c1", "C1 Advisory", is_active=True)
    world.consultants.seed_firm_member(
        "firm-c1", "u-c1", role="manager", is_active=True,
        can_manage_clients=True, can_submit=True,
    )
    world.consultants.seed_client(
        "cc-1", "firm-c1", "org-a", "Client Org", status="active"
    )
    item = world.manual_extraction.seed_item(
        f"item-{uuid.uuid4().hex[:8]}", "org-a", "invoice.pdf",
        status="consultant_reviewed",
    )
    _seed_commercial(world)
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    resp = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "reviewed"
    return item


def _seed_internal_review(client, world, user_provider):
    """Internal `can_review` staff submits a `calculated` item -> `reviewed`."""
    _seed_role(world, role_id="role-rev", name="reviewer",
               perms={"can_review": True})
    _seed_staff(world, user_id="u-rev", role_id="role-rev")
    item = world.manual_extraction.seed_item(
        f"item-{uuid.uuid4().hex[:8]}", "org-a", "internal.pdf", status="calculated"
    )
    user_provider.set_user(staff_user("u-rev"))
    resp = client.post(f"{OPS}/items/{item.id}/submit-review")
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "reviewed"
    return item


def _qc_decision(client, world, user_provider, item_id, *, approved=True,
                 qc_user="u-qc", score=90, notes="verified"):
    _seed_role(world)  # qc_specialist role with can_qc (idempotent seed)
    _seed_staff(world, user_id=qc_user, role_id="role-qc")
    user_provider.set_user(staff_user(qc_user))
    return client.post(
        f"{OPS}/qc/items/{item_id}/decision",
        json={"quality_score": score, "approved": approved, "qc_notes": notes},
    )


def _actions(world, item_id) -> list[str]:
    return [
        e.action for e in world.audit._entries
        if getattr(e, "entity_id", None) == item_id
    ]


def _ledger(world, org="org-a") -> int:
    return asyncio.run(world.billing_ledger.balance(org))


# ---------------------------------------------------------------------------
# Intake + authorized CT-QC decision (internal can_qc)
# ---------------------------------------------------------------------------


def test_consultant_submitted_item_appears_in_ct_qc_intake_queue(
    client, world, user_provider
) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    # Matrix 21 — a Consultant-submitted `reviewed` item is in the EXISTING
    # CT-QC pending queue.
    _seed_role(world)
    _seed_staff(world, user_id="u-qc", role_id="role-qc")
    user_provider.set_user(staff_user("u-qc"))
    resp = client.get(f"{OPS}/qc/ct-queue")
    assert resp.status_code == 200, resp.text
    ids = [row["id"] for row in resp.json()["items"]]
    assert item.id in ids


def test_can_qc_staff_approves_consultant_submitted_item(
    client, world, user_provider
) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    # No billing mutation through submission OR the QC decision.
    assert _ledger(world) == 500
    resp = _qc_decision(client, world, user_provider, item.id, approved=True)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "ct_qc_approved"
    stored = world.manual_extraction._items[item.id]
    assert stored.status == "ct_qc_approved"
    assert stored.quality_score == 90
    assert stored.qc_by == "u-qc"
    assert _ledger(world) == 500  # CT-QC never charges
    assert "ct_qc:approved" in _actions(world, item.id)


def test_can_qc_staff_rejects_consultant_submitted_item(
    client, world, user_provider
) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    resp = _qc_decision(client, world, user_provider, item.id, approved=False,
                        notes="quantity mismatch")
    assert resp.status_code == 200, resp.text
    stored = world.manual_extraction._items[item.id]
    assert stored.status == "ct_qc_rejected"
    assert stored.qc_notes == "quantity mismatch"
    assert _ledger(world) == 500
    assert "ct_qc:rejected" in _actions(world, item.id)


def test_audit_actor_and_before_after_state(
    client, world, user_provider
) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    resp = _qc_decision(client, world, user_provider, item.id, approved=True,
                        qc_user="u-qc2")
    assert resp.status_code == 200, resp.text
    entry = next(
        e for e in world.audit._entries
        if getattr(e, "entity_id", None) == item.id and e.action == "ct_qc:approved"
    )
    assert entry.actor == "u-qc2"
    assert entry.changed_fields.get("status_from") == "reviewed"
    assert entry.changed_fields.get("status_to") == "ct_qc_approved"
    assert entry.changed_fields.get("quality_score") == 90


def test_internal_submitted_reviewed_item_still_qc_decidable(
    client, world, user_provider
) -> None:
    """Existing Internal path preserved: ops `reviewed` items stay QC-decidable."""
    item = _seed_internal_review(client, world, user_provider)
    resp = _qc_decision(client, world, user_provider, item.id, approved=True)
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "ct_qc_approved"


# ---------------------------------------------------------------------------
# Authorization negatives — no one but internal can_qc may decide
# ---------------------------------------------------------------------------


def test_internal_staff_without_can_qc_denied_zero_mutation(
    client, world, user_provider
) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    _seed_role(world, role_id="role-op", name="operator",
               perms={"can_process": True})
    _seed_staff(world, user_id="u-op", role_id="role-op")
    user_provider.set_user(staff_user("u-op"))
    resp = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "reviewed"
    assert "ct_qc:approved" not in _actions(world, item.id)
    assert _ledger(world) == 500


def test_consultant_cannot_make_ct_qc_decision(client, world, user_provider) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    resp = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "reviewed"


def test_pe_staff_cannot_make_ct_qc_decision(client, world, user_provider) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    _seed_role(world)
    _seed_staff(world, user_id="u-pe", role_id="role-qc", entity_id="entity-1")
    user_provider.set_user(staff_user("u-pe", entity_id="entity-1"))
    resp = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "reviewed"


def test_customer_member_cannot_make_ct_qc_decision(
    client, world, user_provider
) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    user_provider.set_user(member_user("org-a", "member-1", "member@test"))
    resp = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "reviewed"

# ---------------------------------------------------------------------------
# State validation + duplicate/race safety
# ---------------------------------------------------------------------------


def test_invalid_source_states_denied_zero_mutation(client, world, user_provider) -> None:
    for status in ("consultant_reviewed", "calculated", "mapping", "extracting"):
        item = world.manual_extraction.seed_item(
            f"item-state-{status}", "org-a", "f.pdf", status=status
        )
        resp = _qc_decision(client, world, user_provider, item.id, approved=True)
        assert resp.status_code == 409, f"{status}: {resp.text}"
        assert world.manual_extraction._items[item.id].status == status
        assert "ct_qc:approved" not in _actions(world, item.id)


def test_unknown_item_404(client, world, user_provider) -> None:
    _seed_role(world)
    _seed_staff(world, user_id="u-qc", role_id="role-qc")
    user_provider.set_user(staff_user("u-qc"))
    resp = client.post(
        f"{OPS}/qc/items/does-not-exist/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert resp.status_code == 404, resp.text


def test_duplicate_decision_rejected_zero_mutation(client, world, user_provider) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    first = _qc_decision(client, world, user_provider, item.id, approved=True)
    assert first.status_code == 200, first.text
    assert world.manual_extraction._items[item.id].status == "ct_qc_approved"
    second = _qc_decision(client, world, user_provider, item.id, approved=False)
    assert second.status_code == 409, second.text
    assert world.manual_extraction._items[item.id].status == "ct_qc_approved"
    # Exactly one successful decision audit; no reject audit for the denied repeat.
    assert _actions(world, item.id).count("ct_qc:approved") == 1
    assert "ct_qc:rejected" not in _actions(world, item.id)


def test_repository_second_decision_returns_none_no_mutation(world) -> None:
    """The repository-level WHERE gate mirrors production: an already-decided
    item cannot be decided again (None) — the endpoint guard turns that into a
    409 with no success audit under a concurrent double-submit."""
    item = world.manual_extraction.seed_item(
        "item-repo-double", "org-a", "f.pdf", status="reviewed"
    )
    first = asyncio.run(
        world.manual_extraction.ct_qc_decision(item.id, True, "u-qc", 90, "ok")
    )
    assert first is not None and first.status == "ct_qc_approved"
    second = asyncio.run(
        world.manual_extraction.ct_qc_decision(item.id, True, "u-qc", 90, "again")
    )
    assert second is None
    assert world.manual_extraction._items[item.id].status == "ct_qc_approved"


def test_invalid_quality_score_rejected(client, world, user_provider) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    _seed_role(world)
    _seed_staff(world, user_id="u-qc", role_id="role-qc")
    user_provider.set_user(staff_user("u-qc"))
    resp = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 150, "approved": True},
    )
    assert resp.status_code == 422, resp.text
    assert world.manual_extraction._items[item.id].status == "reviewed"
    assert "ct_qc:approved" not in _actions(world, item.id)

# ---------------------------------------------------------------------------
# Customer boundary — ct_qc_approved proceeds only via org Owner/Admin
# ---------------------------------------------------------------------------


def test_ct_qc_approval_not_customer_approval(client, world, user_provider) -> None:
    """QC approval leaves the item at ct_qc_approved (never `approved`)."""
    item = _seed_consultant_submission(client, world, user_provider)
    assert _ledger(world) == 500
    resp = _qc_decision(client, world, user_provider, item.id, approved=True)
    assert resp.status_code == 200
    assert world.manual_extraction._items[item.id].status == "ct_qc_approved"
    assert _ledger(world) == 500  # no charge at QC approval


def test_consultant_cannot_approve_ct_qc_approved_item(
    client, world, user_provider
) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    _qc_decision(client, world, user_provider, item.id, approved=True)
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    resp = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "force"},
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "ct_qc_approved"


def test_pe_cannot_approve_ct_qc_approved_item(client, world, user_provider) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    _qc_decision(client, world, user_provider, item.id, approved=True)
    user_provider.set_user(staff_user("u-pe", entity_id="entity-1"))
    resp = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "force"},
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "ct_qc_approved"


def test_customer_member_cannot_approve(client, world, user_provider) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    _qc_decision(client, world, user_provider, item.id, approved=True)
    user_provider.set_user(member_user("org-a", "member-1", "member@test"))
    resp = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "member"},
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "ct_qc_approved"


def test_org_owner_approves_ct_qc_approved_item_charge_at_approval(
    client, world, user_provider
) -> None:
    """Approved consultant-submitted work proceeds ONLY through the existing
    customer-review surface (org Owner/Admin), with the canonical D37 charge."""
    item = _seed_consultant_submission(client, world, user_provider)
    _qc_decision(client, world, user_provider, item.id, approved=True)
    assert _ledger(world) == 500
    user_provider.set_user(org_owner_user("org-a", "owner-1", "owner-1@test"))
    resp = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "approved by owner"},
    )
    assert resp.status_code == 200, resp.text
    assert world.manual_extraction._items[item.id].status == "approved"
    # The ONLY charge is at Customer Approval (1 credit consumed).
    assert _ledger(world) == 499

# ---------------------------------------------------------------------------
# Rework — ct_qc_rejected routes through the existing rework states only
# ---------------------------------------------------------------------------


def test_rejected_item_routes_through_existing_rework_states(
    client, world, user_provider
) -> None:
    """Matrix 14/15 — rejection lands in `ct_qc_rejected` whose ONLY forward
    exits are the canonical rework states `mapping`/`extracting`; it cannot go
    back to `reviewed` or any customer-facing state without reprocessing."""
    item = _seed_consultant_submission(client, world, user_provider)
    resp = _qc_decision(client, world, user_provider, item.id, approved=False)
    assert resp.status_code == 200
    assert world.manual_extraction._items[item.id].status == "ct_qc_rejected"
    # Canonical flow exits from the rejection state.
    exits = set(ITEM_STATUS_FLOW["ct_qc_rejected"])
    assert exits == {"mapping", "extracting"}
    assert not can_transition_item_status("ct_qc_rejected", "reviewed")
    assert not can_transition_item_status("ct_qc_rejected", "customer_review")
    assert not can_transition_item_status("ct_qc_rejected", "approved")
    # No direct re-submission without rework.
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    resub = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resub.status_code == 409, resub.text
    assert world.manual_extraction._items[item.id].status == "ct_qc_rejected"


def test_rejected_item_rework_claim_to_mapping(client, world, user_provider) -> None:
    """Matrix 14 — an org processing member can claim the rejected item back into
    the existing `mapping` rework stage (canonical start-item mechanism)."""
    item = _seed_consultant_submission(client, world, user_provider)
    _qc_decision(client, world, user_provider, item.id, approved=False)
    user_provider.set_user(member_user("org-a", "member-1", "member@test"))
    resp = client.post(
        f"{PROC}/items/{item.id}/start", json={"stage": "mapping"}
    )
    assert resp.status_code == 200, resp.text
    assert world.manual_extraction._items[item.id].status == "mapping"


def test_rejected_item_cannot_reach_customer_review_or_approval(
    client, world, user_provider
) -> None:
    """Matrix 15 — a rejected item cannot be customer-approved from the
    rejection state (409 before any billing/charge side effect)."""
    item = _seed_consultant_submission(client, world, user_provider)
    _qc_decision(client, world, user_provider, item.id, approved=False)
    assert _ledger(world) == 500
    user_provider.set_user(org_owner_user("org-a", "owner-1", "owner-1@test"))
    resp = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "bypass?"},
    )
    assert resp.status_code == 409, resp.text
    assert world.manual_extraction._items[item.id].status == "ct_qc_rejected"
    assert _ledger(world) == 500  # no charge for an invalid/denied approval


def test_rejected_item_preserves_audit_history(client, world, user_provider) -> None:
    """Matrix 16 — rejection audit is preserved with actor and before/after."""
    item = _seed_consultant_submission(client, world, user_provider)
    _qc_decision(client, world, user_provider, item.id, approved=False,
                 qc_user="u-qcrej")
    entry = next(
        e for e in world.audit._entries
        if getattr(e, "entity_id", None) == item.id and e.action == "ct_qc:rejected"
    )
    assert entry.actor == "u-qcrej"
    assert entry.changed_fields.get("status_from") == "reviewed"
    assert entry.changed_fields.get("status_to") == "ct_qc_rejected"
    # Correlation id is populated from the request audit context (middleware).
    assert entry.correlation_id


# ---------------------------------------------------------------------------
# Mutation ordering — no workflow/billing/audit side effect on denials
# ---------------------------------------------------------------------------


def test_denied_decision_produces_no_side_effects(client, world, user_provider) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    subs_before = len(world.billing_subscriptions._subs)
    orders_before = len(world.billing_orders._orders)
    # Unauthorized (no can_qc).
    _seed_role(world, role_id="role-op", name="operator",
               perms={"can_process": True})
    _seed_staff(world, user_id="u-op", role_id="role-op")
    user_provider.set_user(staff_user("u-op"))
    denied = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert denied.status_code == 403
    assert world.manual_extraction._items[item.id].status == "reviewed"
    # No CT-QC decision audit is produced (the only audit on the item is the
    # earlier successful consultant submission).
    decision_actions = [
        a for a in _actions(world, item.id) if a.startswith("ct_qc:")
    ]
    assert decision_actions == []
    assert _ledger(world) == 500
    assert len(world.billing_subscriptions._subs) == subs_before
    assert len(world.billing_orders._orders) == orders_before


def test_ct_qc_never_charges_and_no_notification_side_effects(
    client, world, user_provider
) -> None:
    """Submission and CT-QC decision consume nothing; the charge is at approval."""
    item = _seed_consultant_submission(client, world, user_provider)
    assert _ledger(world) == 500
    _qc_decision(client, world, user_provider, item.id, approved=True)
    assert _ledger(world) == 500
    assert len(world.billing_orders._orders) == 0
    # No notification framework call is triggered by submission or CT-QC.
    events = list(world.events._entries) if hasattr(world.events, "_entries") else []
    assert events == []





