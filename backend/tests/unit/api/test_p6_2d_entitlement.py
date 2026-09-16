"""P6-2D — D6 entitlement preservation verification (CP1 focused tests).

D6 is PRE-EXISTING behaviour (``PO-PHASE6-D6-R-20260910``): entitlement is owned
by the client ORGANISATION, the consultant submission performs a NON-CHARGING
availability preflight, and the canonical approval-time check remains the
authoritative charge point. This task must PRESERVE it, so these tests add only
the two angles not already covered by the existing suites:

* the submission preflight resolves the entitlement from the SERVER-DERIVED
  client organisation — another organisation's (or the actor's) entitlement can
  never substitute;
* a denied submission consumes and charges nothing.

Reused existing coverage (not duplicated here):

* ``tests/unit/api/test_p6bill1_entitlement_and_consultant_commercial.py``
  (ownership, ``test_no_entitlement_denies_chargeable_processing``,
  ``test_entitlement_resolved_server_side``,
  ``test_client_supplied_entitlement_claims_cannot_bypass``,
  ``test_client_a_credits_charge_only_client_a``);
* ``tests/unit/api/test_billing_core.py`` (charge/idempotency semantics);
* ``tests/unit/api/test_p6_2b_2_consultant_submission.py`` (submission is
  non-charging; capability denial is zero-mutation).
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import uuid

from domain.billing import BillingPlan, Subscription
from tests.unit.api.fakes import consultant_user

PROC = "/api/v3/processing"


def _seed_consultant(world, *, user_id="u-c1", firm_id="firm-c1", org_id="org-a"):
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=True)
    world.consultants.seed_firm_member(
        firm_id,
        user_id,
        role="manager",
        is_active=True,
        can_manage_clients=True,
        can_submit=True,
    )
    # FIN-06 precondition: manual processing is enabled for the client org.
    world.manual_processing.seed_grant("organization", org_id)
    world.consultants.seed_client(
        "cc-1", firm_id, org_id, "Client Org", status="active"
    )
    return consultant_user(user_id, f"{user_id}@example.test")


def _seed_entitlement(world, org_id, *, key) -> None:
    """Give exactly one organisation an active plan + subscription."""
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
                effective_from=_dt.datetime.now(_dt.timezone.utc),
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
                current_period_start=_dt.datetime.now(_dt.timezone.utc),
                current_period_end=_dt.datetime.now(_dt.timezone.utc),
                idempotency_key=key,
            ),
            created_by="admin-1",
        )
    )


def _ledger(world, org_id="org-a") -> int:
    return asyncio.run(world.billing_ledger.balance(org_id))


def _submitted_item(world, item_id="item-ent-1"):
    return world.manual_extraction.seed_item(
        item_id, "org-a", "invoice.pdf", status="consultant_reviewed"
    )


def test_entitlement_is_resolved_from_the_client_org_not_another_org(
    client, world, user_provider
) -> None:
    """Only the CLIENT organisation's entitlement authorises submission: an
    entitlement held by a different organisation never substitutes."""
    item = _submitted_item(world)
    _seed_entitlement(world, "org-b", key="sub-org-b")
    user_provider.set_user(_seed_consultant(world))

    denied = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert denied.status_code == 403, denied.text
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"

    _seed_entitlement(world, "org-a", key="sub-org-a")
    allowed = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert allowed.status_code == 200, allowed.text
    assert world.manual_extraction._items[item.id].status == "reviewed"


def test_denied_submission_consumes_and_charges_nothing(
    client, world, user_provider
) -> None:
    item = _submitted_item(world, "item-ent-2")
    user_provider.set_user(_seed_consultant(world))  # no entitlement anywhere

    orders_before = len(world.billing_orders._orders)
    subs_before = len(world.billing_subscriptions._subs)

    response = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert response.status_code == 403, response.text
    assert _ledger(world, "org-a") == 0
    assert len(world.billing_orders._orders) == orders_before
    assert len(world.billing_subscriptions._subs) == subs_before
    assert world.manual_extraction._items[item.id].status == "consultant_reviewed"
