"""V3 white-label: custom domains + custom email senders (D27 / D19 §11-§13).

CarbonTally provides white-label access to its platform. The consultant owns
the domain/registrar/DNS/email infrastructure; CarbonTally provides the
platform, branding, custom-domain integration, verification and authorized
presentation context.

Security:

* Every endpoint is gated by ``require_consultant`` + firm ownership; a
  client-supplied ``consultant_id`` is never trusted (the profile is resolved
  from the authenticated context).
* A domain NEVER grants authorization — the domain only selects which
  authorized brand is presented. Authentication/authorization remain
  authoritative (D19 §12).
* Only VERIFIED senders may be used as a From address; arbitrary From
  addresses are never allowed (D19 §13). Sender verification relies on Resend
  domain verification — EXTERNAL CONFIGURATION REQUIRED in production.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.consultant_auth import (
    ConsultantContext,
    ensure_consultant_permission,
    require_consultant,
)
from api.dependencies import RepositoryBundle, get_repositories
from domain.audit import AuditEntry

router = APIRouter(prefix="/api/v3/consultants/me", tags=["V3 — White-label (D19)"])

_DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$", re.IGNORECASE)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DomainCreate(BaseModel):
    domain: str = Field(..., min_length=1, max_length=253)

    model_config = ConfigDict(extra="forbid")


class DomainVerify(BaseModel):
    token: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class SenderCreate(BaseModel):
    email: str = Field(..., min_length=1, max_length=320)

    model_config = ConfigDict(extra="forbid")


def _domain_out(domain) -> dict:
    return {
        "id": domain.id,
        "domain": domain.domain,
        "status": domain.status,
        "verified_at": domain.verified_at,
        "created_at": domain.created_at,
        # The TXT record value the consultant must publish at
        # ``_carbontally.<domain>``. Never a secret — it is the DNS proof token.
        "verification_token": domain.verification_token,
        "verification_instructions": (
            "Add a TXT record at _carbontally.<domain> with the value "
            f"carbon-tally-verify={domain.verification_token}, then call "
            "the verify endpoint with the token."
        ),
    }


def _sender_out(sender) -> dict:
    return {
        "id": sender.id,
        "email": sender.email,
        "domain": sender.domain,
        "status": sender.status,
        "verified_at": sender.verified_at,
        "created_at": sender.created_at,
    }


async def _audit(
    repos: RepositoryBundle,
    context: ConsultantContext,
    *,
    entity_id: str,
    action: str,
    after: dict,
) -> None:
    """Best-effort audit of white-label mutations (never breaks the flow)."""
    entry = AuditEntry(
        id="",
        correlation_id="",
        entity_type="consultant_whitelabel",
        entity_id=entity_id,
        action=action,
        actor=context.profile.user_id,
        occurred_at=datetime.now(timezone.utc),
        changed_fields=after,
        after=after,
    )
    try:
        await repos.audit.record(entry)
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Custom domains
# ---------------------------------------------------------------------------


@router.get("/custom-domains")
async def list_domains(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List the caller's own firm's custom domains."""
    domains = await repos.whitelabel.list_domains(context.profile.id)
    return {"domains": [_domain_out(d) for d in domains], "total": len(domains)}


