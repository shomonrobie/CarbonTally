"""Composition root for the v2.1 API (prep-pack §4.1, Phase 10.1).

The single place that wires the existing repositories, engines, infrastructure
singletons and the request/audit context for the API layer. The API never
reconstructs engines or repositories inline — it consumes these dependencies.

Design decisions (all aligned with the existing architecture):

* **Authentication is reused, not reinvented.** ``backend/auth.py`` (JWT +
  Supabase roles/permissions) is the existing authentication system; this
  module re-exports ``get_current_user`` and ``require_admin`` rather than
  implementing a second one.
* **Repositories are new instances per request** over the service-role pool
  (prep-pack §4.1). The pool itself is the ``infra.supabase`` singleton.
* **Engines are new instances per request** (stateless, CT-ARCH-009).
* **Infrastructure singletons** (event bus, audit logger, search index) match
  the prep-pack §4.3 process-singleton scope.
* **No database access happens at import time** — the pool is created lazily,
  so importing this module is side-effect free (database safety).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

# --- existing authentication/RBAC (backend/auth.py) — reused, not duplicated --
from auth import (
    AuthUser,
    get_current_user,
    require_admin,
    require_entity_member,  # noqa: F401 — V3 entity-scoped guard
    require_org_admin,  # noqa: F401 — V3 customer-factor approval (D-cf-3)
    require_org_member,  # noqa: F401 — V3 org-isolated surfaces
)

from core.logging import get_logger
from data.audit import AuditRepository
from data.customer_factors import CustomerFactorsRepository
from data.documents import DocumentsRepository
from data.emission_factors import EmissionFactorsRepository
from data.emissions_logs import EmissionsLogsRepository
from data.events import EventsRepository
from data.factor_aliases import FactorAliasesRepository
from data.imports import ImportsRepository
from data.invitations import InvitationsRepository
from data.issues import IssuesRepository
from data.organizations import OrganizationsRepository
from data.processing_entities import ProcessingEntitiesRepository
from data.reports import ReportsRepository
from data.report_versions import ReportVersionsRepository
from data.exports import ExportsRepository
from data.notifications import NotificationsRepository
from data.organization_files import OrganizationFilesRepository
from data.queue_settings import QueueSettingsRepository
from data.review_queue import ReviewQueueRepository
from data.roles import RolesRepository
from data.search import SearchRepository
from data.settings import SettingsRepository
from data.tenant import TenantRepository
from data.upload_batches import UploadBatchesRepository
from data.verifications import VerificationsRepository
from data.consultants import ConsultantsRepository
from data.billing import (
    BillingCommercialConfigRepository,
    BillingCreditLedgerRepository,
    BillingOrdersRepository,
    BillingPlansRepository,
    IdempotencyRepository,
    PaymentRecordsRepository,
    StorageUsageRepository,
    SubscriptionsRepository,
    UsageTrackingRepository,
)
from data.discovery import DiscoveryRepository
from data.messaging import MessagingRepository
from data.whitelabel import WhiteLabelRepository
from data.manual_extraction import ManualExtractionRepository
from data.staff import StaffRepository
from data.suppliers import SuppliersRepository
from data.reporting import ReportingRepository
from domain.matching import MatchingPipelineConfig
from engines.benchmarking import BenchmarkingEngine
from engines.calculation import CalculationEngine
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from engines.matching_stages import RepositoryAliasResolver
from engines.report_generation import ReportGenerationEngine
from engines.validation import ValidationEngine
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus
from infra.search_index import FactorSearchIndex
from infra.supabase import get_service_pool

logger = get_logger(__name__)


# ===========================================================================
# Request / audit context
# ===========================================================================


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Structured per-request context attached by the middleware."""

    correlation_id: str
    client_ip: str = ""
    started_at: str = ""
    user_id: str = ""
    actor: str = ""


