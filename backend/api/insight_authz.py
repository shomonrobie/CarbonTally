"""CarbonTally Insight — I2 authorization and visibility layer.

Authorization: `CT-P8-INSIGHT-I2-I8-MASTER-20260921-001` (I2 only).
I1 precondition: independently verified by OHD (`66adfb5`, verdict PASS).

Ratified authority:

* **D2** §8 (authorization boundary; stored references are not grants; order of
  operations = server-side authorization → scope resolution → RLS → tools),
  §9.1/§9.2/§9.6 (initial visibility = **creator-private**, scoped to
  organisation + creator), §10.4 (PE receive no Insight capability).
* **PO decision (2026-09-21)** — the Insight access model:
  * customer users → Insight for their own authorized organisation;
  * consultants → Insight for customer organisations where the existing
    CarbonTally consultant→customer authorization relationship exists;
  * authorized CarbonTally staff/admin → Insight for internal intelligence
    within their existing staff/admin permissions;
  * auditors → NO access; PE → NO access; public → NO access.

This module is the **single authorization entry point** for the Insight surface.
It does not invent an access model: it *reuses* the platform's authoritative
resolvers —

* customer scope → `auth` organisation membership (already resolved per request
  from ``organization_members WHERE is_active = TRUE``);
* consultant scope → `api.consultant_auth.ensure_consultant_org_access`
  (D15: an ACTIVE ``consultant_clients`` grant, the platform's single source of
  the consultant→customer relationship — no parallel model exists or is created);
* staff scope → `api.operations_auth.resolve_staff_context`
  (an ACTIVE ``staff_profiles`` row and its ``staff_roles.permissions``;
  ``staff_profiles.entity_id IS NULL`` = CarbonTally internal staff).

Creator-private visibility (D2 §9.2) is preserved for **every** persona,
including staff: the PO decision authorizes staff *use* of Insight for internal
intelligence, not the reading of another user's private conversations. Staff data
scope ("within their existing staff/admin permissions") is enforced at the
controlled-tool layer and is a binding I3 invariant — nothing here grants it.

Explicitly NOT implemented (later authorized stages): controlled tools and data
scope (I3), AI interaction records and canonical audit (I4), context (I5), the
Insight UI (I6), retention/privacy/export (I7), providers/billing/hardening (I8).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import Depends, HTTPException, status

from api.consultant_auth import ensure_consultant_org_access
from api.dependencies import RepositoryBundle
from api.operations_auth import resolve_staff_context
from auth import AuthUser, get_current_user

#: D2 §9.1/§9.2 — the only ratified conversation-visibility model.
INSIGHT_VISIBILITY_MODEL = "creator_private"

#: D2 §9.5 / PO decision — customer roles that may use Insight.
CUSTOMER_INSIGHT_ROLES = ("owner", "admin", "member", "viewer")

#: Persona vocabulary (explicit, enumerable, testable).
PERSONA_CUSTOMER = "customer"
PERSONA_CONSULTANT = "consultant"
PERSONA_STAFF_INTERNAL = "staff_internal"
PERSONA_PROCESSING_ENTITY = "processing_entity"
PERSONA_AUDITOR = "auditor"
PERSONA_NON_MEMBER = "non_member"
PERSONA_UNAUTHENTICATED = "unauthenticated"

#: Decision table: persona -> decision. Deny is enumerated, never implicit.
PERSONA_DECISIONS: dict[str, str] = {
    PERSONA_CUSTOMER: "ALLOW — own authorized organisation, creator-private",
    PERSONA_CONSULTANT: "ALLOW — organization covered by an ACTIVE consultant-client grant, creator-private",
    PERSONA_STAFF_INTERNAL: "ALLOW — CarbonTally-internal intelligence scope (existing staff profile), creator-private",
    PERSONA_PROCESSING_ENTITY: "DENY — PE receive no Insight capability (D2 §10.4, PO decision)",
    PERSONA_AUDITOR: "DENY — auditors receive no Insight access (PO decision)",
    PERSONA_NON_MEMBER: "DENY — no established authorization relationship for this organisation",
    PERSONA_UNAUTHENTICATED: "DENY — no authenticated principal",
}


@dataclass(frozen=True)
class InsightAccess:
    """The authorized Insight caller for one request.

    ``organization_id`` + ``user_id`` are the (organisation, creator) scope of
    D2 §9.6. ``persona`` records *which* existing authorization relationship
    granted the scope, so staff/consultant/customer access can never be
    conflated and the grant is auditable. ``staff_permissions`` is carried for
    the later controlled-tool layer (I3) and grants nothing by itself.
    """

    user_id: str
    organization_id: str
    persona: str
    visibility: str = INSIGHT_VISIBILITY_MODEL
    staff_permissions: dict[str, Any] = field(default_factory=dict)


def _denied(detail: str = "CarbonTally Insight access denied") -> HTTPException:
    """Uniform, non-disclosing denial."""
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def require_insight_user(
    current_user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """Router-level gate: authenticated, non-PE principals only.

    Attached to the Insight router so every present and future Insight route is
    deny-by-default (D2 §8.5). Persona/scope resolution happens per request in
    :func:`authorize_insight_scope`, because the organization scope arrives in
    the body (POST) or the query string (GET).
    """
    if current_user is None or not getattr(current_user, "user_id", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.is_entity_staff:
        # PE receive no Insight capability at all (D2 §10.4 / PO decision).
        raise _denied("Processing Entity users receive no CarbonTally Insight access")
    return current_user


async def authorize_insight_scope(
    current_user: AuthUser,
    repos: RepositoryBundle,
    organization_id: str,
) -> InsightAccess:
    """Resolve the caller's authorized scope for one organisation, or deny.

    Evaluation order (scope before role — AGENTS.md §7 / D20):

    1. **Internal staff** — an ACTIVE ``staff_profiles`` row with
       ``entity_id IS NULL`` (``resolve_staff_context``, the same resolver the
       ops surface uses). Staff scope is CarbonTally-internal and is therefore
       evaluated *before* organisation membership, so staff access is never a
       side effect of customer membership (OHD F-01). A staff-shaped identity
       with **no active staff profile** gains no staff scope and falls through
       to the ordinary customer/consultant rules.
    2. **Customer** — active member of the requested organisation, and only that
       organisation.
    3. **Consultant** — the firm holds an ACTIVE ``consultant_clients`` grant for
       the organisation (``ensure_consultant_org_access``, D15). No parallel
       consultant→customer model exists or is created.
    4. Otherwise **deny**, without disclosing which check failed.
    """
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is required",
        )
    if current_user is None or not getattr(current_user, "user_id", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if current_user.is_entity_staff:
        raise _denied("Processing Entity users receive no CarbonTally Insight access")

    # 1. CarbonTally-internal staff/admin scope (explicit staff authorization).
    staff = await resolve_staff_context(current_user, repos)
    if staff is not None:
        if staff.profile.entity_id is not None:
            raise _denied("Processing Entity users receive no CarbonTally Insight access")
        return InsightAccess(
            user_id=current_user.user_id,
            organization_id=organization_id,
            persona=PERSONA_STAFF_INTERNAL,
            staff_permissions=dict(staff.permissions or {}),
        )

    # 2. Customer scope — the caller's own organisation only.
    if current_user.is_org_member and current_user.organization_id:
        if organization_id != current_user.organization_id:
            raise _denied()
        if (current_user.role or "").lower() not in CUSTOMER_INSIGHT_ROLES:
            raise _denied()
        return InsightAccess(
            user_id=current_user.user_id,
            organization_id=organization_id,
            persona=PERSONA_CUSTOMER,
        )

    # 3. Consultant scope — the platform's active consultant-client grant.
    try:
        await ensure_consultant_org_access(current_user, repos, organization_id)
    except HTTPException:
        raise _denied() from None
    return InsightAccess(
        user_id=current_user.user_id,
        organization_id=organization_id,
        persona=PERSONA_CONSULTANT,
    )


def resolve_insight_persona(current_user: Optional[AuthUser]) -> str:
    """Identity-only classification (no database), for tests and diagnostics.

    Scope-bearing personas are resolved by :func:`authorize_insight_scope`,
    which is the authorization decision. This helper only names what the
    principal *is*.
    """
    if current_user is None or not getattr(current_user, "user_id", None):
        return PERSONA_UNAUTHENTICATED
    if current_user.is_entity_staff:
        return PERSONA_PROCESSING_ENTITY
    if current_user.is_internal_staff:
        return PERSONA_STAFF_INTERNAL
    if current_user.is_org_member and current_user.organization_id:
        return PERSONA_CUSTOMER
    return (
        PERSONA_CONSULTANT
        if (current_user.role or "").lower() == "consultant"
        else PERSONA_NON_MEMBER
    )


def visibility_created_by(access: InsightAccess) -> str:
    """The creator filter realising D2 §9.2 — creator-private, all personas.

    Always the concrete principal id: no shared, team, admin or staff
    "see-everything" mode exists in the ratified model, so none is expressible.
    """
    return access.user_id


def conversation_is_visible(access: InsightAccess, conversation) -> bool:
    """Both boundaries at once — organisation **and** creator (D2 §9.6).

    A conversation outside the authorized organisation, or created by another
    principal, is invisible; a stored id is never a grant (D2 §8.4).
    """
    return (
        conversation is not None
        and conversation.organization_id == access.organization_id
        and conversation.created_by == access.user_id
    )
