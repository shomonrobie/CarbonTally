"""Validation of normalised emission factors against DB rules.

Every factor is checked against the constraints of the existing
``emission_factors`` table (non-negative multiplier, country vocabulary,
label lengths) and against the natural-key unique index semantics. Errors
produce a skip; warnings are recorded but do not block the import.
"""
from __future__ import annotations

from typing import Optional

from .models import (
    DuplicateRow,
    EmissionFactor,
    SkippedRow,
    ValidationIssue,
    ValidationReport,
)

SCOPE_VOCABULARY: tuple[str, ...] = ("Scope 1", "Scope 2", "Scope 3", "Outside of Scopes")
ACTIVITY_TYPE_HARD_LIMIT = 255
ACTIVITY_TYPE_SOFT_LIMIT = 150
UNIT_MAX_LEN = 100


def _issue(row: EmissionFactor, field: str, severity: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        row_number=row.row_number,
        defra_id=row.defra_id,
        field=field,
        severity=severity,
        message=message,
    )


def validate_all(
    factors: list[EmissionFactor],
    skipped_in: Optional[list[SkippedRow]] = None,
    country: str = "GB",
) -> ValidationReport:
    """Validate a batch of normalised factors and detect natural-key duplicates.

    The first occurrence of each natural key is kept; later occurrences are
    reported as duplicates and excluded from the load.
    """
    report = ValidationReport()
    if skipped_in:
        report.skipped = list(skipped_in)

    seen: dict[tuple[str, ...], EmissionFactor] = {}

    for factor in factors:
        issues: list[ValidationIssue] = []

        # --- country: must satisfy CHECK (country IN ('GB','IE')) ---
        if factor.country not in ("GB", "IE"):
            issues.append(
                _issue(
                    factor,
                    "country",
                    "error",
                    f"country={factor.country!r} violates the country IN ('GB','IE') constraint.",
                )
            )

        # --- co2e_multiplier: must satisfy CHECK (co2e_multiplier >= 0) ---
        if factor.co2e_multiplier < 0:
            issues.append(
                _issue(factor, "co2e_multiplier", "error", "co2e_multiplier must be >= 0.")
            )

        # --- activity_type length ---
        label_len = len(factor.activity_type)
        if label_len > ACTIVITY_TYPE_HARD_LIMIT:
            issues.append(
                _issue(
                    factor,
                    "activity_type",
                    "error",
                    f"activity_type length {label_len} exceeds the {ACTIVITY_TYPE_HARD_LIMIT} hard limit.",
                )
            )
        elif label_len > ACTIVITY_TYPE_SOFT_LIMIT:
            issues.append(
                _issue(
                    factor,
                    "activity_type",
                    "warning",
                    f"activity_type length {label_len} exceeds the legacy {ACTIVITY_TYPE_SOFT_LIMIT} cap.",
                )
            )

        # --- scope vocabulary (informational) ---
        if factor.scope and factor.scope not in SCOPE_VOCABULARY:
            issues.append(
                _issue(
                    factor,
                    "scope",
                    "warning",
                    f"scope={factor.scope!r} is outside the known vocabulary {SCOPE_VOCABULARY}.",
                )
            )

        # --- unit length sanity ---
        if factor.unit and len(factor.unit) > UNIT_MAX_LEN:
            issues.append(
                _issue(
                    factor,
                    "unit",
                    "warning",
                    f"unit length {len(factor.unit)} exceeds {UNIT_MAX_LEN} characters.",
                )
            )

        for issue in issues:
            report.issues.append(issue)

        errors = [issue for issue in issues if issue.severity == "error"]
        if errors:
            report.skipped.append(
                SkippedRow(
                    row_number=factor.row_number,
                    sheet_name=factor.sheet_name,
                    defra_id=factor.defra_id,
                    reason="validation_error",
                    detail="; ".join(issue.message for issue in errors),
                    activity_type=factor.activity_type,
                )
            )
            continue

        # --- duplicate natural key within the batch ---
        key = factor.natural_key
        if key in seen:
            first = seen[key]
            report.duplicates.append(
                DuplicateRow(
                    row_number=factor.row_number,
                    sheet_name=factor.sheet_name,
                    defra_id=factor.defra_id,
                    natural_key=key,
                    activity_type=factor.activity_type,
                    first_row_number=first.row_number,
                    first_defra_id=first.defra_id,
                )
            )
            report.issues.append(
                _issue(
                    factor,
                    "natural_key",
                    "warning",
                    f"Duplicate natural key; first seen at row {first.row_number} "
                    f"(DEFRA ID {first.defra_id}). This row is skipped.",
                )
            )
            continue

        seen[key] = factor
        report.factors.append(factor)

    return report
