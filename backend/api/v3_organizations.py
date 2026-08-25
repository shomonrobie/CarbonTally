"""V3 tenant surface (V3 legacy-capability reimplementation, extended Phase 6).

Organizations, members, facilities, assets, invitations and roles — thin API
over the V3 repositories. Auth reuses the existing ``auth.py`` guards. Every
field read/written is a real V3M2 column; org isolation is enforced via
``ensure_org_access`` on every org-scoped endpoint.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
)
from auth import AuthUser, require_auth, require_org_member, require_org_admin
from domain.audit import AuditEntry
from services.v3_email import render_simple_html, send_transactional_email

router = APIRouter(prefix="/api/v3/organizations", tags=["V3 — Organizations"])

#: The V3 customer role model — the ``organization_members.role`` CHECK
#: constraint (real schema). No second role system is created.
ORG_ROLES: tuple[str, ...] = ("owner", "admin", "member", "viewer")

ORG_ROLE_DESCRIPTIONS: dict[str, str] = {
    "owner": "Customer Owner — full control of the organisation",
    "admin": "Customer Admin — manage members, facilities, assets and settings",
    "member": "Customer Member — contribute data and view reports",
    "viewer": "Customer Viewer — read-only access",
}

_INVITATION_EXPIRY_DAYS = 7


async def _record_audit(
    repos: RepositoryBundle,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
    reason: Optional[str] = None,
) -> None:
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        correlation_id="",
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        occurred_at=datetime.now(timezone.utc),
        changed_fields={"status": (after or {}).get("status")},
        reason=reason,
        before=before,
        after=after,
    )
    # Append-only audit — failures must never break the customer journey.
    try:
        await repos.audit.record(entry)
    except Exception:  # noqa: BLE001 — audit is append-only best-effort
        pass


def _candidate_out(candidate: Any) -> dict:
    """Safe candidate metadata for the client (never customer data rows)."""
    return {
        "organization_id": candidate.organization_id,
        "name": candidate.name,
        "country": candidate.country,
        "industry": candidate.industry,
        "company_number": candidate.company_number,
        "match_signal": candidate.match_signal,
        "data_summary": candidate.data_summary,
    }


class OrganizationCreate(BaseModel):
    """Self-service organization creation (D35).

    The initial creator becomes the organization OWNER. ``acknowledged_candidates``
    is the customer's EXPLICIT acknowledgment of candidate organizations they
    have been shown and decided not to adopt — the only way a strong
    (exact company-number) duplicate signal is overridden.
    """

    name: str
    country: Optional[str] = None
    company_number: Optional[str] = None
    acknowledged_candidates: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


@router.post("", status_code=201)
async def create_organization(
    payload: OrganizationCreate,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """D35 — customer-initiated organization creation (self-service onboarding).

    Server-authoritative: the service-role pool creates the organization AND
    the initial OWNER membership in ONE transaction, so the creator always owns
    the organization they create (and never an org they are not authorized to
    own). No browser/service-role bypass: the resulting membership row is what
    authorizes the owner's subsequent RLS-scoped requests.

    Duplicate prevention (D19 §6 / D35 §7): candidate signals (name, company
    number, the creator's verified email domain) are matched against existing
    organizations. An EXACT company-number match is a strong duplicate signal
    and blocks creation with ``409 discovery_required`` UNLESS the customer
    explicitly acknowledges the candidates. Weaker signals are returned as
    informational candidates only — candidate matching is NEVER authoritative;
    real adoption still requires the D19 verification + USE ALL/PARTIAL/DISCARD
    flow.
    """
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="organization name must not be empty")
    if len(name) > 200:
        raise HTTPException(status_code=422, detail="organization name is too long (max 200 characters)")

    memberships = await repos.organizations.get_active_memberships_for_user(
        current_user.user_id
    )
    if memberships:
        raise HTTPException(
            status_code=409,
            detail="you already belong to an organization — use the existing workspace",
        )

    company_number = (payload.company_number or "").strip() or None
    email_domain = None
    if current_user.email and "@" in current_user.email:
        email_domain = current_user.email.rsplit("@", 1)[1].lower()

    candidates = await repos.discovery.lookup_candidates(
        name=name,
        company_number=company_number,
        email_domain=email_domain,
        contact_email=current_user.email or None,
        limit=10,
    )

    blocking = [
        c
        for c in candidates
        if company_number
        and c.company_number
        and str(c.company_number).strip().upper() == company_number.upper()
    ]
    acknowledged = {str(c).lower() for c in payload.acknowledged_candidates}
    if blocking and not any(
        str(c.organization_id).lower() in acknowledged for c in blocking
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "An existing organization matching your company number was found. "
                "Review the existing data, or acknowledge the candidates to create "
                "a new organization."
            ),
            headers={"X-Discovery-Required": "true"},
        )

    org_id = str(uuid.uuid4())
    # D37-0: the per-customer commercial mode is resolved from the versioned
    # default for NEW customers (never a global string literal).
    default_billing_mode = await repos.billing_config.get_default_billing_mode()
    created = await repos.organizations.create_with_owner(
        org_id=org_id,
        name=name,
        country=payload.country or None,
        owner_user_id=current_user.user_id,
        primary_contact_email=current_user.email,
        company_number=company_number,
        billing_mode=default_billing_mode,
    )

    reason = "D35 self-service onboarding — creator became OWNER"
    if blocking:
        reason += (
            " (acknowledged_candidates="
            + ",".join(sorted(acknowledged | {str(c.organization_id) for c in blocking}))
            + ")"
        )
    await _record_audit(
        repos,
        entity_type="organization",
        entity_id=org_id,
        action="organization.created",
        actor=current_user.user_id,
        before=None,
        after={"name": name, "status": "active", "role": "owner"},
        reason=reason,
    )
    # Onboarding confirmation (the minimum required app-level transactional
    # email; fail-open when Resend is unconfigured). Signup/verification/password
    # emails are Supabase Auth — EXTERNAL CONFIGURATION.
    try:
        await send_transactional_email(
            to_email=current_user.email,
            subject="Your CarbonTally organization is ready",
            html=render_simple_html(
                brand_name="CarbonTally",
                heading="Your organization is ready",
                body_html=(
                    f"<p>Hi,</p>"
                    f"<p>Your CarbonTally organization <strong>{name}</strong> has "
                    f"been created. You are its Owner.</p>"
                    f"<p>You can now upload documents, process data and build your "
                    f"emissions inventory from your workspace.</p>"
                ),
                footer=(
                    "You received this email because you created a CarbonTally "
                    "organization."
                ),
            ),
        )
    except Exception:  # noqa: BLE001 — email delivery must never break onboarding
        pass

    return {
        "organization": created["organization"],
        "member": created["member"],
        "candidates": [_candidate_out(c) for c in candidates],
        "acknowledged_candidates": sorted(
            acknowledged | {str(c.organization_id) for c in blocking}
        ),
        "onboarding": {
            "status": "ORGANIZATION_CREATED",
            "role": "owner",
            "destination": "/home",
        },
    }


class MemberCreate(BaseModel):
    user_id: str
    role: str = "viewer"


class MemberUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class FacilityCreate(BaseModel):
    name: str
    postcode: Optional[str] = None
    country: str = "GB"
    type: Optional[str] = None
    metadata: dict = {}


class AssetCreate(BaseModel):
    name: str
    facility_id: Optional[str] = None
    type: Optional[str] = None
    metadata: dict = {}


class InvitationCreate(BaseModel):
    email: str
    role: str = "member"

    model_config = ConfigDict(extra="forbid")


class ProfileUpdate(BaseModel):
    """Customer-admin editable organisation profile fields (real V3M2 columns)."""

    name: Optional[str] = None
    company_number: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    company_size: Optional[str] = None
    vat_number: Optional[str] = None
    registration_number: Optional[str] = None
    registered_address: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    financial_year_end: Optional[date] = None
    reporting_standard: Optional[str] = None
    secr_enabled: Optional[bool] = None
    esrs_enabled: Optional[bool] = None
    issb_enabled: Optional[bool] = None
    default_factor_year: Optional[int] = None
    preferred_units: Optional[str] = None
    website: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_name: Optional[str] = None
    billing_contact_email: Optional[str] = None
    billing_contact_name: Optional[str] = None
    billing_address: Optional[str] = None
    tax_rate: Optional[float] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    postcode: Optional[str] = None
    eircode: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None
    business_structure: Optional[str] = None
    reporting_frequency: Optional[str] = None
    accounting_standard: Optional[str] = None
    sustainability_standard: Optional[str] = None
    data_protection_officer: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_url: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class MetadataUpdate(BaseModel):
    """Customer-admin editable organisation metadata fields (real columns)."""

    total_employees: Optional[int] = None
    full_time_employees: Optional[int] = None
    part_time_employees: Optional[int] = None
    contract_employees: Optional[int] = None
    average_employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    total_floor_area_sqm: Optional[float] = None
    occupied_floor_area_sqm: Optional[float] = None
    total_floor_area_sqft: Optional[float] = None
    occupied_floor_area_sqft: Optional[float] = None
    renewable_energy_percentage: Optional[float] = None
    carbon_offset_percentage: Optional[float] = None
    industry_sector: Optional[str] = None
    naics_code: Optional[str] = None
    sic_code: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    sustainability_officer_name: Optional[str] = None
    sustainability_officer_email: Optional[str] = None
    reporting_standard: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


def validate_org_role(role: str) -> None:
    """Reject roles outside the real ``organization_members.role`` CHECK set."""
    if role not in ORG_ROLES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"invalid organization role {role!r}; "
                f"expected one of {', '.join(ORG_ROLES)}"
            ),
        )


def model_to_settable(model: BaseModel) -> dict[str, Any]:
    """Return only the fields the client explicitly supplied (real columns)."""
    return {k: v for k, v in model.model_dump(exclude_unset=True).items() if v is not None}


@router.get("/{org_id}")
async def get_organization(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    org = await repos.organizations.get(org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    metadata = await repos.organizations.get_metadata(org_id)
    return {"organization": org, "metadata": metadata}


# -- members ----------------------------------------------------------------
@router.get("/{org_id}/members")
async def list_members(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    return {"members": await repos.organizations.list_members_with_email(org_id)}


@router.get("/members/{member_id}")
async def get_member(
    member_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    member = await repos.organizations.get_member(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="member not found")
    ensure_org_access(current_user, member["organization_id"])
    return member


@router.post("/{org_id}/members", status_code=201)
async def add_member(
    org_id: str,
    payload: MemberCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    validate_org_role(payload.role)
    return await repos.tenant.add_member(org_id, payload.user_id, payload.role)


@router.put("/members/{member_id}")
async def update_member(
    member_id: str,
    payload: MemberUpdate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    if payload.role is not None:
        validate_org_role(payload.role)
    member = await repos.tenant.update_member(member_id, payload.role, payload.is_active)
    if member is None:
        raise HTTPException(status_code=404, detail="member not found")
    return member


@router.delete("/members/{member_id}", status_code=204)
async def remove_member(
    member_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    member = await repos.organizations.get_member(member_id)
    if member is not None:
        ensure_org_access(current_user, member["organization_id"])
    await repos.tenant.remove_member(member_id)


# -- profile / settings ------------------------------------------------------
@router.get("/{org_id}/profile")
async def get_organization_profile(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    profile = await repos.organizations.get_profile(org_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="organization not found")
    return {"organization": profile}


@router.put("/{org_id}/profile")
async def update_organization_profile(
    org_id: str,
    payload: ProfileUpdate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    fields = model_to_settable(payload)
    if not fields:
        raise HTTPException(status_code=422, detail="no profile fields supplied")
    if "name" in fields and not str(fields["name"]).strip():
        raise HTTPException(status_code=422, detail="organization name must not be empty")
    updated = await repos.organizations.update_profile(
        org_id, fields
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="organization not found")
    return {"organization": updated}


@router.get("/{org_id}/metadata")
async def get_organization_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    metadata = await repos.organizations.get_metadata_full(org_id)
    if metadata is None:
        return {"metadata": {}}
    return {"metadata": metadata}


@router.put("/{org_id}/metadata")
async def update_organization_metadata(
    org_id: str,
    payload: MetadataUpdate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    if not model_to_settable(payload):
        raise HTTPException(status_code=422, detail="no metadata fields supplied")
    updated = await repos.organizations.update_metadata_full(
        org_id, model_to_settable(payload), updated_by=current_user.user_id
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="organization not found")
    return {"metadata": updated}


# -- roles ------------------------------------------------------------------
@router.get("/{org_id}/roles")
async def list_org_roles(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    return {
        "roles": [
            {"id": role, "name": role, "description": ORG_ROLE_DESCRIPTIONS[role]}
            for role in ORG_ROLES
        ]
    }


# -- invitations -------------------------------------------------------------
@router.get("/{org_id}/invitations")
async def list_invitations(
    org_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    return {"invitations": await repos.invitations.list_for_org(org_id)}


@router.post("/{org_id}/invitations", status_code=201)
async def create_invitation(
    org_id: str,
    payload: InvitationCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    validate_org_role(payload.role)
    role_row = await repos.roles.get_by_name(payload.role)
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=_INVITATION_EXPIRY_DAYS)
    invitation = await repos.invitations.create(
        org_id=org_id,
        email=payload.email.strip().lower(),
        token=token,
        role_id=role_row["id"] if role_row is not None else None,
        invited_by=current_user.user_id,
        status="pending",
        expires_at=expires_at,
    )
    return invitation


@router.delete("/invitations/{invitation_id}", status_code=204)
async def revoke_invitation(
    invitation_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    invitation = await repos.invitations.get(invitation_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="invitation not found")
    ensure_org_access(current_user, invitation["organization_id"])
    await repos.invitations.revoke(invitation_id)


# -- facilities -------------------------------------------------------------
@router.get("/{org_id}/facilities")
async def list_facilities(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    return {"facilities": await repos.organizations.get_facilities(org_id)}


@router.get("/facilities/{facility_id}")
async def get_facility(
    facility_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    facility = await repos.tenant.get_facility(facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="facility not found")
    ensure_org_access(current_user, facility.organization_id)
    assets = [
        a for a in await repos.organizations.get_assets(facility.organization_id)
        if str(a.facility_id) == facility_id
    ]
    return {"facility": facility, "assets": assets}


@router.post("/{org_id}/facilities", status_code=201)
async def add_facility(
    org_id: str,
    payload: FacilityCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    return await repos.tenant.add_facility(
        org_id, payload.name, payload.postcode, payload.country, payload.type, payload.metadata
    )


@router.delete("/facilities/{facility_id}", status_code=204)
async def remove_facility(
    facility_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    facility = await repos.tenant.get_facility(facility_id)
    if facility is not None:
        ensure_org_access(current_user, facility.organization_id)
    await repos.tenant.remove_facility(facility_id)


# -- assets -----------------------------------------------------------------
@router.get("/{org_id}/assets")
async def list_assets(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    return {"assets": await repos.organizations.get_assets(org_id)}


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    asset = await repos.tenant.get_asset(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="asset not found")
    ensure_org_access(current_user, asset.organization_id)
    return asset


@router.post("/{org_id}/assets", status_code=201)
async def add_asset(
    org_id: str,
    payload: AssetCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_org_access(current_user, org_id)
    return await repos.tenant.add_asset(
        org_id, payload.facility_id, payload.name, payload.type, payload.metadata
    )


@router.delete("/assets/{asset_id}", status_code=204)
async def remove_asset(
    asset_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    await repos.tenant.remove_asset(asset_id)
