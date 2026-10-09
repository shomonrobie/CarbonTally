"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — Plane C client-portal authorization
(F-3, F-4, F-5, F-7; §11 MUST-1/2/3/8/9, §6.2 resolution order).

Plane C is the CLIENT portal at ``/portal/:clientId/*`` (PO-8 A). ``:clientId``
identifies the CLIENT ORGANISATION. The authenticated actor is a CLIENT USER
(I2) — an organisation member of that organisation, whose organisation is
served by a consultant firm. This module is the single server-side gate for
that plane.

The resolution order (§6.2) is enforced here and fails CLOSED at every step:

    authenticated client identity
      -> the organisation resolved from :clientId must be the actor's own
         organisation (INV-B/INV-C: a foreign :clientId is denied generically,
         with no existence oracle)
      -> the organisation must be served by a consultant relationship (else it
         is a direct customer and Plane C does not apply)
      -> the relationship state must be ACTIVE or RETAINED-READ-ONLY (INV-E)
      -> the firm must be ENTITLED to a client plane (STANDARD has none)
      -> the CLIENT ACCESS PROFILE is the CEILING for every read and write

The UI is never the security boundary (§44). Every portal route calls into this
module; a client cannot change clientId, Organisation or tenant through the URL.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, HTTPException

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, get_current_user
from domain.branding import (
    BrandContext,
    default_brand_context,
    resolve_brand_context,
)
from domain.consultant_entitlement import resolve_entitlements, resolve_mode
from domain.partners import ConsultantClient
from domain.relationship_access import (
    STATE_ACTIVE,
    normalise_profile,
    profile_allows,
    resolve_relationship_state,
    state_has_client_plane,
)

#: The single, non-disclosing denial detail. Every authorization failure on
#: Plane C returns this — the same response whether the organisation exists,
#: belongs to another tenant, has no consultant, or is paused (§11.4, AC-F-17,
#: AC-S-10: no existence oracle, no timing/identifier leak).
PORTAL_DENIED_DETAIL = "Client portal access is not available for this workspace"


def _deny(status_code: int = 403) -> HTTPException:
    return HTTPException(status_code=status_code, detail=PORTAL_DENIED_DETAIL)


@dataclass(frozen=True, slots=True)
class ClientPortalContext:
    """The resolved, server-authoritative Plane C context."""

    organization_id: str
    organization_name: str
    firm_id: str
    firm_name: str
    brand: BrandContext
    mode: str
    profile: str
    state: str
    retained_read_only: bool
    relationship: ConsultantClient

    @property
    def is_retained(self) -> bool:
        return self.state != STATE_ACTIVE


async def resolve_client_portal_context(
    current_user: Optional[AuthUser],
    repos: RepositoryBundle,
    client_id: str,
) -> ClientPortalContext:
    """Resolve (or deny) a Plane C context. Raises a generic 403 on any denial."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Staff/consultant/entity identities have their OWN planes; they are never
    # admitted to the client plane (§7.1 identity separation, AGENTS §45).
    if getattr(current_user, "is_internal_staff", False) or getattr(
        current_user, "is_entity_staff", False
    ):
        raise _deny()

    # MUST-1 / INV-B / INV-C — the actor must be an organisation member of the
    # organisation named by :clientId. A foreign :clientId is denied generically.
    if not getattr(current_user, "is_org_member", False):
        raise _deny()
    if str(getattr(current_user, "organization_id", "") or "") != str(client_id):
        raise _deny()

    relationship = await repos.consultants.get_relationship_for_org(client_id)
    if relationship is None:
        # Not a consultant-managed organisation -> Plane C does not apply.
        raise _deny()

    profile = normalise_profile(relationship.client_access_profile)
    state = resolve_relationship_state(
        relationship.status, relationship.retained_read_only
    )
    if not state_has_client_plane(state):
        # INV-E / AC-S-4 — only ACTIVE or RETAINED may use the plane.
        raise _deny()

    firm_profile = await repos.consultants.get_profile_by_id(
        relationship.consultant_id
    )
    branding = await repos.consultants.get_branding(relationship.consultant_id)
    mode = resolve_mode(
        getattr(branding, "commercial_mode", None) if branding else None,
        bool(getattr(branding, "white_label_enabled", False)) if branding else False,
        bool(getattr(branding, "co_branding_enabled", False)) if branding else False,
    )
    entitlements = resolve_entitlements(mode)
    if not entitlements.client_plane:
        # MUSTNOT-5 / AC-F-16 — a STANDARD firm has no client plane at all.
        raise _deny()

    brand = (
        resolve_brand_context(branding, firm_profile.company_name)
        if firm_profile is not None
        else default_brand_context()
    )

    organization = await repos.organizations.get(client_id)
    organization_name = getattr(organization, "name", None) or "Your organisation"

    return ClientPortalContext(
        organization_id=str(client_id),
        organization_name=str(organization_name),
        firm_id=str(relationship.consultant_id),
        firm_name=(
            brand.display_name
            if brand.kind != "carbon_tally"
            else (firm_profile.company_name if firm_profile else "Your consultant")
        ),
        brand=brand,
        mode=mode,
        profile=profile,
        state=state,
        retained_read_only=bool(relationship.retained_read_only),
        relationship=relationship,
    )


def ensure_client_operation(context: ClientPortalContext, operation: str) -> None:
    """Enforce the profile CEILING for one operation (§8.2/§8.3, PO-9).

    Raises the generic denial when the profile/state does not admit the
    operation. PO-9 operations (map_factors / edit_mappings / recalculate) are
    ALWAYS denied here, in every profile and state.
    """
    if not profile_allows(operation, context.profile, context.state):
        raise _deny()


async def require_client_portal_context(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ClientPortalContext:
    """FastAPI dependency for the ``/portal`` route family."""
    return await resolve_client_portal_context(current_user, repos, client_id)


#: The operations reported to the client plane as a UI hint. Presentation only —
#: enforcement is ``ensure_client_operation``.
_UI_OPERATIONS: dict[str, str] = {
    "read_data": "read_data",
    "read_reports": "read_reports",
    "read_evidence": "read_evidence",
    "comment": "comment",
    "upload_document": "upload_document",
    "edit_master_data": "edit_master_data",
    "correct_submitted_data": "correct_submitted_data",
    "approve_final": "approve_final",
    "map_factors": "map_factors",
    "recalculate": "recalculate",
}


def portal_capabilities(context: ClientPortalContext) -> dict[str, Any]:
    """The operation matrix for the UI (NOT a security boundary)."""
    return {
        name: profile_allows(op, context.profile, context.state)
        for name, op in _UI_OPERATIONS.items()
    }
