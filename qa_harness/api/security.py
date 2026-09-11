"""API security boundary checks (read-only by default).

Encodes the documented security boundaries from the security acceptance
findings (SEC-1..SEC-22) as re-verifiable expectations. Every "denied" must
be a server-side HTTP 403 (or by-design no-path), never UI-only hiding.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from qa_harness.api.authorization import AuthorizationExpectation


@dataclass
class SecurityBoundary:
    id: str
    description: str
    expected: str          # DENIED | ALLOWED | NO_PATH | PO_DECISION_REQUIRED
    severity: str = "P1"
    historical_finding: str = ""
    notes: str = ""


def build_security_boundaries() -> List[SecurityBoundary]:
    """Documented security boundaries (from CARBONTALLY_V3_SECURITY_ACCEPTANCE_FINDINGS.md)."""
    B = SecurityBoundary
    return [
        B("SECB-1", "Viewer must not upload documents (read-only role write)", "DENIED", "P1",
          historical_finding="SEC-1"),
        B("SECB-2", "Member must not approve processed items", "DENIED", "P1", historical_finding="SEC-3/4"),
        B("SECB-3", "Member/Viewer must not edit org profile", "DENIED", "P1", historical_finding="SEC-5/6"),
        B("SECB-4", "Member/Viewer must not add org members", "DENIED", "P1", historical_finding="SEC-7/8"),
        B("SECB-5", "Customer A must not read/search/upload into Customer B", "DENIED", "P0", historical_finding="SEC-9/10/11"),
        B("SECB-6", "Consultant must not upload into a client org (non-member)", "DENIED", "P1",
          historical_finding="SEC-12", notes="functionality gap, not a leak — verify it stays denied if a future path is added"),
        B("SECB-7", "Reviewer must not run the operator queue or calculate", "DENIED", "P1", historical_finding="SEC-14/15"),
        B("SECB-8", "Customers must not reach staff surfaces", "DENIED", "P1", historical_finding="SEC-16"),
        B("SECB-9", "PE must not access org-scoped queues / customer documents", "DENIED", "P0", historical_finding="SEC-17/18"),
        B("SECB-10", "PE must not post to customer-org conversations", "DENIED", "P1", historical_finding="SEC-19"),
        B("SECB-11", "PE has no customer document download path", "NO_PATH", "P0", historical_finding="SEC-20"),
        B("SECB-12", "Owner must not self-approve own custom factor (unless PO decision)", "DENIED", "P2",
          historical_finding="SEC-21"),
        B("SECB-13", "Operator/Reviewer/QC must not edit retention config", "DENIED", "P1", historical_finding="SEC-22"),
        B("SECB-14", "System Admin must reach retention/commercial/audit (role mapping)", "ALLOWED", "P1",
          historical_finding="SEC-2/OPS-6"),
    ]


class ApiSecurityAudit:
    """Classifies API security-boundary probes."""

    def __init__(self, boundaries: Optional[List[SecurityBoundary]] = None) -> None:
        self.boundaries = boundaries or build_security_boundaries()

    def evaluate(self, boundary_id: str, observed: str) -> Optional[SecurityBoundary]:
        """``observed`` is DENIED | ALLOWED | NO_PATH | HTTP <code>.

        Returns the boundary with its observation recorded. A violation is any
        outcome different from the expected one — except for
        ``PO_DECISION_REQUIRED`` which is never auto-asserted.
        """
        for boundary in self.boundaries:
            if boundary.id == boundary_id:
                marker = f"OBSERVED {observed}"
                if observed == boundary.expected or boundary.expected == "PO_DECISION_REQUIRED":
                    boundary.notes = marker
                    return boundary
                if boundary.notes and "OBSERVED" in boundary.notes:
                    boundary.notes += f" | {marker} — expected {boundary.expected}"
                else:
                    boundary.notes = f"{marker} — expected {boundary.expected}"
                return boundary
        return None

    def violations(self) -> List[SecurityBoundary]:
        return [
            b for b in self.boundaries
            if b.notes and "OBSERVED" in b.notes and "— expected" in b.notes
        ]
