"""P6-2C — approval-boundary hardening & workflow-stage authorisation.

Implements the acceptance matrix of contract
``CARBONTALLY-P6-2C-IC-20260910-001`` (PO-P6-2C-D1/D2/D3):

  * D1 — the `calculated -> approved` transition is AUTOMATIC-processing-only; a
    manually processed item has no approval path from `calculated`.
  * D2 — a consultant must hold an existing capability before claiming the
    generic `review` stage (`can_submit`); an active grant alone is not enough.
  * D3 — billing is untouched: exactly one charge, at Customer Approval, and
    never on a denied path.

Tests exercise the real HTTP surface (in-memory repositories), not helpers.
"""
from __future__ import annotations

import asyncio
import dataclasses
import uuid
from datetime import datetime, timezone

from starlette.testclient import TestClient

from api.dependencies import (
    get_audit_logger,
    get_current_user,
    get_event_bus,
    get_factor_search_index,
    get_repositories,
)
from api.router import create_app
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus
from infra.search_index import FactorSearchIndex

from domain.automatic_processing import AutomaticProcessingJob
from domain.billing import BillingPlan, Subscription
from domain.staff import StaffProfile, StaffRole
from services.billing import BillingService

from tests.unit.api.fakes import (
    InMemoryWorld,
    admin_user,
    consultant_user,
    member_user,
    org_owner_user,
    staff_user,
)

PROC = "/api/v3/processing"
OPS = "/api/v3/ops"
MACHINE = "00000000-0000-0000-0000-000000000000"


class UserProvider:
    def __init__(self) -> None:
        self.current = admin_user()

    async def __call__(self):
        from fastapi import HTTPException, status

        if getattr(self, "unauthenticated", False):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="x")
        return self.current

    def set_user(self, user) -> None:
        self.current = user

    def set_unauthenticated(self) -> None:
        self.unauthenticated = True


class _FakeProcessing:
    """Minimal durable-job repo over real ``AutomaticProcessingJob`` records."""

    def __init__(self, jobs=()):
        self.jobs = {j.id: j for j in jobs}

    async def get(self, job_id):
        return self.jobs.get(job_id)

    async def get_by_item(self, item_id):
        rows = [j for j in self.jobs.values() if j.source_item_id == item_id]
        return rows[0] if rows else None

    async def complete_review(self, job_id, *, approved, reviewer,
                              rejection_reason=None, customer_notes=None):
        job = self.jobs.get(job_id)
        if job is None:
            return None
        updated = dataclasses.replace(
            job,
            stage="completed" if approved else "blocked",
            status="completed" if approved else "manual_review",
            customer_approved=approved,
            customer_reviewed_by=reviewer,
            customer_notes=customer_notes,
            customer_rejection_reason=rejection_reason,
        )
        self.jobs[job_id] = updated
        return updated


def install_automatic_job(world, item, *, machine_output=True, stage="review",
                          status="pending", job_id=None):
    """Attach a durable automatic-processing job (P1: job + machine output)."""
    job = AutomaticProcessingJob(
        id=job_id or f"job-{uuid.uuid4().hex[:8]}",
        organization_id="org-a",
        file_name="doc.pdf",
        file_url="http://example.test/doc.pdf",
        stage=stage,
        status=status,
        source_item_id=item.id,
        automation_extracted_data={"items": []} if machine_output else None,
        created_by="u-c1",
    )
    world.processing = _FakeProcessing([job])
    return job


def build():
    world = InMemoryWorld()
    up = UserProvider()
    app = create_app()
    index = FactorSearchIndex()
    index.load(list(world.factors._factors.values()))
    app.dependency_overrides[get_current_user] = up
    app.dependency_overrides[get_repositories] = lambda: world.bundle()
    app.dependency_overrides[get_audit_logger] = lambda: AuditLogger(world.audit)
    app.dependency_overrides[get_event_bus] = lambda: EventBus()
    app.dependency_overrides[get_factor_search_index] = lambda: index
    return TestClient(app, raise_server_exceptions=True), world, up


