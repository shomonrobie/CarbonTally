"""CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A — the CLIENT-ACCESS CEILING on the
FINAL-approval and submitted-data-correction routes of the ORGANISATION plane.

Binding source (unchanged policy — no new decision is taken here):

* ``docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md`` §8.2/§8.3 (the
  client capability matrix and the P-6 "profile enforcement is SERVER-SIDE"
  rule), §16;
* ``docs/architecture/CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05.md`` §23.1
  **G-1** — ``approve_final`` / ``correct_submitted_data`` were classified by the
  ratified matrix but not yet ceiling-bound on the Organisation plane;
* ``docs/architecture/CT-CONSULTANT-CLIENT-PLANE-AUTH-CLOSURE-05A.md``.

Ratified ceilings asserted here (§8.2, unchanged):

    approve_final          ✗ OFF  ✗ READ_ONLY  ✓ COLLABORATIVE  ✗ MANAGED  ✗ RETAINED
    correct_submitted_data ✗ OFF  ✗ READ_ONLY  ✓ COLLABORATIVE  ✗ MANAGED  ✗ RETAINED

The ceiling is a **ceiling only** — it can never grant. Every test therefore also
pins the REGRESSION half: a direct customer (no consultant relationship), a
consultant principal operating its client, and CarbonTally internal staff are
unaffected, and a COLLABORATIVE client keeps exactly the behaviour it had.

Exercised over the real routers/guards (in-memory repositories), not helpers.
"""
from __future__ import annotations

import asyncio
import dataclasses
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

import auth
from api.client_access_guard import (
    CLIENT_OPERATION_DENIED_DETAIL,
    enforce_client_operation,
)
from domain.automatic_processing import AutomaticProcessingJob
from domain.billing import BillingPlan, Subscription
from domain.relationship_access import (
    OP_APPROVE_FINAL,
    OP_CORRECT_SUBMITTED_DATA,
    PROFILE_COLLABORATIVE,
    PROFILE_MANAGED,
    PROFILE_OFF,
    PROFILE_READ_ONLY,
    STATE_ACTIVE,
    STATE_RETAINED_READ_ONLY,
    profile_allows,
)
from services.billing import BillingService
from tests.unit.api.fakes import (
    consultant_user,
    member_user,
    org_owner_user,
    staff_user,
)

PROC = "/api/v3/processing"
MANUAL = "/api/v3/manual-extraction"
MACHINE = "00000000-0000-0000-0000-000000000000"

ORG_A = "org-a"
ORG_B = "org-b"
FIRM_ID = "firm-1"
CLIENT_A = "client-a"
CONSULTANT_ID = "u-cons"

BACKEND = Path(__file__).resolve().parents[3]



# ---------------------------------------------------------------------------
# Helpers — seeding, denial envelope, mutation probes
# ---------------------------------------------------------------------------
@pytest.fixture
def live_tenants(monkeypatch):
    """The in-memory harness has no organisation rows; treat them as active."""
    monkeypatch.setattr(auth, "is_organization_active", lambda organization_id: True)
    monkeypatch.setattr(
        "api.dependencies.is_organization_active", lambda organization_id: True
    )


def _seed_relationship(
    world,
    *,
    profile=PROFILE_MANAGED,
    status="active",
    retained=False,
    org=ORG_A,
    firm_flags=None,
):
    """Seed the consultant-client relationship that makes ``org`` a client org."""
    world.consultants.seed_profile(FIRM_ID, CONSULTANT_ID)
    world.consultants.seed_firm_member(
        FIRM_ID,
        CONSULTANT_ID,
        role="owner",
        can_manage_clients=True,
        can_approve=True,
        **(firm_flags or {}),
    )
    return world.consultants.seed_client(
        CLIENT_A,
        FIRM_ID,
        org,
        "ACME LTD",
        status=status,
        client_access_profile=profile,
        retained_read_only=retained,
    )


