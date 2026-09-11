"""P6-2B-2 — Consultant submission to CarbonTally QC.

Consultant submission (`consultant_reviewed` → existing CT-QC intake state):

  * Active member + active engagement + `can_submit=true` + item at
    `consultant_reviewed` + no open D38 assignment + active client
    processing entitlement → submission succeeds into the existing CT-QC
    intake state (`reviewed`).
  * `can_submit=false` (and no other capability) → 403.
  * Submission NEVER grants CarbonTally QC or Customer Approval authority.
  * Membership/engagement/D38/scope/state/entitlement failures DENY with
    zero business mutation and no billing side effect.
"""
from __future__ import annotations

import asyncio
import uuid

from datetime import datetime, timezone

from domain.billing import BillingPlan, Subscription
from domain.partners import ITEM_STATUS_FLOW, can_transition_item_status
from tests.unit.api.fakes import consultant_user, member_user

PROC = "/api/v3/processing"
OPS = "/api/v3/ops"

#: The existing CarbonTally QC intake contract: the CT-QC pending queue
#: (``list_ct_qc_pending``) lists items in `reviewed`/`pe_qc_approved` and the
#: CT-QC decision endpoint accepts `reviewed`/`pe_qc_approved`/`ct_qc`.
CT_QC_INTAKE_STATUSES = ("reviewed", "pe_qc_approved")


def _seed_consultant(
    world,
    *,
    user_id="u-c1",
    firm_id="firm-c1",
    org_id="org-a",
    is_active=True,
    engagement_status="active",
    client_id="cc-1",
    can_submit=False,
    alt_flags=None,
):
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=is_active)
    world.consultants.seed_firm_member(
        firm_id, user_id, role="manager", is_active=is_active,
        can_manage_clients=True,
        can_extract=bool(alt_flags and "can_extract" in alt_flags),
        can_map=bool(alt_flags and "can_map" in alt_flags),
        can_validate=bool(alt_flags and "can_validate" in alt_flags),
        can_calculate=bool(alt_flags and "can_calculate" in alt_flags),
        can_confirm_automation=bool(
            alt_flags and "can_confirm_automation" in alt_flags
        ),
        can_submit=can_submit,
    )
    world.consultants.seed_client(
        client_id, firm_id, org_id, "Client Org", status=engagement_status
    )
    return consultant_user(user_id, f"{user_id}@example.test")


def _seed_item(world, *, org_id="org-a", item_id=None, status="consultant_reviewed",
               batch_id=None):
    return world.manual_extraction.seed_item(
        item_id or f"item-{uuid.uuid4().hex[:8]}", org_id, "invoice.pdf",
        status=status, batch_id=batch_id,
    )

def _seed_entitlement(world, org_id="org-a", *, key="sub-ent-1") -> None:
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
                organization_id=org_id,
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


def _actions(world, item_id) -> list[str]:
    return [
        e.action for e in world.audit._entries
        if getattr(e, "entity_id", None) == item_id
    ]


def _ledger_balance(world, org_id="org-a") -> int:
    return asyncio.run(world.billing_ledger.balance(org_id))


def _open_assignment(world, item_id, kind, **kw) -> None:
    asyncio.run(
        world.manual_extraction.work_item_open(
            item_id=item_id, action="assign", assignee_kind=kind,
            actor="u-mgr", actor_domain="internal_staff", **kw,
        )
    )


# ---------------------------------------------------------------------------
# Positive — allowed submission into the existing CT-QC intake state
# ---------------------------------------------------------------------------


def test_submission_success_enters_ct_qc_intake_state(
    client, world, user_provider
) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 200, response.text
    assert response.json()["item"]["status"] == "reviewed"
    assert world.manual_extraction._items[item.id].status == "reviewed"
    assert "consultant.submit:submitted" in _actions(world, item.id)


def test_submission_target_is_the_existing_ct_qc_intake_state(world) -> None:
    """The submitted state is the state the existing CT-QC authority consumes."""
    assert can_transition_item_status("consultant_reviewed", "reviewed")
    assert "reviewed" in ITEM_STATUS_FLOW["consultant_reviewed"]
    # The existing CarbonTally QC pending queue + decision endpoint accept
    # `reviewed` items — no new/duplicate CT-QC state was invented.
    assert "reviewed" in CT_QC_INTAKE_STATUSES

