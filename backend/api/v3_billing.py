"""D37 — customer billing surface (org-scoped, server-authoritative).

Every endpoint validates organization scope on the request (the browser is
never authoritative). Customers can VIEW billing state / credits / storage /
orders and REQUEST + APPROVE chargeable Assisted/Managed orders. All mutations
are idempotent (client supplies an ``idempotency_key``) and audited by the
BillingService. No payment-provider integration exists.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import RepositoryBundle, get_repositories
from auth import AuthUser, require_org_member
from services.billing import (
    BillingError,
    BillingService,
    EntitlementUnavailableError,
    IdempotencyConflict,
    OrderStateError,
)

router = APIRouter(prefix="/api/v3/billing", tags=["V3 — Customer Billing (D37)"])


def _svc(repos: RepositoryBundle) -> BillingService:
    return BillingService(repos)


def _billing_error(exc: BillingError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


def _order_out(order) -> dict[str, Any]:
    return {
        "id": order.id,
        "order_type": order.order_type,
        "status": order.status,
        "title": order.title,
        "description": order.description,
        "complexity": order.complexity,
        "items": order.items,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "plan_code": order.plan_code,
        "plan_version": order.plan_version,
        "approved_at": order.approved_at.isoformat() if order.approved_at else None,
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


class AssistedEstimateLine(BaseModel):
    complexity: str = Field(..., pattern=r"^(simple|standard|complex|exceptional)$")
    quantity: int = Field(1, ge=1)
    label: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class AssistedEstimate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    lines: list[AssistedEstimateLine] = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=8, max_length=120)

    model_config = ConfigDict(extra="forbid")


class ManagedOrder(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    quantity_documents: int = Field(1, ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=120)

    model_config = ConfigDict(extra="forbid")


class OrderAction(BaseModel):
    idempotency_key: Optional[str] = Field(None, max_length=120)

    model_config = ConfigDict(extra="forbid")

# ---------------------------------------------------------------------------
# Reads (org-scoped)
# ---------------------------------------------------------------------------


@router.get("/me")
async def billing_overview(
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Entitlement + credit balance + storage + STANDARD allowance."""
    org_id = _resolve_org(current_user)
    try:
        return await _svc(repos).get_entitlement(org_id)
    except EntitlementUnavailableError as exc:
        raise _billing_error(exc)


@router.get("/me/credits")
async def credit_history(
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Append-only credit ledger for the caller's organisation."""
    org_id = _resolve_org(current_user)
    entries = await repos.billing_ledger.list_for_org(org_id)
    return {
        "organization_id": org_id,
        "balance": await repos.billing_ledger.balance(org_id),
        "entries": [
            {
                "id": e.id,
                "entry_type": e.entry_type,
                "credit_delta": e.credit_delta,
                "source": e.source,
                "reason": e.reason,
                "plan_code": e.plan_code,
                "plan_version": e.plan_version,
                "order_id": e.order_id,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
    }


@router.get("/me/orders")
async def list_orders(
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    org_id = _resolve_org(current_user)
    return {"orders": [_order_out(o) for o in await repos.billing_orders.list_for_org(org_id)]}


@router.get("/me/orders/{order_id}")
async def get_order(
    order_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    org_id = _resolve_org(current_user)
    order = await repos.billing_orders.get_for_org(order_id, org_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return {"order": _order_out(order)}


@router.get("/me/payments")
async def list_payments(
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Provider-neutral payment records (read-only; no credentials exposed)."""
    org_id = _resolve_org(current_user)
    records = await repos.billing_payments.list_for_org(org_id)
    return {
        "records": [
            {
                "id": r.id,
                "provider": r.provider,
                "payment_method_type": r.payment_method_type,
                "amount": r.amount,
                "currency": r.currency,
                "status": r.status,
                "order_id": r.order_id,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in records
        ]
    }


@router.post("/me/storage/refresh")
async def refresh_storage(
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Re-measure storage usage server-side (from D32 organization_files)."""
    org_id = _resolve_org(current_user)
    usage = await _svc(repos).meter_storage(org_id)
    return {
        "usage_bytes": usage.usage_bytes,
        "included_bytes": usage.included_bytes,
        "additional_bytes": usage.additional_bytes,
        "measured_at": usage.measured_at.isoformat() if usage.measured_at else None,
    }


# ---------------------------------------------------------------------------
# Assisted Processing (estimate → approval → commercial order)
# ---------------------------------------------------------------------------


@router.post("/orders/assisted", status_code=201)
async def create_assisted_estimate(
    payload: AssistedEstimate,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Create a configurable-price Assisted Processing estimate for approval."""
    org_id = _resolve_org(current_user)
    try:
        order = await _svc(repos).estimate_assisted_order(
            org_id,
            title=payload.title,
            description=payload.description,
            lines=[l.model_dump() for l in payload.lines],
            idempotency_key=payload.idempotency_key,
            actor=current_user.user_id,
        )
    except (BillingError, IdempotencyConflict) as exc:
        raise _billing_error(exc)
    return {"order": _order_out(order)}


@router.post("/orders/{order_id}/approve")
async def approve_order(
    order_id: str,
    payload: OrderAction,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Customer approval authorises the commercial job (idempotent via key)."""
    org_id = _resolve_org(current_user)
    key = payload.idempotency_key or f"approve:{order_id}:{current_user.user_id}"
    try:
        order = await _svc(repos).approve_order(order_id, org_id, actor=current_user.user_id)
    except (BillingError, OrderStateError, IdempotencyConflict) as exc:
        raise _billing_error(exc)
    return {"order": _order_out(order)}


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    org_id = _resolve_org(current_user)
    try:
        order = await _svc(repos).cancel_order(order_id, org_id, actor=current_user.user_id)
    except (BillingError, OrderStateError) as exc:
        raise _billing_error(exc)
    return {"order": _order_out(order)}


# ---------------------------------------------------------------------------
# Managed Processing (common order foundation)
# ---------------------------------------------------------------------------


@router.post("/managed/orders", status_code=201)
async def create_managed_order(
    payload: ManagedOrder,
    current_user: AuthUser = Depends(require_org_member()),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Submit a Managed Processing request (common billing_orders model)."""
    org_id = _resolve_org(current_user)
    try:
        order = await _svc(repos).create_order(
            org_id,
            order_type="managed",
            title=payload.title,
            description=payload.description,
            items=[{
                "description": "Managed Processing batch",
                "quantity": payload.quantity_documents,
                "unit_price": 0.0,
                "quoted": True,
                "line_total": 0.0,
            }],
            idempotency_key=payload.idempotency_key,
            status="estimated",
            metadata={"managed": True, "quantity_documents": payload.quantity_documents},
            actor=current_user.user_id,
        )
    except (BillingError, IdempotencyConflict) as exc:
        raise _billing_error(exc)
    return {"order": _order_out(order)}


def _resolve_org(current_user: AuthUser) -> str:
    org_id = current_user.organization_id or getattr(current_user, "default_org_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="no organization context")
    return org_id