def seed_commercial(world, org="org-a", *, key="p62c-sub"):
    asyncio.run(world.billing_plans.create(
        BillingPlan(id=str(uuid.uuid4()), plan_code="professional",
                    name="Professional", price=149, currency="GBP",
                    included_credits=500, version=1, is_active=True,
                    features={}, effective_from=datetime.now(timezone.utc)),
        created_by="admin-1"))
    asyncio.run(world.billing_subscriptions.upsert_active(
        Subscription(id=str(uuid.uuid4()), organization_id=org,
                     plan_code="professional", plan_version=1, billing_mode="CREDIT",
                     lifecycle_status="active",
                     current_period_start=datetime.now(timezone.utc),
                     current_period_end=datetime.now(timezone.utc),
                     idempotency_key=key),
        created_by="admin-1"))
    asyncio.run(BillingService(world.bundle()).grant_credits(
        org, 500, source="plan_included", reason="monthly",
        idempotency_key=f"{key}-grant"))


def seed_item(world, *, status, org="org-a", item_id=None):
    iid = item_id or f"item-{uuid.uuid4().hex[:8]}"
    return world.manual_extraction.seed_item(iid, org, "doc.pdf", status=status)


def item_status(world, item_id):
    return world.manual_extraction._items[item_id].status


def actions(world, item_id):
    return [e.action for e in world.audit._entries
            if getattr(e, "entity_id", None) == item_id]


def ledger(world, org="org-a"):
    return asyncio.run(world.billing_ledger.balance(org))


def set_machine_extracted_by(world, item_id):
    cur = world.manual_extraction._items[item_id]
    world.manual_extraction._items[item_id] = dataclasses.replace(
        cur, extracted_by=MACHINE)


def seed_consultant(world, *, firm="firm-c1", user="u-c1", client="cc-1",
                    org="org-a", **flags):
    """Seed an active consultant firm member with the given capability flags."""
    world.consultants.seed_profile(firm, user, "C1 Advisory", is_active=True)
    world.consultants.seed_firm_member(
        firm, user, role="manager", is_active=True,
        can_manage_clients=True, **flags,
    )
    world.consultants.seed_client(client, firm, org, "Client Org", status="active")


def seed_staff(world, *, user="u-rev", perms=None, role_id="role-rev",
               entity_id=None, name=None):
    world.staff.seed_role(StaffRole(id=role_id, name=name or role_id,
                                    permissions=perms or {"can_review": True}))
    world.staff.seed_profile(StaffProfile(
        id=f"sp-{user}", user_id=user, first_name="S", last_name="One",
        email=f"{user}@test", role_id=role_id, entity_id=entity_id,
    ))


def approve(client, item_id, *, approved=True, reason="no"):
    return client.post(
        f"{PROC}/items/{item_id}/customer-review",
        json={"approved": approved, "rejection_reason": reason,
              "customer_notes": "t"},
    )


def claim(client, item_id, stage):
    return client.post(f"{PROC}/items/{item_id}/start", json={"stage": stage})


# ---------------------------------------------------------------------------
# D1 — `calculated -> approved` is AUTOMATIC-processing-only (rows 1-7, 10-20)
# ---------------------------------------------------------------------------


def test_owner_can_approve_automatic_calculated_item(client, world, user_provider):
    """Row 18 — the automatic-processing approval path remains functional."""
    item = seed_item(world, status="calculated", item_id="item-auto")
    install_automatic_job(world, item)
    seed_commercial(world)
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    resp = approve(client, item.id)
    assert resp.status_code == 200, resp.text
    assert item_status(world, item.id) == "approved"
    assert ledger(world) == 499  # exactly one charge, at Customer Approval


def test_manual_calculated_approval_denied_automatic_only(
    client, world, user_provider
):
    """Rows 10/11/19 — manual `calculated` has no approval path (D1 + P6-2B-4)."""
    item = seed_item(world, status="calculated", item_id="item-manual")
    seed_commercial(world)
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    before = ledger(world)
    resp = approve(client, item.id)
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "calculated"
    assert ledger(world) == before
    assert actions(world, item.id) == []


def test_manual_calculated_rejection_also_denied(client, world, user_provider):
    item = seed_item(world, status="calculated", item_id="item-manual-rej")
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    resp = approve(client, item.id, approved=False, reason="bad")
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "calculated"


def test_consultant_cannot_approve(client, world, user_provider):
    """Row 1."""
    item = seed_item(world, status="customer_review", item_id="item-cons")
    seed_consultant(world, can_submit=True)
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    resp = approve(client, item.id)
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_pe_cannot_approve(client, world, user_provider):
    """Row 2."""
    item = seed_item(world, status="customer_review", item_id="item-pe")
    user_provider.set_user(staff_user("u-pe", entity_id="entity-1"))
    resp = approve(client, item.id)
    assert resp.status_code in (401, 403), resp.text
    assert item_status(world, item.id) == "customer_review"