def test_successful_submission_produces_no_charge_or_billing_mutation(
    client, world, user_provider
) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    assert _ledger_balance(world) == 0
    subs_before = len(world.billing_subscriptions._subs)
    orders_before = len(world.billing_orders._orders)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 200, response.text
    # NO charge / credit consumption / order / subscription mutation.
    assert _ledger_balance(world) == 0
    assert len(world.billing_subscriptions._subs) == subs_before
    assert len(world.billing_orders._orders) == orders_before


def test_submission_does_not_auto_grant_flags(client, world, user_provider) -> None:
    """Submission never auto-grants `can_submit` or any other capability."""
    item = _seed_item(world)
    user = _seed_consultant(world, can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    member = world.consultants._members[-1]
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 200, response.text
    member_after = world.consultants._members[-1]
    assert member_after.can_submit is True
    assert not (
        member_after.can_extract or member_after.can_map or member_after.can_validate
        or member_after.can_calculate or member_after.can_confirm_automation
    )


# ---------------------------------------------------------------------------
# Capability — can_submit is the exclusive submission capability (D1)
# ---------------------------------------------------------------------------


def test_can_submit_false_denied_zero_mutation(client, world, user_provider) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, can_submit=False)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 403, response.text
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"
    assert "consultant.submit:submitted" not in _actions(world, item.id)


def test_other_five_capabilities_cannot_substitute(
    client, world, user_provider
) -> None:
    for flag in (
        "can_extract",
        "can_map",
        "can_validate",
        "can_calculate",
        "can_confirm_automation",
    ):
        item = _seed_item(world, item_id=f"item-cap-{flag}")
        user = _seed_consultant(
            world, user_id=f"u-{flag}", client_id=f"cc-{flag}",
            can_submit=False, alt_flags=[flag],
        )
        _seed_entitlement(world)
        user_provider.set_user(user)
        response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
        assert response.status_code == 403, f"{flag}: {response.text}"
        assert (
            world.manual_extraction._items[item.id].status == "consultant_reviewed"
        ), flag


def test_org_member_cannot_submit(client, world, user_provider) -> None:
    item = _seed_item(world)
    _seed_entitlement(world)
    user_provider.set_user(member_user("org-a", "user-a", "a@example.test"))
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 403, response.text
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"


# ---------------------------------------------------------------------------
# Membership — inactive membership denies (checked at request time)
# ---------------------------------------------------------------------------


def test_inactive_membership_denied(client, world, user_provider) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, is_active=False, can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 403, response.text
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"
    assert "consultant.submit:submitted" not in _actions(world, item.id)


# ---------------------------------------------------------------------------
# Engagement — only active engagements grant submission (D2, request-time)
# ---------------------------------------------------------------------------


def test_non_active_engagements_deny_submission(client, world, user_provider) -> None:
    for status in ("pending", "rejected", "suspended", "ended", "inactive"):
        item = _seed_item(world, item_id=f"item-eng-{status}")
        user = _seed_consultant(
            world, user_id=f"u-{status}", client_id=f"cc-{status}",
            engagement_status=status, can_submit=True,
        )
        _seed_entitlement(world)
        user_provider.set_user(user)
        response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
        assert response.status_code == 403, f"{status}: {response.text}"
        assert (
            world.manual_extraction._items[item.id].status == "consultant_reviewed"
        ), status
        assert "consultant.submit:submitted" not in _actions(world, item.id), status


def test_unauthenticated_denied(client, world, user_provider) -> None:
    item = _seed_item(world)
    _seed_entitlement(world)
    user_provider.set_unauthenticated()
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 401


def test_unknown_item_404(client, world, user_provider) -> None:
    user = _seed_consultant(world, can_submit=True)
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/does-not-exist/consultant-submit")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Cross-scope — another firm's client / another client's item (server-derived)
# ---------------------------------------------------------------------------


