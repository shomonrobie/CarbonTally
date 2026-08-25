"""D37-0 — provider-neutral billing repositories.

Service-role persistence over the D37-0 billing foundation tables. Every write
is server-authoritative (the service pool); there are NO authenticated RLS
write paths. The credit ledger is append-only.
"""
from __future__ import annotations

from typing import Any, Optional

from data.base import AbstractRepository, dumps_jsonb, loads_jsonb
from domain.billing import (
    BillingOrder,
    BillingPlan,
    CommercialConfig,
    CreditLedgerEntry,
    IdempotencyKey,
    PaymentRecord,
    StorageUsage,
    Subscription,
)

_PLAN_COLUMNS = (
    "id, plan_code, name, description, price, currency, billing_interval, "
    "included_credits, included_storage_bytes, team_member_limit, "
    "processing_limits, features, billing_mode, assisted_processing_available, "
    "managed_processing_available, api_access, is_active, version, "
    "version_label, effective_from, effective_to, created_at"
)

_CONFIG_COLUMNS = (
    "id, config_key, config_value, version, reason, effective_from, "
    "effective_to, created_by, created_at"
)

_LEDGER_COLUMNS = (
    "id, organization_id, entry_type, credit_delta, source, reason, "
    "plan_code, plan_version, subscription_id, external_reference, "
    "correlation_id, created_at, created_by"
)


def _row_to_plan(row: Any) -> BillingPlan:
    r = dict(row)
    return BillingPlan(
        id=str(r["id"]),
        plan_code=str(r["plan_code"]),
        name=str(r["name"]),
        description=r.get("description"),
        price=float(r.get("price") or 0),
        currency=str(r.get("currency") or "GBP"),
        billing_interval=str(r.get("billing_interval") or "month"),
        included_credits=int(r.get("included_credits") or 0),
        included_storage_bytes=int(r.get("included_storage_bytes") or 0),
        team_member_limit=r.get("team_member_limit"),
        processing_limits=loads_jsonb(r.get("processing_limits")) or {},
        features=loads_jsonb(r.get("features")) or {},
        billing_mode=r.get("billing_mode"),
        assisted_processing_available=bool(r.get("assisted_processing_available")),
        managed_processing_available=bool(r.get("managed_processing_available")),
        api_access=bool(r.get("api_access")),
        is_active=bool(r.get("is_active")),
        version=int(r.get("version") or 1),
        version_label=r.get("version_label"),
        effective_from=r.get("effective_from"),
        effective_to=r.get("effective_to"),
        created_at=r.get("created_at"),
    )


def _row_to_config(row: Any) -> CommercialConfig:
    r = dict(row)
    return CommercialConfig(
        id=str(r["id"]),
        config_key=str(r["config_key"]),
        config_value=loads_jsonb(r.get("config_value")) or {},
        version=int(r.get("version") or 1),
        reason=r.get("reason"),
        effective_from=r.get("effective_from"),
        effective_to=r.get("effective_to"),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
    )


def _row_to_ledger(row: Any) -> CreditLedgerEntry:
    r = dict(row)
    return CreditLedgerEntry(
        id=str(r["id"]),
        organization_id=str(r["organization_id"]),
        entry_type=str(r["entry_type"]),
        credit_delta=int(r["credit_delta"]),
        source=str(r["source"]),
        reason=r.get("reason"),
        plan_code=r.get("plan_code"),
        plan_version=r.get("plan_version"),
        subscription_id=str(r["subscription_id"]) if r.get("subscription_id") else None,
        external_reference=r.get("external_reference"),
        correlation_id=r.get("correlation_id"),
        created_at=r.get("created_at"),
        created_by=str(r["created_by"]) if r.get("created_by") else None,
    )


