"""Security rules — authorization expectations at the rule level.

These are the re-verifiable security requirements (from the security
acceptance findings + RLS observations). They are regression targets: the
harness independently verifies each one at run time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SecurityRule:
    id: str
    actor: str
    action: str
    resource: str
    expected: str                 # DENY | ALLOW | NO_PATH | PO DECISION REQUIRED
    severity: str = "P1"
    historical: str = ""


def build_security_rules() -> List[SecurityRule]:
    R = SecurityRule
    return [
        R("SECR-1", "Viewer", "upload document", "own organisation", "DENY", "P1", "SEC-1"),
        R("SECR-2", "Member/Viewer", "approve processed item", "own organisation item", "DENY", "P1", "SEC-3/4"),
        R("SECR-3", "Member/Viewer", "edit org profile", "own organisation", "DENY", "P1", "SEC-5/6"),
        R("SECR-4", "Member/Viewer", "add org member", "own organisation", "DENY", "P1", "SEC-7/8"),
        R("SECR-5", "Customer A", "read/search/upload", "Customer B data", "DENY", "P0", "SEC-9/10/11"),
        R("SECR-6", "Reviewer", "operator queue / calculate", "data-entry queue / item", "DENY", "P1", "SEC-14/15"),
        R("SECR-7", "Customer", "reach staff surfaces", "/api/v3/ops/*", "DENY", "P1", "SEC-16"),
        R("SECR-8", "PE", "org queues / customer documents", "customer org", "DENY", "P0", "SEC-17/18"),
        R("SECR-9", "PE", "post to customer conversation", "customer-org conversation", "DENY", "P1", "SEC-19"),
        R("SECR-10", "PE", "download customer document", "customer source document", "NO_PATH", "P0", "SEC-20"),
        R("SECR-11", "Owner", "self-approve own factor", "own custom factor", "DENY", "P2", "SEC-21"),
        R("SECR-12", "Operator/Reviewer/QC", "edit retention/commercial", "platform config", "DENY", "P1", "SEC-22"),
        R("SECR-13", "System Admin", "retention/commercial/audit", "platform config", "ALLOW", "P1", "SEC-2/OPS-6"),
        R("SECR-14", "Consultant", "cross-portfolio access", "other consultant's clients", "DENY", "P0", "CON-5"),
        R("SECR-15", "Authenticated user", "visitor assistant as messaging", "messaging surface", "DENY",
          "P2", "MSG-5/AI-2",
          # note: assistant must NOT be the authenticated messaging mechanism
          ),
        R("SECR-16", "notifications table", "direct client query", "legacy bell path", "DENY",
          "P2", "NOT-1", ),
    ]


class SecurityRuleCatalog:
    def __init__(self, rules: Optional[List[SecurityRule]] = None) -> None:
        self.rules = rules or build_security_rules()

    def by_severity(self, severity: str) -> List[SecurityRule]:
        return [r for r in self.rules if r.severity == severity]
