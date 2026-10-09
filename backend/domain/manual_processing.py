"""FIN-06 — Manual Processing governance (domain policy).

The PO decision: **Manual Processing is OFF by default** and only CarbonTally
Admin may enable it, with the scope vocabulary

    organization | consultant_firm | consultant_client

and the precedence **most-specific-wins**:

    consultant_client  >  consultant_firm  >  organization  >  platform default

Absence of an explicit governance row for the most specific applicable scope
means the request is **denied** (fail closed). A more specific ``enabled=False``
row therefore overrides a broader ``enabled=True`` row, and vice versa a specific
``True`` enables work inside an otherwise-off scope.

This module is deliberately pure: it contains no database access and no HTTP
concerns, so the precedence model is unit-testable in isolation. The repository
(``data.manual_processing``) supplies the rows; the API layer supplies the
CarbonTally-Admin authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

# ---------------------------------------------------------------------------
# Allocation error fidelity (F-7/F-9 — CT-MP-SUB-004 production readiness)
# ---------------------------------------------------------------------------
# The allocation writers must distinguish an EXPECTED, deterministic
# business refusal (duplicate active allocation / capacity exhausted) from an
# UNEXPECTED infrastructure failure. Previously a bare ``except Exception``
# collapsed every failure into "duplicate allocation", which mis-reported a
# genuine server error as a conflict (AGENTS.md §46). These typed errors are
# raised by the repository ONLY for the expected conditions, so the API layer
# can map them to a precise 409 while every other exception propagates as a
# real server error (500).


class ManualProcessingAllocationError(Exception):
    """Base class for an EXPECTED allocation refusal (mapped to HTTP 409)."""


class DuplicateActiveAllocationError(ManualProcessingAllocationError):
    """The (firm, organisation) pair already holds an ACTIVE allocation."""


class CapacityExceededError(ManualProcessingAllocationError):
    """The firm has no remaining purchased SELECTED_CLIENTS capacity."""


#: Ratified scope vocabulary (mirrors the migration CHECK constraint).
SCOPE_ORGANIZATION = "organization"
SCOPE_CONSULTANT_FIRM = "consultant_firm"
SCOPE_CONSULTANT_CLIENT = "consultant_client"

SCOPE_TYPES: tuple[str, ...] = (
    SCOPE_ORGANIZATION,
    SCOPE_CONSULTANT_FIRM,
    SCOPE_CONSULTANT_CLIENT,
)

#: Most-specific first — the FIRST matching scope with an explicit row wins.
SCOPE_PRECEDENCE: tuple[str, ...] = (
    SCOPE_CONSULTANT_CLIENT,
    SCOPE_CONSULTANT_FIRM,
    SCOPE_ORGANIZATION,
)

#: The platform default when no explicit row matches.
DEFAULT_ENABLED = False


@dataclass(frozen=True, slots=True)
class ManualProcessingGrant:
    """One explicit governance row (``manual_processing_grants``)."""

    scope_type: str
    scope_id: str
    enabled: bool
    reason: Optional[str] = None
    set_by: Optional[str] = None
    set_at: Optional[object] = None


@dataclass(frozen=True, slots=True)
class EffectiveManualProcessing:
    """The resolved governance answer for one organisation context.

    ``enabled`` is the EFFECTIVE value: the FIN-06 governance answer AND the
    subscription entitlement. ``governance_enabled`` preserves the raw
    governance answer so a diagnostic can explain which gate decided.
    """

    enabled: bool
    #: ``explicit`` (a governance row decided it) or ``default`` (nothing matched).
    source_level: str
    source_scope_type: Optional[str] = None
    source_scope_id: Optional[str] = None
    #: Present because the platform default is fail-closed by decision.
    default_off: bool = True
    #: The raw FIN-06 governance value (before the entitlement gate).
    governance_enabled: Optional[bool] = None
    #: The subscription-entitlement gate (``None`` = not evaluated, e.g. the
    #: platform-operator path).
    entitled: Optional[bool] = None
    #: Why the effective value is false: ``not_entitled`` | ``not_enabled``.
    denied_reason: Optional[str] = None
    #: ``feature`` | ``assisted_processing_available`` | ``none``.
    entitlement_source: Optional[str] = None
    plan_code: Optional[str] = None


@dataclass(frozen=True, slots=True)
class OrgContext:
    """The organisations's relationship context used for scope resolution.

    ``consultant_client_id``/``consultant_firm_id`` are populated only when the
    organisation is reached through an ACTIVE consultant-client grant; they are
    never trusted from the client (the API resolves them server-side).
    """

    organization_id: str
    consultant_client_id: Optional[str] = None
    consultant_firm_id: Optional[str] = None


def scope_targets(context: OrgContext) -> dict[str, str]:
    """Return the scope-id candidate for each applicable scope type."""
    targets: dict[str, str] = {}
    if context.consultant_client_id:
        targets[SCOPE_CONSULTANT_CLIENT] = context.consultant_client_id
    if context.consultant_firm_id:
        targets[SCOPE_CONSULTANT_FIRM] = context.consultant_firm_id
    if context.organization_id:
        targets[SCOPE_ORGANIZATION] = context.organization_id
    return targets


def resolve_effective(
    grants: Iterable[ManualProcessingGrant], context: OrgContext
) -> EffectiveManualProcessing:
    """Resolve the effective governance value by most-specific-wins precedence."""
    by_scope: dict[tuple[str, str], ManualProcessingGrant] = {
        (g.scope_type, g.scope_id): g for g in grants
    }
    targets = scope_targets(context)
    for scope_type in SCOPE_PRECEDENCE:
        scope_id = targets.get(scope_type)
        if not scope_id:
            continue
        grant = by_scope.get((scope_type, scope_id))
        if grant is not None:
            return EffectiveManualProcessing(
                enabled=bool(grant.enabled),
                source_level="explicit",
                source_scope_type=scope_type,
                source_scope_id=scope_id,
            )
    return EffectiveManualProcessing(
        enabled=DEFAULT_ENABLED,
        source_level="default",
        source_scope_type=None,
        source_scope_id=None,
    )


def is_scope_type_valid(scope_type: str) -> bool:
    return scope_type in SCOPE_TYPES


# ---------------------------------------------------------------------------
# SUBSCRIPTION ENTITLEMENT (the FIRST gate)
# ---------------------------------------------------------------------------
#
# PO DECISION (ratified business rule): Manual Processing is a SUBSCRIPTION-PLAN
# capability. A customer must subscribe to a plan that includes Manual
# Processing before it can be activated or configured for that customer.
#
# The entitlement is resolved from the EXISTING commercial model — no parallel
# subscription table is created:
#
#   customer_subscriptions (org-scoped, active lifecycle)
#       -> plan_code (+ plan_version)
#           -> billing_plans
#               -> features.manual_processing.enabled   (explicit feature flag)
#                  OR assisted_processing_available     (existing plan column)
#
# ``features.manual_processing`` mirrors the ratified ``features.consultant``
# entitlement-block pattern; ``assisted_processing_available`` is the existing
# D37 plan column whose documented meaning ("CarbonTally automatically
# processes what it can and offers human processing for documents requiring
# additional work") is exactly this capability. When the explicit feature block
# is present it decides outright (so an explicit ``false`` can withhold the
# capability from a plan that is otherwise assisted-capable).
MANUAL_PROCESSING_FEATURE_KEY = "manual_processing"


@dataclass(frozen=True, slots=True)
class ManualProcessingEntitlement:
    """Whether an organisation's ACTIVE subscription plan includes Manual Processing."""

    entitled: bool
    #: ``feature`` (explicit ``features.manual_processing.enabled``),
    #: ``assisted_processing_available`` (existing plan column), ``sponsored``
    #: (consultant-sponsored coverage, CT-MP-SUB-003), ``direct+sponsored`` or
    #: ``none``.
    source: str = "none"
    plan_code: Optional[str] = None
    plan_version: Optional[int] = None
    # -- CT-MP-SUB-003 additive provenance (``None`` for a pure-direct plan) ----
    #: The direct (own-subscription) entitlement component.
    direct_entitled: Optional[bool] = None
    #: The consultant-sponsored entitlement component.
    sponsored_entitled: Optional[bool] = None
    sponsored_firm_id: Optional[str] = None
    sponsored_mode: Optional[str] = None
    sponsored_reason: Optional[str] = None


