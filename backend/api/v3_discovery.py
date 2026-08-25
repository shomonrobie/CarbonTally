"""V3 existing-data discovery & direct-customer adoption (D27 / D19 §5-§9).

Customer-initiated direct onboarding. A customer who completes normal signup
may discover potentially matching organizational data already on the platform.

Workflow:

    POST /discovery/lookup                      candidate signals -> candidates
    POST /discovery/requests                    create request (pending)
    GET  /discovery/requests/{id}               review + safe data counts
    POST /discovery/requests/{id}/verify        email code verification
    POST /discovery/requests/{id}/staff-verify  CarbonTally-staff mediation
    POST /discovery/requests/{id}/choice        use_all | partial | discard

Security (D19 §6): candidate signals (name/company number/email domain/contact
email) are CANDIDATE ONLY. Adoption requires authenticated verification
(control of the candidate org's registered contact email, or staff mediation)
and explicit customer choice. Adoption is IN-PLACE — the existing
``organizations.id`` becomes the direct-customer org; no data copy. DISCARD
records the decision and deletes nothing. Successful adoption ends ACTIVE
consultant grants for the adopted org (D15/D19).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
    require_admin,
    require_org_member,
)
from auth import AuthUser, require_auth
from domain.audit import AuditEntry
from domain.discovery import (
    ADOPTION_CHOICES,
    ADOPTION_SCOPE_CATEGORIES,
    DISCOVERY_STATUSES,
    VERIFICATION_METHODS,
    validate_adoption_scope,
)
from data.discovery import generate_verification_code
from services.v3_email import render_simple_html, send_transactional_email

router = APIRouter(prefix="/api/v3/discovery", tags=["V3 — Discovery (D19)"])


class LookupIn(BaseModel):
    """Candidate signals for existing-data discovery (NEVER authoritative).

    ``organization_id`` is the requesting org for the standard D19 flow. D35
    makes it optional: when omitted, the lookup runs as a PRE-ORG-CREATION
    self-service onboarding lookup for any authenticated user (safe candidate
    metadata + data counts only — never customer data rows).
    """

    organization_id: Optional[str] = None
    name: Optional[str] = None
    company_number: Optional[str] = None
    email_domain: Optional[str] = None
    contact_email: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class RequestCreate(BaseModel):
    organization_id: Optional[str] = None
    candidate_organization_id: str = Field(..., min_length=1)
    verification_method: str = "email"
    note: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class VerifyIn(BaseModel):
    organization_id: Optional[str] = None
    code: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class ChoiceIn(BaseModel):
    organization_id: Optional[str] = None
    choice: str
    scope: dict[str, Any] = Field(default_factory=dict)
    note: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


def _request_out(request: Any, *, include_code_hint: bool = False) -> dict[str, Any]:
    data = {
        "id": request.id,
        "organization_id": request.organization_id,
        "candidate_organization_id": request.candidate_organization_id,
        "status": request.status,
        "verification_method": request.verification_method,
        "verification_attempts": request.verification_attempts,
        "verified_at": request.verified_at,
        "verified_by": request.verified_by,
        "adoption_choice": request.adoption_choice,
        "adoption_scope": request.adoption_scope or {},
        "adopted_at": request.adopted_at,
        "adopted_by": request.adopted_by,
        "discarded_at": request.discarded_at,
        "discarded_by": request.discarded_by,
        "note": request.note,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
    }
    if include_code_hint:
        data["verification_code_hint"] = (
            "delivered to the candidate organisation's registered contact "
            "(when delivery is configured)"
        )
    return data


async def _org_member_role(
    repos: RepositoryBundle, organization_id: str, user_id: str
) -> Optional[str]:
    """Return the caller's role in ``organization_id`` (owner/admin/member/
    viewer) via the tenant repo — independent of the single-bound-org resolver."""
    member = await repos.tenant.get_member_by_user(organization_id, user_id)
    if member is None:
        return None
    if isinstance(member, dict):
        return member.get("role")
    return member.role


async def _require_org_admin_of(
    repos: RepositoryBundle, organization_id: str, user_id: str, current_user: AuthUser
) -> None:
    """Raise 403 unless the caller is an owner/admin of ``organization_id``.

    Checks the authoritative membership row first (org-agnostic), then falls
    back to the AuthUser-derived role when the caller's bound org matches.
    """
    role = await _org_member_role(repos, organization_id, user_id)
    if role in ("owner", "admin"):
        return
    if (
        getattr(current_user, "organization_id", None) == organization_id
        and (
            current_user.role in ("org_owner", "org_admin")
            or current_user.role_name in ("owner", "admin")
        )
    ):
        return
    raise HTTPException(
        status_code=403,
        detail="Organization admin privileges required for this organisation",
    )


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
    try:
        await repos.audit.record(entry)
    except Exception:  # noqa: BLE001 — audit must never break the flow
        pass


# ---------------------------------------------------------------------------
# Lookup — candidate signals only (never authoritative)
# ---------------------------------------------------------------------------


@router.post("/lookup")
async def discovery_lookup(
    payload: LookupIn,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Find POTENTIALLY matching organisations.

    Two authorized modes (D35):
    * ``organization_id`` supplied — the standard D19 flow: the caller must be
      an org member of the requesting org (``ensure_org_access``).
    * ``organization_id`` omitted — PRE-ORG-CREATION self-service onboarding
      lookup for any authenticated user who has not yet created/adopted an
      organization. Returns the same safe candidate metadata + data counts
      only — never customer data rows (D19 §6).

    Candidate signals are matched loosely; the results are candidates only —
    ownership is NEVER inferred from name/domain/supplier/consultant.
    """
    if payload.organization_id:
        ensure_org_access(current_user, payload.organization_id)
    candidates = await repos.discovery.lookup_candidates(
        name=payload.name,
        company_number=payload.company_number,
        email_domain=payload.email_domain,
        contact_email=payload.contact_email,
        limit=10,
    )
    # Never return the caller's own org as a candidate.
    candidates = [
        c
        for c in candidates
        if (
            payload.organization_id is None or c.organization_id != payload.organization_id
        )
        and not (await _org_member_role(repos, c.organization_id, current_user.user_id))
    ]
    return {
        "candidates": [
            {
                "organization_id": c.organization_id,
                "name": c.name,
                "country": c.country,
                "industry": c.industry,
                "company_number": c.company_number,
                "match_signal": c.match_signal,
                "data_summary": c.data_summary,
            }
            for c in candidates
        ],
        "disclaimer": (
            "These are candidate matches only. Adoption requires secure "
            "verification and your explicit choice (D19)."
        ),
    }