@dataclass(frozen=True, slots=True)
class AuditContext:
    """Audit-relevant context for one request (correlation id, actor, ip)."""

    correlation_id: str
    actor: str
    ip_address: str = ""


def get_request_context(request: Request) -> RequestContext:
    """Return the middleware-attached request context."""
    context = getattr(request.state, "request_context", None)
    if context is not None:
        return context
    return RequestContext(correlation_id="", client_ip="")


async def get_audit_context(
    request: Request,
    current_user: AuthUser = Depends(get_current_user),
) -> AuditContext:
    """Build the audit context reused by admin write endpoints.

    ``current_user`` is a FastAPI dependency (never a body param), so this
    dependency never changes the route's body embedding.
    """
    context = get_request_context(request)
    return AuditContext(
        correlation_id=context.correlation_id,
        actor=current_user.user_id,
        ip_address=context.client_ip,
    )


def ensure_org_access(current_user: AuthUser, organization_id: str) -> None:
    """Enforce organisation isolation on business endpoints (scope-aware, D20).

    * CarbonTally INTERNAL staff (``entity_id IS NULL``) may act on any
      organisation (operational access — preserved).
    * Processing Entity staff (``entity_id IS NOT NULL``) NEVER receive
      customer-organisation access (work-scoped only).
    * Organisation members may only act on their own organisation.
    * Any other user (no org membership, not internal staff) is denied.
    """
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is required",
        )
    # D20: Processing Entity staff must not gain Customer Organisation access
    # simply because they are staff.
    if current_user.is_entity_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Processing Entity staff cannot access customer organisations",
        )
    # CarbonTally internal staff keep the operational any-org bypass.
    if current_user.is_internal_staff:
        return
    bound_org = getattr(current_user, "organization_id", None)
    if not bound_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization access denied",
        )
    if bound_org != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization access denied",
        )


async def ensure_processing_org_access(
    current_user: AuthUser,
    repos: "RepositoryBundle",
    organization_id: str,
) -> None:
    """Authorize the caller for the organisation-scoped PROCESSING workflow.

    PO Decision 3 — a consultant firm operates its own customers: an org member
    passes (as today); a consultant with an ACTIVE ``consultant_clients`` grant
    for ``organization_id`` also passes. Cross-firm and unrelated-customer
    isolation is unchanged — the grant is resolved server-side and re-checked on
    every request. Processing Entity staff and everyone else stay denied.
    """
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is required",
        )
    if current_user.is_entity_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Processing Entity staff cannot access customer organisations",
        )
    if current_user.is_internal_staff:
        return
    if current_user.is_org_member:
        ensure_org_access(current_user, organization_id)
        return
    # Consultant path (active grant) — same isolation boundary as RLS.
    from api.consultant_auth import ensure_consultant_org_access

    try:
        await ensure_consultant_org_access(current_user, repos, organization_id)
        return
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization member or authorized consultant access required",
        )


# ===========================================================================
# Repository bundle (per-request, prep-pack §4.1)
# ===========================================================================


@dataclass
class RepositoryBundle:
    """Every repository the API consumes, bound to the service-role pool."""

    factors: EmissionFactorsRepository
    logs: EmissionsLogsRepository
    organizations: OrganizationsRepository
    imports: ImportsRepository
    invitations: InvitationsRepository
    reports: ReportsRepository
    report_versions: ReportVersionsRepository
    audit: AuditRepository
    events: EventsRepository
    aliases: FactorAliasesRepository
    customer_factors: CustomerFactorsRepository
    entities: ProcessingEntitiesRepository
    issues: IssuesRepository
    tenant: TenantRepository
    files: OrganizationFilesRepository
    batches: UploadBatchesRepository
    review_queue: ReviewQueueRepository
    queue_settings: QueueSettingsRepository
    settings: SettingsRepository
    search: SearchRepository
    roles: RolesRepository
    verifications: VerificationsRepository
    notifications: NotificationsRepository
    exports: ExportsRepository
    consultants: ConsultantsRepository
    discovery: DiscoveryRepository
    messaging: MessagingRepository
    whitelabel: WhiteLabelRepository
    manual_extraction: ManualExtractionRepository
    suppliers: SuppliersRepository
    staff: StaffRepository
    reporting: ReportingRepository
    billing_plans: BillingPlansRepository
    billing_config: BillingCommercialConfigRepository
    billing_ledger: BillingCreditLedgerRepository
    billing_subscriptions: SubscriptionsRepository
    billing_orders: BillingOrdersRepository
    billing_storage: StorageUsageRepository
    billing_payments: PaymentRecordsRepository
    billing_idempotency: IdempotencyRepository
    billing_usage: UsageTrackingRepository


