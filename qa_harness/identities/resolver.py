"""Identity resolution: map emails/personas to org/entity/workspace context.

The resolver answers "who is this identity and what may they reach?" without
contacting the application. Cross-boundary pair construction (spec §7) lives
in :mod:`qa_harness.identities.selectors`; this module resolves the data the
selectors need.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from qa_harness.identities import context
from qa_harness.identities.loader import Identity, IdentityLoader


class ResolveError(KeyError):
    """Raised when an identity/org cannot be resolved."""


@dataclass
class ResolvedIdentity:
    """Identity plus its resolved context (org, entity, workspace, landing)."""

    identity: Identity
    organization_id: Optional[str] = None      # populated at run time (DB read)
    organization_name: str = ""
    processing_entity_id: Optional[str] = None
    staff_role: str = ""                       # e.g. operator / reviewer / qc
    member_role: str = ""                      # owner / admin / member / viewer
    is_staff: bool = False
    is_pe: bool = False
    is_consultant: bool = False
    active_client_org_id: Optional[str] = None
    portfolio: List[str] = field(default_factory=list)  # client org ids (consultant)

    @property
    def email(self) -> str:
        return self.identity.email

    @property
    def is_demo(self) -> bool:
        """True when the identity authenticates with the shared demo password."""
        return self.identity.is_demo

    def context_summary(self) -> Dict[str, object]:
        return {
            "email": self.identity.email,
            "persona": self.identity.persona,
            "role_key": self.identity.role_key,
            "workspace": self.identity.workspace,
            "landing_route": self.identity.landing_route,
            "organization_id": self.organization_id,
            "organization_name": self.organization_name or self.identity.org,
            "processing_entity_id": self.processing_entity_id,
            "staff_role": self.staff_role,
            "member_role": self.member_role,
            "is_staff": self.is_staff,
            "is_pe": self.is_pe,
            "is_consultant": self.is_consultant,
            "is_demo": self.is_demo,
            "active_client_org_id": self.active_client_org_id,
            "portfolio_size": len(self.portfolio),
        }


class IdentityResolver:
    """Resolves identities into run-time context.

    Organization/entity ids are filled by the run layer (read-only DB or API
    lookups). The resolver itself only performs deterministic mapping from the
    identity model so tests can be composed before a run.
    """

    def __init__(self, population: Optional[Dict[str, Identity]] = None,
                 loader: Optional[IdentityLoader] = None) -> None:
        self._population = population or (loader.load() if loader else IdentityLoader().load())

    def all(self) -> List[Identity]:
        """The complete identity population (deterministic email order)."""
        return sorted(self._population.values(), key=lambda i: i.email)

    def by_email(self, email: str) -> Identity:
        identity = self._population.get(email)
        if identity is None:
            raise ResolveError(f"unknown demo identity: {email}")
        return identity

    def resolve(self, email: str) -> ResolvedIdentity:
        identity = self.by_email(email)
        resolved = ResolvedIdentity(identity=identity)
        if identity.persona in ("owner", "admin", "member", "viewer"):
            resolved.member_role = "owner" if identity.persona == "owner" else identity.persona
            resolved.organization_name = identity.org
            resolved.organization_id = context.organization_id(identity.org_index)
        elif identity.persona == "client_owner":
            resolved.member_role = "owner"
            resolved.organization_name = identity.org
            resolved.is_consultant = False
            resolved.organization_id = context.client_organization_id(
                identity.consultant_index, identity.client_number
            )
        elif identity.persona == "consultant":
            resolved.is_consultant = True
            resolved.organization_name = identity.org
        elif identity.persona in ("pe_manager", "pe_staff"):
            resolved.is_pe = True
            resolved.is_staff = True
            resolved.staff_role = "reviewer" if identity.persona == "pe_manager" else "operator"
            resolved.organization_name = identity.org
            resolved.processing_entity_id = context.entity_id(identity.entity_index)
        elif identity.persona in ("operator", "reviewer", "qc", "staff-admin", "staff_admin",
                                  "system-admin", "system_admin"):
            resolved.is_staff = True
            resolved.staff_role = {
                "operator": "operator",
                "reviewer": "reviewer",
                "qc": "qc",
                "staff-admin": "staff_admin",
                "staff_admin": "staff_admin",
                "system-admin": "system_admin",
                "system_admin": "system_admin",
            }[identity.persona]
            resolved.organization_name = identity.org or "CarbonTally"
        elif identity.persona in ("legacy", "audit", "fixture"):
            # Fixture accounts are outside the role model: never staff, no
            # member role. Legacy @demo accounts still authenticate with the
            # shared demo password (is_demo comes from the identity domain).
            resolved.organization_name = identity.org
        return resolved

    def organization_identities(self, org_index: int) -> List[Identity]:
        """All four roles for a direct customer org (1..50)."""
        return [
            identity for identity in self._population.values()
            if identity.org_index == org_index and identity.persona in
            ("owner", "admin", "member", "viewer")
        ]

    def consultant_clients(self, consultant_index: int) -> List[Identity]:
        """All client-owner identities of a consultant firm."""
        return [
            identity for identity in self._population.values()
            if identity.consultant_index == consultant_index
            and identity.persona == "client_owner"
        ]
