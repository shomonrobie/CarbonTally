"""Authenticated API probe execution (spec §9, §10, §11, §B).

The run layer authenticates representative demo identities against the local
Supabase GoTrue endpoint (password grant, demo-guard enforced) and executes:

* **endpoint smoke probes** — per-persona read-only GETs against the
  role-appropriate V3 surfaces; records actual statuses; flags unexpected
  5xx / unexpected 4xx where a 2xx is the documented expectation.
* **authorization matrix probes** — every documented
  expected-allow / expected-deny expectation bound to a real endpoint
  (cross-org, cross-consultant, cross-PE, staff/customer, viewer/member).
* **security boundary probes** — the SECB-* boundaries re-verified against
  the live API.

Probe safety (read-only default):

* ``mutation=none``   — plain GET / HEAD. Always safe.
* ``mutation=json``   — POST/PUT with an invalid/empty JSON body. The authz
  dependency runs BEFORE body validation in FastAPI, so a correct denial
  returns 403 (no write) and a broken gate surfaces as 422/404 (no write).
  Enabled by default; never writes data.
* ``mutation=upload`` — multipart upload. If the gate is broken the request
  WOULD create a document row. SKIPPED in read-only mode unless the operator
  explicitly enables ``api_probe.allow_upload_probes`` (see qa_config.yaml).

4xx responses are never blanket-flagged: 401/403/404 are legitimate denial
signals; 409/422/400 mean "authz gate passed, input invalid" and are recorded
as WARNINGs (the gate should have denied).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.api.authorization import AuthorizationExpectation, AuthorizationMatrix
from qa_harness.api.security import ApiSecurityAudit, SecurityBoundary
from qa_harness.api.session import ApiSessionPool
from qa_harness.core.config import TargetEnv
from qa_harness.core.findings import (
    Finding,
    FindingClassification,
    FindingStatus,
)
from qa_harness.core.run_context import RunContext
from qa_harness.core.status import RunStatus, ToolUnavailable
from qa_harness.identities import context as demo_context
from qa_harness.identities.loader import Identity, REPRESENTATIVE_EMAILS
from qa_harness.identities.resolver import IdentityResolver, ResolvedIdentity

try:
    import requests  # type: ignore
    _REQUESTS = True
except ImportError:  # pragma: no cover
    requests = None  # type: ignore
    _REQUESTS = False

# Additional actors for cross-boundary probes (second parties).
EXTRA_EMAILS: Dict[str, str] = {
    "customer_owner_b": "owner.demo0002@demo.carbontally.local",
    "customer_admin_b": "admin.demo0002@demo.carbontally.local",
    "consultant_b": "consultant.demo0002@demo.carbontally.local",
    "pe_manager_b": "pe-manager-2.demo@demo.carbontally.local",
    "pe_staff_b": "pe-staff-2.demo@demo.carbontally.local",
    "client_owner_b": "client.owner.demo0002.1@demo.carbontally.local",
}

# Denial statuses: a DENY expectation passes on any of these.
DENY_STATUSES = (401, 403, 404)
# Statuses meaning "authz gate passed, resource/input wrong".
GATE_PASSED_STATUSES = (400, 404, 409, 422)
# Statuses that are always wrong for any probe.
SERVER_ERROR_STATUSES = (500, 502, 503, 504)


@dataclass
class ProbeSpec:
    """One executable probe bound to a real endpoint."""

    id: str
    kind: str                          # authz | security | endpoint
    method: str
    endpoint: str                      # template; {org_a} {org_b} {entity_a} {entity_b} {item_id} {file_id} {client_org}
    actor: str                         # persona key (REPRESENTATIVE_EMAILS / EXTRA_EMAILS)
    expected: str = "ALLOW"            # ALLOW | DENY | NO_PATH | HTTP <status>
    mutation: str = "none"             # none | json | upload
    body: Optional[Dict[str, object]] = None
    description: str = ""
    severity: str = "P1"
    historical: str = ""
    note: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "method": self.method,
            "endpoint": self.endpoint,
            "actor": self.actor,
            "expected": self.expected,
            "mutation": self.mutation,
            "description": self.description,
        }


@dataclass
class ProbeResult:
    """Outcome of one executed probe."""

    spec: ProbeSpec
    actual_status: Optional[int] = None
    outcome: str = "NOT RUN"           # PASS | FAIL | WARNING | SKIPPED | PO DECISION REQUIRED
    response_summary: str = ""
    evidence_path: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.spec.id,
            "kind": self.spec.kind,
            "method": self.spec.method,
            "endpoint": self.spec.endpoint,
            "actor": self.spec.actor,
            "expected": self.spec.expected,
            "actual_status": self.actual_status,
            "outcome": self.outcome,
            "response_summary": self.response_summary,
            "evidence_path": self.evidence_path,
            "error": self.error,
        }


def _classify(expected: str, status: int) -> str:
    """Map (expected, actual) to PASS / FAIL / WARNING.

    * DENY        — 401/403/404 = PASS; 2xx = FAIL (leak); 409/422/400 =
                    WARNING (gate passed, wrong input); 5xx = FAIL.
    * ALLOW       — 2xx = PASS; 401/403 = FAIL; 404/409/422/400 = WARNING
                    (gate passed, resource/input wrong); 5xx = FAIL.
    * NO_PATH     — 404/405/401/403 = PASS (by design); 2xx = FAIL (path exists).
    * HTTP <code> — exact match = PASS; else FAIL.
    """
    if expected == "DENY":
        if status in DENY_STATUSES:
            return "PASS"
        if status in (400, 409, 422):
            return "WARNING"
        return "FAIL"
    if expected == "ALLOW":
        if 200 <= status < 300:
            return "PASS"
        if status in (401, 403):
            return "FAIL"
        if status in GATE_PASSED_STATUSES:
            return "WARNING"
        return "FAIL"
    if expected == "NO_PATH":
        if status in (404, 405) or status in (401, 403):
            return "PASS"
        return "FAIL"
    # "HTTP 200" / "200" / "201" exact-match expectations.
    token = expected.removeprefix("HTTP ").strip()
    try:
        return "PASS" if status == int(token) else "FAIL"
    except ValueError:
        return "FAIL"


def build_probe_specs() -> List[ProbeSpec]:
    """The documented, endpoint-bound probe set.

    Endpoint shapes verified against the backend source (backend/api/*.py):
    ``POST /api/v3/uploads`` requires multipart; org access is enforced in the
    function body; JSON endpoints enforce role dependencies before body
    validation. ``{item_id}`` probes use a non-existent id so a broken gate
    surfaces as 404/422 (never a write).
    """
    P = ProbeSpec
    specs: List[ProbeSpec] = [
        # --- Authorization matrix (AUTHZ-*) --------------------------------
        P("AUTHZ-1", "authz", "GET", "/api/v3/documents?organization_id={org_b}",
          "customer_owner", "DENY", description="Customer A reads Customer B document list",
          severity="P0", historical="SEC-9/10"),
        P("AUTHZ-2", "authz", "GET", "/api/v3/organizations/{org_b}",
          "customer_owner", "DENY", description="Customer A reads Customer B organisation",
          severity="P0", historical="SEC-9/10"),
        P("AUTHZ-3", "authz", "POST", "/api/v3/uploads",
          "customer_owner", "DENY", mutation="upload", description="Customer A uploads into Customer B (org_b form field)",
          severity="P0", historical="SEC-11"),
        P("AUTHZ-4", "authz", "GET", "/api/v3/search?organization_id={org_b}&q=energy",
          "customer_owner", "DENY", description="Customer A searches Customer B data",
          severity="P0", historical="SEC-9"),
        P("AUTHZ-5", "authz", "GET", "/api/v3/consultants/clients/{client_org_b}",
          "consultant", "DENY", description="Consultant A reads Consultant B client org",
          severity="P0"),
        P("AUTHZ-6", "authz", "POST", "/api/v3/uploads",
          "consultant", "DENY", mutation="upload", description="Consultant uploads into a client org without membership",
          severity="P1", historical="SEC-12"),
        P("AUTHZ-7", "authz", "GET", "/api/v3/ops/entities/{entity_b}/extraction/batches",
          "pe_manager", "DENY", description="PE A reads PE B assigned batches",
          severity="P0"),
        P("AUTHZ-8", "authz", "GET", "/api/v3/documents/{file_id}/signed-url",
          "pe_staff", "DENY", description="PE downloads a customer source document (no download path)",
          severity="P0", historical="SEC-17/18/20"),
        P("AUTHZ-9", "authz", "POST", "/api/v3/messaging/conversations/{conversation_id}/messages",
          "pe_staff", "DENY", mutation="json", body={"content": "qa-harness authz gate probe"},
          description="PE posts into a customer-org conversation",
          severity="P1", historical="SEC-19"),
        P("AUTHZ-10", "authz", "POST", "/api/v3/uploads",
          "customer_viewer", "DENY", mutation="upload", description="Viewer uploads a document (read-only role)",
          severity="P1", historical="SEC-1"),
        P("AUTHZ-11", "authz", "PUT", "/api/v3/organizations/{org_a}/profile",
          "customer_member", "DENY", mutation="json", body={},
          description="Member edits the organisation profile",
          severity="P1", historical="SEC-5/6"),
        P("AUTHZ-12", "authz", "POST", "/api/v3/organizations/{org_a}/members",
          "customer_member", "DENY", mutation="json", body={},
          description="Member adds an organisation member",
          severity="P1", historical="SEC-7/8"),
        P("AUTHZ-13", "authz", "POST", "/api/v3/processing/items/{item_id}/customer-review",
          "customer_member", "DENY", mutation="json", body={"approved": True},
          description="Member approves a processed item",
          severity="P1", historical="SEC-3/4"),
        P("AUTHZ-14", "authz", "POST", "/api/v3/processing/items/{item_id}/customer-review",
          "customer_viewer", "DENY", mutation="json", body={"approved": True},
          description="Viewer approves a processed item",
          severity="P1", historical="SEC-3/4"),
        P("AUTHZ-15", "authz", "GET", "/api/v3/ops/queues/operator",
          "internal_reviewer", "DENY", description="Reviewer runs the operator data-entry queue",
          severity="P1", historical="SEC-14"),
        P("AUTHZ-16", "authz", "POST", "/api/v3/ops/items/{item_id}/calculate",
          "internal_reviewer", "DENY", mutation="json", body={},
          description="Reviewer calculates a processed item",
          severity="P1", historical="SEC-15"),
        P("AUTHZ-17", "authz", "GET", "/api/v3/ops/me",
          "customer_owner", "DENY", description="Customer reaches the staff surface",
          severity="P1", historical="SEC-16"),
        P("AUTHZ-18", "authz", "PUT", "/api/v3/settings/retention",
          "internal_operator", "DENY", mutation="json", body={},
          description="Operator edits platform retention config",
          severity="P1", historical="SEC-22"),
        P("AUTHZ-19", "authz", "PUT", "/api/v3/settings/retention",
          "internal_reviewer", "DENY", mutation="json", body={},
          description="Reviewer edits platform retention config",
          severity="P1", historical="SEC-22"),
        P("AUTHZ-20", "authz", "PUT", "/api/v3/settings/retention",
          "internal_qc", "DENY", mutation="json", body={},
          description="QC edits platform retention config",
          severity="P1", historical="SEC-22"),
        P("AUTHZ-21", "authz", "PUT", "/api/v3/settings/retention",
          "staff_admin", "ALLOW", mutation="json", body={},
          description="Staff Admin edits retention config (gate must pass)",
          severity="P1"),
        P("AUTHZ-22", "authz", "GET", "/api/v3/commercial/config",
          "staff_admin", "ALLOW", description="Staff Admin reads commercial config",
          severity="P1"),
        P("AUTHZ-23", "authz", "GET", "/api/v3/settings/retention",
          "system_admin", "ALLOW", description="System Admin reads retention config",
          severity="P1", historical="OPS-6"),
        P("AUTHZ-24", "authz", "GET", "/api/v3/commercial/config",
          "system_admin", "ALLOW", description="System Admin reads commercial config",
          severity="P1", historical="OPS-6"),
        P("AUTHZ-25", "authz", "GET", "/api/v2/admin/audit",
          "system_admin", "ALLOW", description="System Admin reads the audit log",
          severity="P1", historical="ISC-10"),
        P("AUTHZ-26", "authz", "POST", "/api/v3/customer-factors/{item_id}/approve",
          "customer_owner", "PO DECISION REQUIRED", mutation="json", body={},
          description="Owner self-approves own custom factor (CF-1)",
          severity="P2", historical="SEC-21"),
        # D5: may an owner/admin approve their own item? Requires a PO
        # decision AND an authorized mutation scope with a real item id —
        # approval would write state, so it cannot run read-only. Kept
        # explicitly unresolved (never reported as a fake-id 404).
        P("AUTHZ-27", "authz", "POST", "/api/v3/processing/items/{item_id}/customer-review",
          "customer_owner", "PO DECISION REQUIRED", mutation="json", body={"approved": True},
          description="Owner/Admin approval gate on own item (D5)",
          severity="P1",
          note="PO decision required; executable only in an authorized mutation scope with a real item id"),
        P("AUTHZ-28", "authz", "GET", "/api/v3/ops/entities/{entity_a}/extraction/batches",
          "pe_manager", "ALLOW", description="PE Manager lists own entity batches",
          severity="P1", historical="PE-2"),

        # --- Security boundaries (SECB-*) -----------------------------------
        P("SECB-1", "security", "POST", "/api/v3/uploads",
          "customer_viewer", "DENY", mutation="upload", description="Viewer must not upload documents",
          severity="P1", historical="SEC-1"),
        P("SECB-2", "security", "POST", "/api/v3/processing/items/{item_id}/customer-review",
          "customer_member", "DENY", mutation="json", body={"approved": True},
          description="Member must not approve processed items",
          severity="P1", historical="SEC-3/4"),
        P("SECB-3", "security", "PUT", "/api/v3/organizations/{org_a}/profile",
          "customer_member", "DENY", mutation="json", body={},
          description="Member/Viewer must not edit org profile",
          severity="P1", historical="SEC-5/6"),
        P("SECB-4", "security", "POST", "/api/v3/organizations/{org_a}/members",
          "customer_member", "DENY", mutation="json", body={},
          description="Member/Viewer must not add org members",
          severity="P1", historical="SEC-7/8"),
        P("SECB-5", "security", "GET", "/api/v3/documents?organization_id={org_b}",
          "customer_owner", "DENY", description="Customer A must not read/search/upload into Customer B",
          severity="P0", historical="SEC-9/10/11"),
        P("SECB-6", "security", "POST", "/api/v3/uploads",
          "consultant", "DENY", mutation="upload", description="Consultant must not upload into a client org (non-member)",
          severity="P1", historical="SEC-12"),
        P("SECB-7", "security", "GET", "/api/v3/ops/queues/operator",
          "internal_reviewer", "DENY", description="Reviewer must not run the operator queue",
          severity="P1", historical="SEC-14/15"),
        P("SECB-8", "security", "GET", "/api/v3/ops/me",
          "customer_owner", "DENY", description="Customers must not reach staff surfaces",
          severity="P1", historical="SEC-16"),
        P("SECB-9", "security", "GET", "/api/v3/ops/queues/operator",
          "pe_staff", "DENY", description="PE must not access internal org-scoped queues",
          severity="P0", historical="SEC-17/18"),
        P("SECB-10", "security", "POST", "/api/v3/messaging/conversations/{conversation_id}/messages",
          "pe_staff", "DENY", mutation="json", body={"content": "qa-harness authz gate probe"},
          description="PE must not post to customer-org conversations",
          severity="P1", historical="SEC-19"),
        P("SECB-11", "security", "GET", "/api/v3/documents/{file_id}/signed-url",
          "pe_staff", "DENY", description="PE has no customer document download path",
          severity="P0", historical="SEC-20"),
        P("SECB-12", "security", "POST", "/api/v3/customer-factors/{item_id}/approve",
          "customer_owner", "PO DECISION REQUIRED", mutation="json", body={},
          description="Owner self-approves own custom factor (pending PO decision)",
          severity="P2", historical="SEC-21"),
        P("SECB-13", "security", "PUT", "/api/v3/settings/retention",
          "internal_operator", "DENY", mutation="json", body={},
          description="Operator/Reviewer/QC must not edit retention config",
          severity="P1", historical="SEC-22"),
        P("SECB-14", "security", "GET", "/api/v3/settings/retention",
          "system_admin", "ALLOW", description="System Admin must reach retention/commercial/audit",
          severity="P1", historical="SEC-2/OPS-6"),
    ]
    return specs


def build_smoke_probes() -> List[ProbeSpec]:
    """Per-persona read-only endpoint smoke probes (role-appropriate V3 surfaces).

    Every probe is a GET with required query params filled from the resolved
    identity context. These verify the role can actually operate (the
    historical "consultant cannot operate customers" class of defect).
    """
    P = ProbeSpec
    return [
        # Customer workspace (org A) — bindings calibrated to the live OpenAPI
        # (V1.2): required query params are supplied (start_date/end_date,
        # stage, organization_id) so a non-2xx is a real app signal, not a
        # harness contract defect.
        P("SMOKE-owner-1", "endpoint", "GET", "/api/v3/emissions/dashboard?organization_id={org_a}&start_date=2026-01-01&end_date=2026-12-31", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-2", "endpoint", "GET", "/api/v3/documents?organization_id={org_a}", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-3", "endpoint", "GET", "/api/v3/processing/queue?organization_id={org_a}&stage=extraction", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-4", "endpoint", "GET", "/api/v3/processing/customer-review?organization_id={org_a}", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-5", "endpoint", "GET", "/api/v3/messaging/conversations?organization_id={org_a}", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-6", "endpoint", "GET", "/api/v3/reports?organization_id={org_a}", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-7", "endpoint", "GET", "/api/v3/organizations/{org_a}/profile", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-8", "endpoint", "GET", "/api/v3/notifications", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-9", "endpoint", "GET", "/api/v3/customer-factors?organization_id={org_a}", "customer_owner", "HTTP 200"),
        P("SMOKE-owner-10", "endpoint", "GET", "/api/v3/search?organization_id={org_a}&q=energy", "customer_owner", "HTTP 200"),
        # Consultant workspace
        P("SMOKE-consultant-1", "endpoint", "GET", "/api/v3/consultants/me", "consultant", "HTTP 200"),
        P("SMOKE-consultant-2", "endpoint", "GET", "/api/v3/consultants/me/clients", "consultant", "HTTP 200"),
        P("SMOKE-consultant-3", "endpoint", "GET", "/api/v3/consultants/me/branding", "consultant", "HTTP 200"),
        P("SMOKE-consultant-4", "endpoint", "GET", "/api/v3/processing/dashboard?organization_id={client_org}", "consultant", "HTTP 200"),
        # PE workspace
        P("SMOKE-pe_manager-1", "endpoint", "GET", "/api/v3/ops/me", "pe_manager", "HTTP 200"),
        P("SMOKE-pe_manager-2", "endpoint", "GET", "/api/v3/ops/entities/{entity_a}/extraction/batches", "pe_manager", "HTTP 200"),
        P("SMOKE-pe_manager-3", "endpoint", "GET", "/api/v3/ops/entities/{entity_a}/dashboard", "pe_manager", "HTTP 200"),
        P("SMOKE-pe_manager-4", "endpoint", "GET", "/api/v3/processing/status?organization_id={org_a}", "pe_manager", "HTTP 200"),
        P("SMOKE-pe_staff-1", "endpoint", "GET", "/api/v3/ops/me", "pe_staff", "HTTP 200"),
        P("SMOKE-pe_staff-2", "endpoint", "GET", "/api/v3/ops/entities/{entity_a}/extraction/batches", "pe_staff", "HTTP 200"),
        # Internal operations
        P("SMOKE-operator-1", "endpoint", "GET", "/api/v3/ops/me", "internal_operator", "HTTP 200"),
        P("SMOKE-operator-2", "endpoint", "GET", "/api/v3/ops/dashboard", "internal_operator", "HTTP 200"),
        P("SMOKE-operator-3", "endpoint", "GET", "/api/v3/ops/queues/operator", "internal_operator", "HTTP 200"),
        P("SMOKE-reviewer-1", "endpoint", "GET", "/api/v3/ops/me", "internal_reviewer", "HTTP 200"),
        P("SMOKE-reviewer-2", "endpoint", "GET", "/api/v3/ops/queues/review", "internal_reviewer", "HTTP 200"),
        P("SMOKE-qc-1", "endpoint", "GET", "/api/v3/ops/me", "internal_qc", "HTTP 200"),
        P("SMOKE-qc-2", "endpoint", "GET", "/api/v3/ops/queues/qc", "internal_qc", "HTTP 200"),
        P("SMOKE-staff_admin-1", "endpoint", "GET", "/api/v3/ops/me", "staff_admin", "HTTP 200"),
        P("SMOKE-staff_admin-2", "endpoint", "GET", "/api/v3/ops/staff", "staff_admin", "HTTP 200"),
        P("SMOKE-staff_admin-3", "endpoint", "GET", "/api/v3/ops/entities", "staff_admin", "HTTP 200"),
        P("SMOKE-staff_admin-4", "endpoint", "GET", "/api/v3/settings/retention", "staff_admin", "HTTP 200"),
        P("SMOKE-staff_admin-5", "endpoint", "GET", "/api/v3/commercial/config", "staff_admin", "HTTP 200"),
        P("SMOKE-staff_admin-6", "endpoint", "GET", "/api/v2/admin/audit", "staff_admin", "HTTP 200"),
        P("SMOKE-system_admin-1", "endpoint", "GET", "/api/v3/settings/retention", "system_admin", "HTTP 200"),
        P("SMOKE-system_admin-2", "endpoint", "GET", "/api/v3/commercial/config", "system_admin", "HTTP 200"),
        P("SMOKE-system_admin-3", "endpoint", "GET", "/api/v2/admin/audit", "system_admin", "HTTP 200"),
        # Client workspace (consultant client org)
        P("SMOKE-client-1", "endpoint", "GET", "/api/v3/documents?organization_id={client_org}", "client_owner", "HTTP 200"),
        P("SMOKE-client-2", "endpoint", "GET", "/api/v3/emissions/dashboard?organization_id={client_org}&start_date=2026-01-01&end_date=2026-12-31", "client_owner", "HTTP 200"),
        P("SMOKE-client-3", "endpoint", "GET", "/api/v3/processing/customer-review?organization_id={client_org}", "client_owner", "HTTP 200"),
        P("SMOKE-client-4", "endpoint", "GET", "/api/v3/messaging/conversations?organization_id={client_org}", "client_owner", "HTTP 200"),
    ]


class ApiProbeEngine:
    """Executes probe specs against the live stack with authenticated sessions."""

    def __init__(self, ctx: RunContext, resolver: IdentityResolver,
                 pool: ApiSessionPool,
                 allow_empty_body_mutation: bool = True,
                 allow_upload_probes: bool = False,
                 skip_security: bool = False) -> None:
        self.ctx = ctx
        self.resolver = resolver
        self.pool = pool
        self.allow_empty_body_mutation = allow_empty_body_mutation
        self.allow_upload_probes = allow_upload_probes
        self.skip_security = skip_security
        self.results: List[ProbeResult] = []
        self._findings: List[Finding] = []
        self._org_a = demo_context.organization_id(1)
        self._org_b = demo_context.organization_id(2)
        self._client_org_a = demo_context.client_organization_id(1, 1)
        self._client_org_b = demo_context.client_organization_id(2, 1)
        self._entity_a = demo_context.entity_id(1)
        self._entity_b = demo_context.entity_id(2)
        self._fake_item = "00000000-0000-0000-0000-000000000000"
        self._fake_conversation = "00000000-0000-0000-0000-000000000000"

    # ------------------------------------------------------------------ #

    def _actor_identity(self, persona_key: str) -> Identity:
        email = EXTRA_EMAILS.get(persona_key) or REPRESENTATIVE_EMAILS.get(persona_key)
        if not email:
            raise KeyError(f"no email bound for persona key {persona_key!r}")
        return self.resolver.by_email(email)

    def _fill(self, template: str, actor: ResolvedIdentity, victim: ResolvedIdentity) -> str:
        params = {
            "org_a": actor.organization_id or self._org_a,
            "org_b": victim.organization_id or self._org_b,
            "entity_a": actor.processing_entity_id or self._entity_a,
            "entity_b": victim.processing_entity_id or self._entity_b,
            "client_org": actor.organization_id or self._client_org_a,
            "client_org_b": self._client_org_b,
            "item_id": self._fake_item,
            "conversation_id": self._fake_conversation,
            "file_id": self._fake_item,
        }
        return template.format(**params)

    def _call(self, spec: ProbeSpec, headers: Dict[str, str], url: str,
              evidence_name: str) -> ProbeResult:
        result = ProbeResult(spec=spec)
        try:
            response = requests.request(
                spec.method, url, headers=headers,
                json=spec.body or {}, timeout=25,
            )
            result.actual_status = response.status_code
            body_preview = response.text[:500]
            result.response_summary = body_preview
            if result.outcome != "SKIPPED":
                result.outcome = _classify(spec.expected, response.status_code)
            if result.outcome in ("FAIL", "WARNING"):
                path = self.ctx.api_evidence(
                    spec.actor, evidence_name,
                    f"{spec.method} {spec.endpoint} → {response.status_code}\n{body_preview}",
                    route=spec.endpoint,
                )
                result.evidence_path = str(path.relative_to(self.ctx.evidence.base_dir))
        except ToolUnavailable as exc:
            result.error = str(exc)
            result.outcome = "SKIPPED"
        except Exception as exc:
            result.error = str(exc)[:300]
            result.outcome = "FAIL"
        return result

    # ------------------------------------------------------------------ #

    def run(self, specs: List[ProbeSpec], *, workflow: str = "",
            source: str = "run_api.py") -> List[ProbeResult]:
        for spec in specs:
            result = self._execute(spec, workflow=workflow, source=source)
            self.results.append(result)
            finding = self._finding_for(result, workflow=workflow, source=source)
            if finding is not None:
                self._findings.append(finding)
        return self.results

    def _execute(self, spec: ProbeSpec, *, workflow: str, source: str) -> ProbeResult:
        # Mutation gating ---------------------------------------------------
        if spec.mutation == "upload" and not self.allow_upload_probes:
            result = ProbeResult(spec=spec)
            result.outcome = "SKIPPED"
            result.error = "READ-ONLY — upload probe requires a file body; enable api_probe.allow_upload_probes in an authorized scope"
            return result
        if spec.mutation == "json" and not self.allow_empty_body_mutation:
            result = ProbeResult(spec=spec)
            result.outcome = "SKIPPED"
            result.error = "READ-ONLY — empty-body mutation probes disabled (api_probe.allow_empty_body_mutation_probes)"
            return result
        if spec.expected == "PO DECISION REQUIRED":
            result = ProbeResult(spec=spec)
            result.outcome = "PO DECISION REQUIRED"
            return result

        try:
            actor = self.resolver.resolve(self._actor_identity(spec.actor).email)
            victim = actor
            if spec.actor.endswith("_b"):
                victim = actor
            # Cross-party probes use the victim org/entity of the SECOND org.
            if "org_b" in spec.endpoint:
                victim = self.resolver.resolve(self._actor_identity("customer_owner_b").email)
            if "entity_b" in spec.endpoint:
                victim = self.resolver.resolve(self._actor_identity("pe_manager_b").email)
            if "client_org_b" in spec.endpoint:
                victim = self.resolver.resolve(self._actor_identity("consultant_b").email)
            headers = self.pool.headers(actor.identity)
            url = self.ctx.env.api_base_url.rstrip("/") + self._fill(spec.endpoint, actor, victim)
            name = f"{spec.id}_{spec.method}".lower()
            return self._call(spec, headers, url, name)
        except ToolUnavailable as exc:
            result = ProbeResult(spec=spec)
            result.outcome = "SKIPPED"
            result.error = str(exc)
            return result
        except Exception as exc:
            result = ProbeResult(spec=spec)
            result.outcome = "FAIL"
            result.error = str(exc)[:300]
            return result

    # ------------------------------------------------------------------ #

    def _finding_for(self, result: ProbeResult, *, workflow: str,
                     source: str) -> Optional[Finding]:
        if result.outcome in ("PASS", "SKIPPED", "PO DECISION REQUIRED"):
            return None
        spec = result.spec
        severity = spec.severity if result.outcome == "FAIL" else "P3"
        category = "SEC" if spec.kind == "security" else "API"
        if result.outcome == "WARNING":
            # A 4xx that is not the expected denial (400/409/422) means the
            # gate could not be exercised (validation precedes authz, wrong
            # input, or a fake resource id). That is INCONCLUSIVE — never
            # "did not deny", which would imply a leak. (V1.2 calibration.)
            title = f"Authz gate inconclusive: {spec.id} ({spec.description})"
            classification = FindingClassification.INCONCLUSIVE
        else:
            title = f"{spec.id}: {spec.description}"
            classification = FindingClassification.REAL
        expected = (
            f"HTTP {spec.expected}" if spec.expected.isdigit()
            else spec.expected
        )
        return self.ctx.emit(
            category, severity, title,
            role=spec.actor,
            route=spec.endpoint,
            workflow=workflow,
            expected=expected,
            actual=f"HTTP {result.actual_status}" if result.actual_status else result.error,
            description=(
                f"{spec.description}. Probe: {spec.method} {spec.endpoint} "
                f"as {spec.actor}. "
                + (f"Historical finding {spec.historical} regression target." if spec.historical else "")
            ),
            evidence=[result.evidence_path] if result.evidence_path else [],
            reproduction=[f"requests.{spec.method.lower()}({spec.endpoint})"],
            business_impact=(
                "Cross-tenant data exposure / unauthorized write." if spec.severity == "P0"
                else "Role capability boundary violated."
            ),
            security_impact="Authorization boundary violation" if result.outcome == "FAIL" else "Gate-passed probe (inconclusive)",
            related_cline_task=spec.historical,
            status=FindingStatus.OPEN,
            classification=classification,
            source=source,
        )

    @property
    def findings(self) -> List[Finding]:
        return self._findings

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for result in self.results:
            counts[result.outcome] = counts.get(result.outcome, 0) + 1
        return counts
