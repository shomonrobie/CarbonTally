"""CarbonTally core package — shared kernel for the Business Processing Engine.

Contains the shared error hierarchy (``exceptions``), canonical primitive
types (``types``) and logging configuration (``logging``). The core layer has
**zero external dependencies** and imports nothing except the Python standard
library, so it is safe to import from any other layer.
"""

from .exceptions import (
    AIExtractionFailedError,
    BenchmarkDataInsufficientError,
    CarbonTallyError,
    ExtractionFailedError,
    FactorAmbiguousError,
    FactorNotFoundError,
    ImportValidationError,
    ReportGenerationFailedError,
    UnitMismatchError,
    UnknownProviderError,
    ValidationFailedError,
    WorkflowInvalidTransitionError,
    WorkflowMaxRetriesError,
)
from .logging import configure_logging, get_logger
from .types import Country, DateRange, ReportingYear, Scope, Unit

__all__ = [
    "AIExtractionFailedError",
    "BenchmarkDataInsufficientError",
    "CarbonTallyError",
    "Country",
    "DateRange",
    "ExtractionFailedError",
    "FactorAmbiguousError",
    "FactorNotFoundError",
    "ImportValidationError",
    "ReportingYear",
    "ReportGenerationFailedError",
    "Scope",
    "Unit",
    "UnitMismatchError",
    "UnknownProviderError",
    "ValidationFailedError",
    "WorkflowInvalidTransitionError",
    "WorkflowMaxRetriesError",
    "configure_logging",
    "get_logger",
]
