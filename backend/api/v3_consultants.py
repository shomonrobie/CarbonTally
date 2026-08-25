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
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from api.consultant_auth import (
    CLIENT_STATUSES,
    ConsultantContext,
    ensure_consultant_org_access,
    ensure_consultant_permission,
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
    enforces them)."""
    try:
        from dataclasses import asdict

        base = asdict(context.profile)
    except Exception:  # pragma: no cover - fallback for non-dataclass shapes
        base = dict(context.profile.__dict__)
    base["can_manage_clients"] = bool(context.firm_member.can_manage_clients)
    base["can_upload_documents"] = bool(context.firm_member.can_upload_documents)
    base["can_generate_reports"] = bool(context.firm_member.can_generate_reports)
    base["can_manage_team"] = bool(context.firm_member.can_manage_team)
    return base


@router.post("/me", status_code=201)
async def create_my_profile(
    payload: ProfileCreate,
    current_user: AuthUser = Depends(get_current_user),
    repos: RepositoryBundle = Depends(get_repositories),
):
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


@router.get("/me/clients")
async def list_my_clients(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    clients = await repos.consultants.list_clients(context.profile.id)
    return {"clients": clients}


@router.post("/me/clients", status_code=201)
async def add_client(
    payload: ClientCreate,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_consultant_permission(context, "manage_clients")
    existing = await repos.consultants.get_client_by_org(
        context.profile.id, payload.organization_id
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="client already linked to this firm")
    return await repos.consultants.add_client(
        context.profile.id,
        payload.organization_id,
        payload.client_name,
        payload.client_industry,
        payload.client_contact_email,
        payload.client_contact_name,
    )


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
    ensure_consultant_permission(context, "manage_clients")
    if payload.status not in CLIENT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"invalid client status {payload.status!r}; expected one of {', '.join(CLIENT_STATUSES)}",
        )
    client = await _checked_client(current_user, context, repos, client_id)
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
    ensure_consultant_permission(context, "manage_clients")
    client = await _checked_client(current_user, context, repos, client_id)
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
    ensure_consultant_permission(context, "manage_clients")
    client = await _checked_client(current_user, context, repos, client_id)
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
    ensure_consultant_permission(context, "manage_clients")
    client = await _checked_client(current_user, context, repos, client_id)
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


@router.delete("/clients/{client_id}", status_code=204)
async def deactivate_client(
    client_id: str,
    current_user: AuthUser = Depends(get_current_user),
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_consultant_permission(context, "manage_clients")
    client = await _checked_client(current_user, context, repos, client_id)
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
    return {"members": await repos.consultants.list_firm_members(context.profile.id)}


@router.post("/me/team", status_code=201)
async def add_team_member(
    payload: FirmMemberCreate,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
):
    ensure_consultant_permission(context, "manage_team")
    return await repos.consultants.add_firm_member(context.profile.id, payload.user_id, payload.role)


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
