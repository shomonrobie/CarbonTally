"""CarbonTally error hierarchy (Backend v2.1 §11.1 Error Handling).

Every engine raises a subclass of :class:`CarbonTallyError`. The HTTP status
and machine-readable ``code`` are declared as class variables so the API layer
(Phase 10) can translate any engine failure into a consistent response without
knowing the concrete error type.
"""
from __future__ import annotations

from typing import Any, ClassVar, Optional


class CarbonTallyError(Exception):
    """Base exception for all CarbonTally errors.

    Attributes:
        code: Machine-readable error code (stable across releases).
        http_status: HTTP status the API layer should return for this error.
        message: Human-readable message.
        details: Optional structured error details (JSON-serialisable).
    """

    code: ClassVar[str] = "CARBON_TALLY_ERROR"
    http_status: ClassVar[int] = 500
    message: str
    details: dict[str, Any]

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details if details is not None else {}


class FactorNotFoundError(CarbonTallyError):
    """Raised when no emission factor matches the request (404)."""

    code: ClassVar[str] = "FACTOR_NOT_FOUND"
    http_status: ClassVar[int] = 404


class FactorAmbiguousError(CarbonTallyError):
    """Raised when multiple factors could match; alternatives are returned (409)."""

    code: ClassVar[str] = "FACTOR_AMBIGUOUS"
    http_status: ClassVar[int] = 409


class ExtractionFailedError(CarbonTallyError):
    """Raised when PDF/OCR extraction yields no usable content (422)."""

    code: ClassVar[str] = "EXTRACTION_FAILED"
    http_status: ClassVar[int] = 422


class AIExtractionFailedError(CarbonTallyError):
    """Raised when the AI field-extraction step fails (e.g. LLM API error, 502)."""

    code: ClassVar[str] = "AI_EXTRACTION_FAILED"
    http_status: ClassVar[int] = 502


class ImportValidationError(CarbonTallyError):
    """Raised when an import payload fails validation before loading (422)."""

    code: ClassVar[str] = "IMPORT_VALIDATION_FAILED"
    http_status: ClassVar[int] = 422


class ReportGenerationFailedError(CarbonTallyError):
    """Raised when a report cannot be generated (500)."""

    code: ClassVar[str] = "REPORT_GENERATION_FAILED"
    http_status: ClassVar[int] = 500


class WorkflowInvalidTransitionError(CarbonTallyError):
    """Raised when a workflow transition is not permitted (409)."""

    code: ClassVar[str] = "WORKFLOW_TRANSITION_INVALID"
    http_status: ClassVar[int] = 409


class WorkflowMaxRetriesError(CarbonTallyError):
    """Raised when a workflow has exhausted its retry allowance (429)."""

    code: ClassVar[str] = "WORKFLOW_MAX_RETRIES"
    http_status: ClassVar[int] = 429


class ValidationFailedError(CarbonTallyError):
    """Raised when data-quality checks find blocking errors (422)."""

    code: ClassVar[str] = "VALIDATION_FAILED"
    http_status: ClassVar[int] = 422


class BenchmarkDataInsufficientError(CarbonTallyError):
    """Raised when there is not enough peer data for a benchmark (404)."""

    code: ClassVar[str] = "BENCHMARK_DATA_INSUFFICIENT"
    http_status: ClassVar[int] = 404


class UnitMismatchError(CarbonTallyError):
    """Raised when a consumption unit does not match the factor unit (422)."""

    code: ClassVar[str] = "UNIT_MISMATCH"
    http_status: ClassVar[int] = 422


class DuplicateMembershipError(CarbonTallyError):
    """Raised when an organisation membership already exists (409).

    BL-1 (QA-DB-024) — the real V3 schema enforces membership uniqueness via
    the ``organization_members_org_user_uniq`` unique index; an unguarded
    second ``INSERT`` for the same (organisation, user) would otherwise surface
    as a raw 500. This error translates that invariant into a controlled 409
    conflict response without changing roles or membership semantics.
    """

    code: ClassVar[str] = "DUPLICATE_MEMBERSHIP"
    http_status: ClassVar[int] = 409


class UnknownProviderError(CarbonTallyError):
    """Raised when an emission-factor provider key is not registered (404)."""

    code: ClassVar[str] = "UNKNOWN_PROVIDER"
    http_status: ClassVar[int] = 404