class BillingPlansRepository(AbstractRepository[BillingPlan]):
    """Versioned plan catalogue persistence."""

    async def get(self, id: str) -> Optional[BillingPlan]:
        row = await self._fetch_one(
            f"SELECT {_PLAN_COLUMNS} FROM public.billing_plans WHERE id = $1", id
        )
        return _row_to_plan(row) if row is not None else None

    async def list_current(self, *, active_only: bool = False) -> list[BillingPlan]:
        """The CURRENT version of every plan code (effective_to IS NULL)."""
        rows = await self._fetch_all(
            f"SELECT {_PLAN_COLUMNS} FROM public.billing_plans "
            "WHERE effective_to IS NULL ORDER BY plan_code, version",
        )
        plans = [_row_to_plan(r) for r in rows]
        if active_only:
            plans = [p for p in plans if p.is_active]
        return plans

    async def history(self, plan_code: str) -> list[BillingPlan]:
        rows = await self._fetch_all(
            f"SELECT {_PLAN_COLUMNS} FROM public.billing_plans "
            "WHERE plan_code = $1 ORDER BY version",
            plan_code,
        )
        return [_row_to_plan(r) for r in rows]

    async def get_current_by_code(self, plan_code: str) -> Optional[BillingPlan]:
        row = await self._fetch_one(
            f"SELECT {_PLAN_COLUMNS} FROM public.billing_plans "
            "WHERE plan_code = $1 AND effective_to IS NULL ORDER BY version DESC LIMIT 1",
            plan_code,
        )
        return _row_to_plan(row) if row is not None else None

    async def get_version(self, plan_code: str, version: int) -> Optional[BillingPlan]:
        """The exact plan version (historical terms for an existing subscription)."""
        row = await self._fetch_one(
            f"SELECT {_PLAN_COLUMNS} FROM public.billing_plans "
            "WHERE plan_code = $1 AND version = $2",
            plan_code, version,
        )
        return _row_to_plan(row) if row is not None else None

    async def create(self, plan: BillingPlan, *, created_by: Optional[str]) -> BillingPlan:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.billing_plans (
                plan_code, name, description, price, currency, billing_interval,
                included_credits, included_storage_bytes, team_member_limit,
                processing_limits, features, billing_mode,
                assisted_processing_available, managed_processing_available,
                api_access, is_active, version, version_label, effective_from,
                created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                      $13, $14, $15, $16, $17, $18, $19, $20)
            RETURNING {_PLAN_COLUMNS}
            """,
            plan.plan_code, plan.name, plan.description, str(plan.price), plan.currency,
            plan.billing_interval, plan.included_credits, plan.included_storage_bytes,
            plan.team_member_limit, dumps_jsonb(plan.processing_limits),
            dumps_jsonb(plan.features), plan.billing_mode,
            plan.assisted_processing_available, plan.managed_processing_available,
            plan.api_access, plan.is_active, plan.version, plan.version_label,
            plan.effective_from, created_by,
        )
        if row is None:
            raise RuntimeError("billing_plans insert returned no row")
        return _row_to_plan(row)


    async def publish_new_version(
        self,
        *,
        plan_code: str,
        fields: dict[str, Any],
        reason: Optional[str],
        updated_by: Optional[str],
    ) -> BillingPlan:
        """Publish a NEW version of a plan.

        The current (effective_to IS NULL) row is closed (effective_to = NOW)
        and a new row is inserted with version+1. Historical commercial records
        keep the old version's terms.
        """
        current = await self.get_current_by_code(plan_code)
        base_version = current.version if current is not None else 0

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                if current is not None:
                    await conn.execute(
                        "UPDATE public.billing_plans SET effective_to = NOW() "
                        "WHERE id = $1",
                        current.id,
                    )
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO public.billing_plans (
                        plan_code, name, description, price, currency,
                        billing_interval, included_credits,
                        included_storage_bytes, team_member_limit,
                        processing_limits, features, billing_mode,
                        assisted_processing_available,
                        managed_processing_available, api_access, is_active,
                        version, version_label, effective_from, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                              $13, $14, $15, $16, $17, $18, NOW(), $19)
                    RETURNING {_PLAN_COLUMNS}
                    """,
                    plan_code,
                    fields.get("name") or (current.name if current else plan_code),
                    fields.get("description")
                    if "description" in fields
                    else (current.description if current else None),
                    str(fields.get("price", current.price if current else 0)),
                    fields.get("currency") or (current.currency if current else "GBP"),
                    fields.get("billing_interval")
                    or (current.billing_interval if current else "month"),
                    int(fields.get("included_credits", current.included_credits if current else 0)),
                    int(fields.get("included_storage_bytes", current.included_storage_bytes if current else 0)),
                    fields.get("team_member_limit")
                    if "team_member_limit" in fields
                    else (current.team_member_limit if current else None),
                    dumps_jsonb(fields.get("processing_limits", current.processing_limits if current else {})),
                    dumps_jsonb(fields.get("features", current.features if current else {})),
                    fields.get("billing_mode") if "billing_mode" in fields else (current.billing_mode if current else None),
                    bool(fields.get("assisted_processing_available", current.assisted_processing_available if current else False)),
                    bool(fields.get("managed_processing_available", current.managed_processing_available if current else False)),
                    bool(fields.get("api_access", current.api_access if current else False)),
                    bool(fields.get("is_active", current.is_active if current else True)),
                    base_version + 1,
                    f"v{base_version + 1}",
                    updated_by,
                )
        if row is None:
            raise RuntimeError("billing_plans version insert returned no row")
        return _row_to_plan(row)

    async def save(self, entity: BillingPlan) -> BillingPlan:
        return entity

    async def delete(self, id: str) -> None:
        return None


