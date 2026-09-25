"""CarbonTally domain layer (Backend v2.1 §9, ADR-10).

Pure Python. No framework, database, API or Supabase imports — every object is
an immutable frozen dataclass and every contract is expressed here so the
engine and infrastructure layers implement against this package.
"""

from .audit import AuditEntry, AuditQuery, AuditTrail
from .benchmarking import (
    BenchmarkAvailability,
    BenchmarkMetric,
    BenchmarkRequest,
    BenchmarkResult,
)
from .calculation import (
    CalculationMethodology,
    CalculationResult,
    CalculationSnapshot,
    EmissionLog,
    EmissionsAggregate,
    VerificationResult,
)
from .customer_factor import (
    CUSTOMER_FACTOR_COUNTRIES,
    CUSTOMER_FACTOR_SOURCE,
    CUSTOMER_FACTOR_STATUSES,
    CustomerFactor,
)
from .document import (
    Document,
    ExtractionField,
    ExtractionResult,
    ExtractedPage,
    ExtractedTable,
)
from .entity import ENTITY_STATUSES, ProcessingEntity
from .factor import EmissionFactor, FactorSet, FactorSetMetadata
from .issue import (
    ISSUE_SEVERITIES,
    ISSUE_STATUSES,
    ISSUE_TYPES,
    Issue,
)
from .matching import (
    FactorAlias,
    FactorSearch,
    MatchRequest,
    MatchResult,
    MatchingPipelineConfig,
    MatchingStage,
    StageResult,
    Suggestion,
)
from .organization import Asset, Facility, Organization, OrganizationMember, OrganizationMetadata
from .provider import (
    DiscoveredSheet,
    DiscoveryResult,
    ImportBatch,
    ImportError,
    ImportResult,
    NormalisedFactor,
    ProviderInfo,
    ProviderVersion,
    RawFactorRow,
)
from .report import GeneratedReport, ReportRequest, ReportSection, ReportTemplate
from .validation import ValidationIssue, ValidationReport, ValidationRequest, ValidationSeverity
from .workflow import (
    DOCUMENT_PIPELINE,
    CalculationCompleted,
    CalculationRequested,
    DocumentUploaded,
    DomainEvent,
    ExtractionCompleted,
    ExtractionRequested,
    FactorMatched,
    FactorNotFound,
    FieldsExtracted,
    ImportCompleted,
    ImportRolledBack,
    ImportStarted,
    ReportGenerated,
    Saga,
    SagaStep,
    Transition,
    ValidationFailed,
    WorkflowDefinition,
    WorkflowStateChanged,
)

__all__ = [
    "AuditEntry",
    "AuditQuery",
    "AuditTrail",
    "Asset",
    "BenchmarkAvailability",
    "BenchmarkMetric",
    "BenchmarkRequest",
    "BenchmarkResult",
    "CUSTOMER_FACTOR_COUNTRIES",
    "CUSTOMER_FACTOR_SOURCE",
    "CUSTOMER_FACTOR_STATUSES",
    "CalculationCompleted",
    "CalculationMethodology",
    "CalculationRequested",
    "CalculationResult",
    "CalculationSnapshot",
    "CustomerFactor",
    "DOCUMENT_PIPELINE",
    "DiscoveredSheet",
    "DiscoveryResult",
    "Document",
    "DocumentUploaded",
    "DomainEvent",
    "ENTITY_STATUSES",
    "EmissionFactor",
    "EmissionLog",
    "EmissionsAggregate",
    "ExtractionCompleted",
    "ExtractionField",
    "ExtractionRequested",
    "ExtractionResult",
    "ExtractedPage",
    "ExtractedTable",
    "FactorAlias",
    "FactorMatched",
    "FactorNotFound",
    "FactorSearch",
    "FactorSet",
    "FactorSetMetadata",
    "FieldsExtracted",
    "Facility",
    "GeneratedReport",
    "ISSUE_SEVERITIES",
    "ISSUE_STATUSES",
    "ISSUE_TYPES",
    "ImportBatch",
    "ImportCompleted",
    "ImportError",
    "ImportResult",
    "ImportRolledBack",
    "ImportStarted",
    "Issue",
    "MatchRequest",
    "MatchResult",
    "MatchingPipelineConfig",
    "MatchingStage",
    "NormalisedFactor",
    "Organization",
    "OrganizationMember",
    "OrganizationMetadata",
    "ProcessingEntity",
    "ProviderInfo",
    "ProviderVersion",
    "RawFactorRow",
    "ReportGenerated",
    "ReportRequest",
    "ReportSection",
    "ReportTemplate",
    "Saga",
    "SagaStep",
    "StageResult",
    "Suggestion",
    "Transition",
    "ValidationFailed",
    "ValidationIssue",
    "ValidationReport",
    "ValidationRequest",
    "ValidationSeverity",
    "VerificationResult",
    "WorkflowDefinition",
    "WorkflowStateChanged",
]