@router.post("/custom-domains", status_code=201)
async def create_domain(
    payload: DomainCreate,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Register a custom portal domain (PENDING until DNS TXT verification)."""
    ensure_consultant_permission(context, "manage_team")
    domain = payload.domain.strip().lower().rstrip(".")
    if not _DOMAIN_RE.match(domain):
        raise HTTPException(status_code=422, detail="invalid domain (hostname expected)")
    created = await repos.whitelabel.create_domain(
        consultant_id=context.profile.id, domain=domain
    )
    await _audit(
        repos, context, entity_id=created.id, action="whitelabel.domain.created",
        after={"domain": domain, "status": "pending"},
    )
    return {"domain": _domain_out(created)}


@router.post("/custom-domains/{domain_id}/verify")
async def verify_domain(
    domain_id: str,
    payload: DomainVerify,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Complete domain verification by matching the DNS TXT token.

    In production a DNS lookup check should run first (Vercel/Resend-side);
    the token match records the VERIFIED transition locally. A domain never
    grants authorization by itself (D19 §12).
    """
    ensure_consultant_permission(context, "manage_team")
    ok, message = await repos.whitelabel.verify_domain(
        domain_id, context.profile.id, token=payload.token
    )
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    await _audit(
        repos, context, entity_id=domain_id, action="whitelabel.domain.verified",
        after={"status": "verified"},
    )
    return {"success": True, "status": "verified"}


@router.post("/custom-domains/{domain_id}/activate")
async def activate_domain(
    domain_id: str,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Activate a VERIFIED domain (branding may present on it)."""
    ensure_consultant_permission(context, "manage_team")
    ok = await repos.whitelabel.activate_domain(domain_id, context.profile.id)
    if not ok:
        raise HTTPException(status_code=400, detail="domain must be verified to activate")
    await _audit(
        repos, context, entity_id=domain_id, action="whitelabel.domain.activated",
        after={"status": "active"},
    )
    return {"success": True, "status": "active"}


@router.post("/custom-domains/{domain_id}/remove")
async def remove_domain(
    domain_id: str,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Remove/suspend a custom domain (removed_suspended)."""
    ensure_consultant_permission(context, "manage_team")
    ok = await repos.whitelabel.remove_domain(domain_id, context.profile.id)
    if not ok:
        raise HTTPException(status_code=404, detail="domain not found")
    await _audit(
        repos, context, entity_id=domain_id, action="whitelabel.domain.removed",
        after={"status": "removed_suspended"},
    )
    return {"success": True, "status": "removed_suspended"}

# ---------------------------------------------------------------------------
# Custom senders (optional verified From addresses)
# ---------------------------------------------------------------------------


@router.get("/senders")
async def list_senders(
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List the caller's own firm's custom email senders."""
    senders = await repos.whitelabel.list_senders(context.profile.id)
    return {"senders": [_sender_out(s) for s in senders], "total": len(senders)}


@router.post("/senders", status_code=201)
async def create_sender(
    payload: SenderCreate,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Register a custom sender (PENDING until verified via Resend domain
    verification). Arbitrary From addresses are never allowed (D19 §13)."""
    ensure_consultant_permission(context, "manage_team")
    email = payload.email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="invalid email address")
    created = await repos.whitelabel.create_sender(
        consultant_id=context.profile.id, email=email
    )
    await _audit(
        repos, context, entity_id=created.id, action="whitelabel.sender.created",
        after={"email": email, "status": "pending"},
    )
    return {"sender": _sender_out(created)}


@router.post("/senders/{sender_id}/verify")
async def verify_sender(
    sender_id: str,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Mark a sender VERIFIED.

    In production Resend verifies the underlying domain (SPF/DKIM/DMARC —
    external configuration owned by the consultant); this endpoint records the
    outcome. Only VERIFIED senders may be used as a From address.
    """
    ensure_consultant_permission(context, "manage_team")
    ok = await repos.whitelabel.verify_sender(sender_id, context.profile.id)
    if not ok:
        raise HTTPException(status_code=400, detail="sender must be pending to verify")
    await _audit(
        repos, context, entity_id=sender_id, action="whitelabel.sender.verified",
        after={"status": "verified"},
    )
    return {"success": True, "status": "verified"}


@router.post("/senders/{sender_id}/remove")
async def remove_sender(
    sender_id: str,
    context: ConsultantContext = Depends(require_consultant),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Remove a custom sender (removed)."""
    ensure_consultant_permission(context, "manage_team")
    ok = await repos.whitelabel.remove_sender(sender_id, context.profile.id)
    if not ok:
        raise HTTPException(status_code=404, detail="sender not found")
    await _audit(
        repos, context, entity_id=sender_id, action="whitelabel.sender.removed",
        after={"status": "removed"},
    )
    return {"success": True, "status": "removed"}

