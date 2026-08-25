"""D37-0 — provider-neutral commercial domain objects.

Pure, immutable dataclasses mirroring the D37-0 billing foundation tables
(``billing_plans``, ``billing_commercial_config``, ``billing_credit_ledger``)
plus the per-customer ``organizations.billing_mode`` column. No provider
coupling — provider-specific identifiers live in provider-neutral columns and
are isolated from business logic.

D37 extends this with the subscription lifecycle, the common order model,
storage metering and provider-neutral payment records.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

#: The two supported billing modes (D37-0 §10). Admin-configurable default for
#: NEW customers; per-customer override on the commercial relationship.
BILLING_MODES: tuple[str, ...] = ("CREDIT", "STANDARD")

#: Credit ledger entry types (D37-0 §22).
CREDIT_LEDGER_ENTRY_TYPES: tuple[str, ...] = (
    "grant",
    "consume",
    "adjustment",
    "rollover",
    "emergency_allowance",
    "refund",
    "reversal",
)

#: Credit ledger sources.
CREDIT_LEDGER_SOURCES: tuple[str, ...] = (
    "plan_included",
    "purchase",
    "promotional",
    "adjustment",
    "refund",
    "emergency",
    "rollover",
)

#: Subscription lifecycle states (D37 §23).
SUBSCRIPTION_LIFECYCLE: tuple[str, ...] = (
    "pending",
    "trial",
    "active",
    "past_due",
    "suspended",
    "cancelled",
    "expired",
)

#: Common order types (D37 §25).
ORDER_TYPES: tuple[str, ...] = (
    "automated",
    "assisted",
    "managed",
    "storage",
    "other",
)

#: Order lifecycle states (D37 §26).
ORDER_STATUSES: tuple[str, ...] = (
    "draft",
    "estimated",
    "awaiting_customer_approval",
    "approved",
    "queued",
    "processing",
    "awaiting_qc",
    "completed",
    "cancelled",
    "rejected",
    "failed",
    "refunded",
)

#: Document complexity classes (D37 §10).
COMPLEXITY_CLASSES: tuple[str, ...] = (
    "simple",
    "standard",
    "complex",
    "exceptional",
)

#: Provider-neutral payment record states (D37 §33).
PAYMENT_STATUSES: tuple[str, ...] = (
    "pending",
    "confirmed",
    "failed",
    "refunded",
)



@dataclass(frozen=True, slots=True)
class BillingPlan:
    """A configurable, versioned plan (``billing_plans``).

    ``plan_code`` is the stable identity; ``version``+``effective_from/to``
    make price/feature changes historically safe. A commercial record created
    under plan v1 keeps v1's terms even after v2 is published.
    """

    id: str
    plan_code: str
    name: str
    price: float
    currency: str = "GBP"
    billing_interval: str = "month"
    included_credits: int = 0
    included_storage_bytes: int = 0
    team_member_limit: Optional[int] = None
    processing_limits: dict[str, Any] = field(default_factory=dict)
    features: dict[str, Any] = field(default_factory=dict)
    billing_mode: Optional[str] = None
    assisted_processing_available: bool = False
    managed_processing_available: bool = False
    api_access: bool = False
    is_active: bool = True
    version: int = 1
    version_label: Optional[str] = None
    description: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class CommercialConfig:
    """One versioned commercial rule key (``billing_commercial_config``).

    ``config_value`` is structured JSONB (credit rules, structured-data bands,
    storage, assisted pricing, credit policy, standard allowance). The current
    value is the row with ``effective_to IS NULL``; history is retained.
    """

    id: str
    config_key: str
    config_value: dict[str, Any]
    version: int = 1
    reason: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    created_by: Optional[str] = None


@dataclass(frozen=True, slots=True)
class CreditLedgerEntry:
    """One append-only credit ledger entry (``billing_credit_ledger``).

    The ledger is authoritative and immutable; the balance is derived as
    ``SUM(credit_delta)``. ``external_reference`` provides idempotency for
    future payment/entitlement events.
    """

    id: str
    organization_id: str
    entry_type: str
    credit_delta: int
    source: str
    reason: Optional[str] = None
    plan_code: Optional[str] = None
    plan_version: Optional[int] = None
    subscription_id: Optional[str] = None
    order_id: Optional[str] = None
    external_reference: Optional[str] = None
    correlation_id: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

@dataclass(frozen=True, slots=True)
class Subscription:
    """The organisation's commercial relationship (``customer_subscriptions``).

    Reuses the existing org-scoped table, extended with the provider-neutral
    plan reference (``plan_code`` + ``plan_version``), the per-customer billing
    mode and the D37 lifecycle state. ``lifecycle_status`` is authoritative
    server-side (D37-0 lockdown: authenticated cannot write this table).
    """

    id: str
    organization_id: str
    plan_code: Optional[str] = None
    plan_version: Optional[int] = None
    billing_mode: Optional[str] = None
    lifecycle_status: str = "pending"
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None
    plan: Optional[str] = None  # legacy free-text plan label
    status: Optional[str] = None  # legacy status (kept, unused by D37)
    currency: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class BillingOrder:
    """A common commercial order (``billing_orders``).

    One order model for automated / Assisted / Managed / storage / other.
    ``items`` is an immutable line-item snapshot (the terms under which the
    order was created). Completed orders are never rewritten — corrections are
    new adjustments.
    """

    id: str
    organization_id: str
    order_type: str
    status: str = "draft"
    title: Optional[str] = None
    description: Optional[str] = None
    complexity: Optional[str] = None
    items: list[dict[str, Any]] = field(default_factory=list)
    total_amount: float = 0.0
    currency: str = "GBP"
    plan_code: Optional[str] = None
    plan_version: Optional[int] = None
    config_version: Optional[dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    external_reference: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class StorageUsage:
    """One storage metering snapshot (``billing_storage_usage``)."""

    id: str
    organization_id: str
    usage_bytes: int = 0
    included_bytes: int = 0
    additional_bytes: int = 0
    measured_at: Optional[datetime] = None
    source: str = "organization_files_sum"
    created_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class PaymentRecord:
    """A provider-neutral payment record (``billing_payment_records``).

    Represents payment intent/confirmation for future PayPal / Wise / card
    adapters. Sensitive credentials are NEVER stored; ``provider_transaction_ref``
    is the only provider-specific identity.
    """

    id: str
    organization_id: str
    provider: str
    amount: float
    currency: str = "GBP"
    status: str = "pending"
    payment_method_type: Optional[str] = None
    provider_transaction_ref: Optional[str] = None
    order_id: Optional[str] = None
    subscription_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    recorded_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    """A durable idempotency record (``billing_idempotency_keys``)."""

    key: str
    operation: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    request_hash: Optional[str] = None
    created_at: Optional[datetime] = None