def entitlement_from_plan(plan: Optional[object]) -> ManualProcessingEntitlement:
    """Resolve the plan-derived Manual Processing entitlement (pure).

    ``None`` plan (no active subscription, or an unknown plan code) means NOT
    entitled — fail closed. Entitlement = *eligibility* only; it never activates
    Manual Processing by itself (see :func:`resolve_routing`).
    """
    if plan is None:
        return ManualProcessingEntitlement(entitled=False, source="none")
    plan_code = getattr(plan, "plan_code", None)
    plan_version = getattr(plan, "version", None)
    features = getattr(plan, "features", None)
    block = (
        features.get(MANUAL_PROCESSING_FEATURE_KEY)
        if isinstance(features, dict)
        else None
    )
    if isinstance(block, dict) and "enabled" in block:
        return ManualProcessingEntitlement(
            entitled=bool(block.get("enabled")),
            source="feature",
            plan_code=plan_code,
            plan_version=plan_version,
        )
    assisted = bool(getattr(plan, "assisted_processing_available", False))
    return ManualProcessingEntitlement(
        entitled=assisted,
        source="assisted_processing_available" if assisted else "none",
        plan_code=plan_code,
        plan_version=plan_version,
    )


# ---------------------------------------------------------------------------
# PROCESSOR CONFIGURATION (the routing destination)
# ---------------------------------------------------------------------------
#
# The configured Processing Entity responsible for Manual Processing work for a
# scope. Reuses the FIN-06 scope vocabulary and the SAME most-specific-wins
# precedence (there is no second scope taxonomy, and no invented hierarchy):
#
#   consultant_client  >  consultant_firm  >  organization