def _enable_manual_processing(world, org=ORG_A):
    """FIN-06 prerequisite for the manual-processing ACTION routes."""
    world.manual_processing.seed_entitlement(org)
    world.manual_processing.seed_grant("organization", org)


def _owner(org=ORG_A, uid="client-owner"):
    return org_owner_user(org, uid, f"{uid}@client.test")


def _member(org=ORG_A, uid="client-member"):
    return member_user(org, uid, f"{uid}@client.test")


def _deny_message(response):
    """The platform denial envelope carries the detail at ``error.message``."""
    return response.json()["error"]["message"]


def _seed_item(world, *, status="pending", org=ORG_A, item_id=None):
    iid = item_id or f"item-{uuid.uuid4().hex[:8]}"
    return world.manual_extraction.seed_item(iid, org, "doc.pdf", status=status)


def _item(world, item):
    return world.manual_extraction._items[item.id]


def _actions(world, item_id):
    return [
        e.action
        for e in world.audit._entries
        if getattr(e, "entity_id", None) == item_id
    ]



class _FakeProcessing:
    """Minimal durable-job repo over real ``AutomaticProcessingJob`` records."""

    def __init__(self, jobs=()):
        self.jobs = {j.id: j for j in jobs}

    async def get(self, job_id):
        return self.jobs.get(job_id)

    async def get_by_item(self, item_id):
        rows = [j for j in self.jobs.values() if j.source_item_id == item_id]
        return rows[0] if rows else None

    async def reenqueue(self, job_id, *, stage, reset_attempts=True, updated_by=None):
        job = self.jobs.get(job_id)
        if job is None:
            return None
        updated = dataclasses.replace(
            job, stage=stage, status="pending", updated_by=updated_by
        )
        self.jobs[job_id] = updated
        return updated

    async def sync_item_data(self, job_id, *, extracted_data=None, mapped_data=None):
        job = self.jobs.get(job_id)
        if job is None:
            return None
        updated = dataclasses.replace(
            job,
            automation_extracted_data=extracted_data
            or job.automation_extracted_data,
        )
        self.jobs[job_id] = updated
        return updated

    async def complete_review(
        self, job_id, *, approved, reviewer, rejection_reason=None,
        customer_notes=None,
    ):
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


def _install_job(world, item=None, *, stage="review", status="pending", job_id=None):
    """Attach a durable automatic-processing job (machine-output marker included).

    ``automation_extracted_data`` plus the machine ``extracted_by`` marker are what
    the P1 containment predicate reads to classify the item as AUTOMATIC, which is
    what exempts it from the manual CT-QC prerequisite — i.e. the item is in a
    state a real approval would legitimately act on.
    """
    job = AutomaticProcessingJob(
        id=job_id or f"job-{uuid.uuid4().hex[:8]}",
        organization_id=ORG_A,
        file_name="doc.pdf",
        file_url="http://example.test/doc.pdf",
        stage=stage,
        status=status,
        source_item_id=getattr(item, "id", None),
        automation_extracted_data={"items": []},
        created_by=CONSULTANT_ID,
    )
    world.processing = _FakeProcessing([job])
    if item is not None:
        current = world.manual_extraction._items[item.id]
        world.manual_extraction._items[item.id] = dataclasses.replace(
            current, extracted_by=MACHINE
        )
    return job


def _seed_commercial(world, org=ORG_A):
    """An active subscription + credits, so an ALLOWED approval would CHARGE.

    This is what makes "no mutation on denial" meaningful: the D37 credit
    consumption is the observable side effect an admitted approval produces.
    """
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
                features={"manual_processing": {"enabled": True}},
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
                idempotency_key="ct05a-sub",
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
            idempotency_key="ct05a-sub-grant",
        )
    )


def _ledger(world, org=ORG_A):
    return asyncio.run(world.billing_ledger.balance(org))


def _approve(client, item_id, *, approved=True, reason=None):
    return client.post(
        f"{PROC}/items/{item_id}/customer-review",
        json={
            "approved": approved,
            "rejection_reason": reason,
            "customer_notes": "ct05a",
        },
    )