async def get_pool():
    """The process-wide service-role asyncpg pool (lazy singleton)."""
    return await get_service_pool()


async def get_repositories() -> RepositoryBundle:
    """Per-request repository bundle (stateless repositories, §4.1)."""
    pool = await get_pool()
    return RepositoryBundle(
        factors=EmissionFactorsRepository(pool),
        logs=EmissionsLogsRepository(pool),
        organizations=OrganizationsRepository(pool),
        imports=ImportsRepository(pool),
        invitations=InvitationsRepository(pool),
        reports=ReportsRepository(pool),
        report_versions=ReportVersionsRepository(pool),
        audit=AuditRepository(pool),
        events=EventsRepository(pool),
        aliases=FactorAliasesRepository(pool),
        customer_factors=CustomerFactorsRepository(pool),
        entities=ProcessingEntitiesRepository(pool),
        issues=IssuesRepository(pool),
        tenant=TenantRepository(pool),
        files=OrganizationFilesRepository(pool),
        batches=UploadBatchesRepository(pool),
        review_queue=ReviewQueueRepository(pool),
        queue_settings=QueueSettingsRepository(pool),
        settings=SettingsRepository(pool),
        search=SearchRepository(pool),
        roles=RolesRepository(pool),
        verifications=VerificationsRepository(pool),
        notifications=NotificationsRepository(pool),
        exports=ExportsRepository(pool),
        consultants=ConsultantsRepository(pool),
        discovery=DiscoveryRepository(pool),
        messaging=MessagingRepository(pool),
        whitelabel=WhiteLabelRepository(pool),
        manual_extraction=ManualExtractionRepository(pool),
        suppliers=SuppliersRepository(pool),
        staff=StaffRepository(pool),
        reporting=ReportingRepository(pool),
        billing_plans=BillingPlansRepository(pool),
        billing_config=BillingCommercialConfigRepository(pool),
        billing_ledger=BillingCreditLedgerRepository(pool),
        billing_subscriptions=SubscriptionsRepository(pool),
        billing_orders=BillingOrdersRepository(pool),
        billing_storage=StorageUsageRepository(pool),
        billing_payments=PaymentRecordsRepository(pool),
        billing_idempotency=IdempotencyRepository(pool),
        billing_usage=UsageTrackingRepository(pool),
    )


async def get_aliases_repository(
    repos: RepositoryBundle = Depends(get_repositories),
) -> FactorAliasesRepository:
    """The alias repository on its own (alias-resolver + alias endpoints).

    Declared as a FastAPI dependency on the repository bundle so test suites can
    override ``get_repositories`` without the alias resolver leaking to the
    production pool.
    """
    return repos.aliases


# ===========================================================================
# Infrastructure singletons (prep-pack §4.3)
# ===========================================================================

_audit_logger: Optional[AuditLogger] = None
_event_bus: Optional[EventBus] = None
_search_index: Optional[FactorSearchIndex] = None