@dataclass(frozen=True, slots=True)
class ManualProcessingProcessor:
    """One configured processor row (``manual_processing_processors``)."""

    scope_type: str
    scope_id: str
    processing_entity_id: str
    active: bool = True
    reason: Optional[str] = None
    set_by: Optional[str] = None
    set_at: Optional[object] = None


def resolve_processor(
    processors: Iterable[ManualProcessingProcessor], context: OrgContext
) -> Optional[ManualProcessingProcessor]:
    """Most-specific-wins resolution of the configured processor.

    Inactive configurations never route. No explicit configuration means there
    is NO destination — the caller must NOT invent one (see
    :func:`resolve_routing`, ``no_processor_configured``).
    """
    by_scope: dict[tuple[str, str], ManualProcessingProcessor] = {
        (p.scope_type, p.scope_id): p for p in processors if p.active
    }
    targets = scope_targets(context)
    for scope_type in SCOPE_PRECEDENCE:
        scope_id = targets.get(scope_type)
        if not scope_id:
            continue
        processor = by_scope.get((scope_type, scope_id))
        if processor is not None:
            return processor
    return None


# ---------------------------------------------------------------------------
# EFFECTIVE ROUTING DECISION
# ---------------------------------------------------------------------------

#: Machine-readable routing outcomes (also used in audit records).
OUTCOME_NOT_ENTITLED = "not_entitled"
OUTCOME_NOT_ENABLED = "not_enabled"
OUTCOME_NO_PROCESSOR = "no_processor_configured"
OUTCOME_ROUTABLE = "routable"


@dataclass(frozen=True, slots=True)
class EffectiveManualProcessingRouting:
    """The complete Manual Processing decision for one organisation context.

    ``effective`` is the authoritative business rule:

        manual_processing_effective = subscription_entitled AND governance_enabled

    A stale/manual governance grant can therefore never bypass the subscription
    requirement, and a subscription alone never activates the capability.
    """

    entitled: bool
    enabled: bool
    effective: bool
    configured: bool
    processing_entity_id: Optional[str] = None
    outcome: str = OUTCOME_NOT_ENTITLED
    entitlement_source: str = "none"
    plan_code: Optional[str] = None
    plan_version: Optional[int] = None
    governance_source_level: str = "default"
    governance_scope_type: Optional[str] = None
    governance_scope_id: Optional[str] = None
    processor_scope_type: Optional[str] = None
    processor_scope_id: Optional[str] = None


def resolve_routing(
    entitlement: ManualProcessingEntitlement,
    governance: EffectiveManualProcessing,
    processor: Optional[ManualProcessingProcessor],
) -> EffectiveManualProcessingRouting:
    """Combine entitlement + governance + processor into one decision (pure)."""
    entitled = bool(entitlement.entitled)
    enabled = bool(governance.enabled)
    effective = entitled and enabled
    configured = processor is not None and bool(processor.active)

    if not entitled:
        outcome = OUTCOME_NOT_ENTITLED
    elif not enabled:
        outcome = OUTCOME_NOT_ENABLED
    elif not configured:
        outcome = OUTCOME_NO_PROCESSOR
    else:
        outcome = OUTCOME_ROUTABLE

    return EffectiveManualProcessingRouting(
        entitled=entitled,
        enabled=enabled,
        effective=effective,
        configured=configured,
        processing_entity_id=(
            processor.processing_entity_id if (effective and configured) else None
        ),
        outcome=outcome,
        entitlement_source=entitlement.source,
        plan_code=entitlement.plan_code,
        plan_version=entitlement.plan_version,
        governance_source_level=governance.source_level,
        governance_scope_type=governance.source_scope_type,
        governance_scope_id=governance.source_scope_id,
        processor_scope_type=processor.scope_type if configured else None,
        processor_scope_id=processor.scope_id if configured else None,
    )