# ===========================================================================
# P17 unified Carbon Accounting Management System (CAMS).
#
# Appended additively so the existing export surface is unchanged: every P17
# domain object is re-exported here under the package's established convention,
# and no pre-existing name is removed, renamed or reordered.
# ===========================================================================
from .acting_for import (  # noqa: E402
    ActingForContext,
    ActingForKind,
    Entitlement,
    EntitlementBasis,
    resolve_acting_for,
)
from .cams import (  # noqa: E402
    AccountingDimensions,
    CamsContext,
    CamsPersona,
    describe_dimensions,
    resolve_accounting_dimensions,
)
from .contractual_instruments import (  # noqa: E402
    ContractualInstrument,
    InstrumentAllocation,
    InstrumentType,
    RetirementStatus,
    assert_allocation_within_quantity,
    remaining_quantity,
)
from .data_quality import (  # noqa: E402
    DATA_QUALITY_VALUES,
    DataQuality,
    describe_data_quality,
    is_estimated,
)
from .estimation import (  # noqa: E402
    EstimationMethod,
    EstimationRecord,
    requires_estimation_record,
)
from .scope2 import (  # noqa: E402
    ENERGY_TYPES,
    SCOPE2_METHODS,
    EnergyType,
    Scope2Method,
    instrument_is_eligible,
    requires_instrument,
)
from .scope3 import (  # noqa: E402
    CATEGORY_STATUS,
    DEFERRED_CATEGORIES,
    NOT_IMPLEMENTED_CATEGORIES,
    PARTIAL_CATEGORIES,
    SUPPORTED_CATEGORIES,
    SCOPE3_CATEGORIES,
    Scope3Category,
    Scope3Status,
    TransportBoundary,
    WasteOrigin,
    assert_boundary_complete,
    assert_calculable,
    is_calculable,
)

__all__ += [
    "AccountingDimensions",
    "ActingForContext",
    "ActingForKind",
    "CATEGORY_STATUS",
    "CamsContext",
    "CamsPersona",
    "ContractualInstrument",
    "DATA_QUALITY_VALUES",
    "DEFERRED_CATEGORIES",
    "DataQuality",
    "ENERGY_TYPES",
    "EnergyType",
    "Entitlement",
    "EntitlementBasis",
    "EstimationMethod",
    "EstimationRecord",
    "InstrumentAllocation",
    "InstrumentType",
    "NOT_IMPLEMENTED_CATEGORIES",
    "PARTIAL_CATEGORIES",
    "RetirementStatus",
    "SCOPE2_METHODS",
    "SCOPE3_CATEGORIES",
    "SUPPORTED_CATEGORIES",
    "Scope2Method",
    "Scope3Category",
    "Scope3Status",
    "TransportBoundary",
    "WasteOrigin",
    "assert_allocation_within_quantity",
    "assert_boundary_complete",
    "assert_calculable",
    "describe_data_quality",
    "describe_dimensions",
    "instrument_is_eligible",
    "is_calculable",
    "is_estimated",
    "remaining_quantity",
    "requires_estimation_record",
    "requires_instrument",
    "resolve_accounting_dimensions",
    "resolve_acting_for",
]