def _review_job(client, job_id, *, approved=True, reason=None):
    return client.post(
        f"{PROC}/jobs/{job_id}/review",
        json={
            "approved": approved,
            "rejection_reason": reason,
            "customer_notes": "ct05a",
        },
    )


def _confirm_job(client, job_id, *, corrections=None):
    return client.post(
        f"{PROC}/jobs/{job_id}/confirm",
        json={"stage": "enqueued", **(corrections or {})},
    )


def _extract(client, item_id, payload=None):
    return client.post(
        f"{PROC}/items/{item_id}/extract",
        json={"extracted_data": payload or {"quantity": 10, "unit": "kWh"}},
    )


def _update_item(client, item_id, payload=None):
    return client.put(
        f"{MANUAL}/items/{item_id}",
        json={"extracted_data": payload or {"quantity": 10, "unit": "kWh"}},
    )




# ---------------------------------------------------------------------------
# The ratified ceiling (pure policy) — the two operations CT-05A binds
# ---------------------------------------------------------------------------
class TestRatifiedCeiling:
    @pytest.mark.parametrize(
        "operation",
        [OP_APPROVE_FINAL, OP_CORRECT_SUBMITTED_DATA],
    )
    def test_ceiling_matrix_for_the_two_bound_operations(self, operation):
        """§8.2 — the matrix this task applies, asserted exactly as ratified."""
        assert profile_allows(operation, PROFILE_OFF, STATE_ACTIVE) is False
        assert profile_allows(operation, PROFILE_READ_ONLY, STATE_ACTIVE) is False
        assert profile_allows(operation, PROFILE_COLLABORATIVE, STATE_ACTIVE) is True
        assert profile_allows(operation, PROFILE_MANAGED, STATE_ACTIVE) is False
        # Retained (post-relationship) state is read-only in EVERY profile.
        assert (
            profile_allows(operation, PROFILE_COLLABORATIVE, STATE_RETAINED_READ_ONLY)
            is False
        )

    def test_enforce_allows_collaborative_and_denies_managed(self, world):
        """The enforcement helper the routes call: ALLOW and DENY for one client."""
        from fastapi import HTTPException

        _seed_relationship(world, profile=PROFILE_COLLABORATIVE)
        asyncio.run(
            enforce_client_operation(_owner(), world.bundle(), ORG_A, OP_APPROVE_FINAL)
        )
        asyncio.run(
            enforce_client_operation(
                _owner(), world.bundle(), ORG_A, OP_CORRECT_SUBMITTED_DATA
            )
        )

        world.consultants._clients.clear()
        _seed_relationship(world, profile=PROFILE_MANAGED)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                enforce_client_operation(
                    _owner(), world.bundle(), ORG_A, OP_APPROVE_FINAL
                )
            )
        assert exc.value.status_code == 403
        assert exc.value.detail == CLIENT_OPERATION_DENIED_DETAIL

    def test_direct_customer_is_never_affected(self, world):
        """REGRESSION — no consultant relationship → the ceiling is a no-op."""
        asyncio.run(
            enforce_client_operation(_owner(), world.bundle(), ORG_A, OP_APPROVE_FINAL)
        )
        asyncio.run(
            enforce_client_operation(
                _owner(), world.bundle(), ORG_A, OP_CORRECT_SUBMITTED_DATA
            )
        )