# ---------------------------------------------------------------------------
# CONSULTANT-SPONSORED COVERAGE (CT-MP-SUB-003)
# ---------------------------------------------------------------------------
#
# PO DECISION (CT-PO-MP-SUB-003): Manual Processing may additionally be
# commercially sponsored by a CONSULTANT FIRM for its eligible clients. The
# sponsored entitlement originates from the FIRM's OWN organisation subscription
# (the existing org-scoped D37 commercial model) — no consultant-user billing and
# no parallel subscription system:
#
#   consultant_profiles.organization_id           (the firm's organisation)
#       -> customer_subscriptions (active)         (the firm's subscription)
#           -> billing_plans
#               -> features.consultant_manual_processing = {
#                      enabled: true,
#                      mode: "SELECTED_CLIENTS" | "ALL_ELIGIBLE_CLIENTS",
#                      selected_capacity: <int|null>
#                  }
#
# The consultant-client RELATIONSHIP (``consultant_clients``, status active)
# decides ELIGIBILITY ONLY. Commercial coverage is decided by the purchased
# coverage above. A relationship alone never grants Manual Processing.
COVERAGE_SELECTED_CLIENTS = "SELECTED_CLIENTS"
COVERAGE_ALL_ELIGIBLE_CLIENTS = "ALL_ELIGIBLE_CLIENTS"
COVERAGE_MODES: tuple[str, ...] = (
    COVERAGE_SELECTED_CLIENTS,
    COVERAGE_ALL_ELIGIBLE_CLIENTS,
)

#: The plan feature block that expresses consultant-sponsored Manual Processing.
CONSULTANT_MP_FEATURE_KEY = "consultant_manual_processing"


@dataclass(frozen=True, slots=True)
class ConsultantCoverage:
    """A consultant firm's purchased Manual Processing coverage (plan-derived)."""

    enabled: bool = False
    mode: Optional[str] = None
    selected_capacity: Optional[int] = None
    plan_code: Optional[str] = None
    plan_version: Optional[int] = None


def consultant_coverage_from_plan(plan: Optional[object]) -> ConsultantCoverage:
    """Resolve a firm's consultant-sponsored coverage from its plan (pure).

    ``None`` plan (no firm organisation linkage, no active subscription, or an
    unknown plan code) means NO coverage — fail closed. An unrecognised mode is
    treated as no coverage so a malformed feature block can never silently grant
    all-eligible coverage.
    """
    if plan is None:
        return ConsultantCoverage()
    plan_code = getattr(plan, "plan_code", None)
    plan_version = getattr(plan, "version", None)
    features = getattr(plan, "features", None)
    block = (
        features.get(CONSULTANT_MP_FEATURE_KEY) if isinstance(features, dict) else None
    )
    if not isinstance(block, dict):
        return ConsultantCoverage(plan_code=plan_code, plan_version=plan_version)
    mode = block.get("mode")
    if mode not in COVERAGE_MODES:
        return ConsultantCoverage(plan_code=plan_code, plan_version=plan_version)
    raw_capacity = block.get("selected_capacity")
    capacity: Optional[int]
    try:
        capacity = int(raw_capacity) if raw_capacity is not None else None
    except (TypeError, ValueError):
        capacity = None
    if capacity is not None and capacity < 0:
        capacity = None
    enabled = bool(block.get("enabled", False))
    return ConsultantCoverage(
        enabled=enabled,
        mode=mode if enabled else None,
        selected_capacity=capacity,
        plan_code=plan_code,
        plan_version=plan_version,
    )


@dataclass(frozen=True, slots=True)
class AllocationUsage:
    """Selected-capacity consumption for one firm (pure projection)."""

    mode: Optional[str]
    capacity: Optional[int]
    allocated: int
    available: Optional[int]
    over_allocated: int


def summarize_allocations(coverage: ConsultantCoverage, allocated: int) -> AllocationUsage:
    """Derive allocated/available/over-allocated from a coverage + active count.

    ``ALL_ELIGIBLE_CLIENTS`` has no finite capacity (``available`` is ``None``).
    ``SELECTED_CLIENTS`` with no configured capacity is treated as zero available
    capacity (fail closed) rather than unlimited.
    """
    allocated = max(0, int(allocated))
    if coverage.mode == COVERAGE_ALL_ELIGIBLE_CLIENTS:
        return AllocationUsage(
            mode=coverage.mode, capacity=None, allocated=allocated,
            available=None, over_allocated=0,
        )
    capacity = coverage.selected_capacity
    if capacity is None:
        return AllocationUsage(
            mode=coverage.mode, capacity=None, allocated=allocated,
            available=None, over_allocated=allocated if allocated else 0,
        )
    return AllocationUsage(
        mode=coverage.mode,
        capacity=capacity,
        allocated=allocated,
        available=max(0, capacity - allocated),
        over_allocated=max(0, allocated - capacity),
    )