def test_operations_staff_cannot_approve(client, world, user_provider):
    """Row 3."""
    item = seed_item(world, status="customer_review", item_id="item-ops")
    seed_staff(world, user="u-rev", perms={"can_review": True, "can_process": True})
    user_provider.set_user(staff_user("u-rev"))
    resp = approve(client, item.id)
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_member_cannot_approve(client, world, user_provider):
    """Row 4."""
    item = seed_item(world, status="customer_review", item_id="item-mem")
    user_provider.set_user(member_user("org-a", "m1", "m@test"))
    resp = approve(client, item.id)
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_viewer_cannot_approve(client, world, user_provider):
    """Row 5 (viewer = non-admin org member)."""
    item = seed_item(world, status="customer_review", item_id="item-viewer")
    user_provider.set_user(member_user("org-a", "v1", "v@test"))
    resp = approve(client, item.id)
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_unauthenticated_cannot_approve(client, world, user_provider):
    """Row 6."""
    item = seed_item(world, status="customer_review", item_id="item-anon")
    user_provider.set_unauthenticated()
    resp = approve(client, item.id)
    assert resp.status_code == 401, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_cross_organisation_actor_cannot_approve(client, world, user_provider):
    """Row 7."""
    item = seed_item(world, status="customer_review", item_id="item-xorg")
    user_provider.set_user(org_owner_user("org-b", "o-b", "ob@test"))
    resp = approve(client, item.id)
    assert resp.status_code in (403, 404), resp.text
    assert item_status(world, item.id) == "customer_review"


def test_invalid_state_transition_preserves_409(client, world, user_provider):
    """Row 16."""
    item = seed_item(world, status="pending", item_id="item-bad-state")
    seed_commercial(world)
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    resp = approve(client, item.id)
    assert resp.status_code == 409, resp.text
    assert item_status(world, item.id) == "pending"


def test_pe_origin_guard_intact(client, world, user_provider):
    """Row 20 — PE-originated work still needs CT-QC before customer approval."""
    item = seed_item(world, status="calculated", item_id="item-pe-origin")
    install_automatic_job(world, item)  # automatic, but PE-origin
    world.manual_extraction.seed_item_origin(item.id, "PROCESSING_ENTITY", "entity-1")
    seed_commercial(world)
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    resp = approve(client, item.id)
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "calculated"
    assert ledger(world) == 500


def test_ct_qc_approved_manual_approval_still_works(client, world, user_provider):
    """D1 must not break the legitimate manual post-CT-QC approval path."""
    item = seed_item(world, status="ct_qc_approved", item_id="item-ctqc")
    seed_commercial(world)
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    resp = approve(client, item.id)
    assert resp.status_code == 200, resp.text
    assert item_status(world, item.id) == "approved"
    assert ledger(world) == 499


def test_double_approval_is_idempotent_for_billing(client, world, user_provider):
    """Row 17 — repeated approval cannot double-charge (D37 idempotency)."""
    item = seed_item(world, status="calculated", item_id="item-idem")
    install_automatic_job(world, item)
    seed_commercial(world)
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    first = approve(client, item.id)
    second = approve(client, item.id)
    assert first.status_code == 200, first.text
    assert second.status_code in (200, 409), second.text
    assert item_status(world, item.id) == "approved"
    assert ledger(world) == 499  # one charge only


def test_alternate_endpoints_cannot_bypass_approval(client, world, user_provider):
    """Row 12/13 — ops + PE surfaces cannot set `approved`."""
    # PE entity status route explicitly rejects customer-gated statuses.
    item = seed_item(world, status="calculated", item_id="item-alt-pe")
    seed_staff(world, user="u-pe", perms={"can_process": True},
               role_id="role-pe", entity_id="entity-1")
    user_provider.set_user(staff_user("u-pe", entity_id="entity-1"))
    resp = client.post(
        f"{OPS}/entities/entity-1/extraction/items/{item.id}/status",
        json={"status": "approved"},
    )
    assert resp.status_code in (401, 403, 404), resp.text
    assert item_status(world, item.id) == "calculated"
    # Ops review-stage claim cannot hand a manual item to customer review.
    item2 = seed_item(world, status="calculated", item_id="item-alt-ops")
    seed_staff(world, user="u-rev", perms={"can_review": True})
    user_provider.set_user(staff_user("u-rev"))
    resp2 = client.post(f"{OPS}/items/{item2.id}/start", json={"stage": "review"})
    assert resp2.status_code == 403, resp2.text
    assert item_status(world, item2.id) == "calculated"