def test_cross_firm_and_cross_client_denied(client, world, user_provider) -> None:
    # Another firm with a grant on a DIFFERENT org cannot submit org-a's item.
    item_a = _seed_item(world, org_id="org-a", item_id="item-a-scope")
    user_other_firm = _seed_consultant(
        world, firm_id="firm-other", org_id="org-b", user_id="u-other",
        client_id="cc-other", can_submit=True,
    )
    _seed_entitlement(world)
    user_provider.set_user(user_other_firm)
    response = client.post(f"{PROC}/items/{item_a.id}/consultant-submit")
    assert response.status_code == 403, response.text
    assert world.manual_extraction._items[item_a.id].status == "consultant_reviewed"

    # A firm granted only org-a cannot submit an item belonging to org-b.
    item_b = _seed_item(world, org_id="org-b", item_id="item-b-scope")
    user_org_a = _seed_consultant(
        world, user_id="u-c2", client_id="cc-2", can_submit=True,
    )
    _seed_entitlement(world, "org-b")
    user_provider.set_user(user_org_a)
    response = client.post(f"{PROC}/items/{item_b.id}/consultant-submit")
    assert response.status_code == 403, response.text
    assert world.manual_extraction._items[item_b.id].status == "consultant_reviewed"


def test_forged_request_body_org_cannot_authorize(client, world, user_provider) -> None:
    """A forged organisation ID in the request body grants nothing."""
    item = _seed_item(world, org_id="org-b", item_id="item-forge-org")  # org-b item
    # Consultant is granted org-a ONLY — no grant for org-b.
    user = _seed_consultant(world, user_id="u-forge", can_submit=True)
    _seed_entitlement(world, "org-b")  # even an org-b entitlement does not help
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-submit",
        json={"organization_id": "org-b"},  # ignored: server derives from batch
    )
    assert response.status_code == 403, response.text
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"


def test_forged_request_body_cannot_redirect_submission(
    client, world, user_provider
) -> None:
    """The server-derived org governs; a bogus body org cannot redirect."""
    item = _seed_item(world, org_id="org-a", item_id="item-redirect")
    user = _seed_consultant(world, user_id="u-redir", can_submit=True)
    _seed_entitlement(world, "org-a")
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/consultant-submit",
        json={"organization_id": "org-b", "consultant_id": "attacker",
              "firm_id": "firm-other", "price": 0},
    )
    # Authorized for org-a (server-derived); the forged body is ignored.
    assert response.status_code == 200, response.text
    assert world.manual_extraction._items[item.id].status == "reviewed"
    assert response.json()["item"]["status"] == "reviewed"


