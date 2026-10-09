"""V3 tenant surface (V3 legacy-capability reimplementation, extended Phase 6).

Organizations, members, facilities, assets, invitations and roles — thin API
over the V3 repositories. Auth reuses the existing ``auth.py`` guards. Every
field read/written is a real V3M2 column; org isolation is enforced via
``ensure_org_access`` on every org-scoped endpoint.
"""
from __future__ import annotations

import secrets
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
from api.client_access_guard import require_client_operation
from domain.audit import AuditEntry
from domain.client_identity import (
    INVITATION_EXPIRY_DAYS,
    ClientIdentityError,
    normalise_email,
    resolve_invitation_state,
    validate_client_role,
)
from services.billing import resolve_registration_mode
from services.client_invitations import (
    describe_invitation,
    parse_invitation_expiry,
    send_invitation_email,
)
from services.v3_email import (
    render_simple_html,
    send_transactional_email,
)

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

#: CT04 (PD-1A) — the invitation validity window has a single source in the
#: pure policy module (``domain.client_identity``); this historical private name
#: is kept as an alias so no caller duplicates the number.
_INVITATION_EXPIRY_DAYS = INVITATION_EXPIRY_DAYS


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

    # D-A (ratified, Phase 6): platform registration mode. INVITATION_ONLY
    # closes SELF-SERVICE platform entry (org creation via this route). This is
    # a provisioning gate only — it never grants authorization, org/client
    # access, capability or staff/PE/CT privileges. Authorized provisioning
    # (consultant-created customers, org invitations, CarbonTally onboarding)
    # is unaffected.
    mode = await resolve_registration_mode(repos)
    if mode == "INVITATION_ONLY":
        raise HTTPException(
            status_code=403,
            detail=(
                "Platform registration is currently invitation-only. "
                "Organization creation requires an invitation or CarbonTally provisioning."
            ),
        )

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
            # CT-FINAL-01/02 notifications: the From address AND the delivery
            # provider are admin-configurable platform configuration, never the
            # acting user's mailbox.
            settings_repo=repos.settings,
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


class FacilityUpdate(BaseModel):
    """Editable facility fields (MD-1 — the edit endpoint was missing)."""

    name: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    type: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class AssetCreate(BaseModel):
    name: str
    facility_id: Optional[str] = None
    type: Optional[str] = None
    metadata: dict = {}


class AssetUpdate(BaseModel):
    """Editable asset fields (ISC-4 — asset must be viewable and editable)."""

    name: Optional[str] = None
    facility_id: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class InvitationCreate(BaseModel):
    email: str
    role: str = "member"

    model_config = ConfigDict(extra="forbid")


class InvitationAccept(BaseModel):
    """The single-use token an authenticated invitee presents to join (PD-1A)."""

    token: str

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


def validate_org_role(role: str) -> str:
    """Validate a client role against the PDT-2A boundary (single source).

    Delegates to ``domain.client_identity.validate_client_role`` so the
    owner/admin/member/viewer vocabulary is defined in exactly one place, and
    converts the policy's ``ValueError`` into the API's ``422`` contract (a
    ``ClientIdentityError`` must never surface as a 500).

    Returns the normalised (lower-cased) role.
    """
    try:
        return validate_client_role(role)
    except ClientIdentityError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _parse_dt(value: Any) -> Optional[datetime]:
    """Delegate to the shared expiry parser (single implementation)."""
    return parse_invitation_expiry(value)


def _invitation_view(invitation: dict, *, include_accept_url: bool = False) -> dict:
    """Delegate to the shared state/link projection (single implementation)."""
    return describe_invitation(invitation, include_accept_url=include_accept_url)


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
    # CT04 (PD-2A): the organisation owner/admin administer their OWN
    # organisation's client users. The role vocabulary is the single client-role
    # policy, and the target member is org-scope-checked so an admin of one
    # tenant can never mutate another tenant's member by id (AGENTS.md §44).
    target = await repos.organizations.get_member(member_id)
    if target is not None:
        ensure_org_access(current_user, target["organization_id"])
    role = validate_org_role(payload.role) if payload.role is not None else None
    member = await repos.tenant.update_member(member_id, role, payload.is_active)
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
    rows = await repos.invitations.list_for_org(org_id)
    return {
        "invitations": [_invitation_view(r, include_accept_url=True) for r in rows]
    }


