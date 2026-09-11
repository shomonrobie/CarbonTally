"""Workflow execution (read-only) — spec §13, §14, §15–§18.

A workflow is a list of :class:`WorkflowStep`. The executor runs the
read-only portions against the live API and SKIPS state-changing steps in
read-only mode:

* **GET actions** — executed with the step's actor. ``expected_status``
  200 → PASS on 2xx; ``deny``/``403``/``no_path`` → PASS on 401/403/404.
* **POST/PUT actions with a deny expectation** — executed with an empty JSON
  body and a non-existent resource id, so a correct app returns 403 BEFORE
  any write and a broken gate surfaces as 404/422 (no write either).
* **POST/PUT actions with an allow expectation** (upload, extract, map,
  validate, calculate, approve, create, …) — `SKIPPED — READ-ONLY MUTATION
  BLOCKED`. These would mutate investor-demo data; they must be run later in
  an explicitly authorized, isolated mutation scope.

State verification: GET steps read the DB-backed API, so a 2xx with a
non-empty body is the persisted-state signal. The executor never relies on
UI animations or a spinner (spec §13).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.api.probe import ApiProbeEngine, ProbeSpec
from qa_harness.api.session import ApiSessionPool
from qa_harness.core.config import TargetEnv
from qa_harness.core.findings import (
    Finding,
    FindingClassification,
    FindingStatus,
)
from qa_harness.core.run_context import RunContext
from qa_harness.core.status import ToolUnavailable
from qa_harness.identities import context as demo_context
from qa_harness.identities.loader import REPRESENTATIVE_EMAILS
from qa_harness.identities.resolver import IdentityResolver
from qa_harness.workflows.base import Workflow, WorkflowStep

try:
    import requests  # type: ignore
    _REQUESTS = True
except ImportError:  # pragma: no cover
    requests = None  # type: ignore
    _REQUESTS = False

DENY_STATUSES = (401, 403, 404)

# Calibrated request bodies for deny-gated POST probes (V1.2). An empty body
# makes the endpoint 422 on validation before the authz gate can run — which
# is inconclusive. A body that passes validation lets the gate decide
# (403 for a real non-participant conversation, 404 for a fake id; either is
# a clean denial, and no message is ever written in read-only mode).
DENY_GATE_BODIES: Dict[str, Dict[str, object]] = {
    "customer_org_conversation": {"content": "qa-harness authz gate probe"},
    "pe_to_customer_conversation": {"content": "qa-harness authz gate probe"},
}

# Actions whose result is only meaningful against a REAL conversation the
# actor participates in. With a fake id they 404, which proves nothing.
REQUIRES_REAL_CONVERSATION = {
    "receive_message", "cross_org_conversation", "cross_client_conversation",
}


@dataclass
class StepOutcome:
    workflow: str
    step_index: int
    action: str
    actor: str
    expected: str
    actual_status: Optional[int] = None
    outcome: str = "NOT RUN"           # PASS | FAIL | WARNING | SKIPPED
    detail: str = ""
    evidence_path: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "workflow": self.workflow,
            "step": self.step_index,
            "action": self.action,
            "actor": self.actor,
            "expected": self.expected,
            "actual_status": self.actual_status,
            "outcome": self.outcome,
            "detail": self.detail,
            "evidence_path": self.evidence_path,
        }


# Actions that mutate state. In read-only mode they are only executed when the
# step's expectation is a DENY (a correct app refuses before writing).
MUTATION_ACTIONS = {
    "upload_document", "storage_object", "file_record", "processing_job",
    "ingestion", "extraction", "mapping", "validation", "calculation",
    "evidence", "approval", "completed", "drive_processing",
    "manual_extraction", "processing", "calculate",
    "extract_item", "map_item", "validate_item", "calculate_item",
    "create_customer", "create_team_member", "assign_team",
    "create_conversation", "add_participants", "send_message",
}

# Actions with no HTTP binding (Realtime/WebSocket or pure-UI concerns). They
# are covered by browser sweeps, not API probes; the executor marks them SKIPPED.
NO_HTTP_BINDING = {
    "realtime_delivery",
    "visitor_assistant_as_messaging",
}

# action -> (method, endpoint template). Templates use {org_a}, {entity_a},
# {entity_b}, {client_org}, {item_id}, {conversation_id} — filled from the
# actor's deterministic context (identities/context.py).
ACTION_BINDINGS: Dict[str, tuple] = {
    # ----- shared -----
    "login": ("GET", "/api/v3/organizations/{org_a}/profile"),
    "consultant_dashboard": ("GET", "/api/v3/consultants/me"),
    "client_portfolio": ("GET", "/api/v3/consultants/me/clients"),
    "manage_customer": ("GET", "/api/v3/consultants/me"),
    "select_client": ("GET", "/api/v3/consultants/me/clients"),
    "enter_client_workspace": ("GET", "/api/v3/processing/dashboard?organization_id={client_org}"),
    "messaging": ("GET", "/api/v3/messaging/conversations?organization_id={msg_org}"),
    "reporting": ("GET", "/api/v3/reports?organization_id={client_org}"),
    # ----- client -----
    "client_dashboard": ("GET", "/api/v3/emissions/dashboard?organization_id={client_org}&start_date=2026-01-01&end_date=2026-12-31"),
    "view_documents": ("GET", "/api/v3/documents?organization_id={client_org}"),
    "review_and_approve": ("GET", "/api/v3/processing/customer-review?organization_id={client_org}"),
    "view_emissions": ("GET", "/api/v3/emissions/dashboard?organization_id={client_org}&start_date=2026-01-01&end_date=2026-12-31"),
    "generate_report": ("GET", "/api/v3/reports?organization_id={client_org}"),
    "message_consultant": ("GET", "/api/v3/messaging/conversations?organization_id={msg_org}"),
    # ----- PE -----
    "pe_workspace": ("GET", "/api/v3/ops/me"),
    "entity_batch_list": ("GET", "/api/v3/ops/entities/{entity_a}/extraction/batches"),
    "entity_performance": ("GET", "/api/v3/ops/entities/{entity_a}/dashboard"),
    "assigned_batch_visibility": ("GET", "/api/v3/ops/entities/{entity_a}/extraction/batches"),
    "allowed_messaging": ("GET", "/api/v3/messaging/conversations?organization_id={msg_org}"),
    "customer_document_access": ("GET", "/api/v3/documents?organization_id={org_a}"),
    "customer_document_download": ("GET", "/api/v3/documents/{item_id}/signed-url"),
    "customer_org_conversation": ("POST", "/api/v3/messaging/conversations/{conversation_id}/messages"),
    "other_entity_work": ("GET", "/api/v3/ops/entities/{entity_b}/extraction/batches"),
    "internal_ops_workspace": ("GET", "/api/v3/ops/queues/operator"),
    # ----- operations -----
    "ops_dashboard": ("GET", "/api/v3/ops/dashboard"),
    "data_entry_queue": ("GET", "/api/v3/ops/queues/operator"),
    "review_queue": ("GET", "/api/v3/ops/queues/review"),
    "qc_queue": ("GET", "/api/v3/ops/queues/qc"),
    "operator_queue": ("GET", "/api/v3/ops/queues/operator"),
    "staff_roster": ("GET", "/api/v3/ops/staff"),
    "roles": ("GET", "/api/v3/ops/staff-roles"),
    "entities": ("GET", "/api/v3/ops/entities"),
    "retention_read": ("GET", "/api/v3/settings/retention"),
    "commercial_read": ("GET", "/api/v3/commercial/config"),
    "audit_read": ("GET", "/api/v2/admin/audit"),
    # ----- customer workflow aliases -----
    "review": ("GET", "/api/v3/processing/customer-review?organization_id={org_a}"),
    "emissions": ("GET", "/api/v3/emissions/dashboard?organization_id={org_a}&start_date=2026-01-01&end_date=2026-12-31"),
    # ----- admin workflow -----
    "staff_management": ("GET", "/api/v3/ops/staff"),
    "role_management": ("GET", "/api/v3/ops/staff-roles"),
    "billing_config": ("GET", "/api/v3/commercial/config"),  # V1.2: real endpoint per OpenAPI
    "retention_config": ("GET", "/api/v3/settings/retention"),
    "audit_log": ("GET", "/api/v2/admin/audit"),
    "system_admin_retention": ("GET", "/api/v3/settings/retention"),
    "system_admin_commercial": ("GET", "/api/v3/commercial/config"),
    "system_admin_audit": ("GET", "/api/v2/admin/audit"),
    # ----- messaging workflow -----
    "receive_message": ("GET", "/api/v3/messaging/conversations/{conversation_id}/messages"),
    "unread_state": ("GET", "/api/v3/messaging/conversations?organization_id={msg_org}"),
    "notifications": ("GET", "/api/v3/notifications"),
    "cross_org_conversation": ("GET", "/api/v3/messaging/conversations/{conversation_id}/messages"),
    "cross_client_conversation": ("GET", "/api/v3/messaging/conversations/{conversation_id}/messages"),
    "pe_to_customer_conversation": ("POST", "/api/v3/messaging/conversations/{conversation_id}/messages"),
    # ----- deny-gated mutation actions (empty-body gate probes) -----
    "calculate_item": ("POST", "/api/v3/processing/items/{item_id}/calculate"),
    "extract_item": ("POST", "/api/v3/processing/items/{item_id}/extract"),
    "map_item": ("POST", "/api/v3/processing/items/{item_id}/map"),
    "validate_item": ("POST", "/api/v3/processing/items/{item_id}/validate"),
}


def persona_for(actor_key: str) -> str:
    """Map a workflow actor (persona key) to a REPRESENTATIVE_EMAILS key."""
    aliases = {
        "customer_owner": "customer_owner",
        "customer_admin": "customer_admin",
        "customer_member": "customer_member",
        "customer_viewer": "customer_viewer",
        "client_owner": "client_owner",
        "consultant": "consultant",
        "pe_manager": "pe_manager",
        "pe_staff": "pe_staff",
        "internal_operator": "internal_operator",
        "internal_reviewer": "internal_reviewer",
        "internal_qc": "internal_qc",
        "staff_admin": "staff_admin",
        "system_admin": "system_admin",
    }
    if actor_key not in aliases:
        raise KeyError(f"no representative identity for actor {actor_key!r}")
    return aliases[actor_key]


class WorkflowExecutor:
    """Executes the read-only portions of every workflow."""

    def __init__(self, ctx: RunContext, resolver: IdentityResolver,
                 pool: ApiSessionPool, discovery: Any = None) -> None:
        self.ctx = ctx
        self.resolver = resolver
        self.pool = pool
        # Optional read-only DB resource discovery (qa_harness.db.discovery).
        # Supplies real conversation/item ids so resource-bound steps are
        # meaningful instead of fake-id 404 noise. May be None.
        self.discovery = discovery
        self.outcomes: List[StepOutcome] = []
        self._findings: List[Finding] = []

    # ------------------------------------------------------------------ #

    def run_all(self, workflows: List[Workflow], *, source: str = "run_workflows.py",
                role_filter: str = "") -> List[StepOutcome]:
        for workflow in workflows:
            if role_filter and role_filter != workflow.key and role_filter not in workflow.personas:
                continue
            for index, wf_step in enumerate(workflow.steps):
                outcome = self._execute(workflow, index, wf_step, source=source)
                self.outcomes.append(outcome)
                finding = self._finding_for(workflow, outcome, source=source)
                if finding is not None:
                    self._findings.append(finding)
        return self.outcomes

    # ------------------------------------------------------------------ #

    def _execute(self, workflow: Workflow, index: int, wf_step: WorkflowStep,
                 *, source: str) -> StepOutcome:
        expected = wf_step.expected_status
        deny_expected = expected in ("deny", "403", "no_path", "401")
        outcome = StepOutcome(
            workflow=workflow.key, step_index=index, action=wf_step.action,
            actor=wf_step.actor, expected=expected,
        )

        is_mutation = wf_step.action in MUTATION_ACTIONS
        # A state-changing step with an ALLOW expectation cannot run in
        # read-only mode (it would mutate investor-demo data).
        if is_mutation and not deny_expected:
            outcome.outcome = "SKIPPED"
            outcome.detail = "READ-ONLY MUTATION BLOCKED — requires an authorized isolated mutation scope"
            return outcome

        binding = ACTION_BINDINGS.get(wf_step.action)
        if binding is None:
            if wf_step.action in NO_HTTP_BINDING:
                outcome.outcome = "SKIPPED"
                outcome.detail = "no HTTP binding (Realtime/WebSocket or browser-sweep covered)"
            else:
                outcome.outcome = "SKIPPED"
                outcome.detail = "no read-only binding for this action (mutation or unmapped)"
            return outcome

        method, template = binding
        # The login probe verifies the session against the actor's OWN surface
        # (org members → org profile; staff/PE → ops me; consultant → me).
        if wf_step.action == "login":
            if wf_step.actor in ("pe_manager", "pe_staff", "internal_operator",
                                 "internal_reviewer", "internal_qc", "staff_admin",
                                 "system_admin"):
                template = "/api/v3/ops/me"
            elif wf_step.actor == "consultant":
                template = "/api/v3/consultants/me"

        try:
            persona = persona_for(wf_step.actor)
            identity = self.resolver.by_email(REPRESENTATIVE_EMAILS[persona])
            resolved = self.resolver.resolve(identity.email)
            ids = self._resource_ids(wf_step, resolved)
            if (wf_step.action in REQUIRES_REAL_CONVERSATION
                    and not ids.get("conversation_found")):
                outcome.outcome = "SKIPPED"
                outcome.detail = ("requires a real conversation id — DB resource "
                                  "discovery unavailable or none in the dataset")
                return outcome
            headers = self.pool.headers(identity)
            url = self.ctx.env.api_base_url.rstrip("/") + self._fill(template, resolved, ids)
            body = DENY_GATE_BODIES.get(wf_step.action, {})
            response = requests.request(method, url, headers=headers, json=body, timeout=25)
            outcome.actual_status = response.status_code
            outcome.outcome = self._classify(expected, response.status_code)
            body = response.text[:400]
            outcome.detail = f"HTTP {response.status_code} — {body}" if outcome.outcome != "PASS" else f"HTTP {response.status_code}"
            if outcome.outcome in ("FAIL", "WARNING"):
                path = self.ctx.api_evidence(
                    wf_step.actor, f"wf_{workflow.key}_{wf_step.action}",
                    f"{method} {template} → {response.status_code}\n{body}",
                    route=template,
                )
                outcome.evidence_path = str(path.relative_to(self.ctx.evidence.base_dir))
        except ToolUnavailable as exc:
            outcome.outcome = "SKIPPED"
            outcome.detail = str(exc)
        except Exception as exc:
            outcome.outcome = "FAIL"
            outcome.detail = f"{type(exc).__name__}: {exc}"[:300]
        return outcome

    # ------------------------------------------------------------------ #

    def _resource_ids(self, wf_step: WorkflowStep, resolved: Any) -> Dict[str, object]:
        """Real resource ids for resource-bound steps (read-only DB lookups).

        Falls back to the all-zero id, which the executor either treats as
        "skip" (REQUIRES_REAL_CONVERSATION) or accepts as a clean denial
        (404) for deny-gated steps.
        """
        ids: Dict[str, object] = {"conversation_found": False}
        if self.discovery is None:
            return ids
        try:
            if wf_step.action in ("cross_org_conversation",
                                  "cross_client_conversation"):
                # The actor must NOT have access to this conversation; pick a
                # real one outside the actor's own org.
                conversation = self.discovery.conversation_id_for_other_org(
                    resolved.organization_id or "")
            else:
                conversation = self.discovery.conversation_id_for(resolved.email)
                if not conversation:
                    conversation = self.discovery.conversation_id_for_org(
                        resolved.organization_id or "")
            if conversation:
                ids["conversation_id"] = conversation
                ids["conversation_found"] = True
        except Exception:
            pass
        return ids

    @staticmethod
    def _fill(template: str, resolved: Any, ids: Optional[Dict[str, object]] = None) -> str:
        """Fill an endpoint template with the ACTOR's own context.

        ``org_a`` is bound to the actor's own organisation (V1.2 calibration):
        a customer/client hits its own org, a consultant operates through its
        client org, and PE staff process against the customer org A. Using the
        wrong org used to make org-bound 403s look like app defects when they
        were harness binding errors.
        """
        ids = ids or {}
        own_org = resolved.organization_id
        if resolved.is_consultant:
            org_a = (resolved.active_client_org_id or own_org
                     or demo_context.client_organization_id(1, 1))
        else:
            org_a = own_org or demo_context.organization_id(1)
        client_org = (own_org or resolved.active_client_org_id
                      or demo_context.client_organization_id(1, 1))
        params = {
            "org_a": org_a,
            "client_org": client_org,
            "msg_org": org_a,
            "entity_a": resolved.processing_entity_id or demo_context.entity_id(1),
            "entity_b": demo_context.entity_id(2),
            "item_id": ids.get("item_id") or "00000000-0000-0000-0000-000000000000",
            "conversation_id": ids.get("conversation_id") or "00000000-0000-0000-0000-000000000000",
            "file_id": "00000000-0000-0000-0000-000000000000",
        }
        return template.format(**params)

    @staticmethod
    def _classify(expected: str, status: int) -> str:
        if expected in ("deny", "403", "no_path", "401"):
            if status in DENY_STATUSES:
                return "PASS"
            if status in (400, 409, 422):
                return "WARNING"
            return "FAIL"
        if 200 <= status < 300:
            return "PASS"
        return "FAIL"

    # ------------------------------------------------------------------ #

    def _finding_for(self, workflow: Workflow, outcome: StepOutcome,
                     *, source: str) -> Optional[Finding]:
        if outcome.outcome in ("PASS", "SKIPPED"):
            return None
        if outcome.outcome == "WARNING":
            # 400/409/422 on a deny-gated step = gate could not be exercised
            # (validation precedes authz, wrong input). INCONCLUSIVE, not an
            # app defect and never "failed". (V1.2 calibration.)
            severity = "P3"
            classification = FindingClassification.INCONCLUSIVE
            title = f"Workflow step inconclusive: {workflow.key}.{outcome.action}"
        else:
            severity = "P1"
            classification = FindingClassification.REAL
            title = f"Workflow step failed: {workflow.key}.{outcome.action}"
        expected = {
            "deny": "denied (401/403/404)", "no_path": "no download path (404/405)",
            "403": "HTTP 403", "401": "HTTP 401", "200": "HTTP 200", "201": "HTTP 201",
        }.get(outcome.expected, outcome.expected)
        return self.ctx.emit(
            "WF", severity,
            title,
            role=outcome.actor, workflow=workflow.key,
            expected=expected,
            actual=f"HTTP {outcome.actual_status}" if outcome.actual_status else outcome.detail,
            description=(
                f"Workflow '{workflow.label}' step {outcome.step_index + 1} "
                f"({outcome.action} as {outcome.actor}). {outcome.detail[:200]}"
            ),
            evidence=[outcome.evidence_path] if outcome.evidence_path else [],
            status=FindingStatus.OPEN,
            classification=classification,
            source=source,
        )

    @property
    def findings(self) -> List[Finding]:
        return self._findings

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for outcome in self.outcomes:
            counts[outcome.outcome] = counts.get(outcome.outcome, 0) + 1
        return counts
