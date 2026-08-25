"""V3 consultant authorization (Phase 7).

The consultant→firm→client authorization chain implemented server-side. It
mirrors the authoritative RLS helper ``public.is_org_consultant(org)``:

    authenticated user
        → consultant profile (active)
        → consultant firm membership (active)
        → client grant for the target organisation
            (firm member's ``client_access`` contains the org id
             OR the firm has a ``consultant_clients`` row for the org)

Every consultant-facing endpoint must pass ``require_consultant()`` and then
``ensure_consultant_org_access`` for any organisation the consultant touches —
the browser-supplied ``organization_id``/``client_id`` is never trusted
without this server-side re-authorization.

Consultant action permissions use the real ``consultant_firm_members``
``can_manage_clients`` / ``can_upload_documents`` / ``can_generate_reports`` /
``can_manage_team`` columns (no invented permission matrix).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, get_current_user
from domain.partners import ConsultantFirmMember, ConsultantProfile

#: The consultant role names the schema/seed uses (informational only — the
#: ``can_*`` flag columns are the actual authorization surface).
CONSULTANT_ROLES: tuple[str, ...] = ("owner", "manager", "consultant", "viewer")

#: The real permission columns on ``consultant_firm_members``.
CONSULTANT_PERMISSIONS: dict[str, str] = {
    "manage_clients": "can_manage_clients",
    "upload_documents": "can_upload_documents",
    "generate_reports": "can_generate_reports",
    "manage_team": "can_manage_team",
}

#: ``consultant_clients.status`` values used by the existing repository surface.
#: D19 lifecycle vocabulary: only ``active`` grants access (D15); ``suspended``
#: and ``ended`` carry no access; ``inactive`` is the legacy soft-deactivate.
CLIENT_STATUSES: tuple[str, ...] = ("active", "suspended", "ended", "inactive")


@dataclass(frozen=True, slots=True)
class ConsultantContext:
    """The authenticated consultant's identity (profile + firm membership)."""

    profile: ConsultantProfile
    firm_member: ConsultantFirmMember


async def _resolve_context(
    current_user: AuthUser, repos: RepositoryBundle
) -> Optional[ConsultantContext]:
    profile = await repos.consultants.get_profile_by_user(current_user.user_id)
    if profile is None or not profile.is_active:
        return None
    member = await repos.consultants.get_firm_member_by_user(profile.id, current_user.user_id)
    if member is None or not member.is_active:
        return None
    return ConsultantContext(profile=profile, firm_member=member)


async def resolve_consultant_context(
    current_user: AuthUser, repos: RepositoryBundle
) -> Optional[ConsultantContext]:
    """Non-raising consultant identity resolution (D21 brand-context use).

    Returns ``None`` for any non-consultant caller (customer, Processing
    Entity staff, internal staff without a consultant profile). Never raises —
    used by surfaces that fall back to CarbonTally branding instead of
    rejecting the request.
    """
    if current_user is None:
        return None
    return await _resolve_context(current_user, repos)


async def require_consultant(
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> ConsultantContext:
    """Dependency: the caller must be an active consultant firm member."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    context = await _resolve_context(current_user, repos)
    if context is None:
        raise HTTPException(
            status_code=403,
            detail="Consultant access required (active consultant firm membership)",
        )
    return context


def ensure_consultant_permission(
    context: ConsultantContext, permission: str
) -> None:
    """Reject an action the firm member's real permission flags do not allow."""
    column = CONSULTANT_PERMISSIONS.get(permission)
    if column is None:
        raise HTTPException(status_code=422, detail=f"unknown consultant permission {permission!r}")
    if not getattr(context.firm_member, column, False):
        raise HTTPException(
            status_code=403,
            detail=f"consultant lacks permission: {permission}",
        )


async def ensure_consultant_org_access(
    current_user: AuthUser,
    repos: RepositoryBundle,
    organization_id: str,
) -> ConsultantContext:
    """Authorize the consultant to act on ``organization_id``.

    D15 (APPROVED 2026-08-20): consultant access to a client is based on an
    ACTIVE consultant-client authorization (``consultant_clients.status =
    'active'``). When the relationship ends, consultant access to that client
    ends. The active grant row is the single source of the relationship —
    ``client_access`` (a per-member shortcut) does not independently grant
    organisation access.
    """
    if not organization_id:
        raise HTTPException(status_code=422, detail="organization_id is required")
    context = await _resolve_context(current_user, repos)
    if context is None:
        raise HTTPException(status_code=403, detail="Consultant access required")
    client = await repos.consultants.get_client_by_org(
        context.profile.id, organization_id
    )
    if client is None or client.status != "active":
        raise HTTPException(
            status_code=403,
            detail=(
                "Consultant is not authorized for this client organization "
                "(active consultant-client grant required)"
            ),
        )
    return context
