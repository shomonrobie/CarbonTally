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


class UnknownProviderError(CarbonTallyError):
    """Raised when an emission-factor provider key is not registered (404)."""

    code: ClassVar[str] = "UNKNOWN_PROVIDER"
    http_status: ClassVar[int] = 404
