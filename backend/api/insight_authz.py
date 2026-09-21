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
#:
#: The **canonical production form** is what `auth.py` sets for an organisation
#: member: ``role = f"org_{org_role}"`` and ``role_name = role`` (auth.py:313), so
#: the authenticated principal carries ``org_owner`` / ``org_admin`` /
#: ``org_member`` / ``org_viewer`` (OHD I2 F-01). The bare forms are accepted too,
#: but the ``org_`` shape is the contract the platform actually produces.
CUSTOMER_INSIGHT_ROLES = ("owner", "admin", "member", "viewer")

#: Prefix the platform's resolver applies to an organisation role (auth.py:313).
ORG_ROLE_PREFIX = "org_"

#: Auditor personas — explicitly DENIED (PO decision: auditors have no Insight).
#: No auditor role/table/permission model exists in CarbonTally (D2 §10.3), so this
#: is a named refusal of the persona rather than a new permission system.
AUDITOR_ROLE_NAMES = ("auditor", "org_auditor", "assurance_reviewer", "auditor_reviewer")

#: Existing CarbonTally staff permission that authorizes CarbonTally-internal
#: ops-wide visibility across customer organisations (`can_view_all` — the
#: permission the ops dashboard itself requires, `api/v3_operations.py:629`), plus
#: the platform's superuser flag. Staff Insight scope is bound to *these* existing
#: permissions: staff status alone grants nothing (ODH I2 O-02).
STAFF_INSIGHT_PERMISSIONS = ("can_view_all",)
STAFF_SUPERUSER_FLAG = "is_superuser"

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


def normalize_org_role(role: Optional[str]) -> str:
    """Normalise an organisation role to its bare form.

    `auth.py` produces ``org_<role>`` for organisation members (e.g. ``org_owner``),
    so both the canonical ``org_*`` shape and the bare form resolve to the same
    ratified role. Anything else is returned unchanged (and therefore fails the
    deny-by-default role check).
    """
    value = (role or "").strip().lower()
    if value.startswith(ORG_ROLE_PREFIX):
        value = value[len(ORG_ROLE_PREFIX) :]
    return value


def is_auditor_principal(current_user: Optional[AuthUser]) -> bool:
    """Explicit auditor/assurance-reviewer detection (PO decision: DENY).

    CarbonTally has no auditor role, table or permission model (D2 §10.3); if a
    principal ever carries such a role name it is refused by *name*, rather than
    only by the absence of an authorization relationship (OHD I2 O-01).
    """
    if current_user is None:
        return False
    for candidate in (getattr(current_user, "role", None), getattr(current_user, "role_name", None)):
        if (candidate or "").strip().lower() in AUDITOR_ROLE_NAMES:
            return True
    return False


def staff_context_grants_insight_scope(context) -> bool:
    """Whether the caller's *existing* staff permissions authorize Insight scope.

    Bound to the platform's existing permission vocabulary — the ops-wide customer
    visibility permission the operations dashboard itself requires, or the
    platform superuser flag. Staff identity alone grants nothing (ODH I2 O-02).
    """
    permissions = dict(getattr(context, "permissions", None) or {})
    if any(permissions.get(name) is True for name in STAFF_INSIGHT_PERMISSIONS):
        return True
    return permissions.get(STAFF_SUPERUSER_FLAG) is True


async def organization_is_active(repos: RepositoryBundle, organization_id: str) -> bool:
    """The organisation must exist and be ACTIVE to be an Insight scope.

    OHD I2 F-02: the backend pool bypasses the RLS suspension predicate, so this
    check is performed explicitly. It is narrow to the Insight boundary — no global
    organisation-authorization behaviour is changed.
    """
    lookup = getattr(repos.organizations, "get_by_id", None)
    if lookup is None:
        # No organisation repository surface: fail closed rather than assume active.
        return False
    organization = await lookup(organization_id)
    return organization is not None and bool(getattr(organization, "is_active", False))


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

    # 0. Explicit auditor refusal (PO decision) — named, not an accident of
    #    fall-through (OHD I2 O-01).
    if is_auditor_principal(current_user):
        raise _denied("Auditors receive no CarbonTally Insight access")

    # 0b. The organisation must exist and be ACTIVE (OHD I2 F-02). The backend
    #     pool bypasses the RLS suspension predicate, so this is checked here.
    if not await organization_is_active(repos, organization_id):
        raise _denied("Organization access denied")

    # 1. CarbonTally-internal staff/admin scope. Bound to the caller's *existing*
    #    staff permissions (can_view_all / superuser); staff identity alone grants
    #    nothing, and a staff member without that permission simply gains no staff
    #    scope (ODH I2 O-02).
    staff = await resolve_staff_context(current_user, repos)
    if staff is not None:
        if staff.profile.entity_id is not None:
            raise _denied("Processing Entity users receive no CarbonTally Insight access")
        if staff_context_grants_insight_scope(staff):
            return InsightAccess(
                user_id=current_user.user_id,
                organization_id=organization_id,
                persona=PERSONA_STAFF_INTERNAL,
                staff_permissions=dict(staff.permissions or {}),
            )

    # 2. Customer scope — the caller's own organisation only, using the role shape
    #    the platform's resolver actually produces (``org_owner`` … ``org_viewer``).
    if current_user.is_org_member and current_user.organization_id:
        if organization_id != current_user.organization_id:
            raise _denied()
        if normalize_org_role(current_user.role) not in CUSTOMER_INSIGHT_ROLES:
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
    principal *is*. Auditor is checked first so an auditor identity is named even
    when it also carries a membership (OHD I2 O-01).
    """
    if current_user is None or not getattr(current_user, "user_id", None):
        return PERSONA_UNAUTHENTICATED
    if is_auditor_principal(current_user):
        return PERSONA_AUDITOR
    if current_user.is_entity_staff:
        return PERSONA_PROCESSING_ENTITY
    if current_user.is_internal_staff:
        return PERSONA_STAFF_INTERNAL
    # Customer membership uses the production ``org_<role>`` shape (auth.py:313).
    if current_user.is_org_member and current_user.organization_id:
        if normalize_org_role(current_user.role) in CUSTOMER_INSIGHT_ROLES:
            return PERSONA_CUSTOMER
        return PERSONA_NON_MEMBER
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
