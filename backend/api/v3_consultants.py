"""V3 consultant surface (V3 Phase 7).

Consultant profiles, firm teams, multi-client grants, tasks and the client
workspace. Every endpoint now establishes the consultant identity via
``require_consultant`` and re-authorizes any organisation/client the consultant
touches via ``ensure_consultant_org_access`` (mirroring the authoritative
``is_org_consultant`` RLS helper). The browser-supplied ids are never trusted
without this server-side check.
"""
from __future__ import annotations

import re
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, ConfigDict, field_validator

from api.consultant_auth import (
    CLIENT_STATUSES,
    CONSULTANT_ROLES,
    ConsultantContext,
    ensure_consultant_org_access,
    ensure_consultant_permission,
    ensure_consultant_revocation_authority,
    require_consultant,
)
from api.consultant_branding import (
    default_branding_dict,
    resolve_consultant_branding,
)
from api.dependencies import (
    RepositoryBundle,
    get_audit_logger,
    get_repositories,
    get_request_context,
)
from auth import AuthUser, get_current_user
from infra.audit_logger import AuditLogger
from services.billing import resolve_registration_mode

router = APIRouter(prefix="/api/v3/consultants", tags=["V3 — Consultants"])

#: Simple email/URL/colour validation shared by the D21 branding surface.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_HTTP_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


