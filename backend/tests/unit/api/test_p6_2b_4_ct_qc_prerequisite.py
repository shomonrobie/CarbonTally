"""P6-2B-4 — narrow Phase-6 control: mandatory CT-QC for MANUAL processing.

Closes the verified P6-2B-3 blocker (manual work could reach Customer
Review/Approval without CarbonTally CT-QC) using the agreed P1 containment
predicate, while preserving the automatic processing path (no routine CT-QC).

  * MANUAL (`reviewed`/`calculated`, no automatic job) may NOT enter Customer
    Review or be Customer-Approved until `ct_qc_approved`.
  * AUTOMATIC (durable job + machine output) keeps claiming/approval without
    routine CT-QC.
  * Denials are zero-mutation and produce no CT-QC/customer audit or billing.
"""
from __future__ import annotations

import asyncio
import uuid

from datetime import datetime, timezone

from domain.billing import BillingPlan, Subscription
from domain.partners import can_transition_item_status
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
MACHINE = "00000000-0000-0000-0000-000000000000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_commercial(world, org="org-a", *, key="p62b4-sub") -> None:
    asyncio.run(
        world.billing_plans.create(
            BillingPlan(
                id=str(uuid.uuid4()), plan_code="professional", name="Professional",
                price=149, currency="GBP", included_credits=500, version=1,
                is_active=True, features={}, effective_from=datetime.now(timezone.utc),
            ),
            created_by="admin-1",
        )
    )
    asyncio.run(
        world.billing_subscriptions.upsert_active(
            Subscription(
                id=str(uuid.uuid4()), organization_id=org, plan_code="professional",
                plan_version=1, billing_mode="CREDIT", lifecycle_status="active",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc), idempotency_key=key,
            ),
            created_by="admin-1",
        )
    )
    asyncio.run(
        BillingService(world.bundle()).grant_credits(
            org, 500, source="plan_included", reason="monthly",
            idempotency_key=f"{key}-grant",
        )
    )


def _manual_item(world, *, status="calculated", item_id=None, org="org-a"):
    """MANUAL item (no automatic-processing job)."""
    return world.manual_extraction.seed_item(
        item_id or f"item-{uuid.uuid4().hex[:8]}", org, "manual.pdf", status=status
    )


class _FakeJob:
    def __init__(self, item_id, automation_extracted_data):
        self.source_item_id = item_id
        self.automation_extracted_data = automation_extracted_data


class _FakeProcessing:
    def __init__(self, by_item):
        self._by_item = by_item

    async def get_by_item(self, item_id):
        return self._by_item.get(item_id)


def _install_job(world, item, *, machine_output=True):
    """Attach a durable automatic-processing job to ``item``."""
    job = _FakeJob(item.id, {"activity": "Electricity", "quantity": 1, "unit": "kWh"}
                   if machine_output else None)
    world.processing = _FakeProcessing({item.id: job})


def _seed_consultant_submission(client, world, user_provider):
    """Consultant submits a `consultant_reviewed` item -> `reviewed` (P6-2B-2)."""
    world.consultants.seed_profile("firm-c1", "u-c1", "C1 Advisory", is_active=True)
    world.consultants.seed_firm_member(
        "firm-c1", "u-c1", role="manager", is_active=True,
        can_manage_clients=True, can_submit=True,
    )
    world.consultants.seed_client("cc-1", "firm-c1", "org-a", "Client Org", status="active")
    item = world.manual_extraction.seed_item(
        f"item-{uuid.uuid4().hex[:8]}", "org-a", "consultant.pdf",
        status="consultant_reviewed",
    )
    _seed_commercial(world)
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    resp = client.post(f"{PROC}/items/{item.id}/consultant-submit")
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["status"] == "reviewed"
    return item


def _seed_reviewer(world, *, user_id="u-rev"):
    world.staff.seed_role(StaffRole(id="role-rev", name="reviewer",
                                    permissions={"can_review": True}))
    world.staff.seed_profile(StaffProfile(
        id=f"sp-{user_id}", user_id=user_id, first_name="Rev", last_name="One",
        email=f"{user_id}@test", role_id="role-rev",
    ))


def _audit_actions(world, item_id):
    return [e.action for e in world.audit._entries
            if getattr(e, "entity_id", None) == item_id]


def _ledger(world, org="org-a"):
    return asyncio.run(world.billing_ledger.balance(org))


# ---------------------------------------------------------------------------
# State machine: the legacy reviewed -> customer_review escape is removed
# ---------------------------------------------------------------------------


def test_reviewed_can_only_advance_to_ct_qc_or_rework() -> None:
    assert not can_transition_item_status("reviewed", "customer_review")
    assert can_transition_item_status("reviewed", "ct_qc")
    assert can_transition_item_status("reviewed", "mapping")
    assert can_transition_item_status("reviewed", "calculated")


# ---------------------------------------------------------------------------
# MANUAL work cannot reach Customer Review/Approval before CT-QC
# ---------------------------------------------------------------------------


def test_manual_calculated_cannot_enter_customer_review(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="calculated")
    user_provider.set_user(member_user("org-a", "member-1", "m@test"))
    resp = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "calculated"


def test_manual_calculated_cannot_be_customer_approved(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="calculated")
    _seed_commercial(world)
    user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
    resp = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "x"},
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "calculated"
    assert _ledger(world) == 500  # no charge (guard precedes billing)
    assert _audit_actions(world, item.id) == []