@router.post("/{org_id}/invitations", status_code=201)
async def create_invitation(
    org_id: str,
    payload: InvitationCreate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Create a single-use client-user invitation (PD-1A / PD-2A).

    The requested role is now PERSISTED on the invitation (previously discarded)
    so acceptance creates the membership with exactly the role the inviter was
    authorised to assign. A branded invitation email is dispatched best-effort;
    ``email_delivered`` reports the honest delivery outcome so a mail failure
    never masquerades as success.
    """
    ensure_org_access(current_user, org_id)
    role = validate_org_role(payload.role)
    role_row = await repos.roles.get_by_name(role)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=_INVITATION_EXPIRY_DAYS)
    invitation = await repos.invitations.create(
        org_id=org_id,
        email=normalise_email(payload.email),
        token=token,
        role_id=role_row["id"] if role_row is not None else None,
        invited_by=current_user.user_id,
        status="pending",
        expires_at=expires_at,
        role=role,
        invited_by_firm_id=None,
    )
    org = await repos.organizations.get(org_id)
    org_name = getattr(org, "name", None) or "your organisation"
    delivered = False
    reason = "email not attempted"
    try:
        delivered, reason = await send_invitation_email(
            repos,
            to_email=invitation["email"],
            organization_name=org_name,
            role=role,
            token=token,
        )
    except Exception:  # noqa: BLE001 — a mail failure never breaks the invitation
        delivered = False
        reason = "email delivery failed"
    return {
        **_invitation_view(invitation, include_accept_url=True),
        "email_delivered": delivered,
        "email_status": reason,
    }


@router.post("/invitations/accept")
async def accept_invitation(
    payload: InvitationAccept,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Accept a single-use client-user invitation (PD-1A).

    The authenticated invitee exchanges a still-pending, unexpired, unrevoked
    token for a real organisation membership:

    1. the token is looked up and its EFFECTIVE state resolved (expiry is
       derived, never stored);
    2. the authenticated identity's email must match the invited address (an
       invitation is bound to a person, not merely a token);
    3. the invitation is CONSUMED with an atomic conditional update (single-use
       — a second attempt matches no row); and only then
    4. the membership is created (or re-activated) with the invited role.

    The consultant/org planes never bypass this step, so a client Workspace user
    can only ever appear through an authorised invitation.
    """
    token = (payload.token or "").strip()
    invitation = await repos.invitations.get_by_token(token)
    if invitation is None:
        raise HTTPException(status_code=404, detail="invitation not found")

    state = resolve_invitation_state(
        invitation.get("status"), _parse_dt(invitation.get("expires_at"))
    )
    if state == "accepted":
        raise HTTPException(
            status_code=409, detail="invitation has already been accepted"
        )
    if state == "revoked":
        raise HTTPException(status_code=409, detail="invitation has been revoked")
    if state == "expired":
        raise HTTPException(status_code=410, detail="invitation has expired")

    if normalise_email(invitation.get("email", "")) != normalise_email(
        current_user.email or ""
    ):
        raise HTTPException(
            status_code=403,
            detail="invitation was issued to a different email address",
        )

    # Single-use consumption: the conditional UPDATE is the guarantee.
    consumed = await repos.invitations.consume(
        token, accepted_by=current_user.user_id
    )
    if consumed is None:
        # Lost a race, or expired between the check and the update.
        raise HTTPException(status_code=409, detail="invitation is no longer valid")

    # The invited role is policy-checked defensively before it is written, so a
    # legacy/None role can never create an out-of-vocabulary membership.
    try:
        role = validate_client_role(consumed.get("role") or "member")
    except ClientIdentityError:
        role = "member"

    member = await repos.organizations.accept_invited_membership(
        org_id=consumed["organization_id"],
        user_id=current_user.user_id,
        email=normalise_email(current_user.email or consumed.get("email", "")),
        role=role,
    )
    return {
        "status": "accepted",
        "organization_id": consumed["organization_id"],
        "membership_id": getattr(member, "id", None),
        "role": role,
    }


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
    await repos.invitations.revoke(invitation_id, revoked_by=current_user.user_id)


# ---------------------------------------------------------------------------
# Consultant engagement confirmation (P6-1C) — customer authorizes/refuses
# ---------------------------------------------------------------------------


async def _engagement_row_or_404(
    repos: RepositoryBundle, engagement_id: str, org_id: str
):
    """Fetch a consultant_clients row and verify it targets THIS organisation."""
    row = await repos.consultants.get_client(engagement_id)
    if row is None:
        raise HTTPException(status_code=404, detail="engagement not found")
    if str(row.organization_id) != str(org_id):
        raise HTTPException(
            status_code=403,
            detail="engagement does not belong to this organisation",
        )
    return row


async def _audit_customer_engagement(
    repos: RepositoryBundle,
    engagement_id: str,
    action: str,
    actor: str,
    org_id: str,
) -> None:
    """Append-only audit of a customer engagement decision (human actor)."""
    from datetime import datetime, timezone
    from domain.audit import AuditEntry

    try:
        await repos.audit.record(
            AuditEntry(
                id="",
                correlation_id="",
                entity_type="consultant_clients",
                entity_id=engagement_id,
                action=f"consultant.client.engagement_{action}",
                actor=actor,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={"organization_id": org_id, "status": action},
                before=None,
                after={"organization_id": org_id, "status": action},
            )
        )
    except Exception:  # noqa: BLE001 — audit never breaks the decision
        pass


@router.get("/{org_id}/consultant-engagements")
async def list_consultant_engagements(
    org_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Pending Consultant engagement requests addressed to THIS organisation.

    Requires an authorised customer representative (org owner/admin). The
    organisation can see which Consultant firm is requesting access before it
    decides — no global consultant directory is exposed.
    """
    ensure_org_access(current_user, org_id)
    rows = await repos.consultants.list_engagements_for_org(org_id)
    enriched = []
    for row in rows:
        profile = await repos.consultants.get_profile_by_id(row.consultant_id)
        enriched.append(
            {
                "id": row.id,
                "consultant_id": row.consultant_id,
                "firm_name": profile.company_name if profile else None,
                "status": row.status,
                "client_name": row.client_name,
                "requested_by": row.created_by,
                "requested_at": (
                    row.engagement_requested_at.isoformat()
                    if row.engagement_requested_at else None
                ),
            }
        )
    return {"engagements": enriched}


@router.post("/{org_id}/consultant-engagements/{engagement_id}/accept")
async def accept_consultant_engagement(
    org_id: str,
    engagement_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Customer acceptance — the ONLY path from a pending engagement to active.

    P6-1C: consultant request alone never grants client access. The acceptance
    actor is the authenticated org owner/admin (never a client-supplied id).
    """
    ensure_org_access(current_user, org_id)
    row = await _engagement_row_or_404(repos, engagement_id, org_id)
    from domain.partners import can_transition_consultant_engagement

    if not can_transition_consultant_engagement(
        row.status, "active", actor_side="customer",
        origin=row.relationship_origin or "legacy",
    ):
        raise HTTPException(
            status_code=409,
            detail="engagement is not in a pending state",
        )
    updated = await repos.consultants.transition_client_lifecycle(
        engagement_id, "active", actor_id=current_user.user_id
    )
    await _audit_customer_engagement(
        repos, engagement_id, "accepted", current_user.user_id, org_id
    )
    # P6-2E (D11) — lifecycle event 1 "accepted". Emitted ONLY after the
    # transition + audit succeeded, so a denied/conflicted acceptance (409
    # above) never produces an event. Recipients are derived server-side from
    # the engagement's firm membership.
    from services.consultant_lifecycle import notify_engagement_accepted

    await notify_engagement_accepted(repos, client=updated if updated is not None else row)
    return {"engagement": updated}


@router.post("/{org_id}/consultant-engagements/{engagement_id}/reject")
async def reject_consultant_engagement(
    org_id: str,
    engagement_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
):
    """Customer rejection of a pending Consultant engagement (no access)."""
    ensure_org_access(current_user, org_id)
    row = await _engagement_row_or_404(repos, engagement_id, org_id)
    from domain.partners import can_transition_consultant_engagement

    if not can_transition_consultant_engagement(
        row.status, "rejected", actor_side="customer",
        origin=row.relationship_origin or "legacy",
    ):
        raise HTTPException(
            status_code=409,
            detail="engagement is not in a pending state",
        )
    updated = await repos.consultants.transition_client_lifecycle(
        engagement_id, "rejected", actor_id=current_user.user_id
    )
    await _audit_customer_engagement(
        repos, engagement_id, "rejected", current_user.user_id, org_id
    )
    return {"engagement": updated}


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
    _client_ceiling: AuthUser = Depends(require_client_operation("edit_master_data")),
):
    ensure_org_access(current_user, org_id)
    # MD-1/FAC-1 — the schema enforces ``postcode IS NOT NULL OR eircode IS NOT
    # NULL``; surface that as a clean 422 instead of a raw DB 500.
    if not (payload.postcode or "").strip():
        raise HTTPException(
            status_code=422,
            detail="postcode (or eircode for Ireland) is required when creating a facility",
        )
    return await repos.tenant.add_facility(
        org_id, payload.name, payload.postcode, payload.country, payload.type, payload.metadata
    )


@router.put("/facilities/{facility_id}")
async def update_facility(
    facility_id: str,
    payload: FacilityUpdate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    _client_ceiling: AuthUser = Depends(require_client_operation("edit_master_data")),
):
    """Edit a facility (MD-1 — the edit endpoint was missing)."""
    facility = await repos.tenant.get_facility(facility_id)
    if facility is None:
        raise HTTPException(status_code=404, detail="facility not found")
    ensure_org_access(current_user, facility.organization_id)
    updated = await repos.tenant.update_facility(
        facility_id,
        name=payload.name,
        is_active=payload.is_active,
        postcode=payload.postcode,
        country=payload.country,
        type_=payload.type,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        county=payload.county,
        metadata=payload.metadata,
    )
    return updated


@router.delete("/facilities/{facility_id}", status_code=204)
async def remove_facility(
    facility_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    _client_ceiling: AuthUser = Depends(require_client_operation("edit_master_data")),
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
    _client_ceiling: AuthUser = Depends(require_client_operation("edit_master_data")),
):
    ensure_org_access(current_user, org_id)
    # ISC-4 — ``assets.facility_id`` is NOT NULL; validate at the API layer so
    # a missing/invalid facility is a clean 422 instead of a raw DB 500.
    if not payload.facility_id:
        raise HTTPException(
            status_code=422,
            detail="facility_id is required when creating an asset",
        )
    facilities = await repos.organizations.get_facilities(org_id)
    if not any(str(f.id) == payload.facility_id for f in facilities):
        raise HTTPException(
            status_code=422,
            detail="facility does not belong to this organisation",
        )
    return await repos.tenant.add_asset(
        org_id, payload.facility_id, payload.name, payload.type, payload.metadata
    )


@router.put("/assets/{asset_id}")
async def update_asset(
    asset_id: str,
    payload: AssetUpdate,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    _client_ceiling: AuthUser = Depends(require_client_operation("edit_master_data")),
):
    """Edit an asset (ISC-4 — asset must be viewable and editable)."""
    existing = await repos.tenant.get_asset(asset_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="asset not found")
    ensure_org_access(current_user, existing.organization_id)
    if payload.facility_id is not None:
        facilities = await repos.organizations.get_facilities(existing.organization_id)
        if not any(str(f.id) == payload.facility_id for f in facilities):
            raise HTTPException(
                status_code=422,
                detail="facility does not belong to this organisation",
            )
    return await repos.tenant.update_asset(
        asset_id,
        name=payload.name,
        is_active=payload.is_active,
        facility_id=payload.facility_id,
        type_=payload.type,
        metadata=payload.metadata,
    )


@router.delete("/assets/{asset_id}", status_code=204)
async def remove_asset(
    asset_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
    _client_ceiling: AuthUser = Depends(require_client_operation("edit_master_data")),
):
    await repos.tenant.remove_asset(asset_id)
