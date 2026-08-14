"""Validation domain objects (Backend v2.1 §9, Phase 9A contract 9.1).

Pure Python, immutable frozen dataclasses.

* :class:`ValidationSeverity` — the severity vocabulary
  (``error`` = blocking, ``warning``/``suggestion`` = non-blocking).
* :class:`ValidationIssue` — a single validation finding.
* :class:`ValidationReport` — the engine output (issues + ``ok`` + counts).
* :class:`ValidationRequest` — the engine input.

No framework, database or infrastructure imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from enum import StrEnum
from typing import Any, Optional

from core.types import DateRange


class ValidationSeverity(StrEnum):
    """Severity of a validation finding.

    ``error`` is blocking: a strict validation run raises when any error is
    present. ``warning`` and ``suggestion`` never block.
    """

    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """A single validation finding.

    Attributes:
        code: Stable machine-readable code (e.g. ``VAL_UNIT_MISMATCH``).
        severity: The finding's severity.
        message: Human-readable description.
        entity_type: Aggregate kind the issue concerns (``emissions_log``,
            ``calculation_snapshot``, ``organization``, ``emission_factors``,
            ``activity``).
        entity_id: Id of the entity the issue concerns.
        field: Optional field the issue concerns.
        context: Optional structured, JSON-serialisable context. Provenance
            issues carry ``gas_coverage`` (``CO2`` vs ``CO2e``) so the
            SEAI CO2-only distinction is never lost.
    """

    code: str
    severity: ValidationSeverity
    message: str
    entity_type: str
    entity_id: str
    field: str = ""
    context: dict[str, Any] = dc_field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code must not be empty")
        if not self.message:
            raise ValueError("message must not be empty")
        if not self.entity_type:
            raise ValueError("entity_type must not be empty")
        if not self.entity_id:
            raise ValueError("entity_id must not be empty")

    @property
    def is_blocking(self) -> bool:
        """``True`` when the issue blocks (error severity)."""
        return self.severity is ValidationSeverity.ERROR


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """The outcome of a validation run.

    ``ok`` is ``True`` when no blocking (error) issues exist.
    """

    issues: tuple[ValidationIssue, ...] = ()

    @property
    def ok(self) -> bool:
        """``True`` when there are no blocking (error) issues."""
        return not any(issue.is_blocking for issue in self.issues)

    @property
    def counts(self) -> dict[str, int]:
        """Issue counts by severity value (``error``/``warning``/``suggestion``)."""
        counts: dict[str, int] = {sev.value: 0 for sev in ValidationSeverity}
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return counts

    @property
    def blocking_errors(self) -> tuple[ValidationIssue, ...]:
        """The issues that block (error severity)."""
        return tuple(issue for issue in self.issues if issue.is_blocking)

    def errors(self) -> tuple[ValidationIssue, ...]:
        """Return every error-severity issue."""
        return tuple(
            issue for issue in self.issues if issue.severity is ValidationSeverity.ERROR
        )

    def warnings(self) -> tuple[ValidationIssue, ...]:
        """Return every warning-severity issue."""
        return tuple(
            issue for issue in self.issues if issue.severity is ValidationSeverity.WARNING
        )

    def merge(self, other: ValidationReport) -> ValidationReport:
        """Return a new report combining this report's issues with ``other``'s."""
        return ValidationReport(issues=self.issues + other.issues)


@dataclass(frozen=True, slots=True)
class ValidationRequest:
    """Input contract for the Validation Engine (Phase 9 contract, 9.1).

    Attributes:
        organization_id: The organisation whose data is validated.
        reporting_year: The reporting year under validation.
        period: Optional inclusive date range; when supplied the engine
            validates every emissions log inside it (A6/A7/A8 entity checks).
        scope_filter: Optional scope restriction (e.g. ``Scope 1``).
        entity_ids: Optional facility/asset ids whose organisation ownership
            must be verified (A8).
        strict: When ``True`` the engine raises ``ValidationFailedError``
            (and publishes ``ValidationFailed``) when blocking errors exist.
    """

    organization_id: str
    reporting_year: int
    period: Optional[DateRange] = None
    scope_filter: Optional[str] = None
    entity_ids: tuple[str, ...] = ()
    strict: bool = False

    def __post_init__(self) -> None:
        if not self.organization_id:
            raise ValueError("organization_id must not be empty")
        if not (1990 <= self.reporting_year <= 2100):
            raise ValueError(
                f"reporting_year {self.reporting_year} outside supported range 1990-2100"
            )
