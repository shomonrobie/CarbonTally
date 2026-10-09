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

#: Reason codes surfaced to clients (no internal detail leaks).
_DENIED_NOT_ENABLED = (
    "Manual processing is not enabled for this organisation. "
    "A CarbonTally administrator must enable it."
)
_DENIED_NOT_ENTITLED = (
    "Manual processing is not included in this organisation's subscribed plan. "
    "The organisation must subscribe to a plan that includes Manual Processing "
    "before it can be enabled."
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
    """Resolve the EFFECTIVE Manual Processing state for the caller/target pair.

    Subscription entitlement is the FIRST gate (PO decision): the effective
    value is

        subscription_entitled AND governance_enabled

    so a stale or manually-inserted governance grant can never bypass the
    subscription requirement. The CarbonTally platform operator keeps its
    documented exemption (CarbonTally internal staff perform the platform's own
    processing work).
    """
    if await is_platform_operator(current_user, repos):
        return EffectiveManualProcessing(
            enabled=True, source_level="platform_operator", entitled=None
        )
    context = await resolve_org_context(repos, current_user, organization_id)
    governance = await repos.manual_processing.effective_for_context(context)
    # Local import avoids a module cycle (the service imports the domain only).
    from services.manual_processing_routing import ManualProcessingRouter

    entitlement = await ManualProcessingRouter(repos).entitlement_for(organization_id)
    effective_enabled = bool(entitlement.entitled) and bool(governance.enabled)
    return EffectiveManualProcessing(
        enabled=effective_enabled,
        source_level=governance.source_level,
        source_scope_type=governance.source_scope_type,
        source_scope_id=governance.source_scope_id,
        default_off=governance.default_off,
        governance_enabled=bool(governance.enabled),
        entitled=bool(entitlement.entitled),
        # Report the MOST ACTIONABLE unmet gate: an admin enablement that is
        # missing is reported first (nothing can proceed until it is enabled);
        # entitlement is reported once enablement exists but the plan lacks it.
        denied_reason=None if effective_enabled else (
            "not_entitled"
            if (not entitlement.entitled and governance.enabled)
            else "not_enabled"
        ),
        entitlement_source=entitlement.source,
        plan_code=entitlement.plan_code,
    )


async def ensure_manual_processing_allowed(
    repos, current_user: AuthUser, organization_id: str
) -> EffectiveManualProcessing:
    """Raise 403 unless Manual Processing is effective for this organisation."""
    effective = await effective_manual_processing(repos, current_user, organization_id)
    if not effective.enabled:
        detail = (
            _DENIED_NOT_ENTITLED
            if effective.denied_reason == "not_entitled"
            else _DENIED_NOT_ENABLED
        )
        raise HTTPException(status_code=403, detail=detail)
    return effective
