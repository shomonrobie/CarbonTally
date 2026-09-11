"""V3 actor-context resolver — ``GET /api/v3/me/context``.

Phase 3 / P1-B — the single SERVER-AUTHORITATIVE post-login workspace
resolver. It replaces the frontend probe-chain (org → staff → consultant) that
treated ANY failure (500/403/network) as "brand-new customer" and misrouted
existing users to organisation onboarding.

Design (documented in the identity/workspace/onboarding audit; this is the
approved Phase-1 endpoint):

* Precedence: CarbonTally internal staff → Processing Entity staff →
  consultant → customer organisation member → brand-new user.
* Existing identity resolution is REUSED, never duplicated:
  - ``AuthUser`` (from ``auth.get_current_user``) already resolves staff /
    entity / organisation membership authoritatively;
  - consultant identity reuses ``resolve_consultant_context`` (the same
    resolution ``require_consultant`` uses).
* FAIL-CLOSED: any resolution error (e.g. the database is unreachable) raises
  HTTP 500 — it can never be reported as "brand-new user".
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.consultant_auth import resolve_consultant_context
from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/v3", tags=["Context"])


@router.get("/me/context")
async def me_context(
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Resolve the authenticated actor's workspace + destination.

    Returns ``destination`` (the route the frontend must navigate to) plus
    minimal workspace context. Errors are never interpreted as "new user":
    a resolution failure raises HTTP 500 so the caller can show a controlled
    error/retry state.
    """
    if current_user is None:
        raise HTTPException(
            status_code=401, detail="Authentication required"
        )

    # 1. CarbonTally internal staff → /ops (Internal Operations hub).
    if current_user.is_staff and not current_user.is_entity_staff:
        return {
            "actor_type": "staff",
            "workspaces": ["ops"],
            "primary_workspace": "ops",
            "destination": "/ops",
            "organization": None,
            "staff": {
                "role": current_user.role_name or current_user.role,
                "entity_id": None,
            },
            "consultant": None,
        }

    # 1b. Processing Entity staff → /pe (dedicated PE application shell).
    # V1.2 final architecture: PE work happens in the PE-only application
    # (PEShell), NOT inside the CarbonTally Internal Operations hub.
    if current_user.is_staff and current_user.is_entity_staff:
        return {
            "actor_type": "entity_staff",
            "workspaces": ["pe"],
            "primary_workspace": "pe",
            "destination": "/pe",
            "organization": None,
            "staff": {
                "role": current_user.role_name or current_user.role,
                "entity_id": current_user.entity_id,
            },
            "consultant": None,
        }

    # 2. Consultant (active firm member) → /consultant.
    consultant = await resolve_consultant_context(current_user, repos)
    if consultant is not None:
        return {
            "actor_type": "consultant",
            "workspaces": ["consultant"],
            "primary_workspace": "consultant",
            "destination": "/consultant",
            "organization": None,
            "staff": None,
            "consultant": {
                "profile_id": consultant.profile.id,
                "firm_id": consultant.profile.id,
                "role": consultant.firm_member.role,
            },
        }

    # 3. Customer organisation member → /home.
    if current_user.is_org_member and current_user.organization_id:
        org_name = None
        org = await repos.organizations.get(current_user.organization_id)
        if org is not None:
            org_name = org.name
        return {
            "actor_type": "customer",
            "workspaces": ["customer"],
            "primary_workspace": "customer",
            "destination": "/home",
            "organization": {
                "id": current_user.organization_id,
                "name": org_name,
                "role": current_user.role_name or current_user.role,
            },
            "staff": None,
            "consultant": None,
        }

    # 4. Authenticated but no org/staff/consultant relationship → brand-new
    #    customer onboarding (D35). Reached ONLY when every resolution above
    #    definitively found nothing — never on error.
    return {
        "actor_type": "new_user",
        "workspaces": ["onboarding"],
        "primary_workspace": "onboarding",
        "destination": "/onboarding",
        "organization": None,
        "staff": None,
        "consultant": None,
    }
