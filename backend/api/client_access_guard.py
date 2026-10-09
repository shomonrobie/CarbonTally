"""CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05 — the CLIENT-ACCESS CEILING
on the ORGANISATION plane (the "Plane B and Plane C are the same surface" rule).

Ratified authority
------------------
* ``docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md`` §8.1/§8.2/§8.3 and
  §16: a consultant-managed client's own users reach the SAME Organisation
  surface a direct customer uses; their effective access is the CEILING
  ``RELATIONSHIP ∩ CLIENT ACCESS PROFILE ∩ CLIENT ROLE ∩ ENTITLEMENT`` and §8.3
  P-6 requires that ceiling to be enforced SERVER-SIDE. §16 names the exact
  failure mode this module closes — *letting a consultant-managed client
  inherit direct-customer assumptions inside the authorization layer*.
* ``Research/CT-CONSULTANT-MODEL-UIUX-DESIGN-01`` §8: "PLANE C … is Plane B
  rendered for the client's own users, with … profile-driven capabilities
  (OFF / READ_ONLY / COLLABORATIVE / MANAGED)" and "Planes B and C are the same
  Organisation surface, not two products."
* ``docs/architecture/CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02.md`` §1:
  effective client access includes the profile, and "Frontend controls never
  substitute for backend authorization."

Before this module the profile ceiling was enforced ONLY on the separate Plane C
route family (``/api/v3/portal/{clientId}/*``, ``api/client_portal_auth.py``).
An organization member whose organisation is a consultant-managed client could
therefore reach the DIRECT-CUSTOMER organisation plane with no profile ceiling
and upload documents / edit master data.

This module is a CEILING, never a grant:

* a DIRECT customer (no consultant relationship for the organisation) → the
  ceiling does not apply and nothing changes;
* a consultant principal (admitted via ``managed_org_ids``) and CarbonTally
  internal staff / Processing Entity staff are NOT client users → the ceiling
  does not apply;
* the ceiling is resolved from AUTHORITATIVE rows
  (``consultant_clients`` via ``ConsultantsRepository.get_relationship_for_org``),
  never from client input;
* the decision reuses the SAME pure policy module Plane C uses
  (``domain.relationship_access``), so the two surfaces can never drift.

It never weakens tenant isolation, never bypasses RLS, and never grants any
capability that the existing member/admin guards did not already require.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, HTTPException, status

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, get_current_user
from domain.relationship_access import (
    normalise_profile,
    profile_allows,
    resolve_relationship_state,
)

#: Non-technical denial for a client action the access profile does not permit
#: (AGENTS.md §46/§75). The action is on the caller's OWN organisation, so a
#: clear message discloses nothing cross-tenant.
CLIENT_OPERATION_DENIED_DETAIL = (
    "Your client access level does not permit this action"
)


@dataclass(frozen=True, slots=True)
class ClientAccessCeiling:
    """The resolved client-access ceiling for one organisation member."""

    organization_id: str
    profile: str
    state: str
    relationship_id: str


async def resolve_client_ceiling(
    current_user: Optional[AuthUser],
    repos: Any,
    organization_id: Optional[str],
) -> Optional[ClientAccessCeiling]:
    """Return the client-access ceiling for ``current_user`` on ``organization_id``.

    ``None`` means "no client ceiling applies" — a direct customer, an internal
    staff member, a Processing Entity staff member, a consultant principal, a
    non-member, or a caller acting on an organisation that is not its own. In
    every such case the historical organisation-plane behaviour is unchanged.
    """
    if current_user is None or not organization_id:
        return None

    # Only an ORGANISATION MEMBER can be a client user: CarbonTally internal
    # staff, Processing Entity staff and consultants have their own planes
    # (identity separation, AGENTS.md §45). Internal staff keep their
    # operational cross-organisation bypass.
    if getattr(current_user, "is_internal_staff", False):
        return None
    if getattr(current_user, "is_entity_staff", False):
        return None
    if not getattr(current_user, "is_org_member", False):
        return None

    # Only the caller's OWN organisation can be a consultant-managed client for
    # them. A foreign organisation is decided by the existing tenant guards
    # (``ensure_org_access`` / ``enforce_org_path_scope``), never here.
    bound_org = getattr(current_user, "organization_id", None)
    if not bound_org or str(bound_org) != str(organization_id):
        return None

    consultants = getattr(repos, "consultants", None)
    if consultants is None:
        # No relationship store → no consultant relationship → no ceiling. A
        # direct customer's organisation is unaffected.
        return None
    relationship = await consultants.get_relationship_for_org(str(organization_id))
    if relationship is None:
        # A direct customer / unlinked organisation: no consultant relationship,
        # so the client-access ceiling does not apply.
        return None

    profile = normalise_profile(getattr(relationship, "client_access_profile", None))
    state = resolve_relationship_state(
        getattr(relationship, "status", None),
        bool(getattr(relationship, "retained_read_only", False)),
    )
    return ClientAccessCeiling(
        organization_id=str(organization_id),
        profile=profile,
        state=state,
        relationship_id=str(getattr(relationship, "id", "") or ""),
    )


async def enforce_client_operation(
    current_user: Optional[AuthUser],
    repos: Any,
    organization_id: Optional[str],
    operation: str,
) -> None:
    """Enforce the client-access ceiling for ``operation`` (fail closed).

    Fails ONLY for a client user of a consultant-managed organisation when the
    profile/relationship state does not admit the operation; every other caller
    (direct customer, consultant, internal staff, PE staff) is unaffected.
    """
    ceiling = await resolve_client_ceiling(current_user, repos, organization_id)
    if ceiling is None:
        return
    if not profile_allows(operation, ceiling.profile, ceiling.state):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CLIENT_OPERATION_DENIED_DETAIL,
        )


def require_client_operation(operation: str):
    """Dependency factory: bound an organisation-plane write by the client ceiling.

    Must be used as ``Depends(require_client_operation("edit_master_data"))``
    (see ``require_org_member`` for the no-parentheses hazard). Applies to the
    CALLER'S OWN organisation — the only organisation that can be a
    consultant-managed client for them — so a consultant, internal/PE staff or a
    direct customer is never affected.
    """

    async def client_operation_checker(
        current_user: AuthUser = Depends(get_current_user),
        repos: RepositoryBundle = Depends(get_repositories),
    ) -> AuthUser:
        await enforce_client_operation(
            current_user,
            repos,
            getattr(current_user, "organization_id", None),
            operation,
        )
        return current_user

    return client_operation_checker
