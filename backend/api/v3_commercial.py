"""D37-0 — provider-neutral commercial configuration API (CarbonTally internal).

The trusted surface for the configurable subscription/commercial foundation:

* versioned commercial rules (default billing mode, credit rules,
  structured-data bands, storage, assisted pricing, credit policy,
  standard allowance) — ``billing_commercial_config``;
* the versioned plan catalogue — ``billing_plans``;
* the append-only credit ledger read surface — ``billing_credit_ledger``;
* the per-customer ``billing_mode`` read surface.

Authorization (D37-0 §24): every endpoint requires an ACTIVE CarbonTally
INTERNAL staff profile (``entity_id IS NULL``) AND the real
``can_manage_billing`` staff permission. Ordinary customers, consultants,
Processing Entity staff and customer team members are denied. Every material
change is versioned (a new row — history is never rewritten) and audited
(append-only ``audit_trail``: who, what, before/after version, timestamp,
reason).

Provider-neutral: no payment-provider code, no checkout, no webhooks.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.dependencies import RepositoryBundle, get_repositories
from api.operations_auth import (
    StaffContext,
    ensure_staff_permission,
    require_internal_staff,
    require_staff,
)
from domain.audit import AuditEntry
from domain.billing import BILLING_MODES, BillingPlan

router = APIRouter(prefix="/api/v3/commercial", tags=["V3 — Commercial (D37-0)"])

#: The versioned commercial rule keys the Admin Dashboard may configure.
CONFIG_KEYS: tuple[str, ...] = (
    "default_billing_mode",
    "credit_rules",
    "structured_data_bands",
    "storage",
    "assisted_pricing",
    "credit_policy",
    "standard_allowance",
)


def _require_billing_admin(context: StaffContext) -> None:
    """Internal CarbonTally staff with the real ``can_manage_billing`` flag."""
    require_internal_staff(context)
    ensure_staff_permission(context, "can_manage_billing")


async def _audit(
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
        changed_fields={"version": (after or {}).get("version")},
        reason=reason,
        before=before,
        after=after,
    )
    try:
        await repos.audit.record(entry)
    except Exception:  # noqa: BLE001 — append-only audit must never break the request
        pass


def _config_out(config) -> dict:
    return {
        "id": config.id,
        "config_key": config.config_key,
        "config_value": config.config_value,
        "version": config.version,
        "reason": config.reason,
        "effective_from": config.effective_from.isoformat() if config.effective_from else None,
        "effective_to": config.effective_to.isoformat() if config.effective_to else None,
        "created_by": config.created_by,
    }


def _plan_out(plan) -> dict:
    return {
        "id": plan.id,
        "plan_code": plan.plan_code,
        "name": plan.name,
        "description": plan.description,
        "price": plan.price,
        "currency": plan.currency,
        "billing_interval": plan.billing_interval,
        "included_credits": plan.included_credits,
        "included_storage_bytes": plan.included_storage_bytes,
        "team_member_limit": plan.team_member_limit,
        "processing_limits": plan.processing_limits,
        "features": plan.features,
        "billing_mode": plan.billing_mode,
        "assisted_processing_available": plan.assisted_processing_available,
        "managed_processing_available": plan.managed_processing_available,
        "api_access": plan.api_access,
        "is_active": plan.is_active,
        "version": plan.version,
        "version_label": plan.version_label,
        "effective_from": plan.effective_from.isoformat() if plan.effective_from else None,
        "effective_to": plan.effective_to.isoformat() if plan.effective_to else None,
    }


def _ledger_out(entry) -> dict:
    return {
        "id": entry.id,
        "organization_id": entry.organization_id,
        "entry_type": entry.entry_type,
        "credit_delta": entry.credit_delta,
        "source": entry.source,
        "reason": entry.reason,
        "plan_code": entry.plan_code,
        "plan_version": entry.plan_version,
        "subscription_id": entry.subscription_id,
        "external_reference": entry.external_reference,
        "correlation_id": entry.correlation_id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "created_by": entry.created_by,
    }


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


class ConfigUpdate(BaseModel):
    config_value: dict[str, Any]
    reason: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

class PlanCreate(BaseModel):
    plan_code: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    price: float = Field(0, ge=0)
    currency: str = "GBP"
    billing_interval: str = "month"
    included_credits: int = Field(0, ge=0)
    included_storage_bytes: int = Field(0, ge=0)
    team_member_limit: Optional[int] = Field(None, ge=1)
    processing_limits: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, Any] = Field(default_factory=dict)
    billing_mode: Optional[str] = None
    assisted_processing_available: bool = False
    managed_processing_available: bool = False
    api_access: bool = False
    is_active: bool = True

    model_config = ConfigDict(extra="forbid")


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    billing_interval: Optional[str] = None
    included_credits: Optional[int] = Field(None, ge=0)
    included_storage_bytes: Optional[int] = Field(None, ge=0)
    team_member_limit: Optional[int] = Field(None, ge=1)
    processing_limits: Optional[dict[str, Any]] = None
    features: Optional[dict[str, Any]] = None
    billing_mode: Optional[str] = None
    assisted_processing_available: Optional[bool] = None
    managed_processing_available: Optional[bool] = None
    api_access: Optional[bool] = None
    is_active: Optional[bool] = None
    reason: Optional[str] = None

    model_config = ConfigDict(extra="forbid")



# ---------------------------------------------------------------------------
# Overview / config
# ---------------------------------------------------------------------------


@router.get("/overview")
async def commercial_overview(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Current commercial configuration + plan catalogue + default mode."""
    _require_billing_admin(context)
    configs = await repos.billing_config.list_current()
    plans = await repos.billing_plans.list_current()
    return {
        "config": {c.config_key: _config_out(c) for c in configs},
        "plans": [_plan_out(p) for p in plans],
        "default_billing_mode": await repos.billing_config.get_default_billing_mode(),
        "billing_modes": list(BILLING_MODES),
    }


