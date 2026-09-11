"""Expected-allow / expected-deny authorization matrix (spec §9, §10).

A generic framework:

    ACTOR        →  ACTION        →  RESOURCE        →  EXPECTED → ACTUAL

Examples: Customer A → Customer B document = DENY; Staff Admin →
retention config = ALLOW. Where the project decision is unclear the expected
value is ``PO DECISION REQUIRED`` and nothing is asserted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AuthorizationExpectation:
    id: str
    actor: str
    action: str
    resource: str
    expected: str            # ALLOW | DENY | PO DECISION REQUIRED
    method: str = "GET"
    endpoint: str = ""       # API path (when known)
    actual_status: Optional[int] = None
    actual_result: str = ""
    status: str = "PENDING"
    note: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "expected": self.expected,
            "actual_status": self.actual_status,
            "actual_result": self.actual_result,
            "status": self.status,
            "note": self.note,
        }

    def classify(self, actual_status: int) -> "AuthorizationExpectation":
        """Fill actual + status from the observed HTTP status.

        A response is 'denied' when the status is 401/403/404-by-design; it is
        'allowed' when 2xx. 409/422 mean the gate passed but the state/input
        was wrong — recorded as WARNING, not PASS/FAIL.
        """
        self.actual_status = actual_status
        if actual_status in (401, 403):
            self.actual_result = "DENY"
        elif 200 <= actual_status < 300:
            self.actual_result = "ALLOW"
        elif actual_status in (409, 422, 400):
            self.actual_result = "GATE_PASSED_STATE_WRONG"
        else:
            self.actual_result = f"HTTP {actual_status}"
        if self.expected == "PO DECISION REQUIRED":
            self.status = "PO DECISION REQUIRED"
        elif self.actual_result == self.expected:
            self.status = "PASS"
        elif self.actual_result == "GATE_PASSED_STATE_WRONG":
            self.status = "WARNING"
        else:
            self.status = "FAIL"
        return self


def build_standard_matrix() -> List[AuthorizationExpectation]:
    """Documented authorization expectations (from the persona + security audits)."""
    E = AuthorizationExpectation
    return [
        E("AUTHZ-1", "Customer A", "read document", "Customer B document", "DENY"),
        E("AUTHZ-2", "Customer A", "read organisation", "Customer B organisation", "DENY"),
        E("AUTHZ-3", "Customer A", "upload document", "Customer B organisation", "DENY", method="POST"),
        E("AUTHZ-4", "Customer A", "search", "Customer B data", "DENY"),
        E("AUTHZ-5", "Consultant A", "read client", "Consultant B client", "DENY"),
        E("AUTHZ-6", "Consultant", "upload document", "inactive client org", "DENY", method="POST"),
        E("AUTHZ-7", "PE A", "read batch", "PE B batch", "DENY"),
        E("AUTHZ-8", "PE", "download document", "customer source document", "DENY"),
        E("AUTHZ-9", "PE", "post message", "customer-org conversation", "DENY", method="POST"),
        E("AUTHZ-10", "Viewer", "upload document", "own organisation", "DENY", method="POST",
          note="historical SEC-1: viewer upload must be denied"),
        E("AUTHZ-11", "Member", "edit organisation profile", "own organisation", "DENY", method="PUT"),
        E("AUTHZ-12", "Member", "add organisation member", "own organisation", "DENY", method="POST"),
        E("AUTHZ-13", "Member", "approve processed item", "own organisation item", "DENY"),
        E("AUTHZ-14", "Viewer", "approve processed item", "own organisation item", "DENY"),
        E("AUTHZ-15", "Reviewer", "run operator queue", "data-entry queue", "DENY"),
        E("AUTHZ-16", "Reviewer", "calculate item", "processed item", "DENY"),
        E("AUTHZ-17", "Customer", "reach staff surface", "/api/v3/ops/me", "DENY"),
        E("AUTHZ-18", "Operator", "edit retention config", "platform retention", "DENY", method="PUT"),
        E("AUTHZ-19", "Reviewer", "edit retention config", "platform retention", "DENY", method="PUT"),
        E("AUTHZ-20", "QC", "edit retention config", "platform retention", "DENY", method="PUT"),
        E("AUTHZ-21", "Staff Admin", "edit retention config", "platform retention", "ALLOW", method="PUT"),
        E("AUTHZ-22", "Staff Admin", "read commercial config", "platform commercial", "ALLOW"),
        E("AUTHZ-23", "System Admin", "read retention config", "platform retention", "ALLOW",
          note="historical OPS-6 regression target"),
        E("AUTHZ-24", "System Admin", "read commercial config", "platform commercial", "ALLOW",
          note="historical OPS-6 regression target"),
        E("AUTHZ-25", "System Admin", "read audit log", "platform audit", "ALLOW",
          note="historical ISC-10 regression target"),
        E("AUTHZ-26", "Customer Owner", "approve own custom factor", "own factor", "PO DECISION REQUIRED",
          note="historical CF-1: single-owner org self-approval needs a PO decision"),
        E("AUTHZ-27", "Owner/Admin", "approve processed item", "own organisation item", "ALLOW",
          note="D5 customer approval gate"),
        E("AUTHZ-28", "PE Manager", "list entity batches", "own processing entity", "ALLOW",
          note="historical PE-2 regression target"),
    ]


class AuthorizationMatrix:
    """Holds the expectation set and classifies probe results."""

    def __init__(self, expectations: Optional[List[AuthorizationExpectation]] = None) -> None:
        self.expectations = expectations or build_standard_matrix()

    def record(self, expectation_id: str, actual_status: int) -> Optional[AuthorizationExpectation]:
        for expectation in self.expectations:
            if expectation.id == expectation_id:
                return expectation.classify(actual_status)
        return None

    def failures(self) -> List[AuthorizationExpectation]:
        return [e for e in self.expectations if e.status == "FAIL"]

    def po_decisions(self) -> List[AuthorizationExpectation]:
        return [e for e in self.expectations if e.status == "PO DECISION REQUIRED"]