def test_actor_identity_injection_cannot_approve(client, world, user_provider):
    """Row 14 — a consultant claiming org membership cannot approve."""
    item = seed_item(world, status="customer_review", item_id="item-inject")
    seed_consultant(world, can_submit=True)
    injected = consultant_user("u-c1", "u-c1@x")
    injected.organization_id = "org-a"
    injected.is_org_member = True
    user_provider.set_user(injected)
    resp = approve(client, item.id)
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_job_review_stamps_item_without_charging(client, world, user_provider):
    """Row 23 — the (unchanged) automatic job-review route bills nothing."""
    item = seed_item(world, status="calculated", item_id="item-jobrev")
    install_automatic_job(world, item, stage="review", status="review",
                          job_id="job-r1")
    seed_commercial(world)
    user_provider.set_user(member_user("org-a", "m1", "m@test"))
    denied = client.post(f"{PROC}/jobs/job-r1/review",
                         json={"approved": True, "customer_notes": "x"})
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    ok = client.post(f"{PROC}/jobs/job-r1/review",
                     json={"approved": True, "customer_notes": "x"})
    assert denied.status_code == 403, denied.text
    assert ok.status_code == 200, ok.text
    assert item_status(world, item.id) == "approved"
    assert ledger(world) == 500  # unchanged: job review does not charge

# ---------------------------------------------------------------------------
# D2 — consultant `review` / `source` stage claims require an existing
#      capability (rows 8, 9, 10) ; a grant alone is not enough
# ---------------------------------------------------------------------------


def test_consultant_without_capability_cannot_claim_review(
    client, world, user_provider
):
    """Row 8 — active grant + zero capabilities must not claim `review`."""
    item = seed_item(world, status="calculated", item_id="item-c-zero")
    install_automatic_job(world, item)  # automatic, so only the gate can deny
    seed_consultant(world)  # no capability flags
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    resp = claim(client, item.id, "review")
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "calculated"
    assert actions(world, item.id) == []


def test_consultant_with_can_submit_can_claim_review(client, world, user_provider):
    """Row 9 — the legitimate review-stage claim still works with `can_submit`."""
    item = seed_item(world, status="calculated", item_id="item-c-submit")
    install_automatic_job(world, item)
    seed_consultant(world, can_submit=True)
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    resp = claim(client, item.id, "review")
    assert resp.status_code == 200, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_consultant_cannot_use_other_capability_for_review(
    client, world, user_provider
):
    """`can_extract`/`can_map` are not a substitute for `can_submit` (D2)."""
    item = seed_item(world, status="calculated", item_id="item-c-wrongflag")
    install_automatic_job(world, item)
    seed_consultant(world, can_extract=True, can_map=True, can_validate=True,
                    can_calculate=True)
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    resp = claim(client, item.id, "review")
    assert resp.status_code == 403, resp.text
    assert item_status(world, item.id) == "calculated"


def test_consultant_source_claim_requires_can_extract(client, world, user_provider):
    """Row 10 (S3) — the `source` alias requires the existing `can_extract`."""
    item = seed_item(world, status="pending", item_id="item-src-1")
    seed_consultant(world)  # zero capabilities
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    denied = claim(client, item.id, "source")
    assert denied.status_code == 403, denied.text
    assert item_status(world, item.id) == "pending"


def test_consultant_source_claim_allowed_with_can_extract(
    client, world, user_provider
):
    item = seed_item(world, status="pending", item_id="item-src-2")
    seed_consultant(world, can_extract=True)
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    ok = claim(client, item.id, "source")
    assert ok.status_code == 200, ok.text
    assert item_status(world, item.id) == "extracting"


def test_consultant_idor_cross_firm_denied(client, world, user_provider):
    """Row 15 — a second firm with no grant cannot claim the stage."""
    item = seed_item(world, status="calculated", item_id="item-idor")
    install_automatic_job(world, item)
    seed_consultant(world)  # firm-c1 holds the grant
    world.consultants.seed_profile("firm-c2", "u-c2", "C2", is_active=True)
    world.consultants.seed_firm_member("firm-c2", "u-c2", role="manager",
                                       is_active=True, can_submit=True)
    user_provider.set_user(consultant_user("u-c2", "u-c2@x"))
    resp = claim(client, item.id, "review")
    assert resp.status_code in (403, 404), resp.text
    assert item_status(world, item.id) == "calculated"