def test_manual_reviewed_cannot_enter_customer_review(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="reviewed")
    user_provider.set_user(member_user("org-a", "member-1", "m@test"))
    resp = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert resp.status_code in (403, 409), resp.text
    assert world.manual_extraction._items[item.id].status == "reviewed"


def test_consultant_submitted_reviewed_cannot_bypass_ct_qc(
    client, world, user_provider
) -> None:
    item = _seed_consultant_submission(client, world, user_provider)
    # 1) The same consultant cannot hand their submitted work to Customer Review.
    user_provider.set_user(consultant_user("u-c1", "u-c1@example.test"))
    claim = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert claim.status_code in (403, 409), claim.text
    assert world.manual_extraction._items[item.id].status == "reviewed"
    # 2) The org owner cannot approve it without a CT-QC decision.
    user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
    approve = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "force"},
    )
    assert approve.status_code in (403, 409), approve.text
    assert world.manual_extraction._items[item.id].status == "reviewed"
    assert "ct_qc:approved" not in _audit_actions(world, item.id)
    assert _ledger(world) == 500


def test_internal_ops_cannot_hand_manual_work_to_customer_review(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="calculated")
    _seed_reviewer(world)
    user_provider.set_user(staff_user("u-rev"))
    resp = client.post(
        f"{OPS}/items/{item.id}/start", json={"stage": "review"}
    )
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "calculated"


def test_pe_cannot_use_processing_review_claim(client, world, user_provider) -> None:
    item = _manual_item(world, status="calculated")
    user_provider.set_user(staff_user("u-pe", entity_id="entity-1"))
    resp = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert resp.status_code in (403, 409), resp.text
    assert world.manual_extraction._items[item.id].status == "calculated"


# ---------------------------------------------------------------------------
# MANUAL work that HAS passed CT-QC proceeds normally (charge at approval)
# ---------------------------------------------------------------------------


def test_manual_ct_qc_approved_can_proceed_to_review_and_approval(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="ct_qc_approved")
    _seed_commercial(world)
    user_provider.set_user(member_user("org-a", "member-1", "m@test"))
    claim = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert claim.status_code == 200, claim.text
    assert world.manual_extraction._items[item.id].status == "customer_review"
    user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
    approve = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "ok"},
    )
    assert approve.status_code == 200, approve.text
    assert world.manual_extraction._items[item.id].status == "approved"
    assert _ledger(world) == 499  # the only charge is at Customer Approval

# ---------------------------------------------------------------------------
# AUTOMATIC work keeps the no-routine-CT-QC path
# ---------------------------------------------------------------------------


def test_automatic_item_claims_and_is_approved_without_ct_qc(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="calculated", item_id="item-auto-1")
    _install_job(world, item, machine_output=True)
    _seed_commercial(world)
    user_provider.set_user(member_user("org-a", "member-1", "m@test"))
    claim = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert claim.status_code == 200, claim.text
    assert world.manual_extraction._items[item.id].status == "customer_review"
    user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
    approve = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "auto ok"},
    )
    assert approve.status_code == 200, approve.text
    assert world.manual_extraction._items[item.id].status == "approved"
    assert _ledger(world) == 499
    # Automatic path: no CT-QC decision was required or recorded.
    assert "ct_qc:approved" not in _audit_actions(world, item.id)


def test_automatic_item_approved_directly_from_calculated(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="calculated", item_id="item-auto-2")
    _install_job(world, item, machine_output=True)
    _seed_commercial(world)
    user_provider.set_user(org_owner_user("org-a", "owner-1", "o@test"))
    approve = client.post(
        f"{PROC}/items/{item.id}/customer-review",
        json={"approved": True, "customer_notes": "auto direct"},
    )
    assert approve.status_code == 200, approve.text
    assert world.manual_extraction._items[item.id].status == "approved"
    assert _ledger(world) == 499


# ---------------------------------------------------------------------------
# P1 containment is fail-closed: a job without machine output is still MANUAL
# ---------------------------------------------------------------------------


def test_pending_job_without_machine_output_is_manual(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="calculated", item_id="item-spoof")
    _install_job(world, item, machine_output=False)  # attached job, no machine output
    user_provider.set_user(member_user("org-a", "member-1", "m@test"))
    resp = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "calculated"


def test_machine_extracted_by_only_is_automatic_when_job_present(
    client, world, user_provider
) -> None:
    # Machine marker but NO job link → fail-closed MANUAL (no automatic job).
    item = _manual_item(world, status="calculated", item_id="item-marker-nojob")
    import dataclasses

    world.manual_extraction._items[item.id] = dataclasses.replace(
        world.manual_extraction._items[item.id], extracted_by=MACHINE
    )
    user_provider.set_user(member_user("org-a", "member-1", "m@test"))
    resp = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert resp.status_code == 403, resp.text
    assert world.manual_extraction._items[item.id].status == "calculated"


def test_automatic_via_machine_marker_with_job_is_allowed(
    client, world, user_provider
) -> None:
    item = _manual_item(world, status="calculated", item_id="item-marker-job")
    import dataclasses

    world.manual_extraction._items[item.id] = dataclasses.replace(
        world.manual_extraction._items[item.id], extracted_by=MACHINE
    )
    job = _FakeJob(item.id, None)  # legacy job: no automation_extracted_data column
    world.processing = _FakeProcessing({item.id: job})
    user_provider.set_user(member_user("org-a", "member-1", "m@test"))
    resp = client.post(f"{PROC}/items/{item.id}/start", json={"stage": "review"})
    assert resp.status_code == 200, resp.text
    assert world.manual_extraction._items[item.id].status == "customer_review"