@router.get("/config")
async def list_config(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Every current commercial rule key (versioned)."""
    _require_billing_admin(context)
    return {
        "config": {c.config_key: _config_out(c) for c in await repos.billing_config.list_current()}
    }


@router.get("/config/{config_key}")
async def get_config(
    config_key: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """One commercial rule key: current value + full version history."""
    _require_billing_admin(context)
    if config_key not in CONFIG_KEYS:
        raise HTTPException(status_code=404, detail=f"unknown config key: {config_key}")
    current = await repos.billing_config.get_current(config_key)
    if current is None:
        raise HTTPException(status_code=404, detail="config key not found")
    return {
        "config_key": config_key,
        "current": _config_out(current),
        "history": [_config_out(c) for c in await repos.billing_config.history(config_key)],
    }


@router.put("/config/{config_key}")
async def update_config(
    config_key: str,
    payload: ConfigUpdate,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Publish a NEW version of a commercial rule key (history preserved)."""
    _require_billing_admin(context)
    if config_key not in CONFIG_KEYS:
        raise HTTPException(status_code=404, detail=f"unknown config key: {config_key}")
    if config_key == "default_billing_mode":
        mode = payload.config_value.get("mode")
        if mode not in BILLING_MODES:
            raise HTTPException(
                status_code=422,
                detail=f"default_billing_mode.mode must be one of {list(BILLING_MODES)}",
            )
    current = await repos.billing_config.get_current(config_key)
    updated = await repos.billing_config.update_version(
        config_key=config_key,
        config_value=payload.config_value,
        reason=payload.reason,
        updated_by=context.profile.user_id,
    )
    await _audit(
        repos,
        entity_type="billing_commercial_config",
        entity_id=config_key,
        action="commercial_config.updated",
        actor=context.profile.user_id,
        before={"version": current.version if current else None},
        after={"version": updated.version},
        reason=payload.reason or f"updated {config_key}",
    )
    return {"config_key": config_key, "current": _config_out(updated)}


# ---------------------------------------------------------------------------
# Plans (versioned catalogue)
# ---------------------------------------------------------------------------


@router.get("/plans")
async def list_plans(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Current plans."""
    _require_billing_admin(context)
    return {"plans": [_plan_out(p) for p in await repos.billing_plans.list_current()]}


@router.get("/plans/{plan_code}")
async def get_plan(
    plan_code: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """One plan code: current version + full version history."""
    _require_billing_admin(context)
    current = await repos.billing_plans.get_current_by_code(plan_code)
    if current is None:
        raise HTTPException(status_code=404, detail="plan not found")
    return {
        "plan_code": plan_code,
        "current": _plan_out(current),
        "history": [_plan_out(p) for p in await repos.billing_plans.history(plan_code)],
    }


@router.post("/plans", status_code=201)
async def create_plan(
    payload: PlanCreate,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Create a brand-new plan (version 1)."""
    _require_billing_admin(context)
    if payload.billing_mode is not None and payload.billing_mode not in BILLING_MODES:
        raise HTTPException(status_code=422, detail=f"billing_mode must be one of {list(BILLING_MODES)}")
    existing = await repos.billing_plans.get_current_by_code(payload.plan_code)
    if existing is not None:
        raise HTTPException(status_code=409, detail="plan code already exists — use PUT to publish a new version")
    plan = BillingPlan(
        id=str(uuid.uuid4()),
        plan_code=payload.plan_code,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        currency=payload.currency,
        billing_interval=payload.billing_interval,
        included_credits=payload.included_credits,
        included_storage_bytes=payload.included_storage_bytes,
        team_member_limit=payload.team_member_limit,
        processing_limits=payload.processing_limits,
        features=payload.features,
        billing_mode=payload.billing_mode,
        assisted_processing_available=payload.assisted_processing_available,
        managed_processing_available=payload.managed_processing_available,
        api_access=payload.api_access,
        is_active=payload.is_active,
        version=1,
    )
    created = await repos.billing_plans.create(plan, created_by=context.profile.user_id)
    await _audit(
        repos,
        entity_type="billing_plan",
        entity_id=payload.plan_code,
        action="plan.created",
        actor=context.profile.user_id,
        after={"version": 1, "plan_code": payload.plan_code},
        reason="plan created",
    )
    return {"plan": _plan_out(created)}


@router.put("/plans/{plan_code}")
async def update_plan(
    plan_code: str,
    payload: PlanUpdate,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Publish a NEW version of a plan (history preserved; old terms intact)."""
    _require_billing_admin(context)
    current = await repos.billing_plans.get_current_by_code(plan_code)
    if current is None:
        raise HTTPException(status_code=404, detail="plan not found")
    fields = payload.model_dump(exclude_none=True)
    fields.pop("reason", None)
    if not fields:
        raise HTTPException(status_code=422, detail="no plan fields supplied")
    if "billing_mode" in fields and fields["billing_mode"] is not None and fields["billing_mode"] not in BILLING_MODES:
        raise HTTPException(status_code=422, detail=f"billing_mode must be one of {list(BILLING_MODES)}")
    updated = await repos.billing_plans.publish_new_version(
        plan_code=plan_code,
        fields=fields,
        reason=payload.reason,
        updated_by=context.profile.user_id,
    )
    await _audit(
        repos,
        entity_type="billing_plan",
        entity_id=plan_code,
        action="plan.version_published",
        actor=context.profile.user_id,
        before={"version": current.version},
        after={"version": updated.version},
        reason=payload.reason or "plan updated",
    )
    return {"plan": _plan_out(updated), "previous_version": current.version}


# ---------------------------------------------------------------------------
# Credit ledger (append-only read surface) + org billing modes
# ---------------------------------------------------------------------------


@router.get("/ledger")
async def get_ledger(
    organization_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Append-only credit ledger + derived balance for one organisation."""
    _require_billing_admin(context)
    org = await repos.organizations.get(organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")
    entries = await repos.billing_ledger.list_for_org(organization_id)
    return {
        "organization_id": organization_id,
        "balance": await repos.billing_ledger.balance(organization_id),
        "entries": [_ledger_out(e) for e in entries],
    }


@router.get("/organizations")
async def list_billing_organizations(
    billing_mode: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    """Organisations with their per-customer billing mode (filterable)."""
    _require_billing_admin(context)
    if billing_mode is not None and billing_mode not in BILLING_MODES:
        raise HTTPException(status_code=422, detail=f"billing_mode must be one of {list(BILLING_MODES)}")
    all_orgs = await repos.organizations.list_all()
    result = [
        {
            "id": o.id,
            "name": o.name,
            "country": o.country,
            "is_active": o.is_active,
            "billing_mode": (await repos.organizations.get_billing_mode(o.id)),
        }
        for o in all_orgs
    ]
    if billing_mode is not None:
        result = [r for r in result if r["billing_mode"] == billing_mode]
    return {"organizations": result}


# ---------------------------------------------------------------------------
# D37 — Admin billing operations (staff + can_manage_billing)
# ---------------------------------------------------------------------------


class SubscriptionActivate(BaseModel):
    organization_id: str
    plan_code: str
    billing_mode: Optional[str] = None
    lifecycle_status: str = "active"
    idempotency_key: str = Field(..., min_length=8, max_length=120)

    model_config = ConfigDict(extra="forbid")


class SubscriptionStatusChange(BaseModel):
    lifecycle_status: str = Field(..., pattern=r"^(pending|trial|active|past_due|suspended|cancelled|expired)$")

    model_config = ConfigDict(extra="forbid")


class CreditGrant(BaseModel):
    organization_id: str
    amount: int = Field(..., gt=0)
    source: str = "plan_included"
    reason: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=8, max_length=120)

    model_config = ConfigDict(extra="forbid")


class CreditAdjust(BaseModel):
    organization_id: str
    delta: int
    reason: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=8, max_length=120)

    model_config = ConfigDict(extra="forbid")


class CreditReverse(BaseModel):
    organization_id: str
    original_external_reference: str
    reason: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=8, max_length=120)

    model_config = ConfigDict(extra="forbid")


class CreditRefund(BaseModel):
    organization_id: str
    amount: int = Field(..., gt=0)
    reason: str = Field(..., min_length=1)
    idempotency_key: str = Field(..., min_length=8, max_length=120)

    model_config = ConfigDict(extra="forbid")


class CreditRollover(BaseModel):
    organization_id: str
    eligible_credits: int = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=8, max_length=120)

    model_config = ConfigDict(extra="forbid")


class OrderComplete(BaseModel):
    idempotency_key: Optional[str] = Field(None, max_length=120)

    model_config = ConfigDict(extra="forbid")


def _billing_svc(repos: RepositoryBundle) -> Any:
    from services.billing import BillingService

    return BillingService(repos)


@router.get("/subscriptions")
async def list_subscriptions(
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    subs = await repos.billing_subscriptions.list_all()
    return {"subscriptions": [_sub_out(s) for s in subs]}


@router.post("/subscriptions", status_code=201)
async def activate_subscription(
    payload: SubscriptionActivate,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    try:
        sub = await _billing_svc(repos).activate_subscription(
            payload.organization_id,
            plan_code=payload.plan_code,
            billing_mode=payload.billing_mode,
            lifecycle_status=payload.lifecycle_status,
            idempotency_key=payload.idempotency_key,
            actor=context.profile.user_id,
        )
    except Exception as exc:  # noqa: BLE001 — map billing failures
        raise HTTPException(status_code=getattr(exc, "status_code", 400), detail=str(exc))
    return {"subscription": _sub_out(sub)}


@router.post("/subscriptions/{subscription_id}/status")
async def change_subscription_status(
    subscription_id: str,
    payload: SubscriptionStatusChange,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    sub = await repos.billing_subscriptions.get(subscription_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="subscription not found")
    updated = await _billing_svc(repos).change_subscription_status(
        subscription_id, sub.organization_id, payload.lifecycle_status,
        actor=context.profile.user_id,
    )
    return {"subscription": _sub_out(updated) if updated else None}


@router.get("/orders")
async def list_orders(
    status: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    orders = await repos.billing_orders.list_all(status=status)
    return {"orders": [_admin_order_out(o) for o in orders]}


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    order = await repos.billing_orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return {"order": _admin_order_out(order)}


@router.post("/orders/{order_id}/complete")
async def complete_order(
    order_id: str,
    payload: OrderComplete,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    order = await repos.billing_orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    updated = await _billing_svc(repos).complete_order(
        order_id, order.organization_id, actor=context.profile.user_id
    )
    return {"order": _admin_order_out(updated)}


@router.get("/storage")
async def list_storage(
    organization_id: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    if organization_id:
        usage = await repos.billing_storage.latest_for_org(organization_id)
        return {"organizations": [{**_usage_out(usage), "organization_id": organization_id}] if usage else []}
    orgs = await repos.organizations.list_all()
    result = []
    for org in orgs:
        usage = await repos.billing_storage.latest_for_org(org.id)
        result.append({"organization_id": org.id, **_usage_out(usage)} if usage
                      else {"organization_id": org.id, "usage_bytes": 0})
    return {"organizations": result}


@router.get("/payments")
async def list_payments(
    organization_id: Optional[str] = None,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    records = await repos.billing_payments.list_all()
    if organization_id:
        records = [r for r in records if r.organization_id == organization_id]
    return {"records": [_payment_out(r) for r in records]}


@router.get("/entitlement/{organization_id}")
async def admin_entitlement(
    organization_id: str,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    try:
        return await _billing_svc(repos).get_entitlement(organization_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=getattr(exc, "status_code", 400), detail=str(exc))


@router.post("/credits/grant", status_code=201)
async def grant_credits(
    payload: CreditGrant,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    entry = await _billing_svc(repos).grant_credits(
        payload.organization_id, payload.amount,
        source=payload.source, reason=payload.reason,
        idempotency_key=payload.idempotency_key, actor=context.profile.user_id,
    )
    return {"entry": _ledger_out(entry)}


@router.post("/credits/adjust")
async def adjust_credits(
    payload: CreditAdjust,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    entry = await _billing_svc(repos).adjust_credits(
        payload.organization_id, payload.delta,
        reason=payload.reason, idempotency_key=payload.idempotency_key,
        actor=context.profile.user_id,
    )
    return {"entry": _ledger_out(entry)}


@router.post("/credits/reverse")
async def reverse_credits(
    payload: CreditReverse,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    entry = await _billing_svc(repos).reverse_credits(
        payload.organization_id,
        original_external_reference=payload.original_external_reference,
        reason=payload.reason, idempotency_key=payload.idempotency_key,
        actor=context.profile.user_id,
    )
    return {"entry": _ledger_out(entry)}


@router.post("/credits/refund")
async def refund_credits(
    payload: CreditRefund,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    entry = await _billing_svc(repos).refund_credits(
        payload.organization_id, payload.amount,
        reason=payload.reason, idempotency_key=payload.idempotency_key,
        actor=context.profile.user_id,
    )
    return {"entry": _ledger_out(entry)}


@router.post("/credits/rollover")
async def rollover_credits(
    payload: CreditRollover,
    context: StaffContext = Depends(require_staff),
    repos: RepositoryBundle = Depends(get_repositories),
) -> dict:
    _require_billing_admin(context)
    entry = await _billing_svc(repos).rollover(
        payload.organization_id,
        idempotency_key=payload.idempotency_key,
        eligible_credits=payload.eligible_credits,
        actor=context.profile.user_id,
    )
    return {"entry": _ledger_out(entry)}


def _sub_out(sub) -> dict:
    return {
        "id": sub.id,
        "organization_id": sub.organization_id,
        "plan_code": sub.plan_code,
        "plan_version": sub.plan_version,
        "billing_mode": sub.billing_mode,
        "lifecycle_status": sub.lifecycle_status,
        "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
    }


def _admin_order_out(order) -> dict:
    return {
        "id": order.id,
        "organization_id": order.organization_id,
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


def _usage_out(usage) -> dict:
    return {
        "usage_bytes": usage.usage_bytes,
        "included_bytes": usage.included_bytes,
        "additional_bytes": usage.additional_bytes,
        "measured_at": usage.measured_at.isoformat() if usage.measured_at else None,
    }


def _payment_out(record) -> dict:
    return {
        "id": record.id,
        "organization_id": record.organization_id,
        "provider": record.provider,
        "payment_method_type": record.payment_method_type,
        "provider_transaction_ref": record.provider_transaction_ref,
        "amount": record.amount,
        "currency": record.currency,
        "status": record.status,
        "order_id": record.order_id,
        "recorded_at": record.recorded_at.isoformat() if record.recorded_at else None,
    }


def _ledger_out(entry) -> dict:
    return {
        "id": entry.id,
        "organization_id": entry.organization_id,
        "entry_type": entry.entry_type,
        "credit_delta": entry.credit_delta,
        "source": entry.source,
        "reason": entry.reason,
        "plan_code": entry.plan_code,
        "plan_version": entry.plan_version,
        "order_id": entry.order_id,
        "external_reference": entry.external_reference,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }

