"""Consultant brand-context resolution (D21.4 / D21.6 / D21.7).

The authoritative principle: a surface's brand is ALWAYS derived from the
authenticated, server-verified relationship — never from a client-supplied
``consultant_id`` or URL query parameter. These resolvers are the only entry
points the API surfaces use:

* ``resolve_consultant_branding`` — the caller's OWN firm's branding (the
  caller is already an active consultant firm member).
* ``resolve_report_branding`` — a report's presentation brand: the caller's
  own firm ONLY when the caller is a consultant holding an ACTIVE
  consultant-client grant (D15) for the report's organisation; otherwise the
  CarbonTally fallback (Direct Customers / internal staff / entity staff).

Both are derived from authorized context, so a consultant can never cause
another consultant's branding to appear (cross-consultant isolation).
"""
from __future__ import annotations

from typing import Optional

from api.consultant_auth import resolve_consultant_context
from auth import AuthUser
from domain.branding import (
    BrandContext,
    ConsultantBranding,
    default_brand_context,
    default_branding_dict,
    resolve_brand_context,
)
from domain.partners import ConsultantProfile

__all__ = [
    "BrandContext",
    "ConsultantBranding",
    "default_brand_context",
    "default_branding_dict",
    "resolve_brand_context",
    "resolve_consultant_branding",
    "resolve_report_branding",
]


async def resolve_consultant_branding(
    repos, profile: ConsultantProfile
) -> BrandContext:
    """Resolve the caller's OWN firm branding (already authorized)."""
    branding = await repos.consultants.get_branding(profile.id)
    return resolve_brand_context(branding, profile.company_name)


async def resolve_report_branding(
    repos, current_user: Optional[AuthUser], organization_id: str
) -> BrandContext:
    """Resolve the brand a report surface should present.

    A consultant's brand applies only when the caller holds an ACTIVE grant
    (D15) for the report's organisation. Everyone else — Direct Customers,
    Processing Entity staff, internal staff — receives the CarbonTally
    fallback (Test H / Test I).
    """
    if not organization_id or current_user is None:
        return default_brand_context()
    context = await resolve_consultant_context(current_user, repos)
    if context is None:
        return default_brand_context()
    client = await repos.consultants.get_client_by_org(
        context.profile.id, organization_id
    )
    if client is None or getattr(client, "status", None) != "active":
        return default_brand_context()
    return await resolve_consultant_branding(repos, context.profile)
