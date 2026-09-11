"""P6-2A-R1 — B1 remediation tests: automation confirm / retry authorization.

Proves a Consultant cannot confirm or retry an automatic-processing job unless
the FULL P6-2A contract passes BEFORE any mutation:

    identity → active membership → active engagement → can_confirm_automation
    → server-derived resource scope → D38 conflict → action → mutation

Negative paths assert HTTP 403 AND that no underlying item/job mutation and no
Gate-6 audit side effect occurred (authorization-before-mutation).
"""
from __future__ import annotations

import asyncio
import uuid

from tests.unit.api.fakes import consultant_user
from tests.unit.api.test_v3_automatic_processing_jobs import _install_processing, _job

ORG_A = "org-a"
ORG_B = "org-b"
JOBS = "/api/v3/processing/jobs"


def _seed_consultant(
    world, *, user_id="u-c1", firm_id="firm-c1", org_id=ORG_A, is_active=True,
    engagement_status="active", confirm=True, client_id="cc-1",
):
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=is_active)
    world.consultants.seed_firm_member(
        firm_id, user_id, role="manager", is_active=is_active,
        can_manage_clients=True, can_confirm_automation=confirm,
    )
    world.consultants.seed_client(client_id, firm_id, org_id, "Client Org", status=engagement_status)
    return consultant_user(user_id, f"{user_id}@example.test")


def _seed_item(world, *, org_id=ORG_A, item_id=None, status="pending"):
    return world.manual_extraction.seed_item(
        item_id or f"item-{uuid.uuid4().hex[:8]}", org_id, "invoice.pdf", status=status
    )


def _install_job(world, *, job_id="job-r1", org_id=ORG_A, stage="blocked",
                 status="manual_review", source_item_id=None):
    job = _job(id=job_id, organization_id=org_id, stage=stage, status=status,
               source_item_id=source_item_id)
    _install_processing(world, [job])
    return job


def _state(world, job_id):
    return world.processing.jobs[job_id]


# Positive — full contract satisfied
def test_consultant_with_capability_can_confirm_job(client, world, user_provider) -> None:
    item = _seed_item(world)  # unassigned source item
    job = _install_job(world, source_item_id=item.id)
    user = _seed_consultant(world, confirm=True)
    user_provider.set_user(user)
    response = client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"})
    assert response.status_code == 200, response.text
    assert _state(world, job.id).stage == "enqueued"


def test_consultant_with_capability_can_retry_job(client, world, user_provider) -> None:
    job = _install_job(world, stage="failed", status="failed")
    user = _seed_consultant(world, confirm=True)
    user_provider.set_user(user)
    response = client.post(f"{JOBS}/{job.id}/retry")
    assert response.status_code == 200, response.text
    assert _state(world, job.id).stage == "enqueued"


# Negative capability — zero mutation on deny
def test_consultant_without_capability_denied_confirm_no_mutation(
    client, world, user_provider
) -> None:
    item = _seed_item(world)
    from dataclasses import replace

    item = replace(item, extracted_data={"supplier": "ORIGINAL", "quantity": "1", "unit": "kWh"})
    world.manual_extraction._items[item.id] = item
    job = _install_job(world, source_item_id=item.id)
    user = _seed_consultant(world, confirm=False)
    user_provider.set_user(user)
    response = client.post(
        f"{JOBS}/{job.id}/confirm",
        json={"stage": "enqueued", "extracted_data": {"supplier": "HACKED"}},
    )
    assert response.status_code == 403, response.text
    stored = world.manual_extraction._items[item.id]
    assert stored.extracted_data == {"supplier": "ORIGINAL", "quantity": "1", "unit": "kWh"}
    assert _state(world, job.id).stage == "blocked"
    assert _state(world, job.id).status == "manual_review"
    assert not [e for e in world.audit._entries if e.action == "automatic_processing:confirmed"]


def test_consultant_without_capability_denied_retry_no_mutation(
    client, world, user_provider
) -> None:
    job = _install_job(world, stage="failed", status="failed")
    reprocess_before = _state(world, job.id).reprocess_count
    user = _seed_consultant(world, confirm=False)
    user_provider.set_user(user)
    response = client.post(f"{JOBS}/{job.id}/retry")
    assert response.status_code == 403, response.text
    state = _state(world, job.id)
    assert state.stage == "failed" and state.status == "failed"
    assert state.reprocess_count == reprocess_before
    assert not [e for e in world.audit._entries if e.action == "automatic_processing:retried"]


