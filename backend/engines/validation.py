"""Emissions Validation Engine (Backend v2.1 §7, Phase 9A — contract 9.1).

Validates emissions data quality and calculation integrity for an organisation
over a period. Implements the approved Phase 9 capabilities A1–A9
(input/activity invariants, reproducibility/hash, factor/match country-provider
correctness, scope/unit consistency, snapshot validation, data integrity,
reporting-period, organization/facility, audit-time verification).

The engine never writes to the database. It consumes repository surfaces
through protocols (:class:`LogsSource`, :class:`OrgSource`,
:class:`FactorLookup`), publishes :class:`ValidationFailed` on strict-mode
blocking, and records an audit entry per composite run (CT-ARCH-014).

SEAI CO2-only factors (``factor_source='SEAI'``, ``factor_set='SEAI-2025'``,
``country='IE'``) are first-class: the engine never treats the absence of
CH4/N2O components as a defect, and :func:`gas_coverage` preserves the
``kg CO2`` vs ``kg CO2e`` distinction for provenance-aware callers.

Dependency rules: imports from ``core`` (errors, logging, types), ``domain``
(calculation, factor, matching, organization, validation, workflow events) and
``infra`` (event bus, audit logger). Stateless per request.
"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Protocol

from core.exceptions import ValidationFailedError
from core.logging import get_logger
from core.types import DateRange
from domain.calculation import CalculationSnapshot, EmissionLog
from domain.factor import RESULT_PRECISION, EmissionFactor, gas_coverage
from domain.matching import MatchRequest, MatchResult
from domain.organization import Asset, Facility, Organization, OrganizationMetadata
from domain.validation import (
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSeverity,
)
from domain.workflow import ValidationFailed
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus

logger = get_logger(__name__)

#: Confidence below which a matched result is flagged as low-confidence (A3).
LOW_CONFIDENCE_THRESHOLD = 0.8

#: Known scope vocabulary (mirrors ``core.types.Scope`` values).
_SUPPORTED_SCOPES = ("Scope 1", "Scope 2", "Scope 3", "Outside of Scopes")

#: Stable issue codes.
CODE_INPUT_ACTIVITY_EMPTY = "VAL_INPUT_ACTIVITY_EMPTY"
CODE_INPUT_QUANTITY_NEGATIVE = "VAL_INPUT_QUANTITY_NEGATIVE"
CODE_INPUT_YEAR_RANGE = "VAL_INPUT_YEAR_RANGE"
CODE_INPUT_UNIT_MISSING = "VAL_INPUT_UNIT_MISSING"
CODE_CALC_MISMATCH = "VAL_CALC_MISMATCH"
CODE_CALC_ROUNDING = "VAL_CALC_ROUNDING_TOLERANCE"
CODE_HASH_EMPTY = "VAL_HASH_EMPTY"
CODE_HASH_MISMATCH = "VAL_HASH_MISMATCH"
CODE_MATCH_NO_FACTOR = "VAL_MATCH_FACTOR_MISSING"
CODE_MATCH_COUNTRY = "VAL_COUNTRY_MISMATCH"
CODE_MATCH_PROVIDER = "VAL_PROVIDER_MISMATCH"
CODE_MATCH_UNIT = "VAL_MATCH_UNIT_MISMATCH"
CODE_MATCH_NO_RESULT = "VAL_MATCH_NO_RESULT"
CODE_MATCH_LOW_CONFIDENCE = "VAL_MATCH_LOW_CONFIDENCE"
CODE_UNIT_MISMATCH = "VAL_UNIT_MISMATCH"
CODE_SCOPE_MISMATCH = "VAL_SCOPE_MISMATCH"
CODE_SCOPE_UNKNOWN = "VAL_SCOPE_UNKNOWN"
CODE_SCOPE_MISSING = "VAL_SCOPE_MISSING"
CODE_SCOPE_FAMILY = "VAL_SCOPE_FAMILY_MISMATCH"
CODE_SNAPSHOT_PROVENANCE_MISSING = "VAL_SNAPSHOT_PROVENANCE_MISSING"
CODE_SNAPSHOT_BATCH_MISMATCH = "VAL_SNAPSHOT_BATCH_MISMATCH"
CODE_SNAPSHOT_SOURCE_MISMATCH = "VAL_SNAPSHOT_SOURCE_MISMATCH"
CODE_QUANTITY_NEGATIVE = "VAL_QUANTITY_NEGATIVE"
CODE_CO2E_NEGATIVE = "VAL_CO2E_NEGATIVE"
CODE_FACTOR_ORPHAN = "VAL_FACTOR_ORPHAN"
CODE_SNAPSHOT_LINK_MISSING = "VAL_SNAPSHOT_LINK_MISSING"
CODE_YEAR_MISMATCH = "VAL_YEAR_MISMATCH"
CODE_OUT_OF_PERIOD = "VAL_OUT_OF_PERIOD"
CODE_ORG_NOT_FOUND = "VAL_ORG_NOT_FOUND"
CODE_ORG_INACTIVE = "VAL_ORG_INACTIVE"
CODE_ENTITY_NOT_IN_ORG = "VAL_ENTITY_NOT_IN_ORG"
CODE_METADATA_MISSING = "VAL_METADATA_MISSING"


def _family_expected_scope(activity_type: str) -> Optional[str]:
    """Return the scope implied by the activity family, or ``None``.

    ``Fuels > Electricity > ...`` implies Scope 2; the fuel families
    (Liquid/Solid/Gaseous) imply Scope 1. Used for the A4 family-consistency
    warning only — never as a hard rule, because providers may publish
    edge cases.
    """
    if "> Electricity" in activity_type:
        return "Scope 2"
    if any(
        marker in activity_type
        for marker in ("> Liquid fuels >", "> Solid fuels >", "> Gaseous fuels >")
    ):
        return "Scope 1"
    return None


def _issue(
    code: str,
    severity: ValidationSeverity,
    message: str,
    entity_type: str,
    entity_id: str,
    *,
    field: str = "",
    context: Optional[dict[str, object]] = None,
) -> ValidationIssue:
    """Build a :class:`ValidationIssue` with the standard severity mapping."""
    return ValidationIssue(
        code=code,
        severity=severity,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        field=field,
        context=dict(context or {}),
    )


# ---------------------------------------------------------------------------
# Repository surfaces (protocols) — satisfied structurally by the production
# repositories (data/emissions_logs.py, data/organizations.py,
# data/emission_factors.py) and by fakes in the unit suite.
# ---------------------------------------------------------------------------


class LogsSource(Protocol):
    """The emissions-log surface the engine reads (``EmissionsLogsRepository``)."""

    async def find_by_org(self, org_id: str, period: DateRange) -> list[EmissionLog]: ...


class OrgSource(Protocol):
    """The organisations surface the engine reads (``OrganizationsRepository``)."""

    async def get(self, org_id: str) -> Optional[Organization]: ...

    async def get_metadata(self, org_id: str) -> Optional[OrganizationMetadata]: ...

    async def get_facilities(self, org_id: str) -> list[Facility]: ...

    async def get_assets(self, org_id: str) -> list[Asset]: ...


class FactorLookup(Protocol):
    """The factor surface the engine reads (``EmissionFactorsRepository``)."""

    async def get(self, id: str) -> Optional[EmissionFactor]: ...


class ValidationEngine:
    """Emissions data-quality and calculation-integrity validation (Phase 9A).

    Args:
        logs_repo: Emissions-log repository surface (:class:`LogsSource`).
        org_repo: Organisations repository surface (:class:`OrgSource`).
        factor_repo: Emission-factors repository surface (:class:`FactorLookup`).
        event_bus: Optional bus that receives ``ValidationFailed`` when strict
            mode blocks (fire-and-forget).
        audit_logger: Optional logger that records every composite validation
            run.
    """

    def __init__(
        self,
        logs_repo: LogsSource,
        org_repo: OrgSource,
        factor_repo: FactorLookup,
        *,
        event_bus: Optional[EventBus] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        if logs_repo is None or org_repo is None or factor_repo is None:
            raise ValueError("logs_repo, org_repo and factor_repo must not be None")
        self._logs = logs_repo
        self._orgs = org_repo
        self._factors = factor_repo
        self._event_bus = event_bus
        self._audit_logger = audit_logger

    # ------------------------------------------------------------------
    # Composite entry point
    # ------------------------------------------------------------------

    async def validate(self, request: ValidationRequest) -> ValidationReport:
        """Run the full Phase 9 validation over ``request``.

        Combines A8 (organisation existence/activity), A4/A6/A7 over the
        organisation's logs inside ``request.period``, and the A8 entity
        ownership check. When ``request.strict`` is set and blocking errors
        exist, publishes ``ValidationFailed`` and raises
        ``ValidationFailedError`` (422); warnings never raise.
        """
        report = ValidationReport()
        report = report.merge(
            await self.validate_org(request.organization_id, request.reporting_year)
        )
        if request.period is not None:
            logs = await self._logs.find_by_org(request.organization_id, request.period)
            if request.scope_filter is not None:
                logs = [log for log in logs if log.scope == request.scope_filter]
            report = report.merge(
                await self.validate_logs(
                    logs,
                    request.reporting_year,
                    period=request.period,
                    strict=request.strict,
                )
            )
            report = report.merge(
                await self._validate_membership(
                    request.organization_id, logs, extra_entities=request.entity_ids
                )
            )
        await self._audit(request.organization_id, report)
        if request.strict and not report.ok:
            await self._publish_validation_failed(request.organization_id, report)
            raise ValidationFailedError(
                "validation failed with blocking errors",
                details={
                    "organization_id": request.organization_id,
                    "errors": [issue.message for issue in report.blocking_errors],
                },
            )
        return report

    # ------------------------------------------------------------------
    # A1 — input/activity validation
    # ------------------------------------------------------------------

    def validate_input(
        self,
        *,
        activity: str,
        quantity: Decimal,
        reporting_year: int,
        quantity_unit: str = "",
        factor: Optional[EmissionFactor] = None,
    ) -> ValidationReport:
        """Validate an activity input before matching/calculation (A1).

        Rules (all error/blocking): activity non-empty; quantity >= 0;
        reporting_year in 1990–2100; unit present when the factor requires one.
        """
        issues: list[ValidationIssue] = []
        entity_id = activity or "<empty>"
        if not activity:
            issues.append(
                _issue(
                    CODE_INPUT_ACTIVITY_EMPTY,
                    ValidationSeverity.ERROR,
                    "activity must not be empty",
                    "activity",
                    entity_id,
                    field="activity",
                )
            )
        if quantity < 0:
            issues.append(
                _issue(
                    CODE_INPUT_QUANTITY_NEGATIVE,
                    ValidationSeverity.ERROR,
                    "quantity must be >= 0",
                    "activity",
                    entity_id,
                    field="quantity",
                )
            )
        if not (1990 <= reporting_year <= 2100):
            issues.append(
                _issue(
                    CODE_INPUT_YEAR_RANGE,
                    ValidationSeverity.ERROR,
                    f"reporting_year {reporting_year} outside supported range 1990-2100",
                    "activity",
                    entity_id,
                    field="reporting_year",
                )
            )
        if factor is not None and factor.unit is not None and not quantity_unit:
            issues.append(
                _issue(
                    CODE_INPUT_UNIT_MISSING,
                    ValidationSeverity.ERROR,
                    f"quantity unit is required for factor {factor.id} "
                    f"(unit {factor.unit!r})",
                    "activity",
                    entity_id,
                    field="quantity_unit",
                )
            )
        return ValidationReport(issues=tuple(issues))

    # ------------------------------------------------------------------
    # A4 + A6 + A7 — emissions-log validation
    # ------------------------------------------------------------------

    async def validate_logs(
        self,
        logs: list[EmissionLog],
        reporting_year: int,
        *,
        period: Optional[DateRange] = None,
        strict: bool = False,
    ) -> ValidationReport:
        """Validate a set of emissions logs (A4, A6, A7)."""
        issues: list[ValidationIssue] = []
        for log in logs:
            issues.extend(self._validate_log_integrity(log).issues)  # A6
            issues.extend(  # A7
                self._validate_log_period(
                    log, reporting_year, period=period, strict=strict
                ).issues
            )
            factor = await self._factors.get(log.factor_id)
            if factor is None:
                issues.append(
                    _issue(
                        CODE_FACTOR_ORPHAN,
                        ValidationSeverity.ERROR,
                        f"emissions log {log.id} references missing factor "
                        f"{log.factor_id}",
                        "emissions_log",
                        log.id,
                        field="factor_id",
                    )
                )
            else:
                issues.extend(self._validate_log_consistency(log, factor).issues)  # A4
        return ValidationReport(issues=tuple(issues))

    def _validate_log_integrity(self, log: EmissionLog) -> ValidationReport:
        """A6 — data integrity: non-negative values and snapshot linkage."""
        issues: list[ValidationIssue] = []
        if log.quantity < 0:
            issues.append(
                _issue(
                    CODE_QUANTITY_NEGATIVE,
                    ValidationSeverity.ERROR,
                    f"emissions log {log.id} has negative quantity {log.quantity}",
                    "emissions_log",
                    log.id,
                    field="quantity",
                )
            )
        if log.calculated_kg_co2e < 0:
            issues.append(
                _issue(
                    CODE_CO2E_NEGATIVE,
                    ValidationSeverity.ERROR,
                    f"emissions log {log.id} has negative calculated_kg_co2e "
                    f"{log.calculated_kg_co2e}",
                    "emissions_log",
                    log.id,
                    field="calculated_kg_co2e",
                )
            )
        if log.calculated_kg_co2e > 0 and log.snapshot_id is None:
            issues.append(
                _issue(
                    CODE_SNAPSHOT_LINK_MISSING,
                    ValidationSeverity.WARNING,
                    f"emissions log {log.id} has calculated emissions but no "
                    "linked calculation snapshot",
                    "emissions_log",
                    log.id,
                    field="snapshot_id",
                )
            )
        return ValidationReport(issues=tuple(issues))

    def _validate_log_period(
        self,
        log: EmissionLog,
        reporting_year: int,
        *,
        period: Optional[DateRange],
        strict: bool,
    ) -> ValidationReport:
        """A7 — reporting-period validation."""
        issues: list[ValidationIssue] = []
        if log.date.year != reporting_year:
            issues.append(
                _issue(
                    CODE_YEAR_MISMATCH,
                    ValidationSeverity.WARNING,
                    f"emissions log {log.id} date {log.date.isoformat()} is in "
                    f"year {log.date.year}, not reporting_year {reporting_year}",
                    "emissions_log",
                    log.id,
                    field="date",
                )
            )
        if period is not None and not period.contains(log.date):
            severity = (
                ValidationSeverity.ERROR if strict else ValidationSeverity.WARNING
            )
            issues.append(
                _issue(
                    CODE_OUT_OF_PERIOD,
                    severity,
                    f"emissions log {log.id} date {log.date.isoformat()} is "
                    f"outside period {period.start_date.isoformat()}.."
                    f"{period.end_date.isoformat()}",
                    "emissions_log",
                    log.id,
                    field="date",
                )
            )
        return ValidationReport(issues=tuple(issues))

    def _validate_log_consistency(
        self, log: EmissionLog, factor: EmissionFactor
    ) -> ValidationReport:
        """A4 — scope/unit consistency between a log and its factor."""
        issues: list[ValidationIssue] = []
        if factor.unit is not None and log.unit != factor.unit:
            issues.append(
                _issue(
                    CODE_UNIT_MISMATCH,
                    ValidationSeverity.ERROR,
                    f"emissions log {log.id} unit {log.unit!r} does not match "
                    f"factor {factor.id} unit {factor.unit!r}",
                    "emissions_log",
                    log.id,
                    field="unit",
                )
            )
        if factor.scope is not None and factor.scope not in _SUPPORTED_SCOPES:
            issues.append(
                _issue(
                    CODE_SCOPE_UNKNOWN,
                    ValidationSeverity.ERROR,
                    f"factor {factor.id} scope {factor.scope!r} is not a known "
                    "scope",
                    "emission_factors",
                    factor.id,
                    field="scope",
                )
            )
        if log.scope is not None and log.scope not in _SUPPORTED_SCOPES:
            issues.append(
                _issue(
                    CODE_SCOPE_UNKNOWN,
                    ValidationSeverity.ERROR,
                    f"emissions log {log.id} scope {log.scope!r} is not a known "
                    "scope",
                    "emissions_log",
                    log.id,
                    field="scope",
                )
            )
        if factor.scope is not None and log.scope is not None:
            if log.scope != factor.scope:
                issues.append(
                    _issue(
                        CODE_SCOPE_MISMATCH,
                        ValidationSeverity.ERROR,
                        f"emissions log {log.id} scope {log.scope!r} does not "
                        f"match factor {factor.id} scope {factor.scope!r}",
                        "emissions_log",
                        log.id,
                        field="scope",
                    )
                )
        elif factor.scope is not None and log.scope is None:
            issues.append(
                _issue(
                    CODE_SCOPE_MISSING,
                    ValidationSeverity.WARNING,
                    f"emissions log {log.id} has no scope; factor {factor.id} "
                    f"declares scope {factor.scope!r}",
                    "emissions_log",
                    log.id,
                    field="scope",
                )
            )
        expected_family_scope = _family_expected_scope(factor.activity_type)
        if (
            expected_family_scope is not None
            and factor.scope is not None
            and factor.scope != expected_family_scope
        ):
            issues.append(
                _issue(
                    CODE_SCOPE_FAMILY,
                    ValidationSeverity.WARNING,
                    f"factor {factor.id} scope {factor.scope!r} is inconsistent "
                    f"with activity family (expected {expected_family_scope!r})",
                    "emission_factors",
                    factor.id,
                    field="scope",
                )
            )
        return ValidationReport(issues=tuple(issues))

    # ------------------------------------------------------------------
    # A2 + A5 — calculation-snapshot validation
    # ------------------------------------------------------------------

    def validate_snapshot(
        self,
        snapshot: CalculationSnapshot,
        factor: Optional[EmissionFactor] = None,
        *,
        factor_source: Optional[str] = None,
        factor_set: Optional[str] = None,
        import_batch_id: Optional[str] = None,
    ) -> ValidationReport:
        """Validate a snapshot (A2 reproducibility + A5 provenance).

        A2: ``co2e_kg`` must equal ``quantity * co2e_multiplier`` (quantised)
        and ``content_hash`` must match a recomputation. A5: when the factor is
        batch-linked (SEAI), the persisted provenance (factor_source,
        factor_set, import_batch_id) must be present and consistent. SEAI
        CO2-only factors are valid — CH4/N2O components are never required.
        """
        issues: list[ValidationIssue] = []
        expected = (snapshot.quantity * snapshot.co2e_multiplier).quantize(
            RESULT_PRECISION
        )
        if expected != snapshot.co2e_kg:
            delta = abs(expected - snapshot.co2e_kg)
            if delta <= RESULT_PRECISION:
                issues.append(
                    _issue(
                        CODE_CALC_ROUNDING,
                        ValidationSeverity.WARNING,
                        f"snapshot {snapshot.id} co2e_kg differs from "
                        f"recomputation by {delta} (rounding tolerance)",
                        "calculation_snapshot",
                        snapshot.id,
                        field="co2e_kg",
                    )
                )
            else:
                issues.append(
                    _issue(
                        CODE_CALC_MISMATCH,
                        ValidationSeverity.ERROR,
                        f"snapshot {snapshot.id} co2e_kg {snapshot.co2e_kg} != "
                        f"recomputed {expected}",
                        "calculation_snapshot",
                        snapshot.id,
                        field="co2e_kg",
                    )
                )
        if not snapshot.content_hash:
            issues.append(
                _issue(
                    CODE_HASH_EMPTY,
                    ValidationSeverity.ERROR,
                    f"snapshot {snapshot.id} has no content_hash",
                    "calculation_snapshot",
                    snapshot.id,
                    field="content_hash",
                )
            )
        else:
            recomputed = snapshot.build_content_hash()
            if snapshot.content_hash != recomputed:
                issues.append(
                    _issue(
                        CODE_HASH_MISMATCH,
                        ValidationSeverity.ERROR,
                        f"snapshot {snapshot.id} content_hash does not match "
                        "recomputation",
                        "calculation_snapshot",
                        snapshot.id,
                        field="content_hash",
                    )
                )
        if factor is not None and factor.import_batch_id is not None:
            provenance_context: dict[str, object] = {
                "gas_coverage": gas_coverage(factor),
                "factor_source": factor.factor_source,
                "factor_set": factor.factor_set,
            }
            if import_batch_id is None:
                issues.append(
                    _issue(
                        CODE_SNAPSHOT_PROVENANCE_MISSING,
                        ValidationSeverity.WARNING,
                        f"snapshot {snapshot.id} provenance missing for "
                        f"batch-linked factor {factor.id}",
                        "calculation_snapshot",
                        snapshot.id,
                        field="import_batch_id",
                        context=provenance_context,
                    )
                )
            else:
                if import_batch_id != factor.import_batch_id:
                    issues.append(
                        _issue(
                            CODE_SNAPSHOT_BATCH_MISMATCH,
                            ValidationSeverity.ERROR,
                            f"snapshot {snapshot.id} import_batch_id does not "
                            f"match factor {factor.id}",
                            "calculation_snapshot",
                            snapshot.id,
                            field="import_batch_id",
                            context=provenance_context,
                        )
                    )
                if factor_source is not None and factor_source != factor.factor_source:
                    issues.append(
                        _issue(
                            CODE_SNAPSHOT_SOURCE_MISMATCH,
                            ValidationSeverity.ERROR,
                            f"snapshot {snapshot.id} factor_source "
                            f"{factor_source!r} != factor source "
                            f"{factor.factor_source!r}",
                            "calculation_snapshot",
                            snapshot.id,
                            field="factor_source",
                            context=provenance_context,
                        )
                    )
                if factor_set is not None and factor_set != factor.factor_set:
                    issues.append(
                        _issue(
                            CODE_SNAPSHOT_SOURCE_MISMATCH,
                            ValidationSeverity.ERROR,
                            f"snapshot {snapshot.id} factor_set {factor_set!r} "
                            f"!= factor set {factor.factor_set!r}",
                            "calculation_snapshot",
                            snapshot.id,
                            field="factor_set",
                            context=provenance_context,
                        )
                    )
        return ValidationReport(issues=tuple(issues))

    # ------------------------------------------------------------------
    # A3 — factor/match validation
    # ------------------------------------------------------------------

    def validate_match(
        self, request: MatchRequest, result: MatchResult
    ) -> ValidationReport:
        """Validate a matching outcome (A3).

        Matched results must carry a factor whose country matches the request,
        honour ``preferred_provider`` and agree on unit; low-confidence and
        no-match outcomes are warnings (data quality), never blocking.
        """
        issues: list[ValidationIssue] = []
        if result.status != "matched":
            issues.append(
                _issue(
                    CODE_MATCH_NO_RESULT,
                    ValidationSeverity.WARNING,
                    f"match request {request.id} resolved to {result.status!r}",
                    "factor_match",
                    request.id,
                    field="status",
                    context={"status": result.status},
                )
            )
            return ValidationReport(issues=tuple(issues))
        factor = result.factor
        if factor is None:
            issues.append(
                _issue(
                    CODE_MATCH_NO_FACTOR,
                    ValidationSeverity.ERROR,
                    f"match request {request.id} reported matched but has no "
                    "factor",
                    "factor_match",
                    request.id,
                    field="factor",
                )
            )
            return ValidationReport(issues=tuple(issues))
        match_context: dict[str, object] = {
            "gas_coverage": gas_coverage(factor),
            "factor_source": factor.factor_source,
            "factor_set": factor.factor_set,
            "provider": factor.provider_key,
        }
        if factor.country != request.country:
            issues.append(
                _issue(
                    CODE_MATCH_COUNTRY,
                    ValidationSeverity.ERROR,
                    f"factor {factor.id} country {factor.country!r} does not "
                    f"match request country {request.country!r}",
                    "factor_match",
                    request.id,
                    field="country",
                    context=match_context,
                )
            )
        if (
            request.preferred_provider is not None
            and factor.provider_key != request.preferred_provider
        ):
            issues.append(
                _issue(
                    CODE_MATCH_PROVIDER,
                    ValidationSeverity.ERROR,
                    f"factor {factor.id} provider {factor.provider_key!r} does "
                    f"not match preferred provider "
                    f"{request.preferred_provider!r}",
                    "factor_match",
                    request.id,
                    field="provider_key",
                    context=match_context,
                )
            )
        if (
            request.unit is not None
            and factor.unit is not None
            and request.unit != factor.unit
        ):
            issues.append(
                _issue(
                    CODE_MATCH_UNIT,
                    ValidationSeverity.ERROR,
                    f"factor {factor.id} unit {factor.unit!r} does not match "
                    f"request unit {request.unit!r}",
                    "factor_match",
                    request.id,
                    field="unit",
                    context=match_context,
                )
            )
        if result.confidence < LOW_CONFIDENCE_THRESHOLD:
            issues.append(
                _issue(
                    CODE_MATCH_LOW_CONFIDENCE,
                    ValidationSeverity.WARNING,
                    f"match request {request.id} confidence "
                    f"{result.confidence:.3f} below threshold "
                    f"{LOW_CONFIDENCE_THRESHOLD}",
                    "factor_match",
                    request.id,
                    field="confidence",
                    context=match_context,
                )
            )
        return ValidationReport(issues=tuple(issues))

    # ------------------------------------------------------------------
    # A8 — organization/facility validation
    # ------------------------------------------------------------------

    async def validate_org(
        self,
        org_id: str,
        reporting_year: int,
        *,
        require_intensity_metadata: bool = False,
    ) -> ValidationReport:
        """Validate an organisation (A8).

        Rules: the organisation must exist and be active (errors); when
        ``require_intensity_metadata`` is set, missing intensity metadata
        (floor area / FTE / revenue) is a warning.
        """
        issues: list[ValidationIssue] = []
        org = await self._orgs.get(org_id)
        if org is None:
            issues.append(
                _issue(
                    CODE_ORG_NOT_FOUND,
                    ValidationSeverity.ERROR,
                    f"organization {org_id} does not exist",
                    "organization",
                    org_id,
                )
            )
        else:
            if not org.is_active:
                issues.append(
                    _issue(
                        CODE_ORG_INACTIVE,
                        ValidationSeverity.ERROR,
                        f"organization {org_id} is inactive",
                        "organization",
                        org_id,
                    )
                )
            if require_intensity_metadata:
                metadata = await self._orgs.get_metadata(org_id)
                if metadata is None:
                    issues.append(
                        _issue(
                            CODE_METADATA_MISSING,
                            ValidationSeverity.WARNING,
                            f"organization {org_id} has no intensity metadata "
                            "(floor area / FTE / revenue)",
                            "organization",
                            org_id,
                        )
                    )
        return ValidationReport(issues=tuple(issues))

    async def _validate_membership(
        self,
        org_id: str,
        logs: list[EmissionLog],
        *,
        extra_entities: tuple[str, ...] = (),
    ) -> ValidationReport:
        """A8 — every facility/asset referenced by a log belongs to the org."""
        issues: list[ValidationIssue] = []
        facilities = {f.id for f in await self._orgs.get_facilities(org_id)}
        assets = {a.id for a in await self._orgs.get_assets(org_id)}
        for log in logs:
            if log.facility_id is not None and log.facility_id not in facilities:
                issues.append(
                    _issue(
                        CODE_ENTITY_NOT_IN_ORG,
                        ValidationSeverity.ERROR,
                        f"emissions log {log.id} facility {log.facility_id} does "
                        f"not belong to organization {org_id}",
                        "emissions_log",
                        log.id,
                        field="facility_id",
                    )
                )
            if log.asset_id is not None and log.asset_id not in assets:
                issues.append(
                    _issue(
                        CODE_ENTITY_NOT_IN_ORG,
                        ValidationSeverity.ERROR,
                        f"emissions log {log.id} asset {log.asset_id} does not "
                        f"belong to organization {org_id}",
                        "emissions_log",
                        log.id,
                        field="asset_id",
                    )
                )
        for entity_id in extra_entities:
            if entity_id not in facilities and entity_id not in assets:
                issues.append(
                    _issue(
                        CODE_ENTITY_NOT_IN_ORG,
                        ValidationSeverity.ERROR,
                        f"entity {entity_id} does not belong to organization "
                        f"{org_id}",
                        "organization",
                        org_id,
                        field="entity_id",
                    )
                )
        return ValidationReport(issues=tuple(issues))

    # ------------------------------------------------------------------
    # A9 — audit-time verification
    # ------------------------------------------------------------------

    async def verify_snapshots(
        self, snapshots: Sequence[CalculationSnapshot]
    ) -> ValidationReport:
        """Verify a set of stored snapshots (A9).

        Runs the A2 reproducibility + content-hash checks across every
        snapshot and returns the aggregate report. Provenance (A5) is checked
        via :meth:`validate_snapshot` when the owning factor is supplied.
        """
        report = ValidationReport()
        for snapshot in snapshots:
            report = report.merge(self.validate_snapshot(snapshot))
        return report

    # ------------------------------------------------------------------
    # Side effects (best-effort — never break the validation result)
    # ------------------------------------------------------------------

    async def _audit(self, org_id: str, report: ValidationReport) -> None:
        """Record the composite validation run (CT-ARCH-014)."""
        if self._audit_logger is None:
            return
        try:
            await self._audit_logger.log_action(
                action="validation:completed",
                entity_type="organization",
                entity_id=org_id,
                correlation_id=org_id,
                actor="validation_engine",
                after={"ok": report.ok, "issues": report.counts},
            )
        except Exception:  # noqa: BLE001 - audit must not break validation
            logger.exception(
                "failed to audit validation for organization %s", org_id
            )

    async def _publish_validation_failed(
        self, org_id: str, report: ValidationReport
    ) -> None:
        """Publish ``ValidationFailed`` for strict-mode blocking (fire-and-forget)."""
        if self._event_bus is None:
            return
        event = ValidationFailed(
            event_id=str(uuid.uuid4()),
            occurred_at=datetime.now(timezone.utc),
            correlation_id=org_id,
            entity_type="organization",
            entity_id=org_id,
            errors=tuple(issue.message for issue in report.blocking_errors),
        )
        try:
            await self._event_bus.publish(event)
        except Exception:  # noqa: BLE001 - side effects must not break validation
            logger.exception(
                "failed to publish ValidationFailed for organization %s", org_id
            )