@router.post("/requests", status_code=201)
async def create_request(
    payload: RequestCreate,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Create an existing-data discovery request.

    Two authorized modes (D35):
    * ``organization_id`` supplied — the standard D19 flow: org-admin authority
      over the requesting org is required.
    * ``organization_id`` omitted — PRE-ORG-CREATION self-service onboarding
      request: any authenticated user with no active organization may start one
      against a candidate organisation. The request is bound to the caller
      (``created_by``); only that user may verify and choose an outcome.

    For the ``email`` method a verification code is generated and delivered to
    the candidate org's registered contact (best-effort;
    ``verification_delivered`` reports the honest outcome). Staff-mediated
    requests are completed by CarbonTally internal admins via ``/staff-verify``.
    """
    if payload.organization_id:
        ensure_org_access(current_user, payload.organization_id)
        await _require_org_admin_of(
            repos, payload.organization_id, current_user.user_id, current_user
        )
        existing = await repos.discovery.get_for_candidate(
            payload.organization_id, payload.candidate_organization_id
        )
        if existing is not None and existing.status in (
            "pending_verification", "verified", "adopted",
        ):
            raise HTTPException(
                status_code=409,
                detail=f"a discovery request for this candidate already exists (status={existing.status})",
            )
    else:
        memberships = await repos.organizations.get_active_memberships_for_user(
            current_user.user_id
        )
        if memberships:
            raise HTTPException(
                status_code=409,
                detail="you already belong to an organization — use the existing-data page in the workspace",
            )
        existing = await repos.discovery.get_onboarding_by_candidate(
            payload.candidate_organization_id, current_user.user_id
        )
        if existing is not None and existing.status in (
            "pending_verification", "verified",
        ):
            raise HTTPException(
                status_code=409,
                detail=f"you already have a live onboarding request for this candidate (status={existing.status})",
            )

    if payload.verification_method not in VERIFICATION_METHODS:
        raise HTTPException(
            status_code=422, detail=f"verification_method must be one of {list(VERIFICATION_METHODS)}"
        )
    if payload.organization_id and payload.candidate_organization_id == payload.organization_id:
        raise HTTPException(status_code=422, detail="cannot discover your own organisation")
    candidate = await repos.organizations.get_full(payload.candidate_organization_id)
    if candidate is None or not candidate.get("is_active", True):
        raise HTTPException(status_code=404, detail="candidate organisation not found")
    if candidate.get("customer_type") == "direct":
        raise HTTPException(
            status_code=409,
            detail="candidate organisation is already a Direct CarbonTally Customer",
        )

    if payload.organization_id:
        request = await repos.discovery.create_request(
            organization_id=payload.organization_id,
            candidate_organization_id=payload.candidate_organization_id,
            verification_method=payload.verification_method,
            note=payload.note,
        )
    else:
        request = await repos.discovery.create_onboarding_request(
            candidate_organization_id=payload.candidate_organization_id,
            created_by=current_user.user_id,
            verification_method=payload.verification_method,
            note=payload.note,
        )

    delivered = False
    delivery_note = ""
    if payload.verification_method == "email":
        code = generate_verification_code()
        await repos.discovery.store_verification_code(request.id, code)
        contact_email = (
            candidate.get("primary_contact_email")
            or candidate.get("billing_contact_email")
        )
        if not contact_email:
            delivery_note = "candidate organisation has no registered contact email — use staff mediation"
        else:
            html = render_simple_html(
                brand_name="CarbonTally",
                heading="Verify access to existing organizational data",
                body_html=(
                    f"<p>An existing-data adoption request has been started for "
                    f"<strong>{candidate.get('name')}</strong>.</p>"
                    f"<p>Your verification code is:</p>"
                    f"<p style='font-size:28px;font-weight:700;letter-spacing:2px;"
                    f"font-family:monospace'>{code}</p>"
                    f"<p>It expires in 15 minutes. If you did not start this request, "
                    f"you can ignore this email.</p>"
                ),
            )
            delivered, delivery_note = await send_transactional_email(
                to_email=contact_email,
                subject="CarbonTally — existing-data adoption verification",
                html=html,
            )

    await _record_audit(
        repos,
        entity_type="data_discovery_request",
        entity_id=request.id,
        action="discovery.requested",
        actor=current_user.user_id,
        after={"status": request.status, "candidate": payload.candidate_organization_id},
        reason=payload.note,
    )

    return {
        "request": _request_out(request),
        "verification_delivered": delivered,
        "delivery_note": delivery_note or None,
    }


@router.get("/requests")
async def list_requests(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """List the requesting org's discovery requests."""
    ensure_org_access(current_user, organization_id)
    requests = await repos.discovery.list_for_org(organization_id)
    return {
        "requests": [_request_out(r) for r in requests],
        "total": len(requests),
    }