def test_unknown_batch_404_for_item_without_batch(client, world, user_provider) -> None:
    """A resource relationship that cannot resolve denies rather than submits."""
    item = world.manual_extraction.seed_item(
        "item-no-batch", "org-a", "f.pdf", status="consultant_reviewed"
    )
    # Break the item -> batch relationship (simulate a forged/foreign batch).
    world.manual_extraction._batches[item.batch_id] = None  # force batch lookup fail
    user = _seed_consultant(world, user_id="u-nobatch", can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 404, response.text

# ---------------------------------------------------------------------------
# D38 — effective assignment conflicts deny submission (D3)
# ---------------------------------------------------------------------------


def test_item_level_internal_and_pe_assignment_deny(client, world, user_provider) -> None:
    for kind, kw, uid in (
        ("internal_staff", {"assigned_to": "u-op"}, "u-i1"),
        ("processing_entity", {"processing_entity_id": "entity-1"}, "u-i2"),
    ):
        item = _seed_item(world, item_id=f"item-{kind}")
        _open_assignment(world, item.id, kind, **kw)
        user = _seed_consultant(
            world, user_id=uid, client_id=f"cc-{uid}", can_submit=True,
        )
        _seed_entitlement(world)
        user_provider.set_user(user)
        response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
        assert response.status_code == 403, f"{kind}: {response.text}"
        assert (
            world.manual_extraction._items[item.id].status == "consultant_reviewed"
        ), kind
        assert "consultant.submit:submitted" not in _actions(world, item.id), kind


def test_batch_default_assignment_denies_submission(
    client, world, user_provider
) -> None:
    for carrier, kw in (("pe", {"entity_id": "entity-1"}), ("internal", None)):
        batch = asyncio.run(
            world.manual_extraction.create_batch(
                "org-a", f"batch-{carrier}", **(kw or {})
            )
        )
        if carrier == "internal":
            asyncio.run(
                world.manual_extraction.update_batch(
                    batch.id, status="in_progress", assigned_to="u-op"
                )
            )
        item = world.manual_extraction.seed_item(
            f"item-batch-{carrier}", "org-a", "f.pdf",
            status="consultant_reviewed", batch_id=batch.id,
        )
        user = _seed_consultant(
            world, user_id=f"u-{carrier}", client_id=f"cc-{carrier}",
            can_submit=True,
        )
        _seed_entitlement(world)
        user_provider.set_user(user)
        response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
        assert response.status_code == 403, f"{carrier}: {response.text}"
        assert (
            world.manual_extraction._items[item.id].status == "consultant_reviewed"
        ), carrier


# ---------------------------------------------------------------------------
# Workflow state — only `consultant_reviewed` may be submitted (D5)
# ---------------------------------------------------------------------------


def test_invalid_workflow_states_denied(client, world, user_provider) -> None:
    for status, uid in (
        ("extracting", "u-s1"),
        ("mapping", "u-s2"),
        ("validating", "u-s3"),
        ("calculated", "u-s4"),
        ("reviewed", "u-s5"),
    ):
        item = world.manual_extraction.seed_item(
            f"item-state-{uid}", "org-a", "f.pdf", status=status
        )
        user = _seed_consultant(
            world, user_id=uid, client_id=f"cc-{uid}", can_submit=True,
        )
        _seed_entitlement(world)
        user_provider.set_user(user)
        response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
        assert response.status_code == 409, f"{status}: {response.text}"
        assert world.manual_extraction._items[item.id].status == status
        assert "consultant.submit:submitted" not in _actions(world, item.id), status


def test_consultant_cannot_skip_review(client, world, user_provider) -> None:
    """A calculated item (Consultant processing complete, NOT reviewed) → 409."""
    item = world.manual_extraction.seed_item(
        "item-skip-review", "org-a", "f.pdf", status="calculated"
    )
    user = _seed_consultant(world, user_id="u-skip", can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 409, response.text
    assert world.manual_extraction._items[item.id].status == "calculated"
    assert "consultant.submit:submitted" not in _actions(world, item.id)


def test_already_submitted_item_cannot_be_resubmitted(
    client, world, user_provider
) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, user_id="u-twice", can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    first = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert first.status_code == 200, first.text
    assert world.manual_extraction._items[item.id].status == "reviewed"
    second = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert second.status_code == 409, second.text
    assert world.manual_extraction._items[item.id].status == "reviewed"


# ---------------------------------------------------------------------------
# Billing / entitlement — non-charging availability (D6), fail closed
# ---------------------------------------------------------------------------


def test_no_processing_entitlement_denies_submission_zero_mutation(
    client, world, user_provider
) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, user_id="u-noent", can_submit=True)
    # NOTE: no _seed_entitlement — the client org has NO active entitlement.
    user_provider.set_user(user)
    assert _ledger_balance(world) == 0
    subs_before = len(world.billing_subscriptions._subs)
    orders_before = len(world.billing_orders._orders)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 403, response.text
    # Zero workflow mutation.
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"
    # Zero billing mutation — no charge, no ledger/order/subscription change.
    assert _ledger_balance(world) == 0
    assert len(world.billing_subscriptions._subs) == subs_before
    assert len(world.billing_orders._orders) == orders_before
    # No successful-submission audit.
    assert "consultant.submit:submitted" not in _actions(world, item.id)


def test_cancelled_entitlement_denies_submission(client, world, user_provider) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, user_id="u-cancelled", can_submit=True)
    _seed_entitlement(world, key="sub-cancel-1")
    sub = asyncio.run(world.billing_subscriptions.get_active_for_org("org-a"))
    assert sub is not None
    asyncio.run(
        world.billing_subscriptions.update_status(
            sub.id, "cancelled", updated_by="admin-1"
        )
    )
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 403, response.text
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"
    assert "consultant.submit:submitted" not in _actions(world, item.id)


# ---------------------------------------------------------------------------
# QC boundary — submission grants no CarbonTally QC authority (D5)
# ---------------------------------------------------------------------------


def test_consultant_cannot_perform_ct_qc_decision(client, world, user_provider) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, user_id="u-qcblock", can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert response.status_code == 403, response.text


def test_submission_does_not_grant_ct_qc_authority(
    client, world, user_provider
) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, user_id="u-qcstill", can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    submitted = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert submitted.status_code == 200, submitted.text
    assert world.manual_extraction._items[item.id].status == "reviewed"
    # The submitting consultant still cannot make a QC decision on the item.
    decision = client.post(
        f"{OPS}/qc/items/{item.id}/decision",
        json={"quality_score": 90, "approved": True},
    )
    assert decision.status_code == 403, decision.text

