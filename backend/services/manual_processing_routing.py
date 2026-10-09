"""Automatic extraction failure -> Manual Processing fallback routing.

The missing automatic workflow the forensic audit identified: when the durable
automatic-processing pipeline ends a job in a failure state, the job is routed
to the customer's CONFIGURED Processing Entity for human processing — but ONLY
when Manual Processing is truly effective for that customer.

The authoritative decision chain (all server-side):

    subscription entitlement          (billing_plans via the active subscription)
      -> Manual Processing eligibility
        -> Admin Manual Processing enablement   (FIN-06 governance, most-specific-wins)
          -> configured Processing Entity       (manual_processing_processors)
            -> automatic fallback routing        (this module)
              -> PE work item / assignment       (existing D38 work_item_assignments)

``effective = entitled AND enabled``. A stale governance grant can never bypass
the subscription requirement, and a subscription alone never activates routing.

This module writes only through EXISTING repositories:

* the canonical D38 ``work_item_assignments`` ledger (via
  ``repos.manual_extraction.work_item_open``) for the assignment, so the item
  appears in the existing PE workspace with no parallel task system;
* the existing append-only audit infrastructure (``repos.audit.record``) for
  every decision, so no parallel audit system exists.

It never invents a destination: the configured PE is used, or the failure is
preserved and surfaced explicitly (``no_processor_configured``). Round-robin,
workload balancing and legacy ``queue_settings.auto_assign_enabled`` are NOT
used (the forensic audit established that flag is legacy/unused for this
pipeline).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from core.logging import get_logger
from domain.audit import AuditEntry
from domain.manual_processing import (
    OUTCOME_NO_PROCESSOR,
    OUTCOME_ROUTABLE,
    EffectiveManualProcessingRouting,
    combine_entitlement,
    consultant_coverage_from_plan,
    entitlement_from_plan,
    resolve_routing,
    sponsored_entitlement,
    summarize_allocations,
)
from services.manual_processing_notifications import (
    notify_manual_processing_entry,
    notify_pe_item_assignment,
)

logger = get_logger(__name__)

#: The system actor recorded on an automatic routing decision. Mirrors the
#: automatic-processing worker's existing system actor (nil UUID): a machine
#: identity, never a user / PE / role / D38 principal.
SYSTEM_ACTOR = "00000000-0000-0000-0000-000000000000"

#: The D38 actor domain for a machine routing decision. The ledger CHECK
#: vocabulary is ('internal_staff','processing_entity'): the decision is made by
#: the CarbonTally platform ON the item, so 'internal_staff' is the truthful
#: domain. ``assigned_to`` stays NULL because the assignee is the Processing
#: Entity (the ledger's assignee-shape constraint enforces exactly one).
ROUTING_ACTOR_DOMAIN = "internal_staff"

#: Automatic-processing job stages that mean "the automatic path did not
#: complete" and are therefore the fallback boundary.
FAILURE_STAGES: tuple[str, ...] = ("blocked", "failed")


class ManualProcessingRouter:
    """Resolve and apply automatic extraction-failure routing."""

    def __init__(self, repos: Any) -> None:
        self._repos = repos

    # -- entitlement -------------------------------------------------------
    async def _plan_for_org(self, organization_id: str):
        """The plan of an organisation's ACTIVE subscription (None if none).

        Reuses the existing D37 commercial model: ``customer_subscriptions``
        (org-scoped) -> ``billing_plans`` (plan_code + plan_version). No second
        subscription source is introduced.
        """
        subscription = await self._repos.billing_subscriptions.get_active_for_org(
            organization_id
        )
        plan = None
        if subscription is not None and subscription.plan_code:
            if subscription.plan_version:
                plan = await self._repos.billing_plans.get_version(
                    subscription.plan_code, subscription.plan_version
                )
            if plan is None:
                plan = await self._repos.billing_plans.get_current_by_code(
                    subscription.plan_code
                )
        return plan

    async def direct_entitlement_for(self, organization_id: str):
        """The DIRECT (own-subscription) entitlement of one organisation.

        A missing/inactive subscription or an unknown plan means NOT entitled
        (fail closed).
        """
        return entitlement_from_plan(await self._plan_for_org(organization_id))

    async def sponsored_entitlement_for(self, organization_id: str):
        """The CONSULTANT-SPONSORED entitlement of one client organisation.

        CT-MP-SUB-003: eligibility is the existing ACTIVE ``consultant_clients``
        relationship; commercial coverage is the firm's OWN organisation
        subscription plan (via ``consultant_profiles.organization_id``). A firm
        whose plan has no ``features.consultant_manual_processing`` block grants
        nothing — a relationship alone is never an entitlement.

        When an organisation is linked to multiple firms, any firm that
        sponsors it grants the entitlement; otherwise the most informative
        non-entitled decision is returned (so a diagnostic can explain why).
        """
        grants = await self._repos.manual_processing.active_client_grants(
            organization_id
        )
        if not grants:
            return None
        best = None
        for grant in grants:
            firm_id = grant.get("consultant_id")
            if not firm_id:
                continue
            firm_org = await self._repos.manual_processing.firm_organization_id(
                firm_id
            )
            plan = await self._plan_for_org(firm_org) if firm_org else None
            coverage = consultant_coverage_from_plan(plan)
            allocation = await self._repos.manual_processing.get_active_allocation(
                consultant_id=firm_id, organization_id=organization_id
            )
            allocated_count = (
                await self._repos.manual_processing.count_active_allocations(firm_id)
            )
            decision = sponsored_entitlement(
                firm_id=firm_id,
                has_relationship=True,
                coverage=coverage,
                allocation_active=allocation is not None,
                allocated_count=allocated_count,
            )
            if decision.entitled:
                return decision
            if best is None:
                best = decision
        return best

    async def entitlement_for(self, organization_id: str):
        """The EFFECTIVE entitlement: DIRECT **OR** SPONSORED (CT-MP-SUB-003 §11).

        The two commercial paths are resolved independently and combined, so a
        client keeps operating if either path remains valid, and a client with
        both paths still yields ONE operational Manual Processing service.
        """
        direct = await self.direct_entitlement_for(organization_id)
        sponsored = await self.sponsored_entitlement_for(organization_id)
        return combine_entitlement(direct, sponsored)

    # -- consultant coverage state (Admin control plane) -------------------
    async def coverage_state_for_firm(self, firm_id: str) -> dict:
        """The purchased coverage + allocation state for one consultant firm.

        Read-only projection: it never mutates allocation state and never
        auto-creates/deletes allocations. Used by the Admin coverage view and by
        the client-entitlement diagnostic, so both show the same server answer.
        """
        firm_org = await self._repos.manual_processing.firm_organization_id(firm_id)
        plan = await self._plan_for_org(firm_org) if firm_org else None
        coverage = consultant_coverage_from_plan(plan)
        allocations = await self._repos.manual_processing.list_allocations(
            consultant_id=firm_id
        )
        active = [a for a in allocations if a.state == "active"]
        usage = summarize_allocations(coverage, len(active))
        eligible = await self._repos.manual_processing.eligible_clients(firm_id)
        allocated_orgs = {a.organization_id for a in active}
        return {
            "firm_id": firm_id,
            "firm_organization_id": firm_org,
            "enabled": coverage.enabled,
            "mode": coverage.mode,
            "capacity": usage.capacity,
            "allocated": usage.allocated,
            "available": usage.available,
            "over_allocated": usage.over_allocated,
            "plan_code": coverage.plan_code,
            "plan_version": coverage.plan_version,
            "eligible_clients": [e["organization_id"] for e in eligible],
            "unallocated_eligible_clients": [
                e["organization_id"]
                for e in eligible
                if e["organization_id"] not in allocated_orgs
            ],
            "allocations": [
                {
                    "id": a.id,
                    "organization_id": a.organization_id,
                    "consultant_client_id": a.consultant_client_id,
                    "state": a.state,
                    "reason": a.reason,
                    "allocated_at": a.allocated_at,
                    "released_at": a.released_at,
                }
                for a in allocations
            ],
        }



    # -- combined decision -------------------------------------------------
    async def resolve(self, organization_id: str) -> EffectiveManualProcessingRouting:
        """The complete Manual Processing decision for one organisation.

        Also used by the Admin ``/state`` control-plane endpoint, so the answer
        the Admin UI shows is the same server-side answer routing uses.
        """
        context = await self._repos.manual_processing.org_context_for_organization(
            organization_id
        )
        entitlement = await self.entitlement_for(organization_id)
        governance = await self._repos.manual_processing.effective_for_context(context)
        processor = await self._repos.manual_processing.resolve_processor_for_context(
            context
        )
        return resolve_routing(entitlement, governance, processor)

    # -- the fallback ------------------------------------------------------
    async def route_failed_job(self, job: Any) -> dict:
        """Route one failed/blocked automatic job to its configured PE (idempotent).

        Idempotent by construction: when the item's single OPEN D38 assignment is
        already the configured Processing Entity, the call is a no-op — so a
        worker retry, a re-queue, a repeated failure observation or a worker
        restart can never create a second assignment. Never raises: routing is
        best-effort and must not disturb the worker's failure handling.
        """
        organization_id = str(getattr(job, "organization_id", "") or "")
        job_id = str(getattr(job, "id", "") or "")
        failure_stage = str(getattr(job, "stage", "") or "")
        failure_reason = (
            getattr(job, "manual_review_reason", None)
            or getattr(job, "last_error", None)
            or "automatic processing did not complete"
        )
        try:
            decision = await self.resolve(organization_id)
        except Exception:  # noqa: BLE001 — routing must never break the worker
            logger.exception(
                "manual-processing routing decision failed for job %s", job_id
            )
            return {"routed": False, "reason": "routing_error", "job_id": job_id}

        base = {
            "job_id": job_id,
            "organization_id": organization_id,
            "outcome": decision.outcome,
            "entitled": decision.entitled,
            "enabled": decision.enabled,
            "configured": decision.configured,
        }

        if decision.outcome != OUTCOME_ROUTABLE:
            await self._audit_skip(
                job_id=job_id,
                organization_id=organization_id,
                failure_stage=failure_stage,
                failure_reason=failure_reason,
                decision=decision,
            )
            return {"routed": False, **base, "reason": decision.outcome}

        item_id = getattr(job, "source_item_id", None)
        if not item_id:
            await self._audit_skip(
                job_id=job_id,
                organization_id=organization_id,
                failure_stage=failure_stage,
                failure_reason=failure_reason,
                decision=decision,
                extra={"config_error": "job has no source item"},
            )
            return {"routed": False, **base, "reason": "no_source_item"}

        processor_entity_id = decision.processing_entity_id
        entity = await self._repos.entities.get(processor_entity_id)
        if entity is None or str(getattr(entity, "status", "")) != "active":
            # The configuration points at a missing/inactive entity: surface an
            # explicit configuration error rather than silently doing nothing.
            await self._audit_skip(
                job_id=job_id,
                organization_id=organization_id,
                failure_stage=failure_stage,
                failure_reason=failure_reason,
                decision=decision,
                item_id=str(item_id),
                extra={"config_error": "configured processing entity is not active"},
            )
            return {
                "routed": False,
                **base,
                "reason": "processor_not_active",
                "processing_entity_id": processor_entity_id,
            }

        current = await self._repos.manual_extraction.work_item_current(str(item_id))
        if (
            current is not None
            and current.get("assignee_kind") == "processing_entity"
            and str(current.get("processing_entity_id")) == str(processor_entity_id)
        ):
            # Idempotent: the configured entity already holds the open assignment.
            # N1 (PO-authorised): the PE staff notification is (re)attempted here
            # so a worker retry heals a previously failed delivery. The event key
            # carries the OPEN assignment-row identity, so a repeat can never
            # duplicate the notification.
            await notify_pe_item_assignment(
                self._repos,
                item_id=str(item_id),
                entity_id=processor_entity_id,
                assignment_id=(current or {}).get("id"),
                actor_domain=ROUTING_ACTOR_DOMAIN,
            )
            return {
                "routed": True,
                "idempotent": True,
                **base,
                "item_id": str(item_id),
                "processing_entity_id": processor_entity_id,
            }

        # CT-MP-SUB-003 §17 / PO spec: an existing OPEN HUMAN (internal_staff)
        # assignment must NOT be silently superseded merely because automatic
        # fallback became eligible. Preserve it and record the routing conflict.
        if current is not None and current.get("assignee_kind") == "internal_staff":
            await self._audit_skip(
                job_id=job_id,
                organization_id=organization_id,
                failure_stage=failure_stage,
                failure_reason=failure_reason,
                decision=decision,
                item_id=str(item_id),
                extra={"routing_conflict": "existing_human_assignment_preserved"},
            )
            return {
                "routed": False,
                **base,
                "reason": "human_assignment_preserved",
                "item_id": str(item_id),
            }


        routed_reason = (
            f"automatic processing fallback ({failure_stage or 'failure'}): "
            f"{str(failure_reason)[:300]}"
        )
        routed_assignment = await self._repos.manual_extraction.work_item_open(
            item_id=str(item_id),
            action="assign",
            assignee_kind="processing_entity",
            assigned_to=None,
            processing_entity_id=processor_entity_id,
            actor=SYSTEM_ACTOR,
            actor_domain=ROUTING_ACTOR_DOMAIN,
            reason=routed_reason,
            close_action="superseded",
        )
        await self._audit(
            entity_type="manual_extraction_item",
            entity_id=str(item_id),
            action="manual_processing:auto_routed",
            actor=SYSTEM_ACTOR,
            changed_fields={
                "job_id": job_id,
                "organization_id": organization_id,
                "failure_stage": failure_stage,
                "failure_reason": str(failure_reason)[:300],
                "processing_entity_id": processor_entity_id,
                "processor_scope_type": decision.processor_scope_type,
                "processor_scope_id": decision.processor_scope_id,
                "entitlement_source": decision.entitlement_source,
                "plan_code": decision.plan_code,
                "plan_version": decision.plan_version,
                "governance_source_level": decision.governance_source_level,
                "governance_scope_type": decision.governance_scope_type,
                "governance_scope_id": decision.governance_scope_id,
            },
        )
        # N1 (PO-authorised) — notify the assigned Processing Entity's active
        # staff. The D38 assignment above is already committed and remains
        # authoritative; a notification failure is logged and can never reverse
        # or invalidate it.
        await notify_pe_item_assignment(
            self._repos,
            item_id=str(item_id),
            entity_id=processor_entity_id,
            assignment_id=(routed_assignment or {}).get("id"),
            actor_domain=ROUTING_ACTOR_DOMAIN,
        )
        # N3 (PO-authorised) — the item has now ENTERED Manual Processing, so the
        # responsible consultant for the affected client is notified (single
        # server-derived recipient; fail-safe + audited when not determinable).
        await notify_manual_processing_entry(
            self._repos,
            organization_id=organization_id,
            item_id=str(item_id),
        )
        return {
            "routed": True,
            "idempotent": False,
            **base,
            "item_id": str(item_id),
            "processing_entity_id": processor_entity_id,
        }

    # -- audit helpers -----------------------------------------------------
    async def _audit_skip(
        self,
        *,
        job_id: str,
        organization_id: str,
        failure_stage: str,
        failure_reason: Any,
        decision: EffectiveManualProcessingRouting,
        item_id: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> None:
        action = (
            "manual_processing:auto_route_blocked_no_processor"
            if decision.outcome == OUTCOME_NO_PROCESSOR
            else "manual_processing:auto_route_denied"
        )
        changed = {
            "job_id": job_id,
            "organization_id": organization_id,
            "failure_stage": failure_stage,
            "failure_reason": str(failure_reason)[:300],
            "outcome": decision.outcome,
            "entitled": decision.entitled,
            "enabled": decision.enabled,
            "entitlement_source": decision.entitlement_source,
            "plan_code": decision.plan_code,
            "plan_version": decision.plan_version,
            "governance_source_level": decision.governance_source_level,
            "governance_scope_type": decision.governance_scope_type,
            "governance_scope_id": decision.governance_scope_id,
        }
        if extra:
            changed.update(extra)
        await self._audit(
            entity_type=(
                "manual_extraction_item" if item_id else "automatic_processing_job"
            ),
            entity_id=str(item_id or job_id),
            action=action,
            actor=SYSTEM_ACTOR,
            changed_fields=changed,
        )

    async def _audit(
        self,
        *,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: str,
        changed_fields: dict,
    ) -> None:
        """Record a routing decision via the EXISTING append-only audit ledger."""
        try:
            await self._repos.audit.record(
                AuditEntry(
                    id=str(uuid.uuid4()),
                    correlation_id=entity_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    action=action,
                    actor=actor,
                    occurred_at=datetime.now(timezone.utc),
                    changed_fields=changed_fields,
                    ip_address=None,
                )
            )
        except Exception:  # noqa: BLE001 — audit must never break the worker
            logger.exception("manual-processing routing audit failed (%s)", action)