@router.get("/requests/{request_id}")
async def get_request(
    request_id: str,
    organization_id: Optional[str] = None,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Detail for one request (ownership-scoped) + safe candidate data counts.

    ``organization_id`` supplied — the standard D19 org-scoped fetch. Omitted —
    a pre-org-creation onboarding request is returned only to the user who
    created it (D35).
    """
    if organization_id:
        ensure_org_access(current_user, organization_id)
        request = await repos.discovery.get_for_org(request_id, organization_id)
    else:
        request = await repos.discovery.get_for_onboarding(
            request_id, current_user.user_id
        )
    if request is None:
        raise HTTPException(status_code=404, detail="discovery request not found")
    candidate = await repos.organizations.get_full(request.candidate_organization_id)
    summary = await repos.discovery._org_data_summary(request.candidate_organization_id)
    return {
        "request": _request_out(request),
        "candidate": {
            "organization_id": request.candidate_organization_id,
            "name": (candidate or {}).get("name"),
            "country": (candidate or {}).get("country"),
            "industry": (candidate or {}).get("industry"),
            "data_summary": summary,
        },
        "eligible_categories": list(ADOPTION_SCOPE_CATEGORIES),
    }


@router.post("/requests/{request_id}/verify")
async def verify_request(
    request_id: str,
    payload: VerifyIn,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Verify the request with the email code (control of the candidate org's
    registered contact).

    ``organization_id`` supplied — org-scoped D19 flow. Omitted — the request
    is an onboarding request and only its creator may verify it (D35).
    """
    if payload.organization_id:
        ensure_org_access(current_user, payload.organization_id)
        request = await repos.discovery.get_for_org(request_id, payload.organization_id)
    else:
        request = await repos.discovery.get_for_onboarding(
            request_id, current_user.user_id
        )
    if request is None:
        raise HTTPException(status_code=404, detail="discovery request not found")
    if request.verification_method != "email":
        raise HTTPException(status_code=409, detail="request uses staff-mediated verification")
    ok, reason = await repos.discovery.verify_code(request_id, payload.code, verified_by=current_user.user_id)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    await _record_audit(
        repos,
        entity_type="data_discovery_request",
        entity_id=request_id,
        action="discovery.verified",
        actor=current_user.user_id,
        after={"status": "verified"},
        reason="email code verification (onboarding)" if not payload.organization_id else "email code verification",
    )
    return {"success": True, "status": "verified"}


@router.post("/requests/{request_id}/staff-verify")
async def staff_verify_request(
    request_id: str,
    payload: VerifyIn,
    current_user: AuthUser = Depends(require_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """CarbonTally-internal staff-mediated verification (operational fallback
    when email delivery is unavailable). Requires internal staff admin."""
    ok = await repos.discovery.staff_verify(request_id, verified_by=current_user.user_id)
    if not ok:
        raise HTTPException(status_code=400, detail="request cannot be staff-verified (status must be pending_verification)")
    await _record_audit(
        repos,
        entity_type="data_discovery_request",
        entity_id=request_id,
        action="discovery.staff_verified",
        actor=current_user.user_id,
        after={"status": "verified"},
        reason="CarbonTally staff-mediated verification",
    )
    return {"success": True, "status": "verified"}


# ---------------------------------------------------------------------------
# Adoption choice — USE ALL / PARTIAL / DISCARD (D19 §7)
# ---------------------------------------------------------------------------


@router.post("/requests/{request_id}/choice")
async def choose_adoption(
    request_id: str,
    payload: ChoiceIn,
    current_user: AuthUser = Depends(require_auth()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """The customer's explicit adoption choice.

    * ``use_all``  — adopt the existing org IN-PLACE (identity preserved; no
                     data copy), become its owner, end ACTIVE consultant grants.
    * ``partial``  — adopt in-place and record the selected categories for
                     provenance (safe: no per-record partial-copy semantics).
    * ``discard``  — keep the new org; the discovery decision is recorded and
                     NO data is deleted (a formal deletion is a separate
                     process — D19 §7).

    ``organization_id`` supplied — the standard D19 org-scoped flow. Omitted —
    the request is a PRE-ORG-CREATION onboarding request (D35): only the user
    who created AND verified it may choose an outcome; on USE ALL / PARTIAL the
    existing organisation id becomes the customer's organisation and they
    become its OWNER (the requesting-org deactivation is skipped because there
    is no requesting org).
    """
    if payload.organization_id:
        ensure_org_access(current_user, payload.organization_id)
        request = await repos.discovery.get_for_org(request_id, payload.organization_id)
    else:
        request = await repos.discovery.get_for_onboarding(
            request_id, current_user.user_id
        )
    if request is None:
        raise HTTPException(status_code=404, detail="discovery request not found")
    if request.status not in ("verified",):
        raise HTTPException(
            status_code=409,
            detail=f"adoption requires a verified request (status={request.status})",
        )
    if request.organization_id is None:
        # Onboarding request: the actor must be the creator AND the verifier.
        if request.created_by != current_user.user_id:
            raise HTTPException(status_code=403, detail="you did not initiate this onboarding request")
        if request.verified_by != current_user.user_id:
            raise HTTPException(
                status_code=409,
                detail="this onboarding request was not verified by you",
            )
    if payload.choice not in ADOPTION_CHOICES:
        raise HTTPException(status_code=422, detail=f"choice must be one of {list(ADOPTION_CHOICES)}")
    ok, message = validate_adoption_scope(payload.choice, payload.scope)
    if not ok:
        raise HTTPException(status_code=422, detail=message)

    if payload.choice == "discard":
        updated = await repos.discovery.discard(
            request_id, discarded_by=current_user.user_id, note=payload.note
        )
        await _record_audit(
            repos,
            entity_type="data_discovery_request",
            entity_id=request_id,
            action="discovery.discarded",
            actor=current_user.user_id,
            before={"status": "verified"},
            after={"status": "discarded"},
            reason="customer chose DISCARD — no data deleted",
        )
        return {"request": _request_out(updated), "outcome": "discarded"}

    return await _perform_adoption(
        repos, request_id, request.candidate_organization_id, payload, current_user
    )


async def _perform_adoption(
    repos: RepositoryBundle,
    request_id: str,
    candidate_organization_id: str,
    payload: ChoiceIn,
    current_user: AuthUser,
) -> dict:
    """In-place adoption: the existing org becomes the customer's direct org.

    Identity preservation (D19 §9): the existing ``organizations.id`` is the
    adopted tenant — documents, extraction history, mappings, validation,
    calculations, reports, report versions, audit history and provenance all
    remain attached to the SAME org id. No copy, no rewrite of historical
    ``created_by``/``processed_by``/``assigned_to`` values.

    Steps:
      1. grant the verified customer owner membership in the adopted org;
      2. deactivate the customer's membership in the (new) requesting org so
         their org context resolves to the adopted org;
      3. end every ACTIVE consultant grant for the adopted org (D15/D19);
      4. label the org ``direct`` (informational);
      5. audit every step.
    """
    actor = current_user.user_id

    existing_member = await repos.tenant.get_member_by_user(
        candidate_organization_id, actor
    )
    if existing_member is not None:
        existing_id = existing_member.get("id") if isinstance(existing_member, dict) else existing_member.id
        await repos.tenant.update_member(existing_id, role="owner", is_active=True)
    else:
        await repos.tenant.add_member(candidate_organization_id, actor, "owner")

    # Deactivate the user's membership in the redundant (new) requesting org so
    # the single-org resolver binds the adopted org. Skipped for D35 onboarding
    # requests (organization_id is None — the customer had no requesting org).
    if payload.organization_id is not None:
        requesting_member = await repos.tenant.get_member_by_user(
            payload.organization_id, actor
        )
        if requesting_member is not None:
            requesting_id = (
                requesting_member.get("id")
                if isinstance(requesting_member, dict)
                else requesting_member.id
            )
            await repos.tenant.update_member(requesting_id, role=None, is_active=False)

    # End ACTIVE consultant relationships (D19 §10 — access terminates).
    ended_grants = []
    active_grants = await repos.consultants.list_active_client_grants(
        candidate_organization_id
    )
    for grant in active_grants:
        ended = await repos.consultants.transition_client_lifecycle(
            grant.id, "ended", actor_id=actor
        )
        if ended is not None:
            ended_grants.append(grant.id)
            await _record_audit(
                repos,
                entity_type="consultant_client",
                entity_id=grant.id,
                action="consultant_client.ended",
                actor=actor,
                before={"status": "active"},
                after={"status": "ended"},
                reason="customer became a Direct CarbonTally Customer (D19 adoption)",
            )

    await repos.organizations.set_customer_type(candidate_organization_id, "direct")

    updated = await repos.discovery.adopt(
        request_id,
        choice=payload.choice,
        scope=payload.scope if payload.choice == "partial" else None,
        adopted_by=actor,
    )

    await _record_audit(
        repos,
        entity_type="data_discovery_request",
        entity_id=request_id,
        action="discovery.adopted",
        actor=actor,
        before={"status": "verified"},
        after={"status": "adopted", "choice": payload.choice},
        reason="in-place direct-customer adoption (D19)",
    )

    await _record_audit(
        repos,
        entity_type="organization",
        entity_id=candidate_organization_id,
        action="organization.direct_customer",
        actor=actor,
        after={"customer_type": "direct"},
        reason="customer-initiated adoption completed",
    )

    try:
        await repos.notifications.create(
            actor,
            notification_type="general",
            title="Existing data adopted",
            message=(
                f"You are now a Direct CarbonTally Customer for "
                f"{candidate_organization_id}. Historical organizational data "
                "has been preserved in place."
            ),
            link="/home",
        )
    except Exception:  # noqa: BLE001 — notification must never break adoption
        pass

    return {
        "request": _request_out(updated),
        "outcome": "adopted",
        "adopted_organization_id": candidate_organization_id,
        "choice": payload.choice,
        "scope": payload.scope if payload.choice == "partial" else None,
        "ended_consultant_grants": ended_grants,
        "note": (
            "Adoption is in-place: the existing organisation and all historical "
            "data (documents, extractions, mappings, calculations, reports, "
            "audit/provenance) are preserved under the same organisation id."
        ),
    }