class BrandingUpdate(BaseModel):
    """The firm's self-service branding configuration (D21.1 / D21.14).

    Every field is optional so a client can send a partial update. The
    validated fields map 1:1 onto the existing ``consultant_profiles``
    branding columns — no duplicate branding table.
    """

    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    footer_text: Optional[str] = None
    email_from: Optional[str] = None
    website: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    support_hours: Optional[str] = None
    client_portal_url: Optional[str] = None
    white_label_enabled: Optional[bool] = None
    co_branding_enabled: Optional[bool] = None

    @field_validator("brand_name")
    @classmethod
    def _clean_brand_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 200:
            raise ValueError("brand_name must be 200 characters or fewer")
        return value or None

    @field_validator("logo_url", "website", "client_portal_url")
    @classmethod
    def _validate_http_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 2048:
            raise ValueError("URL must be 2048 characters or fewer")
        if not _HTTP_URL_RE.match(value):
            raise ValueError("must be an absolute http(s) URL")
        return value

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_colour(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip().lower()
        if not _COLOR_RE.match(value):
            raise ValueError("colour must be a hex value like #0f766e")
        return value

    @field_validator("email_from", "support_email")
    @classmethod
    def _validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 320 or not _EMAIL_RE.match(value):
            raise ValueError("must be a valid email address")
        return value

    @field_validator("footer_text")
    @classmethod
    def _clean_footer(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 2000:
            raise ValueError("footer_text must be 2000 characters or fewer")
        return value or None

    @field_validator("support_phone")
    @classmethod
    def _clean_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 100:
            raise ValueError("support_phone must be 100 characters or fewer")
        return value or None

    @field_validator("support_hours")
    @classmethod
    def _clean_hours(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 200:
            raise ValueError("support_hours must be 200 characters or fewer")
        return value or None


def _can_manage_branding(context: ConsultantContext) -> bool:
    """Firm-level branding administration permission (D21.2 / D21.14).

    Uses the existing consultant authorization surface: the firm owner or any
    member with the ``can_manage_team`` flag (the firm-administration
    permission). No new permission column is introduced.
    """
    return (
        context.firm_member.role == "owner"
        or bool(context.firm_member.can_manage_team)
    )



class ProfileCreate(BaseModel):
    company_name: str


class ClientCreate(BaseModel):
    organization_id: str
    client_name: str
    client_industry: Optional[str] = None
    client_contact_email: Optional[str] = None
    client_contact_name: Optional[str] = None


class ClientStatusUpdate(BaseModel):
    status: str


class FirmMemberCreate(BaseModel):
    user_id: str
    role: str = "consultant"


class TaskCreate(BaseModel):
    task_title: str
    task_type: Optional[str] = None
    priority: Optional[str] = None
    client_id: Optional[str] = None
    metadata: dict = {}


async def _checked_client(
    current_user: AuthUser,
    context: ConsultantContext,
    repos: RepositoryBundle,
    client_id: str,
):
    """Load a client grant and verify the caller's firm owns it.

    Ownership-only: the firm may manage its own grant rows (view status,
    deactivate, reactivate) even when the grant is inactive. Data-access
    endpoints additionally enforce the ACTIVE grant via
    ``_authorized_client_org`` (D15).
    """
    client = await repos.consultants.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="client not found")
    if client.consultant_id != context.profile.id:
        raise HTTPException(status_code=403, detail="client belongs to another consultant firm")
    return client


@router.get("/me")
async def get_my_profile(
    context: ConsultantContext = Depends(require_consultant),
):
    """The consultant profile plus the firm member's real permission flags
    (D25 — additive: existing profile fields unchanged; the ``can_*`` flags let
    the UI gate client-lifecycle/branding controls the way the backend already
    enforces them).

    P6-1B adds the authoritative MEMBERSHIP block (active membership state,
    operating firm, role) and an ``entitlement_scope`` block. Both are derived
    server-side from the resolved membership/firm — never from client state.
    """
    try:
        from dataclasses import asdict

        base = asdict(context.profile)
    except Exception:  # pragma: no cover - fallback for non-dataclass shapes
        base = dict(context.profile.__dict__)
    base["can_manage_clients"] = bool(context.firm_member.can_manage_clients)
    base["can_upload_documents"] = bool(context.firm_member.can_upload_documents)
    base["can_generate_reports"] = bool(context.firm_member.can_generate_reports)
    base["can_manage_team"] = bool(context.firm_member.can_manage_team)

    def _iso(value):
        return value.isoformat() if value else None

    base["membership"] = {
        "id": context.firm_member.id,
        "firm_id": context.firm_member.firm_id,
        "role": context.firm_member.role,
        "is_active": bool(context.firm_member.is_active),
        "joined_at": _iso(context.firm_member.joined_at),
        "invited_at": _iso(context.firm_member.invited_at),
        "source": "consultant_firm_members",
    }
    # Entitlement scope (P6-1B §5/§12): Consultant capability is an
    # ORGANISATION-scoped commercial entitlement. The organisation↔firm binding
    # for org-upgraded consultants is not yet established (deferred D-C
    # mapping), so no capability is bound here; existing pre-commercial
    # consultant profiles/workspaces remain permitted (preserved distinction).
    base["entitlement_scope"] = {
        "consultant_capability_required_for_workspace": False,
        "bound_organization_id": None,
        "note": (
            "Consultant capability is organization-scoped. Firm↔organization "
            "binding is not yet established; pre-commercial consultant "
            "workspace access remains permitted by the existing architecture."
        ),
    }
    return base


@router.post("/me", status_code=201)
async def create_my_profile(
    payload: ProfileCreate,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
    # D-A (ratified, Phase 6): platform registration mode. INVITATION_ONLY
    # closes CONSULTANT SELF-registration. Registration never authorizes
    # client access or capabilities — the invited/authorized provisioning flow
    # owns activation. CarbonTally-created demo/seeded identities are untouched.
    mode = await resolve_registration_mode(repos)
    if mode == "INVITATION_ONLY":
        raise HTTPException(
            status_code=403,
            detail=(
                "Platform registration is currently invitation-only. "
                "Consultant self-registration is closed; provisioning requires an invitation."
            ),
        )
    existing = await repos.consultants.get_profile_by_user(current_user.user_id)
    if existing is not None:
        raise HTTPException(status_code=409, detail="consultant profile already exists")
    return await repos.consultants.create_profile(current_user.user_id, payload.company_name)


# ---------------------------------------------------------------------------
# D21 — White-Label Foundation: branding configuration
# ---------------------------------------------------------------------------


def _safe_branding_snapshot(branding: Any) -> dict[str, Any]:
    """A safe before/after audit snapshot (no credentials ever stored)."""
    if branding is None:
        return {}
    return {
        "brand_name": branding.brand_name,
        "logo_url": branding.logo_url,
        "primary_color": branding.primary_color,
        "secondary_color": branding.secondary_color,
        "footer_text": branding.footer_text,
        "email_from": branding.email_from,
        "website": branding.website,
        "client_portal_url": branding.client_portal_url,
        "white_label_enabled": branding.white_label_enabled,
        "co_branding_enabled": branding.co_branding_enabled,
    }


@router.get("/me/branding")
async def get_my_branding(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Read the caller's own firm branding (D21.1/D21.2 — self-scoped).

    There is NO ``consultant_id`` parameter: the branding always belongs to the
    authenticated consultant's own firm. Any client-supplied id is ignored
    (D21.14 — never authorize from a client-provided consultant id).
    """
    branding = await repos.consultants.get_branding(context.profile.id)
    return {
        "branding": (
            branding.to_dict()
            if branding is not None
            else default_branding_dict(context.profile.id)
        ),
        "brand_context": (
            await resolve_consultant_branding(repos, context.profile)
        ).to_dict(),
        "can_manage_branding": _can_manage_branding(context),
    }


@router.get("/me/branding/context")
async def get_my_brand_context(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The resolved presentation brand for the caller's own firm (D21.4)."""
    return {
        "brand_context": (
            await resolve_consultant_branding(repos, context.profile)
        ).to_dict()
    }


@router.put("/me/branding")
async def update_my_branding(
    request: Request,
    payload: BrandingUpdate,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
    audit: AuditLogger = Depends(get_audit_logger),
):
    """Update the caller's own firm branding (D21.1/D21.2/D21.14).

    Authorization chain: authenticated → active consultant firm membership →
    firm-administration permission (owner or ``can_manage_team``) → the firm's
    OWN profile row. The profile id is resolved server-side from the
    authenticated context — never from the payload.
    """
    if not _can_manage_branding(context):
        raise HTTPException(
            status_code=403,
            detail="consultant lacks permission: manage_branding",
        )
    fields = payload.model_dump(exclude_unset=True)
    before = await repos.consultants.get_branding(context.profile.id)
    updated = await repos.consultants.update_branding(context.profile.id, fields)
    if updated is None:
        raise HTTPException(status_code=404, detail="consultant profile not found")
    correlation_id = ""
    if request is not None:
        correlation_id = get_request_context(request).correlation_id
    await audit.log_action(
        action="consultant.branding.update",
        entity_type="consultant_profile",
        entity_id=context.profile.id,
        correlation_id=correlation_id,
        actor=current_user.user_id,
        changed_fields={k: v for k, v in fields.items()},
        before=_safe_branding_snapshot(before),
        after=_safe_branding_snapshot(updated),
        reason="D21 consultant branding self-service update",
    )
    return {
        "branding": updated.to_dict(),
        "brand_context": (
            await resolve_consultant_branding(repos, context.profile)
        ).to_dict(),
        "can_manage_branding": True,
    }


def _ensure_firm_transition_allowed(client, target: str) -> None:
    """P6-1C — gate consultant-side lifecycle moves by relationship origin.

    ``engagement_request`` rows (Case B — pre-existing organisations) are
    strictly governed by the domain engagement policy: the firm can never
    activate a pending engagement (customer acceptance is the boundary) and may
    only withdraw/re-request/suspend/end once live. Legacy and
    consultant-CREATED client relationships keep the ratified D19 firm
    lifecycle (target vocabulary enforced by the repository whitelist); the
    firm may never manufacture a ``pending``/``rejected`` state for them.
    """
    from domain.partners import can_transition_consultant_engagement

    origin = getattr(client, "relationship_origin", None) or "legacy"
    if origin == "engagement_request":
        if not can_transition_consultant_engagement(
            client.status, target, actor_side="consultant", origin="engagement_request"
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "consultant-side transition not permitted for this engagement "
                    f"(status={client.status!r}, origin={origin!r}, target={target!r})"
                ),
            )
        return
    if target in ("pending", "rejected"):
        raise HTTPException(
            status_code=403,
            detail="pending/rejected engagement states are reserved for pre-existing-"
            "organisation engagements (engagement_request origin)",
        )


async def _audit_engagement(repos, client_id: str, action: str, actor: str, after: str) -> None:
    """Append-only audit for engagement lifecycle actions (human actor only)."""
    from datetime import datetime, timezone
    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id="",
                entity_type="consultant_clients",
                entity_id=client_id,
                action=action,
                actor=actor,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={"status": after},
                before=None,
                after={"status": after},
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the request
        pass


@router.get("/me/clients")
async def list_my_clients(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    clients = await repos.consultants.list_clients(context.profile.id)
    return {"clients": clients}


@router.get("/me/engagements")
async def list_my_engagements(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """The firm's Case-B engagement relationships (origin=engagement_request).

    Lets the firm inspect pending/rejected/active engagement state for
    ALREADY-existing client organisations without treating pending as access.
    """
    rows = await repos.consultants.list_clients(context.profile.id)
    engagements = [
        c for c in rows
        if (c.relationship_origin or "legacy") == "engagement_request"
    ]
    return {"engagements": engagements}


@router.post("/me/clients", status_code=201)
async def add_client(
    payload: ClientCreate,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """P6-1C — REQUEST an engagement with an ALREADY-existing organisation.

    A consultant cannot claim or access an existing CarbonTally organisation
    merely by knowing its id (CT-CONSULT-003). This route creates a PENDING
    engagement (``status='pending'``, ``relationship_origin=
    'engagement_request'``); only an authorised customer representative can
    ACCEPT it into ``active``. Consultant-CREATED customers (Case A) are still
    granted active immediately through ``POST /me/customers`` and are never
    routed here.
    """
    ensure_consultant_permission(context, "manage_clients")
    org_id = payload.organization_id

    existing = await repos.consultants.get_client_by_org(context.profile.id, org_id)
    if existing is not None:
        status = existing.status or "active"
        if status in ("active", "pending", "suspended"):
            raise HTTPException(
                status_code=409,
                detail="a relationship with this organisation already exists (active or pending)",
            )
        # rejected / ended / inactive -> re-request (pending) under the policy.
        _ensure_firm_transition_allowed(existing, "pending")
        updated = await repos.consultants.transition_client_lifecycle(
            existing.id, "pending", actor_id=current_user.user_id
        )
        await _audit_engagement(
            repos, existing.id, "consultant.client.engagement_requested",
            current_user.user_id, "pending",
        )
        return updated

    # Target validation (server-side; never trust the raw id).
    target_org = await repos.organizations.get(org_id)
    if target_org is None or not getattr(target_org, "is_active", True):
        raise HTTPException(
            status_code=404,
            detail="organisation not found or not available for engagement",
        )
    profile = await repos.organizations.get_profile(org_id)
    if profile is not None and str(profile.get("customer_type") or "") in ("internal", "pe_only"):
        raise HTTPException(
            status_code=403,
            detail="engagement is not permitted with this organisation type",
        )

    created = await repos.consultants.add_client(
        context.profile.id,
        org_id,
        payload.client_name,
        payload.client_industry,
        payload.client_contact_email,
        payload.client_contact_name,
        created_by=current_user.user_id,
        relationship_origin="engagement_request",
        status="pending",
    )
    await _audit_engagement(
        repos, created.id, "consultant.client.engagement_requested",
        current_user.user_id, "pending",
    )
    return created


class CustomerCreate(BaseModel):
    """PO Decision 3 — a consultant creates a new customer organisation.

    ``name`` is the organisation name; ``owner_email``/``owner_name`` identify
    the customer's owner (created as the organisation OWNER). ``client_name``
    is the display label on the consultant's client list.
    """

    name: str
    owner_email: str
    owner_name: Optional[str] = None
    client_name: Optional[str] = None
    country: str = "GB"
    industry: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


@router.post("/me/customers", status_code=201)
async def create_customer(
    payload: CustomerCreate,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """PO Decision 3 (CON-1) — create a customer organisation for the firm.

    The consultant firm's own customers are first-class organisations owned by
    the customer owner. This endpoint:

    1. creates (or reuses) the owner's auth identity (GoTrue admin);
    2. creates the organisation with the owner membership (server-authoritative,
       same transaction as self-service onboarding);
    3. links the firm via ``consultant_clients`` (active grant) so the
       consultant's existing client workspace / isolation applies unchanged.

    Cross-firm and unrelated-customer isolation is unchanged — the new
    organisation is only reachable by its members and firms with an active
    ``consultant_clients`` grant.
    """
    ensure_consultant_permission(context, "manage_clients")

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="customer name must not be empty")
    owner_email = payload.owner_email.strip().lower()
    if not owner_email or "@" not in owner_email:
        raise HTTPException(status_code=422, detail="a valid owner_email is required")

    owner_user_id = await _resolve_or_create_owner_identity(
        owner_email, payload.owner_name
    )
    if owner_user_id is None:
        raise HTTPException(
            status_code=502,
            detail="customer owner identity could not be provisioned (auth is unavailable)",
        )

    # 2. Create the organisation with the owner membership (one transaction).
    org_id = str(uuid.uuid4())
    default_billing_mode = await repos.billing_config.get_default_billing_mode()
    created = await repos.organizations.create_with_owner(
        org_id=org_id,
        name=name,
        country=payload.country or None,
        owner_user_id=owner_user_id,
        primary_contact_email=owner_email,
        billing_mode=default_billing_mode,
    )

    # 3. Link the firm (active grant) — the consultant's client workspace.
    #    Scope E (P6-BILL-1): the actor is the authenticated consultant
    #    (server-authoritative provenance for the grant).
    await repos.consultants.add_client(
        context.profile.id,
        org_id,
        client_name=(payload.client_name or name),
        client_industry=payload.industry,
        client_contact_email=owner_email,
        client_contact_name=payload.owner_name,
        created_by=current_user.user_id,
    )

    await _audit_consultant_created_customer(repos, context, org_id, name, owner_email)

    return {
        "organization": created["organization"],
        "owner_email": owner_email,
        "owner_user_id": owner_user_id,
        "client_linked": True,
    }


@router.get("/clients/{client_id}")
async def get_client(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    client = await _checked_client(current_user, context, repos, client_id)
    org = await repos.organizations.get(client.organization_id)
    return {
        "client": client,
        "organization_name": org.name if org is not None else None,
    }


@router.put("/clients/{client_id}")
async def update_client_status(
    client_id: str,
    payload: ClientStatusUpdate,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_consultant_revocation_authority(context)
    if payload.status not in CLIENT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"invalid client status {payload.status!r}; expected one of {', '.join(CLIENT_STATUSES)}",
        )
    client = await _checked_client(current_user, context, repos, client_id)
    _ensure_firm_transition_allowed(client, payload.status)
    updated = await repos.consultants.transition_client_lifecycle(
        client.id, payload.status, actor_id=current_user.user_id
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="client not found")
    await _audit_client_lifecycle(
        repos, context, client_id, "active", updated.status,
        actor=current_user.user_id,
    )
    return updated


@router.post("/clients/{client_id}/suspend")
async def suspend_client(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """D19 lifecycle: SUSPENDED — temporary loss of client-data access.

    Access is denied immediately at both the API and RLS layers (only
    ``status='active'`` grants access). Historical audit/provenance remains.
    """
    ensure_consultant_revocation_authority(context)
    client = await _checked_client(current_user, context, repos, client_id)
    _ensure_firm_transition_allowed(client, "suspended")
    updated = await repos.consultants.transition_client_lifecycle(
        client.id, "suspended", actor_id=current_user.user_id
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="client not found")
    await _audit_client_lifecycle(
        repos, context, client_id, client.status, "suspended",
        actor=current_user.user_id,
    )
    return updated


@router.post("/clients/{client_id}/end")
async def end_client(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """D19 lifecycle: ENDED — permanent loss of client-data access.

    Historical provenance is NOT authorization; a new relationship requires a
    new explicit grant (D19 §4).
    """
    ensure_consultant_revocation_authority(context)
    client = await _checked_client(current_user, context, repos, client_id)
    _ensure_firm_transition_allowed(client, "ended")
    updated = await repos.consultants.transition_client_lifecycle(
        client.id, "ended", actor_id=current_user.user_id
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="client not found")
    await _audit_client_lifecycle(
        repos, context, client_id, client.status, "ended",
        actor=current_user.user_id,
    )
    return updated


@router.post("/clients/{client_id}/reactivate")
async def reactivate_client(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """D19 lifecycle: restore to ACTIVE (a new explicit grant decision)."""
    ensure_consultant_revocation_authority(context)
    client = await _checked_client(current_user, context, repos, client_id)
    _ensure_firm_transition_allowed(client, "active")
    updated = await repos.consultants.transition_client_lifecycle(
        client.id, "active", actor_id=current_user.user_id
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="client not found")
    await _audit_client_lifecycle(
        repos, context, client_id, client.status, "active",
        actor=current_user.user_id,
    )
    return updated


async def _audit_client_lifecycle(
    repos: RepositoryBundle,
    context: ConsultantContext,
    client_id: str,
    before: Optional[str],
    after: str,
    *,
    actor: str,
) -> None:
    """Best-effort audit of a client lifecycle transition (never breaks)."""
    from datetime import datetime, timezone
    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id="",
                entity_type="consultant_client",
                entity_id=client_id,
                action=f"consultant_client.{after}",
                actor=actor,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={"status": after},
                before={"status": before},
                after={"status": after},
            )
        )
    except Exception:  # noqa: BLE001
        pass


async def _resolve_or_create_owner_identity(
    owner_email: str, owner_name: Optional[str]
) -> Optional[str]:
    """Resolve (or create) the customer owner's auth identity (GoTrue admin).

    CON-1 — consultants provision their own customers' owners. Runs with the
    service key (server-side only); never returns the generated password.
    Idempotent: an existing email resolves to the existing identity.
    """
    import os
    import secrets

    import httpx

    supabase_url = os.getenv("SUPABASE_URL", "")
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if not supabase_url or not service_key:
        return None
    admin_headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
    async with httpx.AsyncClient(timeout=30) as http:
        list_resp = await http.get(
            f"{supabase_url}/auth/v1/admin/users?per_page=1000", headers=admin_headers
        )
        if list_resp.status_code == 200:
            for u in list_resp.json().get("users", []):
                if str(u.get("email", "")).lower() == owner_email:
                    return str(u["id"])
        generated_password = secrets.token_urlsafe(18)
        create_resp = await http.post(
            f"{supabase_url}/auth/v1/admin/users",
            headers={**admin_headers, "Content-Type": "application/json"},
            json={
                "email": owner_email,
                "password": generated_password,
                "email_confirm": True,
                "user_metadata": {"full_name": owner_name} if owner_name else {},
            },
        )
        if create_resp.status_code in (200, 201):
            return str(create_resp.json()["id"])
        if create_resp.status_code in (409, 422):
            list2 = await http.get(
                f"{supabase_url}/auth/v1/admin/users?per_page=1000", headers=admin_headers
            )
            if list2.status_code == 200:
                for u in list2.json().get("users", []):
                    if str(u.get("email", "")).lower() == owner_email:
                        return str(u["id"])
        return None


async def _audit_consultant_created_customer(
    repos: RepositoryBundle,
    context: ConsultantContext,
    org_id: str,
    name: str,
    owner_email: str,
) -> None:
    """Best-effort audit of consultant-created customers (never breaks)."""
    from datetime import datetime, timezone
    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id="",
                entity_type="organization",
                entity_id=org_id,
                action="consultant.customer.created",
                actor=context.profile.user_id,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={"name": name, "owner_email": owner_email},
                before=None,
                after={"name": name, "owner_email": owner_email},
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the customer journey
        pass


@router.delete("/clients/{client_id}", status_code=204)
async def deactivate_client(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_consultant_revocation_authority(context)
    client = await _checked_client(current_user, context, repos, client_id)
    _ensure_firm_transition_allowed(client, "inactive")
    await repos.consultants.update_client_status(client.id, "inactive")


@router.get("/me/dashboard")
async def consultant_dashboard(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Consultant dashboard — real aggregates over the firm's clients.

    Client count, per-status counts, pending-review volume, open issues and
    report counts are computed from the firm's ``consultant_clients`` rows
    joined against the real client-org processing/issues/report data.
    """
    clients = await repos.consultants.list_clients(context.profile.id)
    by_status: dict[str, int] = {}
    active_clients: list[dict[str, Any]] = []
    pending_reviews = 0
    open_issues = 0
    ready_reports = 0
    for client in clients:
        by_status[client.status or "unknown"] = by_status.get(client.status or "unknown", 0) + 1
        if client.status in (None, "active"):
            active_clients.append({"id": client.id, "client_name": client.client_name})
            status = await repos.manual_extraction.workflow_status(client.organization_id)
            pending_reviews += int(status.get("customer_review", 0) or 0)
            issues = await repos.issues.list_for_org(client.organization_id)
            open_issues += len([i for i in issues if i.status == "open"])
            counts = await repos.reports.count_by_status(client.organization_id)
            ready_reports += counts.get("completed", 0)
    return {
        "client_count": len(clients),
        "clients_by_status": by_status,
        "active_client_count": len(active_clients),
        "pending_reviews": pending_reviews,
        "open_issues": open_issues,
        "ready_reports": ready_reports,
    }


@router.get("/me/team")
async def list_my_team(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    members = await repos.consultants.list_firm_members(context.profile.id)
    # CL-61 — human-readable roster (name/email via public.users) instead of
    # raw UUIDs (AGENTS.md §75: business context over internal IDs).
    names = await repos.consultants.get_user_summaries([m.user_id for m in members])
    enriched = []
    for m in members:
        info = names.get(m.user_id, {})
        enriched.append(
            {
                "id": m.id,
                "user_id": m.user_id,
                "role": m.role,
                "is_active": m.is_active,
                "can_manage_clients": m.can_manage_clients,
                "can_upload_documents": m.can_upload_documents,
                "can_generate_reports": m.can_generate_reports,
                "can_manage_team": m.can_manage_team,
                "client_access": m.client_access,
                "joined_at": m.joined_at,
                "invited_at": m.invited_at,
                "email": info.get("email"),
                "first_name": info.get("first_name"),
                "last_name": info.get("last_name"),
            }
        )
    return {"members": enriched}


@router.post("/me/team", status_code=201)
async def add_team_member(
    payload: FirmMemberCreate,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """P6-1B — hardened firm membership provisioning.

    Only a firm member holding the real ``can_manage_team`` permission may add
    a member to the FIRM resolved server-side (``context.profile.id``). The new
    member is created with a validated display role and ALL ``can_*`` permission
    flags FALSE — no permission flag is grantable through this endpoint (the
    schema has no such fields, and forged extra payload fields are ignored).
    The authenticated actor is recorded in the append-only audit trail; a
    client-supplied actor is never accepted. Duplicate active membership and
    self-add are rejected.
    """
    ensure_consultant_permission(context, "manage_team")
    role = (payload.role or "consultant").strip().lower()
    if role not in CONSULTANT_ROLES:
        raise HTTPException(
            status_code=422,
            detail=f"role must be one of {list(CONSULTANT_ROLES)}",
        )
    if payload.user_id == current_user.user_id:
        raise HTTPException(
            status_code=422,
            detail="a consultant cannot add themselves to their own firm",
        )
    existing = await repos.consultants.get_firm_member_by_user(
        context.profile.id, payload.user_id
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="user is already a member of this firm")
    created = await repos.consultants.add_firm_member(
        context.profile.id, payload.user_id, role
    )
    # Server-authoritative actor for the security-sensitive membership mutation.
    from datetime import datetime, timezone
    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id="",
                entity_type="consultant_firm_member",
                entity_id=created.id,
                action="consultant.team.added",
                actor=current_user.user_id,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={"user_id": payload.user_id, "role": role},
                before=None,
                after={"user_id": payload.user_id, "role": role, "is_active": True},
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the team action
        pass
    return created


@router.post("/me/team/{member_id}/deactivate")
async def deactivate_team_member(
    member_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """CL-61 close-out — revoke a team member's consultant access.

    Server-side: ``is_active=false`` on the firm-membership row makes
    ``require_consultant`` reject the member on every subsequent request
    (immediate, not a UI-only affordance). A consultant cannot revoke
    themselves.
    """
    ensure_consultant_permission(context, "manage_team")
    member = await repos.consultants.get_firm_member(context.profile.id, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="team member not found")
    if member.user_id == current_user.user_id:
        raise HTTPException(status_code=422, detail="a consultant cannot deactivate themselves")
    updated = await repos.consultants.set_firm_member_active(
        context.profile.id, member_id, False
    )
    await _audit_team_member_change(repos, context, member_id, "deactivated")
    return {"member": updated, "is_active": False}


@router.post("/me/team/{member_id}/reactivate")
async def reactivate_team_member(
    member_id: str,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Restore a previously revoked team member's consultant access."""
    ensure_consultant_permission(context, "manage_team")
    member = await repos.consultants.get_firm_member(context.profile.id, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="team member not found")
    updated = await repos.consultants.set_firm_member_active(
        context.profile.id, member_id, True
    )
    await _audit_team_member_change(repos, context, member_id, "reactivated")
    return {"member": updated, "is_active": True}


async def _audit_team_member_change(
    repos: RepositoryBundle,
    context: ConsultantContext,
    member_id: str,
    action: str,
) -> None:
    """Append-only audit trail for team membership lifecycle changes."""
    from datetime import datetime, timezone
    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id="",
                entity_type="consultant_firm_member",
                entity_id=member_id,
                action=f"consultant.team.{action}",
                actor=context.profile.user_id,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={"is_active": action == "reactivated"},
                before=None,
                after={"is_active": action == "reactivated"},
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the team action
        pass


@router.get("/me/tasks")
async def list_my_tasks(
    status: Optional[str] = None,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return {"tasks": await repos.consultants.list_tasks(context.profile.id, status)}


@router.post("/me/tasks", status_code=201)
async def create_task(
    payload: TaskCreate,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    return await repos.consultants.create_task(
        context.profile.id,
        payload.task_title,
        payload.task_type,
        payload.priority,
        payload.client_id,
        payload.metadata,
    )


@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    task = await repos.consultants.update_task_status(task_id, status)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


# ---------------------------------------------------------------------------
# Client workspace / client data (consultant-authorized reuse of V3 repos)
# ---------------------------------------------------------------------------


async def _authorized_client_org(
    client_id: str,
    current_user: AuthUser,
    context: ConsultantContext,
    repos: RepositoryBundle,
) -> str:
    """Resolve a client grant → org and re-authorize the consultant for it.

    D15 (APPROVED 2026-08-20): data access requires an ACTIVE consultant-client
    authorization — an inactive/ended grant denies access.
    """
    client = await _checked_client(current_user, context, repos, client_id)
    await ensure_consultant_org_access(
        current_user, repos, client.organization_id
    )
    return client.organization_id


@router.get("/clients/{client_id}/context")
async def client_workspace_context(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Client workspace context — real org/profile + processing + issues + reports.

    The active client is explicit in every response so the UI can always show
    which organisation the consultant is working on.
    """
    client = await _checked_client(current_user, context, repos, client_id)
    org_id = client.organization_id
    profile = await repos.organizations.get_profile(org_id)
    processing = await repos.manual_extraction.workflow_status(org_id)
    issues = await repos.issues.list_for_org(org_id)
    reports = await repos.reports.list_full(org_id)
    counts = await repos.reports.count_by_status(org_id)
    return {
        "client": client,
        "organization": profile,
        "reporting_period": {
            "reporting_year": None,  # populated by the workspace from the org's factor year/reporting data
        },
        "processing": processing,
        "issues": {
            "total": len(issues),
            "open": len([i for i in issues if i.status == "open"]),
        },
        "reports": {
            "total": len(reports),
            "by_status": counts,
        },
    }


@router.get("/clients/{client_id}/dashboard")
async def client_dashboard(
    client_id: str,
    start_date: str,
    end_date: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Authorized client emissions dashboard (reuses the V3 emissions repo)."""
    org_id = await _authorized_client_org(client_id, current_user, context, repos)
    from api.v3_emissions import build_period

    from datetime import date as _Date

    try:
        period = build_period(
            _Date.fromisoformat(start_date), _Date.fromisoformat(end_date)
        )
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid start_date/end_date (ISO format required)")
    by_scope = await repos.logs.aggregate(org_id, period, "scope")
    by_asset = await repos.logs.aggregate(org_id, period, "asset")
    by_facility = await repos.logs.aggregate(org_id, period, "facility")
    return {
        "organization_id": org_id,
        "period": {"start_date": start_date, "end_date": end_date},
        "total_co2e_kg": str(by_scope.total_co2e_kg),
        "total_rows": by_scope.total_rows,
        "by_scope": {k: str(v) for k, v in by_scope.by_scope.items()},
        "by_asset": {k: str(v) for k, v in by_asset.by_group.items()},
        "by_facility": {k: str(v) for k, v in by_facility.by_group.items()},
    }


@router.get("/clients/{client_id}/reports")
async def client_reports(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    org_id = await _authorized_client_org(client_id, current_user, context, repos)
    reports = await repos.reports.list_full(org_id)
    return {
        "reports": reports,
        "count_by_status": await repos.reports.count_by_status(org_id),
        # D21.7 report branding: derived from the caller's OWN authorized firm
        # (never another consultant's, never a client-supplied id).
        "branding": (
            await resolve_consultant_branding(repos, context.profile)
        ).to_dict(),
    }


@router.get("/clients/{client_id}/documents")
async def client_documents(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    org_id = await _authorized_client_org(client_id, current_user, context, repos)
    return {"documents": await repos.files.list_for_org(org_id)}


def _classify_upload(filename: str, mime: str) -> str:
    """Duplicate of the document-surface classifier (avoids a private import)."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf" or "pdf" in mime:
        return "PDF"
    if ext in ("jpg", "jpeg", "png", "gif", "webp") or "image" in mime:
        return "IMAGE"
    if ext in ("csv", "xlsx", "xls"):
        return "SPREADSHEET"
    return "OTHER"


@router.post("/clients/{client_id}/documents", status_code=201)
async def upload_client_document(
    client_id: str,
    data_type: str = Form("utility"),
    file: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """CON-2/3 — a consultant uploads a document FOR an authorized client.

    The active ``consultant_clients`` grant is the authorization (D15); the
    document is stored under the client organisation's private bucket path and
    enters the SAME durable server-side pipeline as a customer upload
    (organization_files → extraction item → automatic-processing job → OCR).
    """
    # Active-grant + firm-ownership (404 cross-firm, 403 when not active).
    org_id = await _authorized_client_org(client_id, current_user, context, repos)
    ensure_consultant_permission(context, "upload_documents")

    from api.v3_documents import create_document_and_enqueue

    filename = file.filename or "untitled"
    content = await file.read()
    file_type = _classify_upload(filename, file.content_type or "")
    record = await create_document_and_enqueue(
        organization_id=org_id,
        filename=filename,
        content=content,
        mime_type=file.content_type or "application/octet-stream",
        file_type=file_type,
        data_type=data_type,
        uploaded_by=current_user.user_id,
        repos=repos,
    )
    return {
        "document": {
            "id": record.id,
            "name": record.name,
            "organization_id": org_id,
            "client_id": client_id,
        }
    }


@router.get("/clients/{client_id}/processing/items")
async def client_processing_items(
    client_id: str,
    stage: Optional[str] = None,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """CON-3 — the client's processing items (with context) for the consultant
    workspace. Org-scoped and grant-authorized; item rows carry the batch name
    and the owning organisation label so the consultant can identify work."""
    org_id = await _authorized_client_org(client_id, current_user, context, repos)
    if stage:
        items = await repos.manual_extraction.list_by_stage(org_id, stage)
    else:
        items = await repos.manual_extraction.list_items_for_org(org_id)
    org = await repos.organizations.get(org_id)
    return {
        "items": [
            {
                "id": i.id,
                "file_name": i.file_name,
                "status": i.status,
                "batch_id": i.batch_id,
                "file_id": i.file_id,
                "organization": {"id": org_id, "name": org.name if org else None},
            }
            for i in items
        ],
        "total": len(items),
    }


@router.get("/clients/{client_id}/evidence")
async def client_evidence(
    client_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """E7 close-out — the consultant's evidence view for an authorized client.

    Returns the client organisation's persisted calculation history with
    human-readable provenance (factor source, reporting year, calculated at)
    from the SAME emission_logs surface the customer sees — the consultant is
    grant-authorized (active ``consultant_clients``), never a bypass. Cross-firm
    and inactive grants are denied by ``_authorized_client_org``.
    """
    org_id = await _authorized_client_org(client_id, current_user, context, repos)

    # Reuse the emissions snapshot shaping so the consultant sees the same
    # evidence contract as the customer (no parallel evidence system).
    from datetime import date as _Date

    from api.v3_emissions import build_period, shape_snapshot

    period = build_period(_Date(1990, 1, 1), _Date.today())
    total = await repos.logs.count_snapshots(org_id, period)
    rows = await repos.logs.list_snapshots(org_id, period, limit, offset)
    org = await repos.organizations.get(org_id)
    return {
        "organization": {"id": org_id, "name": org.name if org else None},
        "client_id": client_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "calculations": [shape_snapshot(r) for r in rows],
    }


@router.get("/clients/{client_id}/processing/status")
async def client_processing_status(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    org_id = await _authorized_client_org(client_id, current_user, context, repos)
    return {
        "status": await repos.manual_extraction.workflow_status(org_id),
        "batches": await repos.manual_extraction.list_batches(org_id),
    }


@router.get("/clients/{client_id}/issues")
async def client_issues(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    org_id = await _authorized_client_org(client_id, current_user, context, repos)
    return {"issues": await repos.issues.list_for_org(org_id)}