# ---------------------------------------------------------------------------
# approve_final — POST /api/v3/processing/items/{id}/customer-review
# ---------------------------------------------------------------------------
class TestApproveFinalCeiling:
    """The FINAL-approval route for a consultant-managed client.

    The item is seeded exactly in the state a real, ADMITTED approval mutates
    (automatic item at ``calculated`` with an active subscription), so the DENY
    assertions also prove the absence of the D37 charge, the workflow transition
    and the ``processing.customer_review`` audit event.
    """

    def _arrange(self, world, *, profile, item_id=None, org=ORG_A):
        _seed_relationship(world, profile=profile, org=org)
        item = _seed_item(world, status="calculated", org=org, item_id=item_id)
        if org == ORG_A:
            _install_job(world, item)
        _seed_commercial(world, org)
        return item

    @pytest.mark.parametrize(
        "profile", [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF]
    )
    def test_client_owner_cannot_final_approve_unless_collaborative(
        self, client, world, user_provider, live_tenants, profile
    ):
        item = self._arrange(world, profile=profile)
        user_provider.set_user(_owner())
        response = _approve(client, item.id)
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL
        # NO mutation, NO false success, NO charge.
        assert _item(world, item).status == "calculated"
        assert "processing.customer_review" not in _actions(world, item.id)
        assert _ledger(world) == 500

    def test_retained_client_cannot_final_approve(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(
            world, profile=PROFILE_MANAGED, status="ended", retained=True
        )
        item = _seed_item(world, status="calculated")
        _install_job(world, item)
        _seed_commercial(world)
        user_provider.set_user(_owner())
        response = _approve(client, item.id)
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL
        assert _item(world, item).status == "calculated"
        assert _ledger(world) == 500

    def test_collaborative_client_owner_keeps_the_existing_allow(
        self, client, world, user_provider, live_tenants
    ):
        """ALLOW — COLLABORATIVE + authorised client role: unchanged behaviour."""
        item = self._arrange(world, profile=PROFILE_COLLABORATIVE)
        user_provider.set_user(_owner())
        response = _approve(client, item.id)
        assert response.status_code == 200, response.text
        assert _item(world, item).status == "approved"
        assert "processing.customer_review" in _actions(world, item.id)
        assert _ledger(world) == 499  # exactly one charge, at Customer Approval

    def test_collaborative_client_without_the_client_role_keeps_the_existing_deny(
        self, client, world, user_provider, live_tenants
    ):
        """The client-ROLE gate is preserved: the profile ceiling cannot grant it."""
        item = self._arrange(world, profile=PROFILE_COLLABORATIVE)
        user_provider.set_user(_member())
        response = _approve(client, item.id)
        assert response.status_code == 403
        assert _deny_message(response) != CLIENT_OPERATION_DENIED_DETAIL
        assert _item(world, item).status == "calculated"
        assert _ledger(world) == 500

    def test_direct_customer_is_unaffected(
        self, client, world, user_provider, live_tenants
    ):
        """REGRESSION — no consultant relationship → existing behaviour."""
        item = _seed_item(world, status="calculated")
        _install_job(world, item)
        _seed_commercial(world)
        user_provider.set_user(_owner())
        response = _approve(client, item.id)
        assert response.status_code == 200, response.text
        assert _item(world, item).status == "approved"

    def test_consultant_principal_keeps_its_operating_authority(
        self, client, world, user_provider, live_tenants
    ):
        """REGRESSION — a consultant approving a MANAGED client is unaffected."""
        item = self._arrange(world, profile=PROFILE_MANAGED)
        user_provider.set_user(consultant_user(CONSULTANT_ID, "cons@x.test"))
        response = _approve(client, item.id)
        assert response.status_code == 200, response.text
        assert _item(world, item).status == "approved"

    def test_internal_staff_is_unaffected(
        self, client, world, user_provider, live_tenants
    ):
        """REGRESSION — the ceiling never applies to CarbonTally staff."""
        item = self._arrange(world, profile=PROFILE_MANAGED)
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        response = _approve(client, item.id)
        assert response.status_code == 200, response.text
        assert _item(world, item).status == "approved"


# ---------------------------------------------------------------------------
# approve_final — POST /api/v3/processing/jobs/{job_id}/review
# (the automatic-processing mirror of the same FINAL decision)
# ---------------------------------------------------------------------------
class TestApproveFinalJobReviewCeiling:
    def _arrange(self, world, *, profile):
        _seed_relationship(world, profile=profile)
        item = _seed_item(world, status="calculated")
        job = _install_job(world, item, stage="review", status="pending")
        return item, job

    @pytest.mark.parametrize(
        "profile", [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF]
    )
    def test_client_owner_cannot_approve_a_job_unless_collaborative(
        self, client, world, user_provider, live_tenants, profile
    ):
        item, job = self._arrange(world, profile=profile)
        user_provider.set_user(_owner())
        response = _review_job(client, job.id)
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL
        assert world.processing.jobs[job.id].customer_approved in (None, False)
        assert _item(world, item).status == "calculated"

    def test_collaborative_client_owner_keeps_the_existing_allow(
        self, client, world, user_provider, live_tenants
    ):
        _item_, job = self._arrange(world, profile=PROFILE_COLLABORATIVE)
        user_provider.set_user(_owner())
        response = _review_job(client, job.id)
        assert response.status_code == 200, response.text
        assert world.processing.jobs[job.id].customer_approved is True

    def test_direct_customer_is_unaffected(
        self, client, world, user_provider, live_tenants
    ):
        item = _seed_item(world, status="calculated")
        job = _install_job(world, item, stage="review", status="pending")
        user_provider.set_user(_owner())
        response = _review_job(client, job.id)
        assert response.status_code == 200, response.text
        assert world.processing.jobs[job.id].customer_approved is True



# ---------------------------------------------------------------------------
# correct_submitted_data — POST /api/v3/processing/items/{id}/extract
# ---------------------------------------------------------------------------
class TestCorrectSubmittedDataCeiling:
    """The item workbench data-correction route ("correct the extracted fields").

    ``_enable_manual_processing`` satisfies the FIN-06 prerequisite, so the
    ceiling is the ONLY remaining difference for the DENY cases — and the
    COLLABORATIVE / direct-customer controls prove the same setup really does
    mutate the item when the profile admits the operation.
    """

    def _arrange(self, world, *, profile=None, item_id=None, firm_flags=None):
        if profile is not None:
            _seed_relationship(world, profile=profile, firm_flags=firm_flags)
        _enable_manual_processing(world)
        return _seed_item(world, status="pending", item_id=item_id)

    @pytest.mark.parametrize(
        "profile", [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF]
    )
    def test_client_cannot_correct_submitted_data_unless_collaborative(
        self, client, world, user_provider, live_tenants, profile
    ):
        item = self._arrange(world, profile=profile)
        user_provider.set_user(_owner())
        response = _extract(client, item.id)
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL
        # zero side effect: no data write, no status transition, no audit event
        assert not (_item(world, item).extracted_data or {})
        assert _item(world, item).status == "pending"
        assert "org_item_extraction:edited" not in _actions(world, item.id)

    def test_retained_client_cannot_correct_submitted_data(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(
            world, profile=PROFILE_MANAGED, status="ended", retained=True
        )
        _enable_manual_processing(world)
        item = _seed_item(world, status="pending")
        user_provider.set_user(_owner())
        response = _extract(client, item.id)
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL
        assert _item(world, item).status == "pending"

    def test_collaborative_client_keeps_the_existing_allow(
        self, client, world, user_provider, live_tenants
    ):
        item = self._arrange(world, profile=PROFILE_COLLABORATIVE)
        user_provider.set_user(_owner())
        response = _extract(client, item.id)
        assert response.status_code == 200, response.text
        assert _item(world, item).status == "extracted"

    def test_direct_customer_is_unaffected(
        self, client, world, user_provider, live_tenants
    ):
        """REGRESSION — no consultant relationship → existing behaviour."""
        item = self._arrange(world)
        user_provider.set_user(_owner())
        response = _extract(client, item.id)
        assert response.status_code == 200, response.text
        assert _item(world, item).status == "extracted"

    def test_consultant_principal_keeps_its_operating_authority(
        self, client, world, user_provider, live_tenants
    ):
        """REGRESSION — a consultant correcting a MANAGED client's item."""
        item = self._arrange(
            world, profile=PROFILE_MANAGED, firm_flags={"can_extract": True}
        )
        user_provider.set_user(consultant_user(CONSULTANT_ID, "cons@x.test"))
        response = _extract(client, item.id)
        assert response.status_code == 200, response.text
        assert _item(world, item).status == "extracted"


# ---------------------------------------------------------------------------
# correct_submitted_data — PUT /api/v3/manual-extraction/items/{id}
# ---------------------------------------------------------------------------
class TestManualExtractionUpdateCeiling:
    @pytest.mark.parametrize(
        "profile", [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF]
    )
    def test_client_cannot_rewrite_item_data_unless_collaborative(
        self, client, world, user_provider, live_tenants, profile
    ):
        _seed_relationship(world, profile=profile)
        _enable_manual_processing(world)
        item = _seed_item(world, status="pending")
        user_provider.set_user(_owner())
        response = _update_item(client, item.id)
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL
        assert not (_item(world, item).extracted_data or {})

    def test_collaborative_client_keeps_the_existing_allow(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(world, profile=PROFILE_COLLABORATIVE)
        _enable_manual_processing(world)
        item = _seed_item(world, status="pending")
        user_provider.set_user(_owner())
        response = _update_item(client, item.id)
        assert response.status_code == 200, response.text
        assert _item(world, item).extracted_data

    def test_direct_customer_is_unaffected(
        self, client, world, user_provider, live_tenants
    ):
        _enable_manual_processing(world)
        item = _seed_item(world, status="pending")
        user_provider.set_user(_owner())
        response = _update_item(client, item.id)
        assert response.status_code == 200, response.text



# ---------------------------------------------------------------------------
# correct_submitted_data — POST /api/v3/processing/jobs/{job_id}/confirm
# (the human rework gate: human corrections persisted onto the source item)
# ---------------------------------------------------------------------------
class TestConfirmJobCorrectionCeiling:
    def _arrange(self, world, *, profile=None):
        if profile is not None:
            _seed_relationship(world, profile=profile)
        item = _seed_item(world, status="pending")
        job = _install_job(world, item, stage="blocked", status="pending")
        return item, job

    @pytest.mark.parametrize(
        "profile", [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF]
    )
    def test_client_cannot_confirm_with_corrections_unless_collaborative(
        self, client, world, user_provider, live_tenants, profile
    ):
        item, job = self._arrange(world, profile=profile)
        user_provider.set_user(_owner())
        response = _confirm_job(
            client, job.id, corrections={"extracted_data": {"quantity": 42}}
        )
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL
        assert world.processing.jobs[job.id].stage == "blocked"
        assert not (_item(world, item).extracted_data or {})

    def test_collaborative_client_keeps_the_existing_allow(
        self, client, world, user_provider, live_tenants
    ):
        item, job = self._arrange(world, profile=PROFILE_COLLABORATIVE)
        user_provider.set_user(_owner())
        response = _confirm_job(
            client, job.id, corrections={"extracted_data": {"quantity": 42}}
        )
        assert response.status_code == 200, response.text
        assert world.processing.jobs[job.id].stage == "enqueued"

    def test_direct_customer_is_unaffected(
        self, client, world, user_provider, live_tenants
    ):
        item, job = self._arrange(world)
        user_provider.set_user(_owner())
        response = _confirm_job(
            client, job.id, corrections={"extracted_data": {"quantity": 42}}
        )
        assert response.status_code == 200, response.text


# ---------------------------------------------------------------------------
# Tenant isolation + identity separation + authentication
# ---------------------------------------------------------------------------
class TestIsolationAndAuthentication:
    def test_client_acting_on_a_foreign_organisation_is_denied_by_the_tenant_guard(
        self, client, world, user_provider, live_tenants
    ):
        """The ceiling ignores a foreign org; the existing tenant guard denies."""
        _seed_relationship(world, profile=PROFILE_COLLABORATIVE, org=ORG_A)
        foreign = _seed_item(world, status="calculated", org=ORG_B)
        user_provider.set_user(_owner())
        response = _approve(client, foreign.id)
        assert response.status_code == 403
        assert CLIENT_OPERATION_DENIED_DETAIL not in response.text
        assert _item(world, foreign).status == "calculated"

    def test_processing_entity_staff_are_denied_by_the_existing_guard(
        self, client, world, user_provider, live_tenants
    ):
        from tests.unit.api.fakes import entity_operator_user

        _seed_relationship(world, profile=PROFILE_MANAGED)
        item = _seed_item(world, status="calculated")
        user_provider.set_user(entity_operator_user("entity-1", "u-pe"))
        response = _approve(client, item.id)
        assert response.status_code == 403
        assert CLIENT_OPERATION_DENIED_DETAIL not in response.text

    def test_unauthenticated_final_approval_is_denied(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(world, profile=PROFILE_COLLABORATIVE)
        item = _seed_item(world, status="calculated")
        user_provider.set_unauthenticated()
        assert _approve(client, item.id).status_code == 401

    def test_unauthenticated_correction_is_denied(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(world, profile=PROFILE_COLLABORATIVE)
        _enable_manual_processing(world)
        item = _seed_item(world, status="pending")
        user_provider.set_unauthenticated()
        assert _extract(client, item.id).status_code == 401


# ---------------------------------------------------------------------------
# Coverage invariant — the ceiling must stay bound to every route CT-05A closed
# ---------------------------------------------------------------------------
#: (module, handler, operation, the mutation the denial must precede)
_BOUND_ROUTES = (
    (
        "api.v3_processing_workflow",
        "customer_review_item",
        "OP_APPROVE_FINAL",
        "repos.manual_extraction.customer_review(",
    ),
    (
        "api.v3_processing_workflow",
        "extract_item",
        "OP_CORRECT_SUBMITTED_DATA",
        "save_extracted_data(",
    ),
    (
        "api.v3_automatic_processing",
        "review_job",
        "OP_APPROVE_FINAL",
        "complete_review(",
    ),
    (
        "api.v3_automatic_processing",
        "confirm_job",
        "OP_CORRECT_SUBMITTED_DATA",
        "reenqueue(",
    ),
    (
        "api.v3_manual_extraction",
        "update_item",
        "OP_CORRECT_SUBMITTED_DATA",
        "repos.manual_extraction.update_item(",
    ),
)


class TestEnforcementCoverageInvariant:
    def test_routes_outside_the_closure_scope_stay_unbound(self):
        """No accidental spill-over onto the org-plane routes NOT in CT-05A scope."""
        import inspect

        from api import v3_processing_workflow as workflow

        for handler_name in ("map_item", "validate_item", "calculate_item", "start_item"):
            source = inspect.getsource(getattr(workflow, handler_name))
            assert "enforce_client_operation" not in source, handler_name

    @pytest.mark.parametrize(
        "module_name,handler_name,operation,mutation",
        _BOUND_ROUTES,
        ids=[f"{m.split('.')[-1]}.{h}" for m, h, _o, _x in _BOUND_ROUTES],
    )
    def test_route_binds_the_ceiling_before_its_mutation(
        self, module_name, handler_name, operation, mutation
    ):
        import importlib
        import inspect

        module = importlib.import_module(module_name)
        source = inspect.getsource(getattr(module, handler_name))
        assert "enforce_client_operation(" in source, handler_name
        assert operation in source, handler_name
        # Fail-closed ordering: authorization precedes the mutation.
        assert source.index("enforce_client_operation(") < source.index(mutation), (
            handler_name
        )

    def test_backend_has_no_second_client_authorization_system(self):
        """One ceiling, one policy module — never a parallel authorizer."""
        guard = (BACKEND / "api" / "client_access_guard.py").read_text()
        assert "domain.relationship_access" in guard
        assert "profile_allows" in guard