async def get_audit_logger() -> AuditLogger:
    """The process-wide :class:`infra.audit_logger.AuditLogger` singleton."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(AuditRepository(await get_pool()))
    return _audit_logger


async def get_event_bus() -> EventBus:
    """The process-wide :class:`infra.event_bus.EventBus` singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def get_factor_search_index() -> FactorSearchIndex:
    """The process-wide factor search index, loaded lazily from the repository.

    Loaded once from ``EmissionFactorsRepository.load_all_for_index()`` and
    reused across requests (prep-pack §4.3: loaded at startup, rebuilt on import
    events). Importing this module never touches the database; the load happens
    on first dependency resolution only.
    """
    global _search_index
    if _search_index is None:
        index = FactorSearchIndex()
        factors = await EmissionFactorsRepository(await get_pool()).load_all_for_index()
        index.load(factors)
        _search_index = index
    return _search_index


# ===========================================================================
# Engine factories (new instance per request, CT-ARCH-009)
# ===========================================================================


async def get_matching_engine(
    repos: RepositoryBundle = Depends(get_repositories),
    index: FactorSearchIndex = Depends(get_factor_search_index),
    aliases: FactorAliasesRepository = Depends(get_aliases_repository),
    event_bus: EventBus = Depends(get_event_bus),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> FactorMatchingEngine:
    """Per-request :class:`FactorMatchingEngine` over the search index.

    The engine is wired with the customer-factor lookup (D-cf-5): approved
    customer factors are resolved ahead of the CarbonTally pipeline when the
    request carries an ``organization_id``.
    """
    config = MatchingPipelineConfig()
    resolver: Optional[RepositoryAliasResolver] = RepositoryAliasResolver(aliases)
    stages = build_matching_pipeline(config, alias_resolver=resolver)
    return FactorMatchingEngine(
        index,
        stages,
        config=config,
        event_bus=event_bus,
        audit_logger=audit_logger,
        customer_factor_lookup=repos.customer_factors,
    )


async def get_calculation_engine(
    repos: RepositoryBundle = Depends(get_repositories),
    event_bus: EventBus = Depends(get_event_bus),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> CalculationEngine:
    """Per-request :class:`CalculationEngine` (``EmissionsLogsRepository`` sink)."""
    return CalculationEngine(
        repos.logs,
        event_bus=event_bus,
        audit_logger=audit_logger,
    )


async def get_validation_engine(
    repos: RepositoryBundle = Depends(get_repositories),
    event_bus: EventBus = Depends(get_event_bus),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> ValidationEngine:
    """Per-request :class:`ValidationEngine`."""
    return ValidationEngine(
        repos.logs,
        repos.organizations,
        repos.factors,
        event_bus=event_bus,
        audit_logger=audit_logger,
    )


async def get_benchmarking_engine(
    repos: RepositoryBundle = Depends(get_repositories),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> BenchmarkingEngine:
    """Per-request :class:`BenchmarkingEngine` (internal benchmarks, Phase 9B)."""
    return BenchmarkingEngine(
        repos.logs,
        repos.organizations,
        factor_lookup=repos.factors,
        audit_logger=audit_logger,
    )


async def get_report_engine(
    repos: RepositoryBundle = Depends(get_repositories),
    event_bus: EventBus = Depends(get_event_bus),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> ReportGenerationEngine:
    """Per-request :class:`ReportGenerationEngine` with injected sub-engines."""
    calculation_engine = CalculationEngine(
        repos.logs,
        event_bus=event_bus,
        audit_logger=audit_logger,
    )
    validation_engine = ValidationEngine(
        repos.logs,
        repos.organizations,
        repos.factors,
        event_bus=event_bus,
        audit_logger=audit_logger,
    )
    benchmarking_engine = BenchmarkingEngine(
        repos.logs,
        repos.organizations,
        factor_lookup=repos.factors,
        audit_logger=audit_logger,
    )
    return ReportGenerationEngine(
        repos.reports,
        repos.organizations,
        repos.logs,
        factor_lookup=repos.factors,
        validation_engine=validation_engine,
        benchmarking_engine=benchmarking_engine,
        calculation_engine=calculation_engine,
        event_bus=event_bus,
        audit_logger=audit_logger,
    )