@dataclass(frozen=True, slots=True)
class ConsultantAllocation:
    """One selected-mode sponsored client allocation (``consultant_mp_allocations``).

    ``state`` is ``active`` (consumes one capacity unit) or ``released`` (the unit
    is returned to the firm's available capacity). Released rows are retained for
    audit; they are never deleted.
    """

    id: str
    consultant_id: str
    consultant_client_id: str
    organization_id: str
    state: str = "active"
    reason: Optional[str] = None
    allocated_by: Optional[str] = None
    allocated_at: Optional[object] = None
    released_by: Optional[str] = None
    released_at: Optional[object] = None
    updated_at: Optional[object] = None


@dataclass(frozen=True, slots=True)
class ConsultantEntitlement:
    """The consultant-sponsored entitlement component for one client org."""

    entitled: bool = False
    firm_id: Optional[str] = None
    mode: Optional[str] = None
    selected_capacity: Optional[int] = None
    plan_code: Optional[str] = None
    plan_version: Optional[int] = None
    #: ``all_eligible`` | ``selected_allocated`` | ``not_allocated`` |
    #: ``no_coverage`` | ``no_relationship``.
    reason: str = "no_relationship"
    allocated: int = 0
    available: Optional[int] = None
    over_allocated: int = 0


def sponsored_entitlement(
    *,
    firm_id: Optional[str],
    has_relationship: bool,
    coverage: ConsultantCoverage,
    allocation_active: bool,
    allocated_count: int,
) -> ConsultantEntitlement:
    """Decide the sponsored entitlement for one eligible client (pure).

    Deterministic: a relationship is required for eligibility; purchased coverage
    is required for commercial entitlement; ``SELECTED_CLIENTS`` additionally
    requires an ACTIVE allocation for the client.
    """
    if not has_relationship or firm_id is None:
        return ConsultantEntitlement(
            entitled=False, firm_id=firm_id, reason="no_relationship"
        )
    usage = summarize_allocations(coverage, allocated_count)
    base = dict(
        firm_id=firm_id,
        mode=coverage.mode,
        selected_capacity=coverage.selected_capacity,
        plan_code=coverage.plan_code,
        plan_version=coverage.plan_version,
        allocated=usage.allocated,
        available=usage.available,
        over_allocated=usage.over_allocated,
    )
    if not coverage.enabled:
        return ConsultantEntitlement(entitled=False, reason="no_coverage", **base)
    if coverage.mode == COVERAGE_ALL_ELIGIBLE_CLIENTS:
        return ConsultantEntitlement(entitled=True, reason="all_eligible", **base)
    if allocation_active:
        return ConsultantEntitlement(entitled=True, reason="selected_allocated", **base)
    return ConsultantEntitlement(entitled=False, reason="not_allocated", **base)


def combine_entitlement(
    direct: ManualProcessingEntitlement,
    sponsored: Optional[ConsultantEntitlement],
) -> ManualProcessingEntitlement:
    """The effective entitlement: DIRECT **OR** SPONSORED (CT-MP-SUB-003 §11).

    Both commercial facts are preserved on the result for audit/billing; the
    operationally-effective answer is the OR of the two, so a client with both
    paths still yields ONE operational Manual Processing service.
    """
    direct_on = bool(direct.entitled)
    sponsored_on = bool(sponsored is not None and sponsored.entitled)
    if direct_on and sponsored_on:
        source = "direct+sponsored"
    elif direct_on:
        source = direct.source
    elif sponsored_on:
        source = "sponsored"
    else:
        source = "none"
    return ManualProcessingEntitlement(
        entitled=direct_on or sponsored_on,
        source=source,
        plan_code=direct.plan_code,
        plan_version=direct.plan_version,
        direct_entitled=direct_on,
        sponsored_entitled=sponsored_on,
        sponsored_firm_id=(sponsored.firm_id if sponsored is not None else None),
        sponsored_mode=(sponsored.mode if sponsored is not None else None),
        sponsored_reason=(sponsored.reason if sponsored is not None else None),
    )