# ===========================================================================
# P17 unified Carbon Accounting Management System (CAMS)
#
# The P17 accounting dimensions are accounting CLAIMS, not formatting choices.
# A Scope 2 result without a recorded method, a Scope 3 result without a
# category, an ambiguous transport/waste boundary or an unsubstantiated
# estimate is not merely incomplete - it is a number that cannot be defended.
# Each error below therefore fails closed at 422 (or 409 where the failure is a
# conflict with already-persisted accounting), and the API layer translates it
# through the existing CarbonTallyError envelope with no special casing.
# ===========================================================================


class AccountingDimensionError(CarbonTallyError):
    """Raised when an accounting dimension is missing or invalid for new writes (422).

    Historical P16 rows legitimately carry no category or method; that is why
    the database enforces the requirement with ``NOT VALID`` constraints. This
    error applies to NEW accounting claims only.
    """

    code: ClassVar[str] = "ACCOUNTING_DIMENSION_INVALID"
    http_status: ClassVar[int] = 422


class Scope2MethodRequiredError(CarbonTallyError):
    """Raised when a Scope 2 result has no recorded accounting method (422)."""

    code: ClassVar[str] = "SCOPE2_METHOD_REQUIRED"
    http_status: ClassVar[int] = 422


class Scope3CategoryRequiredError(CarbonTallyError):
    """Raised when a Scope 3 result has no recorded category (422)."""

    code: ClassVar[str] = "SCOPE3_CATEGORY_REQUIRED"
    http_status: ClassVar[int] = 422


class Scope3CategoryNotSupportedError(CarbonTallyError):
    """Raised when a category whose architecture status is NOT_IMPLEMENTED or
    DEFERRED is asked to calculate (422).

    The category taxonomy exists so the boundary is explicit; it does not imply
    that a methodology exists. Refusing loudly is the correct behaviour: an
    invented methodology would be a fabricated accounting claim.
    """

    code: ClassVar[str] = "SCOPE3_CATEGORY_NOT_SUPPORTED"
    http_status: ClassVar[int] = 422


class Scope3MethodNotSupportedError(CarbonTallyError):
    """Raised when a Scope 3 category methodology is not permitted for that
    category by its contract (422).

    P17-PRODUCT-01 §29 requires the reporting layer to state the methodology a
    category used, and §34 lists category-specific methodology as a must-have.
    A method outside the category's own contract vocabulary is refused rather
    than stored: recording a methodology the contract does not recognise would be
    an invented accounting claim, and silently substituting another method would
    be a silent methodology fallback.
    """

    code: ClassVar[str] = "SCOPE3_METHOD_NOT_SUPPORTED"
    http_status: ClassVar[int] = 422


class BoundaryAmbiguityError(CarbonTallyError):
    """Raised when a category boundary (transport, waste, consolidation) is
    ambiguous and the result must not be counted (422).

    DC-04 (category 4 vs 9), DC-05 (category 5 vs 12) and DC-07 (categories 8/13
    without a consolidation approach) all fail closed rather than guessing.
    """

    code: ClassVar[str] = "BOUNDARY_AMBIGUITY"
    http_status: ClassVar[int] = 422


class InstrumentEligibilityError(CarbonTallyError):
    """Raised when a contractual instrument may not back a market-based result (422)."""

    code: ClassVar[str] = "INSTRUMENT_NOT_ELIGIBLE"
    http_status: ClassVar[int] = 422


class InstrumentOverAllocatedError(CarbonTallyError):
    """Raised when allocations would exceed the instrument quantity (409).

    DC-09. The sum-versus-quantity rule cannot be a single-row CHECK, so this is
    enforced by the allocating service plus the ``p17_instrument_over_allocated``
    detector; it surfaces as a conflict because it collides with already
    persisted allocations rather than being malformed input.
    """

    code: ClassVar[str] = "INSTRUMENT_OVER_ALLOCATED"
    http_status: ClassVar[int] = 409


class EstimationRecordRequiredError(CarbonTallyError):
    """Raised when an estimated result has no persisted estimation record (422).

    T-INV-12 / no-silent-estimation. An "estimated" flag without method, inputs
    or assumptions is not auditable and is refused.
    """

    code: ClassVar[str] = "ESTIMATION_RECORD_REQUIRED"
    http_status: ClassVar[int] = 422


class ActingForError(CarbonTallyError):
    """Raised when an acting-for context is requested that the actor may not assume (403).

    ACTING FOR is operational context, never an authorization boundary
    (POST-ARCH §35; UIUX-01 §6, §44). This error exists precisely to keep it that
    way: the actor must already be entitled to the target organization through
    membership or an active delegation, and acting-for adds context on top of
    that entitlement rather than substituting for it.
    """

    code: ClassVar[str] = "ACTING_FOR_DENIED"
    http_status: ClassVar[int] = 403
