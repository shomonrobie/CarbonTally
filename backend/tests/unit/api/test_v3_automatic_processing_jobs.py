"""WS4 Gate 5 (task T7) — API positive/negative tests for the durable
automatic-processing job surface (``/api/v3/processing/jobs``).

Covers the design-regression row: job list/detail returns the typed
``automation`` block for the owning org; cross-org detail denied (403); PE staff
denied; confirm/retry/review authorization unchanged; the write-once automation
block survives the human confirm gate at the API boundary.

All fakes are in-memory; no database access.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from auth import AuthUser
from domain.audit import AuditEntry
from domain.automatic_processing import AutomaticProcessingJob

ORG_A = "org-a"
ORG_B = "org-b"


class MemoryProcessing:
    """In-memory ``DocumentProcessingRepository`` surface used by the API."""

    def __init__(self, jobs: Optional[list[AutomaticProcessingJob]] = None) -> None:
        self.jobs: dict[str, AutomaticProcessingJob] = {}
        for job in jobs or []:
            self.jobs[job.id] = job

    async def get(self, job_id: str) -> Optional[AutomaticProcessingJob]:
        return self.jobs.get(job_id)

    async def list_for_org(
        self,
        organization_id: str,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AutomaticProcessingJob]:
        rows = [
            j
            for j in self.jobs.values()
            if j.organization_id == organization_id
            and (status is None or j.status == status)
            and (stage is None or j.stage == stage)
        ]
        return rows[offset : offset + limit]

    async def count_by_stage(self, org_id: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for j in self.jobs.values():
            if j.organization_id == org_id:
                key = j.stage or "enqueued"
                out[key] = out.get(key, 0) + 1
        return out

    def _store(self, job: AutomaticProcessingJob) -> AutomaticProcessingJob:
        self.jobs[job.id] = job
        return job

    async def reenqueue(
        self,
        job_id: str,
        *,
        stage: str = "enqueued",
        reset_attempts: bool = True,
        updated_by: Optional[str] = None,
    ) -> Optional[AutomaticProcessingJob]:
        job = self.jobs.get(job_id)
        if job is None:
            return None
        import dataclasses

        self.last_updated_by = updated_by
        base = dataclasses.asdict(job)
        base.update(
            {
                "stage": stage,
                "status": "pending",
                "manual_review_reason": None,
                "last_error": None,
                "reprocess_count": job.reprocess_count + 1,
                # G6-C: authoritative human re-enqueue actor (mirrors repo).
                "updated_by": updated_by,
            }
        )
        # Automation block is never rewritten by human gates (write-once).
        return self._store(AutomaticProcessingJob(**base))

    async def complete_review(
        self,
        job_id: str,
        *,
        approved: bool,
        reviewer: str,
        rejection_reason: Optional[str] = None,
        customer_notes: Optional[str] = None,
    ) -> Optional[AutomaticProcessingJob]:
        job = self.jobs.get(job_id)
        if job is None:
            return None
        import dataclasses

        self.last_reviewer = reviewer
        base = dataclasses.asdict(job)
        base.update(
            {
                "stage": "completed" if approved else "blocked",
                "status": "completed" if approved else "manual_review",
                # G6-C: authoritative human review decision (mirrors repo).
                "customer_reviewed_by": reviewer,
                "customer_reviewed_at": datetime.now(timezone.utc),
                "customer_approved": approved,
                "customer_rejection_reason": rejection_reason,
                "customer_notes": customer_notes,
            }
        )
        return self._store(AutomaticProcessingJob(**base))

    async def sync_item_data(
        self,
        job_id: str,
        *,
        extracted_data: Optional[dict] = None,
        mapped_data: Optional[dict] = None,
    ) -> Optional[AutomaticProcessingJob]:
        """Mirror of the repository sync (G6-D): copy corrected data onto the
        job; automation/G6-A fields are never touched here."""
        job = self.jobs.get(job_id)
        if job is None:
            return None
        import dataclasses

        base = dataclasses.asdict(job)
        if extracted_data is not None:
            base["extracted_data"] = extracted_data
        if mapped_data is not None:
            base["mapped_data"] = mapped_data
        return self._store(AutomaticProcessingJob(**base))


def _job(**overrides: object) -> AutomaticProcessingJob:
    base = dict(
        id=str(uuid.uuid4()),
        organization_id=ORG_A,
        file_name="invoice.pdf",
        file_url="uploads/org-a/invoice.pdf",
        processing_type="utility",
        status="review",
        stage="review",
        source_item_id=None,
        pipeline_version="v3-auto-1.0",
        automation_provider="openai",
        automation_model="gpt-test",
        automation_model_version=None,
    )
    base.update(overrides)
    return AutomaticProcessingJob(**base)


def _pe_user() -> AuthUser:
    return AuthUser(
        user_id="pe-1",
        email="pe@carbontally.test",
        role="pe_manager",
        role_name="pe_manager",
        is_entity_staff=True,
    )


def _install_processing(world, jobs: list[AutomaticProcessingJob]) -> MemoryProcessing:
    mem = MemoryProcessing(jobs)
    world.processing = mem
    return mem


def test_detail_returns_automation_block_for_owning_org(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    job = _job()
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.get(f"/api/v3/processing/jobs/{job.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == job.id
    assert body["automation"] == {
        "provider": "openai",
        "model": "gpt-test",
        "model_version": None,
    }
    assert body["ai_extraction"] is None


def test_list_returns_jobs_with_automation_blocks(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    job_a = _job(automation_provider="openai", automation_model="gpt-test")
    _install_processing(world, [job_a, _job(id=str(uuid.uuid4()), organization_id=ORG_B)])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.get(f"/api/v3/processing/jobs?organization_id={ORG_A}")
    assert response.status_code == 200
    body = response.json()
    assert body["organization_id"] == ORG_A
    assert body["total"] == 1
    assert len(body["jobs"]) == 1
    assert body["jobs"][0]["automation"]["provider"] == "openai"


def test_detail_cross_org_denied(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    job = _job()
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_B, "user-b", "b@carbontally.test"))
    response = client.get(f"/api/v3/processing/jobs/{job.id}")
    assert response.status_code == 403


def test_list_cross_org_denied(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    _install_processing(world, [_job()])
    user_provider.set_user(member_user(ORG_B, "user-b", "b@carbontally.test"))
    response = client.get(f"/api/v3/processing/jobs?organization_id={ORG_A}")
    assert response.status_code == 403


def test_detail_pe_staff_denied(world, client, user_provider) -> None:
    job = _job()
    _install_processing(world, [job])
    user_provider.set_user(_pe_user())
    response = client.get(f"/api/v3/processing/jobs/{job.id}")
    assert response.status_code == 403


def test_detail_unauthenticated_denied(world, client, user_provider) -> None:
    job = _job()
    _install_processing(world, [job])
    user_provider.set_unauthenticated()
    response = client.get(f"/api/v3/processing/jobs/{job.id}")
    assert response.status_code == 401


def test_confirm_keeps_automation_block_and_org_boundary(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    job = _job(stage="blocked", status="manual_review")
    _install_processing(world, [job])
    # Owning org member confirms -> 200 and automation block survives the gate.
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/confirm",
        json={"stage": "enqueued"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == job.id
    assert response.json()["automation"]["provider"] == "openai"
    assert response.json()["automation"]["model"] == "gpt-test"
    # Cross-org member confirm -> denied (authorization unchanged).
    _install_processing(world, [_job(stage="blocked", status="manual_review")])
    job2 = next(iter(world.processing.jobs.values()))
    user_provider.set_user(member_user(ORG_B, "user-b", "b@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job2.id}/confirm",
        json={"stage": "enqueued"},
    )
    assert response.status_code == 403
    # PE staff confirm -> denied (PE boundary unchanged).
    _install_processing(world, [_job(stage="blocked", status="manual_review")])
    job3 = next(iter(world.processing.jobs.values()))
    user_provider.set_user(_pe_user())
    response = client.post(
        f"/api/v3/processing/jobs/{job3.id}/confirm",
        json={"stage": "enqueued"},
    )
    assert response.status_code == 403


def test_review_requires_org_admin(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user, org_owner_user

    job = _job()
    _install_processing(world, [job])
    # A plain org member is not an org admin -> review denied (unchanged).
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/review", json={"approved": True}
    )
    assert response.status_code == 403
    # Org owner (admin authority) may review -> automation block intact.
    _install_processing(world, [job])
    user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/review", json={"approved": True}
    )
    assert response.status_code == 200
    assert response.json()["automation"]["provider"] == "openai"



# ---------------------------------------------------------------------------
# WS4 Gate 6 (workstream W2 / gap G6-B) — human-after-automation audit
# attribution for the job-level human gates (confirm / retry / review).
# ---------------------------------------------------------------------------


def _entries_for(world, action: Optional[str] = None) -> list[AuditEntry]:
    rows = list(world.audit._entries)
    if action is not None:
        rows = [e for e in rows if e.action == action]
    return rows


def test_confirm_records_human_gate_audit(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    job = _job(
        stage="blocked", status="manual_review",
        automation_provider="openai", automation_model="gpt-test",
        automation_extracted_data={"activity": "Diesel", "quantity": 1250},
    )
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/confirm", json={"stage": "enqueued"}
    )
    assert response.status_code == 200
    rows = _entries_for(world, "automatic_processing:confirmed")
    assert len(rows) == 1
    ev = rows[0]
    assert ev.actor == "user-a"  # authenticated human, never automatic_pipeline
    assert ev.entity_type == "document_processing_queue"
    assert ev.entity_id == job.id
    assert ev.correlation_id == job.id
    cf = ev.changed_fields or {}
    assert cf.get("stage_from") == "blocked"
    assert cf.get("stage_to") == "enqueued"
    assert cf.get("status_to") == "pending"
    assert cf.get("gate") == "confirm"
    # Gate-5 provenance + G6-A preserved output unchanged by the human gate.
    stored = world.processing.jobs[job.id]
    assert stored.automation_provider == "openai"
    assert stored.automation_model == "gpt-test"
    assert stored.automation_extracted_data == {
        "activity": "Diesel", "quantity": 1250,
    }


def test_retry_records_human_gate_audit(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    job = _job(stage="failed", status="failed")
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.post(f"/api/v3/processing/jobs/{job.id}/retry")
    assert response.status_code == 200
    rows = _entries_for(world, "automatic_processing:retried")
    assert len(rows) == 1
    ev = rows[0]
    assert ev.actor == "user-a"
    assert ev.entity_id == job.id
    assert ev.correlation_id == job.id
    cf = ev.changed_fields or {}
    assert cf.get("stage_from") == "failed"
    assert cf.get("stage_to") == "enqueued"
    assert cf.get("gate") == "retry"


def test_review_approve_records_human_gate_audit(world, client, user_provider) -> None:
    from tests.unit.api.fakes import org_owner_user

    job = _job(stage="review", status="review")
    _install_processing(world, [job])
    user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/review",
        json={"approved": True, "customer_notes": "looks good"},
    )
    assert response.status_code == 200
    rows = _entries_for(world, "automatic_processing:approved")
    assert len(rows) == 1
    ev = rows[0]
    assert ev.actor == "owner-a"
    assert ev.entity_id == job.id
    assert ev.correlation_id == job.id
    cf = ev.changed_fields or {}
    assert cf.get("approved") is True
    assert cf.get("stage_from") == "review"
    assert cf.get("stage_to") == "completed"
    assert cf.get("customer_notes") == "looks good"


def test_review_reject_records_human_gate_audit(world, client, user_provider) -> None:
    from tests.unit.api.fakes import org_owner_user

    job = _job(stage="review", status="review")
    _install_processing(world, [job])
    user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/review",
        json={"approved": False, "rejection_reason": "quantity is wrong"},
    )
    assert response.status_code == 200
    rows = _entries_for(world, "automatic_processing:rejected")
    assert len(rows) == 1
    ev = rows[0]
    assert ev.actor == "owner-a"
    cf = ev.changed_fields or {}
    assert cf.get("approved") is False
    assert cf.get("stage_to") == "blocked"
    assert cf.get("rejection_reason") == "quantity is wrong"


def test_actor_comes_from_auth_context_not_client_field(
    world, client, user_provider,
) -> None:
    from tests.unit.api.fakes import member_user, org_owner_user

    job = _job(stage="blocked", status="manual_review")
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    # A client-supplied "actor" field must be ignored — actor comes from the
    # authenticated request context only.
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/confirm",
        json={"stage": "enqueued", "actor": "automatic_pipeline"},
    )
    assert response.status_code == 200
    rows = _entries_for(world, "automatic_processing:confirmed")
    assert len(rows) == 1
    assert rows[0].actor == "user-a"

    job2 = _job(stage="review", status="review")
    _install_processing(world, [job2])
    user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job2.id}/review",
        json={"approved": True, "actor": "some-intruder"},
    )
    assert response.status_code == 200
    rows = _entries_for(world, "automatic_processing:approved")
    assert len(rows) == 1
    assert rows[0].actor == "owner-a"


def test_machine_and_human_events_distinguishable_and_ordered(
    world, client, user_provider,
) -> None:
    from tests.unit.api.fakes import member_user

    job = _job(stage="blocked", status="manual_review")
    _install_processing(world, [job])
    # Seed the machine extraction event (actor automatic_pipeline) that precedes
    # the human gate.
    machine = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id=job.id,
        entity_type="document_processing_queue",
        entity_id=job.id,
        action="automatic_processing:extracted",
        actor="automatic_pipeline",
        occurred_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    world.audit._entries.append(machine)
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/confirm", json={"stage": "enqueued"}
    )
    assert response.status_code == 200
    machine_rows = _entries_for(world, "automatic_processing:extracted")
    human_rows = _entries_for(world, "automatic_processing:confirmed")
    assert len(machine_rows) == 1 and len(human_rows) == 1
    # Distinguishable: machine actor label vs authenticated human actor on the
    # same job/resource correlation.
    assert machine_rows[0].actor == "automatic_pipeline"
    assert human_rows[0].actor == "user-a"
    assert machine_rows[0].entity_id == human_rows[0].entity_id == job.id
    # Ordering: machine extraction happened first, human gate later.
    assert machine_rows[0].occurred_at < human_rows[0].occurred_at


def test_unauthorized_cross_scope_action_creates_no_human_event(
    world, client, user_provider,
) -> None:
    from tests.unit.api.fakes import member_user

    job = _job(stage="blocked", status="manual_review")
    _install_processing(world, [job])
    before = len(world.audit._entries)
    user_provider.set_user(member_user(ORG_B, "user-b", "b@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/confirm", json={"stage": "enqueued"}
    )
    assert response.status_code == 403
    assert len(world.audit._entries) == before  # no event for a denied action



# ---------------------------------------------------------------------------
# WS4 Gate 6 (workstream W3 / gap G6-C) — expose minimal human-after-automation
# attribution in the job payload (original machine output + authoritative
# human actors), distinct from the machine `automation` block.
# ---------------------------------------------------------------------------


def test_payload_exposes_original_vs_current_output(
    world, client, user_provider,
) -> None:
    from tests.unit.api.fakes import member_user

    original = {"activity": "Diesel", "quantity": 1250, "unit": "litres"}
    corrected = {"activity": "Natural gas", "quantity": 900, "unit": "kWh"}
    job = _job(
        stage="blocked", status="manual_review",
        automation_provider="openai", automation_model="gpt-test",
        automation_extracted_data=original,
        extracted_data=corrected,  # human-corrected current output
    )
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.get(f"/api/v3/processing/jobs/{job.id}")
    assert response.status_code == 200
    body = response.json()
    # Automated provenance is present and the original machine output is
    # distinguishable from the current (human-corrected) output.
    assert body["automation"] == {
        "provider": "openai", "model": "gpt-test", "model_version": None,
    }
    assert body["automation_extracted_data"] == original
    assert body["extracted_data"] == corrected
    assert body["automation_extracted_data"] != body["extracted_data"]
    # A separate, distinct human block exists (never mixed into `automation`).
    assert "human" in body
    assert "provider" not in body["human"]


def test_payload_human_actor_from_auth_context_not_client_field(
    world, client, user_provider,
) -> None:
    from tests.unit.api.fakes import member_user

    job = _job(stage="blocked", status="manual_review")
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    # Client-supplied actor/identity fields are ignored; the authoritative
    # updated_by value comes from the authenticated user only.
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/confirm",
        json={"stage": "enqueued", "actor": "automatic_pipeline", "created_by": "x"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["human"]["updated_by"] == "user-a"
    assert body["human"]["created_by"] is None  # no client-supplied value
    # Machine provenance and the G6-A preserved output (absent here) are not
    # fabricated by the human gate.
    assert body["automation"] == {
        "provider": "openai", "model": "gpt-test", "model_version": None,
    }


def test_payload_exposes_customer_review_attribution(
    world, client, user_provider,
) -> None:
    from tests.unit.api.fakes import org_owner_user

    job = _job(stage="review", status="review")
    _install_processing(world, [job])
    user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner@carbontally.test"))
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/review",
        json={"approved": True, "customer_notes": "verified"},
    )
    assert response.status_code == 200
    body = response.json()
    human = body["human"]
    assert human["customer_reviewed_by"] == "owner-a"
    assert human["customer_approved"] is True
    assert human["customer_reviewed_at"] is not None
    assert human["customer_notes"] == "verified"
    # The human reviewer is never represented inside machine provenance.
    assert body["automation"] == {
        "provider": "openai", "model": "gpt-test", "model_version": None,
    }
    assert human["updated_by"] is None  # no confirm/retry happened


def test_payload_legacy_job_remains_truthful(world, client, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    job = _job(
        automation_provider=None, automation_model=None,
        automation_model_version=None, automation_extracted_data=None,
    )
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    response = client.get(f"/api/v3/processing/jobs/{job.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["automation"] == {
        "provider": None, "model": None, "model_version": None,
    }
    assert body["automation_extracted_data"] is None
    # No human attribution is inferred for a job without human actions.
    assert body["human"] == {
        "created_by": None,
        "updated_by": None,
        "customer_reviewed_by": None,
        "customer_reviewed_at": None,
        "customer_approved": None,
        "customer_rejection_reason": None,
        "customer_notes": None,
    }



def test_confirm_extraction_correction_records_item_audit(
    world, client, user_provider,
) -> None:
    from dataclasses import replace

    from tests.unit.api.fakes import member_user

    machine_extractor = "00000000-0000-0000-0000-000000000000"
    item_id = str(uuid.uuid4())
    world.manual_extraction.seed_item(item_id, ORG_A, "invoice.pdf")
    item = world.manual_extraction._items[item_id]
    world.manual_extraction._items[item_id] = replace(
        item,
        status="extracted",
        extracted_by=machine_extractor,  # machine/system marker
        extracted_data={"activity": "Diesel", "quantity": 1250, "unit": "litres"},
    )
    original = {"activity": "Diesel", "quantity": 1250, "unit": "litres"}
    job = _job(
        stage="blocked", status="manual_review",
        source_item_id=item_id,
        automation_provider="openai", automation_model="gpt-test",
        automation_extracted_data=dict(original),
        extracted_data=dict(original),
    )
    _install_processing(world, [job])
    user_provider.set_user(member_user(ORG_A, "user-a", "a@carbontally.test"))
    corrected = {"activity": "Natural gas", "quantity": 900, "unit": "kWh"}
    response = client.post(
        f"/api/v3/processing/jobs/{job.id}/confirm",
        json={"stage": "enqueued", "extracted_data": corrected},
    )
    assert response.status_code == 200
    # Item-level extraction-correction audit (G6-D): authenticated actor,
    # machine-origin flag, correlation to the job.
    rows = [
        e
        for e in world.audit._entries
        if e.action == "automatic_processing:item_extraction_corrected"
    ]
    assert len(rows) == 1
    ev = rows[0]
    assert ev.actor == "user-a"
    assert ev.entity_type == "manual_extraction_item"
    assert ev.entity_id == item_id
    assert ev.correlation_id == job.id
    cf = ev.changed_fields or {}
    assert cf.get("corrected_machine_output") is True
    assert cf.get("previous_extracted_by") == machine_extractor
    assert "quantity" in (cf.get("changed_keys") or [])
    # Item now shows the human as the extractor with the corrected data.
    stored_item = world.manual_extraction._items[item_id]
    assert stored_item.extracted_by == "user-a"
    assert stored_item.extracted_data == corrected
    # G6-A original output and Gate-5 provenance survive on the job.
    stored = world.processing.jobs[job.id]
    assert stored.automation_extracted_data == original
    assert stored.automation_provider == "openai"
    assert stored.automation_model == "gpt-test"
    # The job-level human confirm event (G6-B) is still recorded.
    assert any(e.action == "automatic_processing:confirmed" for e in world.audit._entries)

