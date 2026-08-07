"""Unit tests for core.exceptions, core.types and core.logging."""
from __future__ import annotations

import logging
from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from core import configure_logging, get_logger
from core.exceptions import (
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
from core.types import Country, DateRange, Scope, Unit, ReportingYear


class TestErrorHierarchy:
    """Every error carries its frozen code + http_status and stores details."""

    @pytest.mark.parametrize(
        ("error_cls", "code", "status"),
        [
            (FactorNotFoundError, "FACTOR_NOT_FOUND", 404),
            (FactorAmbiguousError, "FACTOR_AMBIGUOUS", 409),
            (ExtractionFailedError, "EXTRACTION_FAILED", 422),
            (AIExtractionFailedError, "AI_EXTRACTION_FAILED", 502),
            (ImportValidationError, "IMPORT_VALIDATION_FAILED", 422),
            (ReportGenerationFailedError, "REPORT_GENERATION_FAILED", 500),
            (WorkflowInvalidTransitionError, "WORKFLOW_TRANSITION_INVALID", 409),
            (WorkflowMaxRetriesError, "WORKFLOW_MAX_RETRIES", 429),
            (ValidationFailedError, "VALIDATION_FAILED", 422),
            (BenchmarkDataInsufficientError, "BENCHMARK_DATA_INSUFFICIENT", 404),
            (UnitMismatchError, "UNIT_MISMATCH", 422),
            (UnknownProviderError, "UNKNOWN_PROVIDER", 404),
        ],
    )
    def test_code_and_status(
        self, error_cls: type[CarbonTallyError], code: str, status: int
    ) -> None:
        err = error_cls("boom")
        assert err.code == code
        assert err.http_status == status
        assert err.message == "boom"
        assert err.details == {}
        assert isinstance(err, CarbonTallyError)

    def test_details_are_stored(self) -> None:
        err = FactorNotFoundError("no match", details={"activity": "diesel"})
        assert err.details == {"activity": "diesel"}

    def test_str_is_message(self) -> None:
        err = FactorNotFoundError("no match")
        assert str(err) == "no match"

    def test_default_details_is_empty_dict(self) -> None:
        assert FactorNotFoundError("x").details == {}


class TestCoreTypes:
    def test_country_values(self) -> None:
        assert Country.GB.value == "GB"
        assert Country.IE.value == "IE"

    def test_scope_values(self) -> None:
        assert Scope.SCOPE_1.value == "Scope 1"
        assert Scope.SCOPE_3.value == "Scope 3"
        assert Scope.OUTSIDE_OF_SCOPES.value == "Outside of Scopes"

    def test_str_enums_are_str(self) -> None:
        assert Country.GB.value == "GB"
        assert Scope.SCOPE_2.value == "Scope 2"

    def test_unit_and_year_are_typed(self) -> None:
        unit = Unit("kWh")
        year = ReportingYear(2025)
        assert unit == "kWh"
        assert year == 2025

    def test_date_range_contains(self) -> None:
        rng = DateRange(date(2025, 1, 1), date(2025, 12, 31))
        assert rng.contains(date(2025, 6, 1))
        assert rng.contains(date(2025, 1, 1))
        assert not rng.contains(date(2024, 12, 31))

    def test_date_range_rejects_reversed(self) -> None:
        with pytest.raises(ValueError):
            DateRange(date(2025, 12, 31), date(2025, 1, 1))

    def test_date_range_overlaps(self) -> None:
        a = DateRange(date(2025, 1, 1), date(2025, 6, 30))
        b = DateRange(date(2025, 6, 30), date(2025, 12, 31))
        assert a.overlaps(b)
        c = DateRange(date(2026, 1, 1), date(2026, 12, 31))
        assert not a.overlaps(c)

    def test_date_range_is_immutable(self) -> None:
        rng = DateRange(date(2025, 1, 1), date(2025, 12, 31))
        with pytest.raises(FrozenInstanceError):
            rng.start_date = date(2026, 1, 1)  # type: ignore[misc]


class TestLogging:
    def test_configure_logging_does_not_stack_handlers(self) -> None:
        configure_logging(logging.INFO)
        root = logging.getLogger()
        configure_logging(logging.INFO)
        assert len(root.handlers) == 1

    def test_get_logger_returns_named_logger(self) -> None:
        assert get_logger("tests") is logging.getLogger("tests")
