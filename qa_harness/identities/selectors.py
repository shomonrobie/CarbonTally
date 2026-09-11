"""Deterministic identity selection from the complete population.

Supports:

* representative sets (the 13 documented personas),
* full-role sweeps (e.g. all 50 customer owners) with deterministic sampling,
* cross-boundary pairs (Customer A vs B, Client A vs B, Consultant A vs B,
  PE A vs B, Internal vs PE, Viewer vs Member, Member vs Admin, Staff vs
  Staff Admin, Staff Admin vs System Admin).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from qa_harness.identities.loader import Identity, IdentityLoader
from qa_harness.identities.resolver import IdentityResolver

# Internal roles ordered by escalating authority — used for boundary pairs.
_INTERNAL_ROLE_ORDER = [
    "operator", "reviewer", "qc", "staff_admin", "system_admin",
]


@dataclass(frozen=True)
class BoundaryPair:
    """A deterministic cross-boundary actor pair for authorization tests."""

    label: str
    actor_a: Identity
    actor_b: Identity
    boundary: str          # e.g. cross-org / cross-client / role-escalation
    expectation: str       # e.g. "A must not access B data"

    def to_tuple(self) -> Tuple[Identity, Identity]:
        return (self.actor_a, self.actor_b)


def select_by_role(population: Dict[str, Identity], role_key: str,
                   limit: Optional[int] = None, offset: int = 0) -> List[Identity]:
    """Deterministically select identities of one role (sorted by email)."""
    matches = sorted(
        (i for i in population.values() if i.role_key == role_key),
        key=lambda i: i.email,
    )
    if limit is not None:
        matches = matches[offset: offset + limit]
    return matches


class RepresentativeSelector:
    """Selects the documented representative set plus optional extensions."""

    def __init__(self, population: Optional[Dict[str, Identity]] = None,
                 loader: Optional[IdentityLoader] = None) -> None:
        self.loader = loader or IdentityLoader()
        self.population = population or self.loader.load()

    def representatives(self) -> List[Identity]:
        return self.loader.representative()

    def with_extended_org_pair(self) -> List[Identity]:
        """Representatives + a second customer org (Org 2) for cross-org tests."""
        reps = self.representatives()
        emails = {i.email for i in reps}
        extra = [
            i for i in self.population.values()
            if i.org_index == 2 and i.email not in emails
        ]
        return reps + sorted(extra, key=lambda i: i.email)


def _identity_for(population: Dict[str, Identity], persona: str,
                  index: int = 1) -> Identity:
    """Fetch a specific identity by persona + deterministic index."""
    role_to_persona = {
        "customer_owner": "owner", "customer_admin": "admin",
        "customer_member": "member", "customer_viewer": "viewer",
    }
    if persona in role_to_persona:
        email = f"{role_to_persona[persona]}.demo{index:04d}@demo.carbontally.local"
    elif persona == "consultant":
        email = f"consultant.demo{index:04d}@demo.carbontally.local"
    elif persona == "pe_manager":
        email = f"pe-manager-{index}.demo@demo.carbontally.local"
    elif persona == "pe_staff":
        email = f"pe-staff-{index}.demo@demo.carbontally.local"
    elif persona in _INTERNAL_ROLE_ORDER:
        email = f"{persona.replace('_', '-')}.demo@demo.carbontally.local"
    else:
        raise KeyError(f"no deterministic selector for persona {persona!r}")
    return population[email]


def cross_boundary_pairs(population: Dict[str, Identity]) -> List[BoundaryPair]:
    """The deterministic cross-boundary pair set (spec §7)."""
    pairs: List[BoundaryPair] = []
    pairs.append(BoundaryPair(
        label="Customer A vs Customer B",
        actor_a=_identity_for(population, "customer_owner", 1),
        actor_b=_identity_for(population, "customer_owner", 2),
        boundary="cross-org",
        expectation="Customer A must not access Customer B data (docs, facilities, search, uploads).",
    ))
    # Client A vs Client B under the SAME consultant (consultant 1, clients 1 and 2).
    client_a = next(i for i in population.values()
                    if i.consultant_index == 1 and i.client_number == 1)
    client_b = next(i for i in population.values()
                    if i.consultant_index == 1 and i.client_number == 2)
    pairs.append(BoundaryPair(
        label="Client A vs Client B (same consultant)",
        actor_a=client_a,
        actor_b=client_b,
        boundary="cross-client",
        expectation="Client A must not access Client B data.",
    ))
    pairs.append(BoundaryPair(
        label="Consultant A vs Consultant B",
        actor_a=_identity_for(population, "consultant", 1),
        actor_b=_identity_for(population, "consultant", 2),
        boundary="cross-portfolio",
        expectation="Consultant A must not access Consultant B's portfolio.",
    ))
    pairs.append(BoundaryPair(
        label="PE A vs PE B",
        actor_a=_identity_for(population, "pe_manager", 1),
        actor_b=_identity_for(population, "pe_manager", 2),
        boundary="cross-entity",
        expectation="PE A must not access PE B's work.",
    ))
    pairs.append(BoundaryPair(
        label="Internal staff vs PE staff",
        actor_a=_identity_for(population, "operator"),
        actor_b=_identity_for(population, "pe_staff", 1),
        boundary="staff-scope",
        expectation="Internal operator and PE operator are distinct staff scopes.",
    ))
    pairs.append(BoundaryPair(
        label="Viewer vs Member",
        actor_a=_identity_for(population, "customer_viewer", 1),
        actor_b=_identity_for(population, "customer_member", 1),
        boundary="role-escalation",
        expectation="Viewer must be denied every write the Member is allowed.",
    ))
    pairs.append(BoundaryPair(
        label="Member vs Admin",
        actor_a=_identity_for(population, "customer_member", 1),
        actor_b=_identity_for(population, "customer_admin", 1),
        boundary="role-escalation",
        expectation="Member must be denied admin actions (profile edit, members, approval).",
    ))
    pairs.append(BoundaryPair(
        label="Staff vs Staff Admin",
        actor_a=_identity_for(population, "reviewer"),
        actor_b=_identity_for(population, "staff_admin"),
        boundary="internal-role-escalation",
        expectation="Reviewer must be denied staff-admin actions (retention, commercial).",
    ))
    pairs.append(BoundaryPair(
        label="Staff Admin vs System Admin",
        actor_a=_identity_for(population, "staff_admin"),
        actor_b=_identity_for(population, "system_admin"),
        boundary="internal-role-escalation",
        expectation="Both admin roles reach the admin control plane (historical OPS-6 regression target).",
    ))
    return pairs
