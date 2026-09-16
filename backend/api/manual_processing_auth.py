"""FIN-06 — Manual Processing enforcement (server-side authorization boundary).

The governance gate is applied at every manual-processing entry point so that a
direct API call cannot bypass the admin control:

* manual-extraction batch creation (new work);
* manual-extraction item creation (adding work to a batch);
* the manual stage actions on the processing workflow (extract/map/validate/
  calculate/submit) for non-automatic (i.e. human-processed) items.

ACTOR RULES (documented interpretation of the PO decision — flagged for PO
confirmation in the FIN-06 report):

* **CarbonTally internal staff** (``staff_profiles.entity_id IS NULL``) act as the
  platform operator: they keep their existing staff permission gating
  (``can_process``/``can_extract`` etc.) and are NOT blocked by a customer-scope
  governance row. Blocking them would stop the platform's own processing work.
* **Everyone else** (organisation members/admins, consultant users, consultant
  client users) needs an effective ALLOW for the target organisation, resolved by
  most-specific-wins precedence; absence of a matching row means DENIED.
"""
from __future__ import annotations

from fastapi import HTTPException

from api.consultant_auth import resolve_consultant_firm_id
from auth import AuthUser
from domain.manual_processing import EffectiveManualProcessing, OrgContext

#: Reason code surfaced to clients (no internal detail leaks).
_DENIED_DETAIL = (
    "Manual processing is not enabled for this organisation. "
    "A CarbonTally administrator must enable it."
)


async def resolve_org_context(
    repos, current_user: AuthUser, organization_id: str
) -> OrgContext:
    """Server-resolve the relationship context for one organisation.

    Consultant callers get the firm id and the ACTIVE consultant-client grant id
    for the organisation, both resolved server-side (never from the request), so
    the governance resolver can honour consultant scopes without duplicating the
    tenancy model.
    """
    context = OrgContext(organization_id=organization_id)
    firm_id = await resolve_consultant_firm_id(current_user, repos)
    if not firm_id:
        return context
    grant = await repos.consultants.get_client_by_org(firm_id, organization_id)
    if grant is None:
        return context
    if str(getattr(grant, "status", "") or "") != "active":
        return context
    return OrgContext(
        organization_id=organization_id,
        consultant_client_id=str(getattr(grant, "id", "") or "") or None,
        consultant_firm_id=str(firm_id),
    )


async def is_platform_operator(current_user: AuthUser, repos) -> bool:
    """True for active CarbonTally internal staff (``entity_id IS NULL``)."""
    if not current_user.is_staff:
        return False
    profile = await repos.staff.get_by_user(current_user.user_id)
    if profile is None or not profile.is_active:
        return False
    return profile.entity_id is None


async def effective_manual_processing(
    repos, current_user: AuthUser, organization_id: str
) -> EffectiveManualProcessing:
    """Resolve the effective governance value for the caller/target pair."""
    if await is_platform_operator(current_user, repos):
        return EffectiveManualProcessing(
            enabled=True, source_level="platform_operator"
        )
    context = await resolve_org_context(repos, current_user, organization_id)
    return await repos.manual_processing.effective_for_context(context)


async def ensure_manual_processing_allowed(
    repos, current_user: AuthUser, organization_id: str
) -> EffectiveManualProcessing:
    """Raise 403 unless manual processing is enabled for this organisation."""
    effective = await effective_manual_processing(repos, current_user, organization_id)
    if not effective.enabled:
        raise HTTPException(status_code=403, detail=_DENIED_DETAIL)
    return effective