class BillingCommercialConfigRepository(AbstractRepository[CommercialConfig]):
    """Versioned key/value commercial rule persistence."""

    async def get(self, id: str) -> Optional[CommercialConfig]:
        row = await self._fetch_one(
            f"SELECT {_CONFIG_COLUMNS} FROM public.billing_commercial_config WHERE id = $1", id
        )
        return _row_to_config(row) if row is not None else None

    async def get_current(self, config_key: str) -> Optional[CommercialConfig]:
        row = await self._fetch_one(
            f"SELECT {_CONFIG_COLUMNS} FROM public.billing_commercial_config "
            "WHERE config_key = $1 AND effective_to IS NULL "
            "ORDER BY version DESC LIMIT 1",
            config_key,
        )
        return _row_to_config(row) if row is not None else None

    async def list_current(self) -> list[CommercialConfig]:
        rows = await self._fetch_all(
            f"SELECT {_CONFIG_COLUMNS} FROM public.billing_commercial_config "
            "WHERE effective_to IS NULL ORDER BY config_key",
        )
        return [_row_to_config(r) for r in rows]

    async def history(self, config_key: str) -> list[CommercialConfig]:
        rows = await self._fetch_all(
            f"SELECT {_CONFIG_COLUMNS} FROM public.billing_commercial_config "
            "WHERE config_key = $1 ORDER BY version",
            config_key,
        )
        return [_row_to_config(r) for r in rows]

    async def get_default_billing_mode(self) -> str:
        """The current default billing mode for NEW customers ('CREDIT' fallback)."""
        config = await self.get_current("default_billing_mode")
        if config is not None and config.config_value:
            mode = config.config_value.get("mode")
            if mode in ("CREDIT", "STANDARD"):
                return str(mode)
        return "CREDIT"

    async def update_version(
        self,
        *,
        config_key: str,
        config_value: dict[str, Any],
        reason: Optional[str],
        updated_by: Optional[str],
    ) -> CommercialConfig:
        """Publish a NEW version of a commercial rule key.

        The current row is closed (effective_to = NOW); a new row with
        version+1 becomes current. History is never rewritten.
        """
        current = await self.get_current(config_key)
        base_version = current.version if current is not None else 0

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                if current is not None:
                    await conn.execute(
                        "UPDATE public.billing_commercial_config SET effective_to = NOW() "
                        "WHERE id = $1",
                        current.id,
                    )
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO public.billing_commercial_config (
                        config_key, config_value, version, reason,
                        effective_from, created_by
                    ) VALUES ($1, $2, $3, $4, NOW(), $5)
                    RETURNING {_CONFIG_COLUMNS}
                    """,
                    config_key,
                    dumps_jsonb(config_value),
                    base_version + 1,
                    reason,
                    updated_by,
                )
        if row is None:
            raise RuntimeError("billing_commercial_config insert returned no row")
        return _row_to_config(row)

    async def save(self, entity: CommercialConfig) -> CommercialConfig:
        return entity

    async def delete(self, id: str) -> None:
        return None


class BillingCreditLedgerRepository(AbstractRepository[CreditLedgerEntry]):
    """Append-only credit ledger persistence (foundation)."""

    async def get(self, id: str) -> Optional[CreditLedgerEntry]:
        row = await self._fetch_one(
            f"SELECT {_LEDGER_COLUMNS} FROM public.billing_credit_ledger WHERE id = $1", id
        )
        return _row_to_ledger(row) if row is not None else None

    async def record(self, entry: CreditLedgerEntry) -> CreditLedgerEntry:
        """Append one immutable ledger entry (idempotent via external_reference)."""
        row = await self._fetch_one(
            f"""
            INSERT INTO public.billing_credit_ledger (
                organization_id, entry_type, credit_delta, source, reason,
                plan_code, plan_version, subscription_id, external_reference,
                correlation_id, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING {_LEDGER_COLUMNS}
            """,
            entry.organization_id, entry.entry_type, entry.credit_delta,
            entry.source, entry.reason, entry.plan_code, entry.plan_version,
            entry.subscription_id, entry.external_reference,
            entry.correlation_id, entry.created_by,
        )
        if row is None:
            raise RuntimeError("billing_credit_ledger insert returned no row")
        return _row_to_ledger(row)

    async def list_for_org(self, organization_id: str) -> list[CreditLedgerEntry]:
        rows = await self._fetch_all(
            f"SELECT {_LEDGER_COLUMNS} FROM public.billing_credit_ledger "
            "WHERE organization_id = $1 ORDER BY created_at",
            organization_id,
        )
        return [_row_to_ledger(r) for r in rows]

    async def balance(self, organization_id: str) -> int:
        row = await self._fetch_one(
            "SELECT COALESCE(SUM(credit_delta), 0) FROM public.billing_credit_ledger "
            "WHERE organization_id = $1",
            organization_id,
        )
        return int(row[0]) if row is not None else 0

    async def save(self, entity: CreditLedgerEntry) -> CreditLedgerEntry:
        return entity

    async def delete(self, id: str) -> None:
        return None


class SubscriptionsRepository(AbstractRepository[Subscription]):
    """Org-scoped subscription lifecycle persistence (``customer_subscriptions``).

    Reuses the existing table (extended by the D37 migration). The legacy
    Stripe-named columns are not touched; the D37 fields reference the
    versioned plan catalogue and the lifecycle vocabulary.
    """

    _COLUMNS = (
        "id, organization_id, plan_code, plan_version, billing_mode, "
        "lifecycle_status, current_period_start, current_period_end, "
        "activated_at, cancelled_at, plan, status, currency, created_at, updated_at"
    )

    async def get(self, id: str) -> Optional[Subscription]:
        row = await self._fetch_one(
            f"SELECT {self._COLUMNS} FROM public.customer_subscriptions WHERE id = $1", id
        )
        return self._row(row) if row is not None else None

    async def get_active_for_org(self, organization_id: str) -> Optional[Subscription]:
        row = await self._fetch_one(
            f"SELECT {self._COLUMNS} FROM public.customer_subscriptions "
            "WHERE organization_id = $1 AND lifecycle_status IN "
            "('trial', 'active', 'past_due', 'suspended') "
            "ORDER BY created_at DESC LIMIT 1",
            organization_id,
        )
        return self._row(row) if row is not None else None

    async def get_latest_for_org(self, organization_id: str) -> Optional[Subscription]:
        row = await self._fetch_one(
            f"SELECT {self._COLUMNS} FROM public.customer_subscriptions "
            "WHERE organization_id = $1 ORDER BY created_at DESC LIMIT 1",
            organization_id,
        )
        return self._row(row) if row is not None else None

    async def list_for_org(self, organization_id: str) -> list[Subscription]:
        rows = await self._fetch_all(
            f"SELECT {self._COLUMNS} FROM public.customer_subscriptions "
            "WHERE organization_id = $1 ORDER BY created_at",
            organization_id,
        )
        return [self._row(r) for r in rows]

    async def list_all(self) -> list[Subscription]:
        rows = await self._fetch_all(
            f"SELECT {self._COLUMNS} FROM public.customer_subscriptions ORDER BY created_at"
        )
        return [self._row(r) for r in rows]

    async def upsert_active(
        self, subscription: Subscription, *, created_by: Optional[str]
    ) -> Subscription:
        """Insert (or renew) the org's active commercial relationship.

        A new row supersedes any previous active row (which is closed to
        ``cancelled``). One active relationship per org is enforced by the
        unique partial index.
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE public.customer_subscriptions SET lifecycle_status = 'cancelled' "
                    "WHERE organization_id = $1 AND lifecycle_status IN "
                    "('trial', 'active', 'past_due', 'suspended')",
                    subscription.organization_id,
                )
                row = await conn.fetchrow(
                    f"""
                    INSERT INTO public.customer_subscriptions (
                        organization_id, plan, plan_code, plan_version, billing_mode,
                        lifecycle_status, current_period_start, current_period_end,
                        activated_at, idempotency_key, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING {self._COLUMNS}
                    """,
                    subscription.organization_id, subscription.plan_code,
                    subscription.plan_code, subscription.plan_version,
                    subscription.billing_mode, subscription.lifecycle_status,
                    subscription.current_period_start, subscription.current_period_end,
                    subscription.activated_at, subscription.idempotency_key, created_by,
                )
        if row is None:
            raise RuntimeError("customer_subscriptions insert returned no row")
        return self._row(row)

    async def update_status(
        self, id: str, lifecycle_status: str, *, updated_by: Optional[str]
    ) -> Optional[Subscription]:
        row = await self._fetch_one(
            f"""
            UPDATE public.customer_subscriptions
               SET lifecycle_status = $2, updated_at = NOW(), updated_by = $3
             WHERE id = $1
            RETURNING {self._COLUMNS}
            """,
            id, lifecycle_status, updated_by,
        )
        return self._row(row) if row is not None else None

    async def save(self, entity: Subscription) -> Subscription:
        return entity

    async def delete(self, id: str) -> None:
        return None

    @staticmethod
    def _row(r) -> Subscription:
        d = dict(r)
        return Subscription(
            id=str(d["id"]),
            organization_id=str(d["organization_id"]),
            plan_code=d.get("plan_code"),
            plan_version=d.get("plan_version"),
            billing_mode=d.get("billing_mode"),
            lifecycle_status=d.get("lifecycle_status") or "pending",
            current_period_start=d.get("current_period_start"),
            current_period_end=d.get("current_period_end"),
            activated_at=d.get("activated_at"),
            cancelled_at=d.get("cancelled_at"),
            plan=d.get("plan"),
            status=d.get("status"),
            currency=d.get("currency"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )


class BillingOrdersRepository(AbstractRepository[BillingOrder]):
    """Common order persistence (``billing_orders``)."""

    _COLUMNS = (
        "id, organization_id, order_type, status, title, description, complexity, "
        "items, total_amount, currency, plan_code, plan_version, config_version, "
        "idempotency_key, external_reference, approved_by, approved_at, "
        "completed_at, cancelled_by, cancelled_at, metadata, created_by, "
        "created_at, updated_at"
    )

    async def get(self, id: str) -> Optional[BillingOrder]:
        row = await self._fetch_one(
            f"SELECT {self._COLUMNS} FROM public.billing_orders WHERE id = $1", id
        )
        return self._row(row) if row is not None else None

    async def get_for_org(self, id: str, organization_id: str) -> Optional[BillingOrder]:
        row = await self._fetch_one(
            f"SELECT {self._COLUMNS} FROM public.billing_orders "
            "WHERE id = $1 AND organization_id = $2",
            id, organization_id,
        )
        return self._row(row) if row is not None else None

    async def list_for_org(self, organization_id: str) -> list[BillingOrder]:
        rows = await self._fetch_all(
            f"SELECT {self._COLUMNS} FROM public.billing_orders "
            "WHERE organization_id = $1 ORDER BY created_at DESC",
            organization_id,
        )
        return [self._row(r) for r in rows]

    async def list_all(self, *, status: Optional[str] = None) -> list[BillingOrder]:
        if status:
            rows = await self._fetch_all(
                f"SELECT {self._COLUMNS} FROM public.billing_orders "
                "WHERE status = $1 ORDER BY created_at DESC",
                status,
            )
        else:
            rows = await self._fetch_all(
                f"SELECT {self._COLUMNS} FROM public.billing_orders ORDER BY created_at DESC"
            )
        return [self._row(r) for r in rows]

    async def create(self, order: BillingOrder, *, created_by: Optional[str]) -> BillingOrder:
        row = await self._fetch_one(
            f"""
            INSERT INTO public.billing_orders (
                organization_id, order_type, status, title, description,
                complexity, items, total_amount, currency, plan_code,
                plan_version, config_version, idempotency_key,
                external_reference, metadata, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                      $14, $15, $16)
            RETURNING {self._COLUMNS}
            """,
            order.organization_id, order.order_type, order.status, order.title,
            order.description, order.complexity, dumps_jsonb(order.items),
            str(order.total_amount), order.currency, order.plan_code,
            order.plan_version, dumps_jsonb(order.config_version or {}),
            order.idempotency_key, order.external_reference,
            dumps_jsonb(order.metadata), created_by,
        )
        if row is None:
            raise RuntimeError("billing_orders insert returned no row")
        return self._row(row)

    async def update_status(
        self,
        id: str,
        status: str,
        *,
        actor: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[BillingOrder]:
        if metadata is not None:
            row = await self._fetch_one(
                f"""
                UPDATE public.billing_orders
                   SET status = $2, updated_at = NOW(), metadata = $3
                 WHERE id = $1
                RETURNING {self._COLUMNS}
                """,
                id, status, dumps_jsonb(metadata),
            )
        else:
            row = await self._fetch_one(
                f"""
                UPDATE public.billing_orders
                   SET status = $2, updated_at = NOW()
                 WHERE id = $1
                RETURNING {self._COLUMNS}
                """,
                id, status,
            )
        return self._row(row) if row is not None else None

    async def mark_approved(
        self, id: str, *, approved_by: Optional[str] = None
    ) -> Optional[BillingOrder]:
        row = await self._fetch_one(
            f"""
            UPDATE public.billing_orders
               SET status = 'approved', approved_by = $2, approved_at = NOW(),
                   updated_at = NOW()
             WHERE id = $1
            RETURNING {self._COLUMNS}
            """,
            id, approved_by,
        )
        return self._row(row) if row is not None else None

    async def mark_completed(self, id: str) -> Optional[BillingOrder]:
        row = await self._fetch_one(
            f"""
            UPDATE public.billing_orders
               SET status = 'completed', completed_at = NOW(), updated_at = NOW()
             WHERE id = $1
            RETURNING {self._COLUMNS}
            """,
            id,
        )
        return self._row(row) if row is not None else None

    async def save(self, entity: BillingOrder) -> BillingOrder:
        return entity

    async def delete(self, id: str) -> None:
        return None

    @staticmethod
    def _row(r) -> BillingOrder:
        d = dict(r)
        return BillingOrder(
            id=str(d["id"]),
            organization_id=str(d["organization_id"]),
            order_type=str(d["order_type"]),
            status=str(d["status"]),
            title=d.get("title"),
            description=d.get("description"),
            complexity=d.get("complexity"),
            items=loads_jsonb(d.get("items")) or [],
            total_amount=float(d.get("total_amount") or 0),
            currency=str(d.get("currency") or "GBP"),
            plan_code=d.get("plan_code"),
            plan_version=d.get("plan_version"),
            config_version=loads_jsonb(d.get("config_version")) or {},
            idempotency_key=d.get("idempotency_key"),
            external_reference=d.get("external_reference"),
            approved_by=str(d["approved_by"]) if d.get("approved_by") else None,
            approved_at=d.get("approved_at"),
            completed_at=d.get("completed_at"),
            cancelled_by=str(d["cancelled_by"]) if d.get("cancelled_by") else None,
            cancelled_at=d.get("cancelled_at"),
            metadata=loads_jsonb(d.get("metadata")) or {},
            created_by=str(d["created_by"]) if d.get("created_by") else None,
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )


class StorageUsageRepository(AbstractRepository[StorageUsage]):
    """Storage metering snapshots (``billing_storage_usage``)."""

    async def get(self, id: str) -> Optional[StorageUsage]:
        row = await self._fetch_one(
            "SELECT id, organization_id, usage_bytes, included_bytes, "
            "additional_bytes, measured_at, source, created_at "
            "FROM public.billing_storage_usage WHERE id = $1",
            id,
        )
        return self._row(row) if row is not None else None

    async def latest_for_org(self, organization_id: str) -> Optional[StorageUsage]:
        row = await self._fetch_one(
            "SELECT id, organization_id, usage_bytes, included_bytes, "
            "additional_bytes, measured_at, source, created_at "
            "FROM public.billing_storage_usage "
            "WHERE organization_id = $1 ORDER BY measured_at DESC LIMIT 1",
            organization_id,
        )
        return self._row(row) if row is not None else None

    async def history_for_org(self, organization_id: str) -> list[StorageUsage]:
        rows = await self._fetch_all(
            "SELECT id, organization_id, usage_bytes, included_bytes, "
            "additional_bytes, measured_at, source, created_at "
            "FROM public.billing_storage_usage "
            "WHERE organization_id = $1 ORDER BY measured_at DESC",
            organization_id,
        )
        return [self._row(r) for r in rows]

    async def record(self, usage: StorageUsage) -> StorageUsage:
        row = await self._fetch_one(
            "INSERT INTO public.billing_storage_usage "
            "(organization_id, usage_bytes, included_bytes, additional_bytes, source) "
            "VALUES ($1, $2, $3, $4, $5) RETURNING id, organization_id, usage_bytes, "
            "included_bytes, additional_bytes, measured_at, source, created_at",
            usage.organization_id, usage.usage_bytes, usage.included_bytes,
            usage.additional_bytes, usage.source,
        )
        if row is None:
            raise RuntimeError("billing_storage_usage insert returned no row")
        return self._row(row)

    async def save(self, entity: StorageUsage) -> StorageUsage:
        return entity

    async def delete(self, id: str) -> None:
        return None

    @staticmethod
    def _row(r) -> StorageUsage:
        d = dict(r)
        return StorageUsage(
            id=str(d["id"]),
            organization_id=str(d["organization_id"]),
            usage_bytes=int(d.get("usage_bytes") or 0),
            included_bytes=int(d.get("included_bytes") or 0),
            additional_bytes=int(d.get("additional_bytes") or 0),
            measured_at=d.get("measured_at"),
            source=d.get("source") or "organization_files_sum",
            created_at=d.get("created_at"),
        )


class PaymentRecordsRepository(AbstractRepository[PaymentRecord]):
    """Provider-neutral payment records (``billing_payment_records``)."""

    async def get(self, id: str) -> Optional[PaymentRecord]:
        row = await self._fetch_one(
            "SELECT * FROM public.billing_payment_records WHERE id = $1", id
        )
        return self._row(row) if row is not None else None

    async def list_for_org(self, organization_id: str) -> list[PaymentRecord]:
        rows = await self._fetch_all(
            "SELECT * FROM public.billing_payment_records "
            "WHERE organization_id = $1 ORDER BY recorded_at DESC",
            organization_id,
        )
        return [self._row(r) for r in rows]

    async def list_all(self) -> list[PaymentRecord]:
        rows = await self._fetch_all(
            "SELECT * FROM public.billing_payment_records ORDER BY recorded_at DESC"
        )
        return [self._row(r) for r in rows]

    async def create(self, record: PaymentRecord) -> PaymentRecord:
        row = await self._fetch_one(
            """
            INSERT INTO public.billing_payment_records (
                organization_id, provider, payment_method_type,
                provider_transaction_ref, amount, currency, status,
                order_id, subscription_id, idempotency_key, metadata, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING *
            """,
            record.organization_id, record.provider, record.payment_method_type,
            record.provider_transaction_ref, str(record.amount), record.currency,
            record.status, record.order_id, record.subscription_id,
            record.idempotency_key, dumps_jsonb(record.metadata), record.created_by,
        )
        if row is None:
            raise RuntimeError("billing_payment_records insert returned no row")
        return self._row(row)

    async def update_status(
        self, id: str, status: str, *, provider_transaction_ref: Optional[str] = None
    ) -> Optional[PaymentRecord]:
        row = await self._fetch_one(
            """
            UPDATE public.billing_payment_records
               SET status = $2,
                   provider_transaction_ref = COALESCE($3, provider_transaction_ref),
                   confirmed_at = CASE WHEN $2 = 'confirmed' THEN NOW() ELSE confirmed_at END
             WHERE id = $1
            RETURNING *
            """,
            id, status, provider_transaction_ref,
        )
        return self._row(row) if row is not None else None

    async def save(self, entity: PaymentRecord) -> PaymentRecord:
        return entity

    async def delete(self, id: str) -> None:
        return None

    @staticmethod
    def _row(r) -> PaymentRecord:
        d = dict(r)
        return PaymentRecord(
            id=str(d["id"]),
            organization_id=str(d["organization_id"]),
            provider=str(d["provider"]),
            amount=float(d.get("amount") or 0),
            currency=str(d.get("currency") or "GBP"),
            status=str(d.get("status") or "pending"),
            payment_method_type=d.get("payment_method_type"),
            provider_transaction_ref=d.get("provider_transaction_ref"),
            order_id=str(d["order_id"]) if d.get("order_id") else None,
            subscription_id=str(d["subscription_id"]) if d.get("subscription_id") else None,
            idempotency_key=d.get("idempotency_key"),
            recorded_at=d.get("recorded_at"),
            confirmed_at=d.get("confirmed_at"),
            metadata=loads_jsonb(d.get("metadata")) or {},
            created_by=str(d["created_by"]) if d.get("created_by") else None,
        )


class UsageTrackingRepository(AbstractRepository[object]):
    """Trusted writes to the existing ``usage_tracking`` table (D37 STANDARD)."""

    async def get(self, id: str) -> Optional[object]:
        return None

    async def record(self, organization_id: str, units: int, when=None) -> None:
        from datetime import datetime, timezone

        day = when or datetime.now(timezone.utc)
        await self._fetch_one(
            """
            INSERT INTO public.usage_tracking
                (organization_id, usage_date, usage_month, ai_files_processed)
            VALUES ($1, $2, to_char($2, 'YYYY-MM'), $3)
            """,
            organization_id, day, units,
        )

    async def save(self, entity: object) -> object:
        return entity

    async def delete(self, id: str) -> None:
        return None


class IdempotencyRepository(AbstractRepository[IdempotencyKey]):
    """Durable idempotency (``billing_idempotency_keys``)."""

    async def get(self, key: str) -> Optional[IdempotencyKey]:
        row = await self._fetch_one(
            "SELECT key, operation, entity_type, entity_id, request_hash, created_at "
            "FROM public.billing_idempotency_keys WHERE key = $1",
            key,
        )
        return self._row(row) if row is not None else None

    async def claim(
        self,
        key: str,
        operation: str,
        *,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        request_hash: Optional[str] = None,
    ) -> IdempotencyKey:
        """Atomically insert the key (duplicate -> unique violation)."""
        row = await self._fetch_one(
            "INSERT INTO public.billing_idempotency_keys "
            "(key, operation, entity_type, entity_id, request_hash) "
            "VALUES ($1, $2, $3, $4, $5) RETURNING key, operation, entity_type, "
            "entity_id, request_hash, created_at",
            key, operation, entity_type, entity_id, request_hash,
        )
        if row is None:
            raise RuntimeError("billing_idempotency_keys insert returned no row")
        return self._row(row)

    async def save(self, entity: IdempotencyKey) -> IdempotencyKey:
        return entity

    async def delete(self, id: str) -> None:
        return None

    @staticmethod
    def _row(r) -> IdempotencyKey:
        d = dict(r)
        return IdempotencyKey(
            key=str(d["key"]),
            operation=str(d["operation"]),
            entity_type=d.get("entity_type"),
            entity_id=d.get("entity_id"),
            request_hash=d.get("request_hash"),
            created_at=d.get("created_at"),
        )