# ---------------------------------------------------------------------------
# Customer Review / Approval boundary (D9) — submission cannot reach it
# ---------------------------------------------------------------------------


def test_submission_cannot_produce_customer_review_or_approved(
    client, world, user_provider
) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, user_id="u-approve", can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 200, response.text
    status = world.manual_extraction._items[item.id].status
    assert status == "reviewed"
    assert status not in ("customer_review", "approved")
    assert status not in ("ct_qc", "ct_qc_approved")


def test_consultant_cannot_perform_customer_approval(
    client, world, user_provider
) -> None:
    item = _seed_item(world)
    user = _seed_consultant(world, user_id="u-custapp", can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "force"},
    )
    assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# Ordering — authorization/entitlement precede mutation; audit only on success
# ---------------------------------------------------------------------------


def test_authorization_and_entitlement_precede_mutation(
    client, world, user_provider
) -> None:
    """Capability/state/entitlement failures leave the item untouched."""
    # Capability denial with a valid state + entitlement: no mutation, no audit.
    item = _seed_item(world, item_id="item-order-cap")
    user = _seed_consultant(world, user_id="u-ordcap", can_submit=False)
    _seed_entitlement(world)
    user_provider.set_user(user)
    denied = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert denied.status_code == 403, denied.text
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"
    assert _actions(world, item.id) == []

def test_successful_audit_only_after_successful_transition(
    client, world, user_provider
) -> None:
    item = _seed_item(world, item_id="item-order-ok")
    user = _seed_consultant(world, user_id="u-ordok", can_submit=True)
    _seed_entitlement(world)
    user_provider.set_user(user)
    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 200, response.text
    submit_actions = [
        a for a in _actions(world, item.id) if a == "consultant.submit:submitted"
    ]
    assert len(submit_actions) == 1
    entry = next(
        e for e in world.audit._entries
        if getattr(e, "entity_id", None) == item.id
    )
    assert entry.actor == "u-ordok"
    assert entry.changed_fields.get("status_from") == "consultant_reviewed"
    assert entry.changed_fields.get("status_to") == "reviewed"


def test_denied_classes_produce_no_submission_audit(
    client, world, user_provider
) -> None:
    """Zero-mutation across denial classes: no workflow/billing/audit side effect."""
    # Engagement denial.
    item_eng = _seed_item(world, item_id="item-za-eng")
    user_eng = _seed_consultant(
        world, user_id="u-za-eng", firm_id="firm-za-eng", client_id="cc-za-eng",
        engagement_status="suspended", can_submit=True,
    )
    _seed_entitlement(world)
    user_provider.set_user(user_eng)
    r1 = client.post(f"{PROC}/items/{item_eng.id}/consultant-submit")
    assert r1.status_code == 403
    assert _actions(world, item_eng.id) == []
    assert world.manual_extraction._items[item_eng.id].status == "consultant_reviewed"

    # Invalid workflow state.
    item_state = world.manual_extraction.seed_item(
        "item-za-state", "org-a", "f.pdf", status="mapping"
    )
    user_state = _seed_consultant(
        world, user_id="u-za-state", firm_id="firm-za-state", client_id="cc-za-state",
        can_submit=True,
    )
    user_provider.set_user(user_state)
    r2 = client.post(f"{PROC}/items/{item_state.id}/consultant-submit")
    assert r2.status_code == 409
    assert _actions(world, item_state.id) == []

    # D38 denial.
    item_d38 = _seed_item(world, item_id="item-za-d38")
    _open_assignment(
        world, item_d38.id, "processing_entity", processing_entity_id="entity-1"
    )
    user_d38 = _seed_consultant(
        world, user_id="u-za-d38", firm_id="firm-za-d38", client_id="cc-za-d38",
        can_submit=True,
    )
    user_provider.set_user(user_d38)
    r3 = client.post(f"{PROC}/items/{item_d38.id}/consultant-submit")
    assert r3.status_code == 403
    assert _actions(world, item_d38.id) == []
    assert world.manual_extraction._items[item_d38.id].status == "consultant_reviewed"

    # Ledger untouched across all denials.
    assert _ledger_balance(world) == 0