def test_org_member_stage_claim_behaviour_unchanged(client, world, user_provider):
    """P6-2-D10 — organisation members are unaffected by the consultant gate."""
    item = seed_item(world, status="calculated", item_id="item-member")
    install_automatic_job(world, item)
    user_provider.set_user(member_user("org-a", "m1", "m@test"))
    resp = claim(client, item.id, "review")
    assert resp.status_code == 200, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_internal_staff_stage_claim_behaviour_unchanged(client, world, user_provider):
    """Internal staff keep their existing stage-claim behaviour."""
    item = seed_item(world, status="calculated", item_id="item-staff")
    install_automatic_job(world, item)
    seed_staff(world, user="u-staff", perms={"can_process": True})
    user_provider.set_user(staff_user("u-staff"))
    resp = claim(client, item.id, "review")
    assert resp.status_code == 200, resp.text
    assert item_status(world, item.id) == "customer_review"


def test_reviewed_cannot_reach_customer_review(client, world, user_provider):
    """Row 11 — the P6-2B-4 protection remains intact."""
    item = seed_item(world, status="reviewed", item_id="item-reviewed")
    user_provider.set_user(member_user("org-a", "m1", "m@test"))
    resp = claim(client, item.id, "review")
    assert resp.status_code == 409, resp.text
    assert item_status(world, item.id) == "reviewed"


def test_denied_actions_do_not_create_success_audit(client, world, user_provider):
    """Row 21 — a denied approval writes no audit record for the item."""
    item = seed_item(world, status="calculated", item_id="item-audit")
    seed_commercial(world)
    seed_consultant(world, can_submit=True)
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    denied = approve(client, item.id)
    assert denied.status_code == 403, denied.text
    assert actions(world, item.id) == []
    # A successful consultant review DOES audit (unchanged behaviour).
    item2 = seed_item(world, status="calculated", item_id="item-audit-ok")
    seed_consultant(world, can_submit=True)
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    ok = client.post(f"{PROC}/items/{item2.id}/consultant-review",
                     json={"passed": True, "consultant_notes": "ok"})
    assert ok.status_code == 200, ok.text
    assert actions(world, item2.id)


def _origin(world, item_id):
    return asyncio.run(world.manual_extraction.get_item_origin(item_id))


def test_provenance_fields_unchanged_by_p6_2c_flows(client, world, user_provider):
    """Row 22 — processing origin / entity linkage is untouched by P6-2C."""
    item = seed_item(world, status="calculated", item_id="item-prov")
    install_automatic_job(world, item)
    seed_commercial(world)
    before = _origin(world, item.id)
    user_provider.set_user(org_owner_user("org-a", "o1", "o@test"))
    resp = approve(client, item.id)
    assert resp.status_code == 200, resp.text
    after = _origin(world, item.id)
    assert before == after
    stored = world.manual_extraction._items[item.id]
    assert getattr(stored, "processing_entity_id", None) in (None, "")
    assert item_status(world, item.id) == "approved"


def test_denied_stage_claim_leaves_provenance_untouched(client, world, user_provider):
    item = seed_item(world, status="calculated", item_id="item-prov-deny")
    install_automatic_job(world, item)
    seed_consultant(world)  # zero capabilities → denied
    before = _origin(world, item.id)
    user_provider.set_user(consultant_user("u-c1", "u-c1@x"))
    resp = claim(client, item.id, "review")
    assert resp.status_code == 403, resp.text
    assert _origin(world, item.id) == before


def test_s4_ops_and_pe_paths_cannot_bypass_stage_gating(client, world, user_provider):
    """S4 parity — PE entity route rejects review/validation stage claims."""
    item = seed_item(world, status="calculated", item_id="item-pe-stage")
    seed_staff(world, user="u-pe", perms={"can_process": True, "can_review": True},
               role_id="role-pe", entity_id="entity-1")
    user_provider.set_user(staff_user("u-pe", entity_id="entity-1"))
    resp = client.post(
        f"{OPS}/entities/entity-1/extraction/items/{item.id}/start",
        json={"stage": "review"},
    )
    assert resp.status_code in (401, 403, 404), resp.text
    assert item_status(world, item.id) == "calculated"
    # Internal ops surface requires can_review (parity already present).
    seed_staff(world, user="u-norev", perms={"can_process": True},
               role_id="role-op")
    user_provider.set_user(staff_user("u-norev"))
    resp2 = client.post(f"{OPS}/items/{item.id}/start", json={"stage": "review"})
    assert resp2.status_code == 403, resp2.text
    assert item_status(world, item.id) == "calculated"





