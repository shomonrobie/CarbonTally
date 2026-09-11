"""RLS state and expected-allow / expected-deny framework (read-only).

Two parts:

* :class:`RlsAudit` — inspects RLS enabled/forced state and policies.
* :class:`RlsExpectation` — a generic expected-allow/expected-deny rule
  (ACTOR / ACTION / RESOURCE / EXPECTED / ACTUAL) that the run layer executes
  as a PostgREST or SQL-as-role query. Findings carry ``PO DECISION REQUIRED``
  when the project decision is unclear (spec §9).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.db.schema_inventory import TableInfo


@dataclass
class RlsExpectation:
    """One expected-allow/expected-deny rule.

    ``actor`` and ``resource`` are free-text labels resolved by the run layer
    (e.g. from the identity resolver). ``expected`` is ALLOW or DENY;
    ``actual`` is filled from the executed probe.
    """

    id: str
    actor: str
    action: str
    resource: str
    expected: str          # ALLOW | DENY | PO DECISION REQUIRED
    actual: str = ""
    status: str = "PENDING"
    note: str = ""

    def to_row(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "expected": self.expected,
            "actual": self.actual or "NOT RUN",
            "status": self.status,
            "note": self.note,
        }


def build_standard_expectations() -> List[RlsExpectation]:
    """Documented RLS/authorization expectations (spec §9)."""
    deny = "DENY"
    allow = "ALLOW"
    return [
        RlsExpectation("RLS-1", "Customer A", "read document", "Customer B document", deny),
        RlsExpectation("RLS-2", "Customer A", "read organisation", "Customer B organisation", deny),
        RlsExpectation("RLS-3", "Customer A", "search", "Customer B data", deny),
        RlsExpectation("RLS-4", "Customer A", "upload", "Customer B organisation", deny),
        RlsExpectation("RLS-5", "Consultant A", "read client", "Consultant B client", deny),
        RlsExpectation("RLS-6", "Consultant A", "read data", "Consultant B portfolio", deny),
        RlsExpectation("RLS-7", "PE A", "read batch", "PE B batch", deny),
        RlsExpectation("RLS-8", "PE", "download document", "customer source document", deny,
                       note="D20 no-download boundary"),
        RlsExpectation("RLS-9", "PE", "post message", "customer-org conversation", deny,
                       note="Customer↔PE direct messaging not possible (MSG-3)"),
        RlsExpectation("RLS-10", "Viewer", "upload document", "own organisation", deny,
                       note="read-only role must not write (historical SEC-1)"),
        RlsExpectation("RLS-11", "Member", "admin action", "org profile / members / approval", deny),
        RlsExpectation("RLS-12", "Member", "approve item", "processed item", deny),
        RlsExpectation("RLS-13", "Viewer", "approve item", "processed item", deny),
        RlsExpectation("RLS-14", "Reviewer", "run operator queue", "data-entry queue", deny,
                       note="can_process gate"),
        RlsExpectation("RLS-15", "Reviewer", "calculate", "processed item", deny),
        RlsExpectation("RLS-16", "Customer", "reach staff surface", "/ops", deny),
        RlsExpectation("RLS-17", "Staff", "staff-admin action", "retention / commercial", deny),
        RlsExpectation("RLS-18", "Staff Admin", "approved staff-admin action", "retention / commercial / audit", allow),
        RlsExpectation("RLS-19", "System Admin", "approved system-admin action", "retention / commercial / audit", allow,
                       note="historical OPS-6 regression target"),
        RlsExpectation("RLS-20", "Customer Owner", "approve own custom factor", "own factor", "PO DECISION REQUIRED",
                       note="single-owner org self-approval needs a PO decision (historical CF-1)"),
    ]


class RlsAudit:
    """Compares probed RLS state against documented expectations.

    The probe itself is read-only (pg_class / pg_policies queries). Executing
    an allow/deny expectation requires running a query as a specific role or
    through PostgREST — the run layer does that; this class classifies.
    """

    def __init__(self, expectations: Optional[List[RlsExpectation]] = None,
                 require_rls_on: Optional[List[str]] = None) -> None:
        self.expectations = expectations or build_standard_expectations()
        self.require_rls_on = require_rls_on or [
            "organizations", "organization_members", "organization_files",
            "upload_batches", "manual_extraction_batches", "manual_extraction_items",
            "emission_factors", "customer_factors", "calculation_snapshots",
            "emissions_logs", "issues", "report_versions", "conversations",
            "conversation_participants", "messages", "notifications", "facilities",
            "assets", "suppliers", "vehicles", "consultant_clients", "processing_queue",
        ]

    def tables_without_rls(self, probed: Dict[str, TableInfo]) -> List[str]:
        return [name for name in self.require_rls_on if name in probed and not probed[name].rls_enabled]

    def policies_for(self, probed: Dict[str, TableInfo], table: str) -> List[str]:
        return list(probed.get(table, TableInfo(name=table)).triggers)  # placeholder; real policies come from pg_policies probe

    def classify(self, expectation: RlsExpectation, actual_denied: bool) -> RlsExpectation:
        """Fill actual/status from a probe result.

        ``actual_denied=True`` means the access was refused (403 / zero rows).
        A DENY expectation with denial observed = PASS; an ALLOW expectation
        with denial observed = FAIL; anything vs PO DECISION REQUIRED stays
        open.
        """
        expectation.actual = "DENY" if actual_denied else "ALLOW"
        if expectation.expected == "PO DECISION REQUIRED":
            expectation.status = "PO DECISION REQUIRED"
        elif expectation.actual == expectation.expected:
            expectation.status = "PASS"
        else:
            expectation.status = "FAIL"
        return expectation