# Negative engagement / membership / firm
def test_non_active_engagements_deny_job_actions(client, world, user_provider) -> None:
    for status in ("pending", "rejected", "suspended", "ended", "inactive"):
        job = _install_job(world, job_id=f"job-{status}")
        user = _seed_consultant(
            world, user_id=f"u-{status}", client_id=f"cc-{status}",
            engagement_status=status, confirm=True,
        )
        user_provider.set_user(user)
        response = client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"})
        assert response.status_code == 403, f"{status}: {response.text}"
        assert _state(world, job.id).stage == "blocked"


def test_inactive_membership_denied_confirm(client, world, user_provider) -> None:
    job = _install_job(world)
    user = _seed_consultant(world, is_active=False, confirm=True)
    user_provider.set_user(user)
    assert (
        client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"}).status_code
        == 403
    )


def test_other_firm_consultant_denied_confirm(client, world, user_provider) -> None:
    job = _install_job(world)  # job org = org-a
    user = _seed_consultant(world, firm_id="firm-other", org_id=ORG_B, confirm=True)
    user_provider.set_user(user)
    assert (
        client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"}).status_code
        == 403
    )


# Resource scope
def test_cross_client_job_denied(client, world, user_provider) -> None:
    job = _install_job(world, job_id="job-b", org_id=ORG_B)
    user = _seed_consultant(world, org_id=ORG_A, confirm=True)
    user_provider.set_user(user)
    assert (
        client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"}).status_code
        == 403
    )


def test_fabricated_job_id_404(client, world, user_provider) -> None:
    user = _seed_consultant(world, confirm=True)
    user_provider.set_user(user)
    response = client.post(f"{JOBS}/does-not-exist/confirm", json={"stage": "enqueued"})
    assert response.status_code == 404


def test_source_item_org_mismatch_denied(client, world, user_provider) -> None:
    """Job org (org-a) vs its source item org (org-b) → resource conflict DENY."""
    item_b = _seed_item(world, org_id=ORG_B, item_id="item-crossb")
    job = _install_job(world, source_item_id=item_b.id)  # job org = org-a
    user = _seed_consultant(world, org_id=ORG_A, confirm=True)
    user_provider.set_user(user)
    response = client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"})
    assert response.status_code == 403, response.text


# D38 conflict
def test_open_internal_assignment_denies_confirm(client, world, user_provider) -> None:
    item = _seed_item(world)
    job = _install_job(world, source_item_id=item.id)
    asyncio.run(
        world.manual_extraction.work_item_open(
            item_id=item.id, action="assign", assignee_kind="internal_staff",
            assigned_to="u-op", actor="u-mgr", actor_domain="internal_staff",
        )
    )
    user = _seed_consultant(world, confirm=True)
    user_provider.set_user(user)
    assert (
        client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"}).status_code
        == 403
    )


def test_open_pe_assignment_denies_confirm(client, world, user_provider) -> None:
    item = _seed_item(world)
    job = _install_job(world, source_item_id=item.id)
    asyncio.run(
        world.manual_extraction.work_item_open(
            item_id=item.id, action="assign", assignee_kind="processing_entity",
            processing_entity_id="entity-1", actor="u-mgr", actor_domain="internal_staff",
        )
    )
    user = _seed_consultant(world, confirm=True)
    user_provider.set_user(user)
    assert (
        client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"}).status_code
        == 403
    )


def test_batch_default_assignment_denies_confirm(client, world, user_provider) -> None:
    """Batch-level default (PE entity_id AND internal assigned_to) → DENY."""
    for carrier, kw in (("pe", {"entity_id": "entity-1"}), ("internal", None)):
        batch = asyncio.run(
            world.manual_extraction.create_batch(ORG_A, f"batch-{carrier}", **(kw or {}))
        )
        if carrier == "internal":
            asyncio.run(
                world.manual_extraction.update_batch(
                    batch.id, status="in_progress", assigned_to="u-op"
                )
            )
        item = world.manual_extraction.seed_item(
            f"item-{carrier}-{uuid.uuid4().hex[:4]}", ORG_A, "f.pdf", batch_id=batch.id
        )
        job = _install_job(world, job_id=f"job-batch-{carrier}", source_item_id=item.id)
        user = _seed_consultant(world, client_id=f"cc-{carrier}", confirm=True)
        user_provider.set_user(user)
        response = client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"})
        assert response.status_code == 403, f"{carrier}: {response.text}"


def test_unauthenticated_denied(client, world, user_provider) -> None:
    job = _install_job(world)
    user_provider.set_unauthenticated()
    response = client.post(f"{JOBS}/{job.id}/confirm", json={"stage": "enqueued"})
    assert response.status_code == 401

