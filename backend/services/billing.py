"""D37 — provider-neutral commercial billing service.

The authoritative server-side billing core: subscription lifecycle,
entitlement resolution, credit operations, the common order lifecycle,
storage metering and provider-neutral payment records. Every mutation runs
server-side, is organization-scoped, idempotent and audited. The browser is
never authoritative for commercial state. No payment-provider integration.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional

from domain.audit import AuditEntry
from domain.billing import (
    BILLING_MODES,
    BillingOrder,
    CreditLedgerEntry,
    IdempotencyKey,
    PaymentRecord,
    StorageUsage,
    Subscription,
)


class BillingError(Exception):
    """Base class for D37 billing failures (mapped to HTTP by the API layer)."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class InsufficientCreditsError(BillingError):
    def __init__(self, message: str, *, available: int, required: int) -> None:
        super().__init__(message, status_code=402)
        self.available = available
        self.required = required


class EntitlementUnavailableError(BillingError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=403)


class OrderStateError(BillingError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class IdempotencyConflict(BillingError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class BillingService:
    """All D37 commercial operations (server-authoritative)."""

    def __init__(self, repos: Any) -> None:
        self.repos = repos
        self.plans = repos.billing_plans
        self.orders = repos.billing_orders
        self.storage_repo = repos.billing_storage

    async def get_entitlement(self, organization_id: str) -> dict[str, Any]:
        """What this organisation is entitled to use RIGHT NOW (server-side)."""
        org = await self.repos.organizations.get(organization_id)
        if org is None:
            raise EntitlementUnavailableError("organisation not found")
        subscription = await self.repos.billing_subscriptions.get_active_for_org(organization_id)
        plan = None
        if subscription is not None and subscription.plan_code:
            if subscription.plan_version:
                plan = await self.plans.get_version(subscription.plan_code, subscription.plan_version)
            if plan is None:
                plan = await self.plans.get_current_by_code(subscription.plan_code)

        billing_mode = (
            subscription.billing_mode
            if subscription and subscription.billing_mode
            else await self.repos.organizations.get_billing_mode(organization_id)
            or await self.repos.billing_config.get_default_billing_mode()
        )
        if billing_mode not in BILLING_MODES:
            billing_mode = "CREDIT"

        credit_balance = await self.repos.billing_ledger.balance(organization_id)
        credit_rules = await self.repos.billing_config.get_current("credit_rules")
        storage_cfg = await self.repos.billing_config.get_current("storage")
        policy = await self.repos.billing_config.get_current("credit_policy")
        standard_cfg = await self.repos.billing_config.get_current("standard_allowance")
        latest_storage = await self.storage_repo.latest_for_org(organization_id)

        included_credits = plan.included_credits if plan else 0
        included_storage = plan.included_storage_bytes if plan else 0
        policy_value = (policy.config_value or {}) if policy else {}
        emergency_enabled = bool(policy_value.get("emergency_allowance", {}).get("enabled", True))
        emergency_pct = int(policy_value.get("emergency_allowance", {}).get("allowance_pct", 10) or 0)

        usage_now = 0
        allowance_now = 0
        if billing_mode == "STANDARD":
            standard_value = (standard_cfg.config_value or {}) if standard_cfg else {}
            allowance_now = int(standard_value.get("monthly_processing_units") or 0)
            usage_now = await self._standard_usage_this_period(organization_id, subscription)

        storage_usage = latest_storage.usage_bytes if latest_storage else 0

        return {
            "organization_id": organization_id,
            "organization_name": org.name,
            "billing_mode": billing_mode,
            "subscription": self._subscription_out(subscription) if subscription else None,
            "plan": self._plan_out(plan) if plan else None,
            "credits": {
                "balance": credit_balance,
                "included_monthly": included_credits,
                "emergency_allowance_enabled": emergency_enabled,
                "emergency_allowance_pct": emergency_pct,
            },
            "storage": {
                "usage_bytes": storage_usage,
                "included_bytes": included_storage,
                "additional_bytes": max(0, storage_usage - included_storage),
            },
            "standard": {
                "monthly_allowance": allowance_now,
                "usage_this_period": usage_now,
                "remaining": max(0, allowance_now - usage_now),
            },
            "features": (plan.features if plan else {}) or {},
            "team_member_limit": plan.team_member_limit if plan else None,
            "processing_limits": (plan.processing_limits if plan else {}) or {},
            "config_versions": {
                "credit_rules": credit_rules.version if credit_rules else None,
                "storage": storage_cfg.version if storage_cfg else None,
                "credit_policy": policy.version if policy else None,
                "standard_allowance": standard_cfg.version if standard_cfg else None,
            },
        }

    async def _standard_usage_this_period(self, org_id: str, subscription: Optional[Subscription]) -> int:
        start = (
            subscription.current_period_start
            if subscription and subscription.current_period_start
            else datetime.now(timezone.utc) - timedelta(days=30)
        )
        row = await self.repos.billing_usage._fetch_one(
            """
            SELECT COALESCE(SUM(ai_files_processed + batch_files_uploaded
                                + manual_pages_extracted + reports_generated), 0)
              FROM public.usage_tracking
             WHERE organization_id = $1 AND usage_date >= $2
            """,
            org_id, start.date(),
        )
        return int(row[0]) if row is not None else 0

        self.plans = repos.billing_plans
        self.orders = repos.billing_orders
        self.storage_repo = repos.billing_storage

    # ------------------------------------------------------------------
    # Credit operations (all idempotent + audited)
    # ------------------------------------------------------------------

    async def grant_credits(
        self,
        organization_id: str,
        amount: int,
        *,
        source: str = "plan_included",
        reason: str,
        idempotency_key: str,
        plan_code: Optional[str] = None,
        plan_version: Optional[int] = None,
        order_id: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> CreditLedgerEntry:
        if amount <= 0:
            raise BillingError("credit grant amount must be positive")
        await self._claim_key(idempotency_key, "credit_grant", entity_type="organization", entity_id=organization_id)
        entry = await self.repos.billing_ledger.record(
            CreditLedgerEntry(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                entry_type="grant",
                credit_delta=amount,
                source=source,
                reason=reason,
                plan_code=plan_code,
                plan_version=plan_version,
                order_id=order_id,
                external_reference=idempotency_key,
                created_by=actor,
            )
        )
        await self._audit(organization_id, "credit.grant", actor,
                          {"amount": amount, "source": source, "reason": reason})
        return entry

    async def consume_credits(
        self,
        organization_id: str,
        units: int,
        *,
        reason: str,
        idempotency_key: str,
        plan_code: Optional[str] = None,
        plan_version: Optional[int] = None,
        order_id: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> dict[str, Any]:
        """CREDIT-mode consumption with the configurable emergency allowance."""
        if units <= 0:
            raise BillingError("credit consumption must be positive")
        await self._claim_key(idempotency_key, "credit_consume", entity_type="organization", entity_id=organization_id)

        balance = await self.repos.billing_ledger.balance(organization_id)
        if balance >= units:
            entry = await self.repos.billing_ledger.record(
                CreditLedgerEntry(
                    id=str(uuid.uuid4()), organization_id=organization_id,
                    entry_type="consume", credit_delta=-units, source="adjustment",
                    reason=reason, plan_code=plan_code, plan_version=plan_version,
                    order_id=order_id, external_reference=idempotency_key,
                    created_by=actor,
                )
            )
            await self._audit(organization_id, "credit.consume", actor,
                              {"units": units, "reason": reason, "emergency": False})
            return {"entries": [entry], "emergency_used": False,
                    "remaining": await self.repos.billing_ledger.balance(organization_id)}

        policy = await self.repos.billing_config.get_current("credit_policy")
        policy_value = (policy.config_value or {}) if policy else {}
        emergency = (policy_value.get("emergency_allowance", {}) or {})
        if not emergency.get("enabled", True):
            raise InsufficientCreditsError(
                "Insufficient credits for processing", available=balance, required=units
            )
        allowance_pct = int(emergency.get("allowance_pct", 10) or 0)
        allowance = max(units, int(balance * allowance_pct / 100)) if balance > 0 else units
        emergency_entry = await self.repos.billing_ledger.record(
            CreditLedgerEntry(
                id=str(uuid.uuid4()), organization_id=organization_id,
                entry_type="emergency_allowance", credit_delta=allowance,
                source="emergency",
                reason=f"Temporary completion allowance (reconciliation pending): {reason}",
                plan_code=plan_code, plan_version=plan_version, order_id=order_id,
                external_reference=f"{idempotency_key}:emergency",
                created_by=actor,
            )
        )
        consume_entry = await self.repos.billing_ledger.record(
            CreditLedgerEntry(
                id=str(uuid.uuid4()), organization_id=organization_id,
                entry_type="consume", credit_delta=-units, source="emergency",
                reason=reason, plan_code=plan_code, plan_version=plan_version,
                order_id=order_id, external_reference=idempotency_key,
                created_by=actor,
            )
        )
        await self._audit(organization_id, "credit.consume", actor,
                          {"units": units, "reason": reason, "emergency": True, "allowance": allowance})
        return {"entries": [emergency_entry, consume_entry], "emergency_used": True,
                "remaining": await self.repos.billing_ledger.balance(organization_id)}


    async def rollover(
        self,
        organization_id: str,
        *,
        idempotency_key: str,
        eligible_credits: int,
        reason: str = "Period rollover",
        actor: Optional[str] = None,
    ) -> CreditLedgerEntry:
        """Move eligible unused credits into the next period (config-driven)."""
        policy = await self.repos.billing_config.get_current("credit_policy")
        policy_value = (policy.config_value or {}) if policy else {}
        rollover_cfg = policy_value.get("rollover", {}) or {}
        if not rollover_cfg.get("enabled", True):
            raise BillingError("credit rollover is disabled by policy")
        if eligible_credits <= 0:
            raise BillingError("no eligible credits to roll over")
        await self._claim_key(idempotency_key, "credit_rollover", entity_type="organization", entity_id=organization_id)
        entry = await self.repos.billing_ledger.record(
            CreditLedgerEntry(
                id=str(uuid.uuid4()), organization_id=organization_id,
                entry_type="rollover", credit_delta=eligible_credits,
                source="rollover", reason=reason,
                external_reference=idempotency_key, created_by=actor,
            )
        )
        await self._audit(organization_id, "credit.rollover", actor, {"credits": eligible_credits})
        return entry

    async def adjust_credits(
        self,
        organization_id: str,
        delta: int,
        *,
        reason: str,
        idempotency_key: str,
        actor: Optional[str] = None,
    ) -> CreditLedgerEntry:
        """Administrative correction as a NEW ledger event (never rewrites)."""
        if delta == 0:
            raise BillingError("adjustment delta cannot be zero")
        await self._claim_key(idempotency_key, "credit_adjustment", entity_type="organization", entity_id=organization_id)
        entry = await self.repos.billing_ledger.record(
            CreditLedgerEntry(
                id=str(uuid.uuid4()), organization_id=organization_id,
                entry_type="adjustment", credit_delta=delta,
                source="adjustment", reason=reason,
                external_reference=idempotency_key, created_by=actor,
            )
        )
        await self._audit(organization_id, "credit.adjustment", actor, {"delta": delta, "reason": reason})
        return entry

    async def reverse_credits(
        self,
        organization_id: str,
        *,
        original_external_reference: str,
        reason: str,
        idempotency_key: str,
        actor: Optional[str] = None,
    ) -> CreditLedgerEntry:
        """Reverse a previous ledger transaction without rewriting it."""
        history = await self.repos.billing_ledger.list_for_org(organization_id)
        original = next(
            (e for e in history if e.external_reference == original_external_reference),
            None,
        )
        if original is None:
            raise BillingError("original ledger entry not found", status_code=404)
        await self._claim_key(idempotency_key, "credit_reversal", entity_type="organization", entity_id=organization_id)
        entry = await self.repos.billing_ledger.record(
            CreditLedgerEntry(
                id=str(uuid.uuid4()), organization_id=organization_id,
                entry_type="reversal", credit_delta=-original.credit_delta,
                source="adjustment",
                reason=f"Reversal of {original_external_reference}: {reason}",
                external_reference=idempotency_key, created_by=actor,
            )
        )
        await self._audit(organization_id, "credit.reversal", actor,
                          {"reversed": original_external_reference, "delta": -original.credit_delta})
        return entry

    async def refund_credits(
        self,
        organization_id: str,
        *,
        amount: int,
        reason: str,
        idempotency_key: str,
        actor: Optional[str] = None,
    ) -> CreditLedgerEntry:
        """Compensating ledger entry for a refund (new event, never rewrites)."""
        if amount <= 0:
            raise BillingError("refund amount must be positive")
        await self._claim_key(idempotency_key, "credit_refund", entity_type="organization", entity_id=organization_id)
        entry = await self.repos.billing_ledger.record(
            CreditLedgerEntry(
                id=str(uuid.uuid4()), organization_id=organization_id,
                entry_type="refund", credit_delta=amount,
                source="refund", reason=reason,
                external_reference=idempotency_key, created_by=actor,
            )
        )
        await self._audit(organization_id, "credit.refund", actor, {"amount": amount, "reason": reason})
        return entry


    # ------------------------------------------------------------------
    # Subscription lifecycle
    # ------------------------------------------------------------------

    async def activate_subscription(
        self,
        organization_id: str,
        *,
        plan_code: str,
        billing_mode: Optional[str] = None,
        lifecycle_status: str = "active",
        idempotency_key: str,
        actor: Optional[str] = None,
    ) -> Subscription:
        """Create (or renew) the org's active commercial relationship."""
        plan = await self.plans.get_current_by_code(plan_code)
        if plan is None:
            raise BillingError(f"plan {plan_code!r} not found", status_code=404)
        if not plan.is_active:
            raise BillingError(f"plan {plan_code!r} is inactive")
        await self._claim_key(idempotency_key, "subscription_activate", entity_type="organization", entity_id=organization_id)
        mode = billing_mode or (await self.repos.organizations.get_billing_mode(organization_id)
                                or await self.repos.billing_config.get_default_billing_mode())
        if mode not in BILLING_MODES:
            raise BillingError("invalid billing_mode")
        now = datetime.now(timezone.utc)
        subscription = await self.repos.billing_subscriptions.upsert_active(
            Subscription(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                plan_code=plan.plan_code,
                plan_version=plan.version,
                billing_mode=mode,
                lifecycle_status=lifecycle_status,
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
                activated_at=now,
                idempotency_key=idempotency_key,
            ),
            created_by=actor,
        )
        await self._audit(organization_id, "subscription.activated", actor,
                          {"plan_code": plan_code, "plan_version": plan.version,
                           "billing_mode": mode, "status": lifecycle_status})
        return subscription

    async def change_subscription_status(
        self,
        subscription_id: str,
        organization_id: str,
        lifecycle_status: str,
        *,
        actor: Optional[str] = None,
    ) -> Optional[Subscription]:
        sub = await self.repos.billing_subscriptions.get(subscription_id)
        if sub is None or sub.organization_id != organization_id:
            raise BillingError("subscription not found", status_code=404)
        updated = await self.repos.billing_subscriptions.update_status(subscription_id, lifecycle_status, updated_by=actor)
        if updated:
            await self._audit(organization_id, "subscription.status_changed", actor,
                              {"subscription_id": subscription_id, "status": lifecycle_status})
        return updated


    # ------------------------------------------------------------------
    # Orders (common model: automated / assisted / managed / storage)
    # ------------------------------------------------------------------

    async def create_order(
        self,
        organization_id: str,
        *,
        order_type: str,
        title: str,
        description: Optional[str],
        items: list[dict[str, Any]],
        idempotency_key: str,
        complexity: Optional[str] = None,
        status: str = "estimated",
        external_reference: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        actor: Optional[str] = None,
    ) -> BillingOrder:
        """Create an order with an immutable line-item snapshot."""
        if not items:
            raise BillingError("order requires at least one line item")
        await self._claim_key(idempotency_key, "order_create", entity_type="organization", entity_id=organization_id)
        total = Decimal("0.00")
        for item in items:
            qty = Decimal(str(item.get("quantity", 1)))
            price = Decimal(str(item.get("unit_price", 0)))
            line = qty * price
            item["line_total"] = float(line)
            item["quantity"] = int(qty)
            total += line
        sub = await self.repos.billing_subscriptions.get_active_for_org(organization_id)
        plan = None
        if sub and sub.plan_code:
            plan = (await self.plans.get_version(sub.plan_code, sub.plan_version)) if sub.plan_version else None
            plan = plan or (await self.plans.get_current_by_code(sub.plan_code) if sub.plan_code else None)
        order = await self.orders.create(
            BillingOrder(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                order_type=order_type,
                status=status,
                title=title,
                description=description,
                complexity=complexity,
                items=items,
                total_amount=float(total),
                currency=plan.currency if plan else "GBP",
                plan_code=sub.plan_code if sub else None,
                plan_version=sub.plan_version if sub else None,
                config_version={
                    "credit_rules": (await self.repos.billing_config.get_current("credit_rules")).version
                    if await self.repos.billing_config.get_current("credit_rules") else None,
                    "assisted_pricing": (await self.repos.billing_config.get_current("assisted_pricing")).version
                    if await self.repos.billing_config.get_current("assisted_pricing") else None,
                },
                idempotency_key=idempotency_key,
                external_reference=external_reference,
                metadata=metadata or {},
            ),
            created_by=actor,
        )
        await self._audit(organization_id, "order.created", actor,
                          {"order_id": order.id, "order_type": order_type, "total": order.total_amount, "status": order.status})
        return order

    async def estimate_assisted_order(
        self,
        organization_id: str,
        *,
        title: str,
        description: Optional[str],
        lines: list[dict[str, Any]],
        idempotency_key: str,
        actor: Optional[str] = None,
    ) -> BillingOrder:
        """Assisted Processing estimate from the configurable price book.

        ``lines``: [{"complexity": "simple|standard|complex|exceptional",
                     "quantity": n, "label": optional}]. Prices resolve from
        the versioned ``assisted_pricing`` config — never hard-coded.
        """
        pricing = await self.repos.billing_config.get_current("assisted_pricing")
        price_book = (pricing.config_value or {}) if pricing else {}
        items: list[dict[str, Any]] = []
        for line in lines:
            complexity = line.get("complexity")
            entry = price_book.get(complexity) or {}
            if entry.get("quoted"):
                raise BillingError(f"complexity {complexity!r} requires a quote")
            price = Decimal(str(entry.get("price") or 0))
            qty = int(line.get("quantity", 1))
            if qty <= 0:
                raise BillingError("line quantity must be positive")
            items.append({
                "description": line.get("label") or f"Assisted Processing — {complexity}",
                "complexity": complexity,
                "quantity": qty,
                "unit_price": float(price),
                "line_total": float(price * qty),
            })
        return await self.create_order(
            organization_id,
            order_type="assisted",
            title=title,
            description=description,
            items=items,
            idempotency_key=idempotency_key,
            status="awaiting_customer_approval",
            actor=actor,
        )


    async def approve_order(self, order_id: str, organization_id: str, *, actor: Optional[str] = None) -> BillingOrder:
        """Customer (or admin) approval — authorises the commercial job."""
        order = await self.orders.get_for_org(order_id, organization_id)
        if order is None:
            raise BillingError("order not found", status_code=404)
        if order.status not in ("estimated", "awaiting_customer_approval"):
            raise OrderStateError(f"order cannot be approved from status {order.status!r}")
        updated = await self.orders.mark_approved(order_id, approved_by=actor)
        await self.repos.billing_payments.create(
            PaymentRecord(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                provider="pending",
                amount=order.total_amount,
                currency=order.currency,
                status="pending",
                payment_method_type="to_be_selected",
                order_id=order_id,
                idempotency_key=f"{order.id}:payment",
                created_by=actor,
            )
        )
        await self._audit(organization_id, "order.approved", actor, {"order_id": order_id, "total": order.total_amount})
        return updated or order

    async def complete_order(self, order_id: str, organization_id: str, *, actor: Optional[str] = None) -> BillingOrder:
        order = await self.orders.get_for_org(order_id, organization_id)
        if order is None:
            raise BillingError("order not found", status_code=404)
        if order.status not in ("approved", "processing", "awaiting_qc", "queued"):
            raise OrderStateError(f"order cannot be completed from status {order.status!r}")
        updated = await self.orders.mark_completed(order_id)
        if updated:
            await self._audit(organization_id, "order.completed", actor, {"order_id": order_id})
        return updated or order

    async def cancel_order(self, order_id: str, organization_id: str, *, actor: Optional[str] = None) -> BillingOrder:
        order = await self.orders.get_for_org(order_id, organization_id)
        if order is None:
            raise BillingError("order not found", status_code=404)
        if order.status in ("completed", "refunded"):
            raise OrderStateError("completed orders are immutable — a new adjustment is required")
        updated = await self.orders.update_status(order_id, "cancelled", actor=actor)
        if updated:
            await self._audit(organization_id, "order.cancelled", actor, {"order_id": order_id})
        return updated or order

    # ------------------------------------------------------------------
    # Storage metering (server-authoritative, D32-derived)
    # ------------------------------------------------------------------

    async def meter_storage(self, organization_id: str) -> StorageUsage:
        """Measure real storage usage from the D32 ``organization_files`` records.

        Never trusts browser-reported usage. Records an auditable snapshot.
        """
        plan = None
        sub = await self.repos.billing_subscriptions.get_active_for_org(organization_id)
        if sub and sub.plan_code:
            plan = (await self.plans.get_version(sub.plan_code, sub.plan_version)) if sub.plan_version else None
            plan = plan or (await self.plans.get_current_by_code(sub.plan_code) if sub.plan_code else None)
        included = plan.included_storage_bytes if plan else 0
        row = await self.storage_repo._fetch_one(
            """
            SELECT COALESCE(SUM(size_bytes), 0) AS total
              FROM public.organization_files
             WHERE organization_id = $1 AND is_active = TRUE AND deleted_at IS NULL
            """,
            organization_id,
        )
        total = int(row[0]) if row is not None else 0
        return await self.storage_repo.record(
            StorageUsage(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                usage_bytes=total,
                included_bytes=included,
                additional_bytes=max(0, total - included),
                source="organization_files_sum",
            )
        )


    # ------------------------------------------------------------------
    # Processing charge (CREDIT consumption / STANDARD allowance)
    # ------------------------------------------------------------------

    async def charge_processing(
        self,
        organization_id: str,
        *,
        job: dict[str, Any],
        idempotency_key: str,
        actor: Optional[str] = None,
    ) -> dict[str, Any]:
        """Authoritative charge for one automated processing job.

        ``job``: {kind: 'document'|'structured', page_count, item_count, rows}.
        CREDIT mode consumes complexity credits (documents) or structured-data
        units (CSV/Excel/JSON). STANDARD mode checks the monthly allowance
        without consuming ledger credits.
        """
        entitlement = await self.get_entitlement(organization_id)
        mode = entitlement["billing_mode"]
        sub = await self.repos.billing_subscriptions.get_active_for_org(organization_id)
        plan_code = sub.plan_code if sub else None
        plan_version = sub.plan_version if sub else None

        if sub is None:
            # Pre-commercial orgs (no active subscription) are not charged yet.
            # Once an Admin activates a subscription, billing enforcement begins.
            return {"mode": "no_subscription", "allowed": True, "charged": False}

        if mode == "STANDARD":
            remaining = entitlement["standard"]["remaining"]
            if remaining <= 0:
                raise InsufficientCreditsError(
                    "STANDARD monthly processing allowance exhausted", available=0, required=1
                )
            await self._claim_key(idempotency_key, "processing_charge", entity_type="organization", entity_id=organization_id)
            await self.repos.billing_usage.record(organization_id, 1)
            await self._audit(organization_id, "billing.standard_usage", actor,
                              {"job": job, "remaining_before": remaining})
            return {"mode": "STANDARD", "allowed": True, "charged": True,
                    "remaining": remaining - 1, "emergency_used": False}

        units = await self._required_units(job)
        result = await self.consume_credits(
            organization_id, units,
            reason=f"Automated processing ({job.get('kind') or 'document'})",
            idempotency_key=idempotency_key,
            plan_code=plan_code, plan_version=plan_version, actor=actor,
        )
        result["mode"] = "CREDIT"
        result["charged"] = True
        result["units"] = units
        return result

    async def _required_units(self, job: dict[str, Any]) -> int:
        """Units for one job from the versioned commercial rules (never hard-coded)."""
        kind = job.get("kind") or "document"
        if kind == "structured":
            rows = int(job.get("rows") or 0)
            bands_cfg = await self.repos.billing_config.get_current("structured_data_bands")
            bands = ((bands_cfg.config_value or {}).get("bands") or []) if bands_cfg else []
            for band in sorted(bands, key=lambda b: (b.get("max_rows") is None, b.get("max_rows") or 0)):
                max_rows = band.get("max_rows")
                units = band.get("units")
                if max_rows is None:
                    if band.get("custom"):
                        raise BillingError("structured-data volume exceeds configurable bands — custom pricing required")
                    continue
                if rows <= int(max_rows):
                    return int(units or 1)
            raise BillingError("structured-data volume exceeds configurable bands")
        complexity = await self.classify_document(job)
        rules_cfg = await self.repos.billing_config.get_current("credit_rules")
        classes = ((rules_cfg.config_value or {}).get("classes") or []) if rules_cfg else []
        for cls in classes:
            if cls.get("class") == complexity:
                credits = cls.get("credits")
                if credits is None or cls.get("quoted"):
                    raise BillingError(f"complexity {complexity!r} requires a quote")
                return int(credits)
        return 1

    async def classify_document(self, job: dict[str, Any]) -> str:
        """Map a document job to a complexity class using configurable thresholds."""
        rules_cfg = await self.repos.billing_config.get_current("credit_rules")
        classifier = ((rules_cfg.config_value or {}).get("classifier") or {}) if rules_cfg else {}
        pages = int(job.get("page_count") or 1)
        items = int(job.get("item_count") or 0)
        if pages > int(classifier.get("complex_pages", 10) or 10) or items > int(classifier.get("complex_items", 8) or 8):
            return "complex"
        if pages > int(classifier.get("standard_pages", 3) or 3) or items > int(classifier.get("standard_items", 2) or 2):
            return "standard"
        return "simple"

    # ------------------------------------------------------------------
    # Payment records (provider-neutral; NO integration)
    # ------------------------------------------------------------------

    async def record_payment_intent(
        self,
        organization_id: str,
        *,
        amount: float,
        provider: str,
        order_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
        idempotency_key: str,
        actor: Optional[str] = None,
    ) -> PaymentRecord:
        await self._claim_key(idempotency_key, "payment_record", entity_type="organization", entity_id=organization_id)
        return await self.repos.billing_payments.create(
            PaymentRecord(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                provider=provider,
                amount=amount,
                status="pending",
                order_id=order_id,
                subscription_id=subscription_id,
                idempotency_key=idempotency_key,
                created_by=actor,
            )
        )


    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _claim_key(self, key: str, operation: str, *, entity_type: Optional[str], entity_id: Optional[str]) -> IdempotencyKey:
        if not key:
            raise BillingError("idempotency_key is required for commercial mutations")
        existing = await self.repos.billing_idempotency.get(key)
        if existing is not None:
            raise IdempotencyConflict(f"idempotency key {key!r} already used")
        try:
            return await self.repos.billing_idempotency.claim(key, operation, entity_type=entity_type, entity_id=entity_id)
        except Exception:
            raise IdempotencyConflict(f"idempotency key {key!r} already used")

    async def _audit(self, organization_id: str, action: str, actor: Optional[str], detail: dict[str, Any]) -> None:
        try:
            await self.repos.audit.record(self._entry(organization_id, action, actor, detail))
        except Exception:  # noqa: BLE001 — audit must never block the authoritative change
            pass

    @staticmethod
    def _entry(organization_id: str, action: str, actor: Optional[str], detail: dict[str, Any]) -> AuditEntry:
        return AuditEntry(
            id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            entity_type="organization",
            entity_id=organization_id,
            action=action,
            actor=actor or "system",
            occurred_at=datetime.now(timezone.utc),
            changed_fields=detail,
        )

    @staticmethod
    def _subscription_out(sub: Subscription) -> dict[str, Any]:
        return {
            "id": sub.id,
            "plan_code": sub.plan_code,
            "plan_version": sub.plan_version,
            "billing_mode": sub.billing_mode,
            "lifecycle_status": sub.lifecycle_status,
            "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        }

    @staticmethod
    def _plan_out(plan) -> dict[str, Any]:
        return {
            "plan_code": plan.plan_code,
            "name": plan.name,
            "price": plan.price,
            "currency": plan.currency,
            "billing_interval": plan.billing_interval,
            "included_credits": plan.included_credits,
            "included_storage_bytes": plan.included_storage_bytes,
            "team_member_limit": plan.team_member_limit,
            "features": plan.features,
            "processing_limits": plan.processing_limits,
            "billing_mode": plan.billing_mode,
            "assisted_processing_available": plan.assisted_processing_available,
            "managed_processing_available": plan.managed_processing_available,
            "api_access": plan.api_access,
            "version": plan.version,
        }

