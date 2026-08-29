"""V3 customer-owned emission factor endpoints (ADR-V3-002 — DECIDED).

Implements the settled customer-factor surface:

* Drafts may be created/edited/validated by organisation staff (D-cf-3).
* Approval to ``active`` is restricted to the Organisation Admin/Owner and the
  creator may never approve their own factor (D-cf-3 — no self-approval).
* Deactivation is soft (``inactive``/``archived``); there is no hard-delete
  surface (V3M-3 has no DELETE policy).
* Approved customer factors are matched ahead of CarbonTally-managed factors
  (D-cf-5) by the matching engine; snapshots record provenance via
  ``factor_kind='customer_factor'`` + ``customer_factor_id`` (O1 / ADR-V3-014).
"""
from __future__ import annotations

import uuid
from dataclasses import fields, replace
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.contracts import (
    CustomerFactorCreate,
    CustomerFactorListOut,
    CustomerFactorOut,
    CustomerFactorUpdate,
    customer_factor_out,
)
from api.dependencies import (
    RepositoryBundle,
    ensure_org_access,
    get_repositories,
    require_org_admin,
    require_org_member,
)
from auth import AuthUser
from domain.audit import AuditEntry
from domain.customer_factor import CustomerFactor
from engines.validation import validate_customer_factor

router = APIRouter(prefix="/api/v3/customer-factors", tags=["V3 — Customer Factors"])


async def _audit_factor(
    repos: RepositoryBundle,
    factor: CustomerFactor,
    *,
    action: str,
    actor: str,
    changed: dict,
) -> None:
    """Append-only audit for customer-factor lifecycle events (CL-43).

    Audit failures must never break the authoritative change (matching the
    established append-only audit pattern elsewhere in the API).
    """
    try:
        await repos.audit.record(
            AuditEntry(
                id=str(uuid.uuid4()),
                correlation_id=factor.id,
                entity_type="customer_factors",
                entity_id=factor.id,
                action=action,
                actor=actor,
                occurred_at=datetime.now(timezone.utc),
                changed_fields={
                    "organization_id": factor.organization_id,
                    "activity_type": factor.activity_type,
                    "unit": factor.unit,
                    "scope": factor.scope,
                    "reporting_year": factor.reporting_year,
                    "country": factor.country,
                    "status": factor.status,
                    "version": factor.version,
                    **changed,
                },
                reason="customer factor lifecycle event",
            )
        )
    except Exception:  # noqa: BLE001 — append-only audit must never break the request
        pass



def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:  # pragma: no cover - pydantic guards format
        raise HTTPException(status_code=422, detail="co2e_multiplier must be a number") from exc


def _reject_invalid(factor: CustomerFactor) -> None:
    """Enforce the customer-factor shape rules (A-ext) before persistence.

    Uses the single existing validation implementation
    (``engines.validation.validate_customer_factor``) — no second validator.
    Blocking (error-severity) findings are rejected with HTTP 422.
    """
    report = validate_customer_factor(factor)
    if not report.ok:
        raise HTTPException(
            status_code=422,
            detail="customer factor failed validation",
            headers={"X-CarbonTally-Validation": "failed"},
        )


def _validation_candidate(existing: CustomerFactor, **changes) -> CustomerFactor:
    """Build a validation-only ``CustomerFactor`` that skips ``__post_init__``.

    ``dataclasses.replace`` re-runs ``CustomerFactor.__post_init__`` (the
    generated ``__init__`` calls it), so constructing an invalid update — e.g. a
    negative ``co2e_multiplier`` — raises ``ValueError`` before
    ``validate_customer_factor`` can reject it with HTTP 422. This candidate is
    built from ``existing`` with the proposed field changes applied and is only
    ever handed to the validator; the real object is constructed afterwards,
    once the values are known-good.
    """
    candidate = object.__new__(CustomerFactor)
    for f in fields(CustomerFactor):
        object.__setattr__(
            candidate, f.name, changes.get(f.name, getattr(existing, f.name))
        )
    return candidate


@router.get("", response_model=CustomerFactorListOut)
async def list_customer_factors(
    organization_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> CustomerFactorListOut:
    """List customer factors for an organisation (org isolation enforced)."""
    ensure_org_access(current_user, organization_id)
    factors = await repos.customer_factors.get_org_factors(organization_id)
    return CustomerFactorListOut(
        total=len(factors), factors=[customer_factor_out(f) for f in factors]
    )


@router.get("/{factor_id}", response_model=CustomerFactorOut)
async def get_customer_factor(
    factor_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> CustomerFactorOut:
    """Return one customer factor (404 when unknown)."""
    factor = await repos.customer_factors.get(factor_id)
    if factor is None:
        raise HTTPException(status_code=404, detail=f"customer factor {factor_id} not found")
    ensure_org_access(current_user, factor.organization_id)
    return customer_factor_out(factor)


@router.post("", response_model=CustomerFactorOut, status_code=201)
async def create_customer_factor(
    payload: CustomerFactorCreate,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> CustomerFactorOut:
    """Create a customer factor as a DRAFT (D-cf-3 — approval required later).

    CL-43 / D-cf-4 lifecycle:
    * ``version`` is optional. When omitted the API resolves the next free
      version in the family (max + 1) — this is the supported way to open a
      NEW VERSION of an approved factor without editing the active row.
    * A duplicate family/version is a clean HTTP 409 (never a raw 500).
    """
    ensure_org_access(current_user, payload.organization_id)
    now = datetime.now(timezone.utc)

    family = await repos.customer_factors.find_by_family(
        payload.organization_id,
        payload.activity_type.strip(),
        payload.reporting_year,
        payload.country,
        payload.unit,
        payload.scope,
    )
    if payload.version is not None:
        # Explicit version: the family/version must be free.
        existing = next((f for f in family if f.version == payload.version), None)
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "a customer factor with this activity/unit/scope family "
                    f"already exists at version {payload.version} — create a "
                    "new version instead"
                ),
            )
        version = payload.version
    else:
        newest = max(family, key=lambda f: f.version) if family else None
        if newest is not None and newest.status == "draft":
            # Duplicate create: the newest slot in the family is still a draft.
            # Editing it (PUT) is the supported path; a second identical create
            # must never silently succeed as a brand-new factor.
            raise HTTPException(
                status_code=409,
                detail=(
                    "a draft customer factor already exists in this family at "
                    f"version {newest.version} — edit the draft, approve it, or "
                    "create an explicit new version"
                ),
            )
        version = await repos.customer_factors.next_version(
            payload.organization_id,
            payload.activity_type.strip(),
            payload.reporting_year,
            payload.country,
            payload.unit,
            payload.scope,
        )

    factor = CustomerFactor(
        id=str(uuid.uuid4()),
        organization_id=payload.organization_id,
        name=payload.name.strip(),
        description=payload.description,
        activity_type=payload.activity_type.strip(),
        co2e_multiplier=_decimal(payload.co2e_multiplier),
        unit=payload.unit,
        scope=payload.scope,
        country=payload.country,
        reporting_year=payload.reporting_year,
        factor_source="CUSTOMER",
        status="draft",
        version=version,
        metadata=payload.metadata,
        created_at=now,
        updated_at=now,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )
    _reject_invalid(factor)
    try:
        stored = await repos.customer_factors.save(factor)
    except Exception as exc:  # noqa: BLE001 — race on the family/version index
        import asyncpg

        if isinstance(exc, asyncpg.exceptions.UniqueViolationError):
            raise HTTPException(
                status_code=409,
                detail=(
                    "a customer factor with this family and version "
                    f"({version}) already exists — create a new version instead"
                ),
            ) from exc
        raise
    await _audit_factor(
        repos,
        factor,
        action="customer_factor:created",
        actor=current_user.user_id,
        changed={
            "version": version,
            "status": factor.status,
            "activity_type": factor.activity_type,
            "unit": factor.unit,
            "scope": factor.scope,
        },
    )
    return customer_factor_out(stored)


@router.put("/{factor_id}", response_model=CustomerFactorOut)
async def update_customer_factor(
    factor_id: str,
    payload: CustomerFactorUpdate,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> CustomerFactorOut:
    """Edit a DRAFT customer factor (D-cf-4: approved factors change only via a
    new version)."""
    existing = await repos.customer_factors.get(factor_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"customer factor {factor_id} not found")
    ensure_org_access(current_user, existing.organization_id)
    if existing.status != "draft":
        raise HTTPException(
            status_code=409,
            detail="only draft customer factors can be edited; create a new version instead",
        )
    merged = {
        "name": payload.name.strip() if payload.name is not None else existing.name,
        "description": payload.description if payload.description is not None else existing.description,
        "activity_type": payload.activity_type.strip() if payload.activity_type is not None else existing.activity_type,
        "co2e_multiplier": _decimal(payload.co2e_multiplier) if payload.co2e_multiplier is not None else existing.co2e_multiplier,
        "unit": payload.unit if payload.unit is not None else existing.unit,
        "scope": payload.scope if payload.scope is not None else existing.scope,
        "metadata": payload.metadata if payload.metadata is not None else existing.metadata,
        "updated_by": current_user.user_id,
    }
    # Validate the merged values BEFORE constructing the frozen domain object.
    # ``dataclasses.replace`` re-runs ``CustomerFactor.__post_init__``, so an
    # invalid update would otherwise raise ValueError (HTTP 500) instead of
    # being rejected by validate_customer_factor with HTTP 422.
    _reject_invalid(_validation_candidate(existing, **merged))
    updated = replace(existing, **merged)
    stored = await repos.customer_factors.save(updated)
    return customer_factor_out(stored)


@router.post("/{factor_id}/approve", response_model=CustomerFactorOut)
async def approve_customer_factor(
    factor_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> CustomerFactorOut:
    """Approve a customer factor (PO Decision 1 — owner self-approval).

    An organisation OWNER may create and approve their organisation's custom
    factor (the old blanket no-self-approval is removed for owners). For
    non-owner approvers the no-self-approval rule is preserved: an admin who
    created a factor still needs a different authorising actor.
    """
    existing = await repos.customer_factors.get(factor_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"customer factor {factor_id} not found")
    ensure_org_access(current_user, existing.organization_id)
    # PO Decision 1: org owners may self-approve (audited via updated_by).
    is_owner = getattr(current_user, "role", None) == "org_owner"
    if existing.created_by == current_user.user_id and not is_owner:
        raise HTTPException(
            status_code=403,
            detail="a factor's creator cannot approve their own factor (only the organisation owner may self-approve)",
        )
    if not existing.can_transition_to("active"):
        raise HTTPException(
            status_code=409,
            detail=f"cannot approve a factor in status {existing.status!r}",
        )
    stored = await repos.customer_factors.update_status(
        factor_id, "active", updated_by=current_user.user_id
    )
    await _audit_factor(
        repos,
        stored,
        action="customer_factor:approved",
        actor=current_user.user_id,
        changed={"previous_status": existing.status, "version": existing.version},
    )
    return customer_factor_out(stored)


@router.post("/{factor_id}/deactivate", response_model=CustomerFactorOut)
async def deactivate_customer_factor(
    factor_id: str,
    current_user: AuthUser = Depends(require_org_admin()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> CustomerFactorOut:
    """Soft-deactivate a customer factor (``inactive``; V3M-3 no-DELETE)."""
    existing = await repos.customer_factors.get(factor_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"customer factor {factor_id} not found")
    ensure_org_access(current_user, existing.organization_id)
    if not existing.can_transition_to("inactive"):
        raise HTTPException(
            status_code=409,
            detail=f"cannot deactivate a factor in status {existing.status!r}",
        )
    stored = await repos.customer_factors.update_status(
        factor_id, "inactive", updated_by=current_user.user_id
    )
    await _audit_factor(
        repos,
        stored,
        action="customer_factor:deactivated",
        actor=current_user.user_id,
        changed={"previous_status": existing.status, "version": existing.version},
    )
    return customer_factor_out(stored)


