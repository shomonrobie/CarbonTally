"""Validator: applies DB rules and reports every non-imported row.

Nothing is silently skipped. Mapped rows carry a ``skip_reason`` from the
mapper (no id / no activity name / no factor value / invalid factor); rows that
pass mapping are checked against the ``emission_factors`` constraints and the
natural-key unique index. Missing units are reported as warnings (the unit
column is nullable). Blank rows, end markers and unsupported sheets are
surfaced from the parser counters into the report.
"""
from __future__ import annotations

from .models import (
    DuplicateRow,
    EmissionFactor,
    ImportStats,
    SkippedRow,
    ValidationIssue,
    ValidationReport,
    WorkbookAnalysis,
)

SCOPE_VOCABULARY: tuple[str, ...] = ("Scope 1", "Scope 2", "Scope 3", "Outside of Scopes")
ACTIVITY_TYPE_HARD_LIMIT = 255
ACTIVITY_TYPE_SOFT_LIMIT = 150
UNIT_MAX_LEN = 100

SKIP_REASON_LABELS: dict[str, str] = {
    "no_defra_id": "missing DEFRA ID",
    "no_activity_name": "missing activity name",
    "no_factor_value": "no factor value published",
    "invalid_factor": "invalid factor (non-numeric or negative)",
    "validation_error": "DB validation error",
}


def _issue(row: EmissionFactor, field: str, severity: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        row_number=row.row_number,
        defra_id=row.defra_id,
        field=field,
        severity=severity,
        message=message,
    )


def _skip(row: EmissionFactor, reason: str, detail: str) -> SkippedRow:
    return SkippedRow(
        row_number=row.row_number,
        sheet_name=row.sheet_name,
        defra_id=row.defra_id,
        reason=reason,
        detail=detail,
        activity_type=row.activity_type or None,
    )


def _skip_detail(row: EmissionFactor) -> str:
    label = SKIP_REASON_LABELS.get(row.skip_reason or "", row.skip_reason or "")
    if row.skip_reason == "invalid_factor":
        detail = f"factor value {row.metadata.get('raw_factor_value', '')!r} is invalid."
    elif row.skip_reason == "no_factor_value":
        detail = "DEFRA published no conversion factor for this row."
    elif row.skip_reason == "no_activity_name":
        detail = "row has no activity label (levels/column text/GHG unit)."
    else:
        detail = "row has no DEFRA ID."
    return f"{label}: {detail}"


def validate_all(
    mapped: list[EmissionFactor],
    country: str = "GB",
) -> ValidationReport:
    """Validate mapped factors and detect natural-key duplicates.

    The first occurrence of each natural key is kept; later occurrences are
    reported as duplicates and excluded from the load.
    """
    report = ValidationReport()
    seen: dict[tuple[str, ...], EmissionFactor] = {}

    for row in mapped:
        # --- mapper-level skip (source data problem) -------------------------
        if row.skip_reason is not None:
            report.skipped.append(_skip(row, row.skip_reason, _skip_detail(row)))
            continue

        issues: list[ValidationIssue] = []

        if row.country not in ("GB", "IE"):
            issues.append(
                _issue(row, "country", "error",
                       f"country={row.country!r} violates the country IN ('GB','IE') constraint.")
            )

        if row.co2e_multiplier < 0:
            issues.append(_issue(row, "co2e_multiplier", "error", "co2e_multiplier must be >= 0."))

        label_len = len(row.activity_type)
        if label_len > ACTIVITY_TYPE_HARD_LIMIT:
            issues.append(
                _issue(row, "activity_type", "error",
                       f"activity_type length {label_len} exceeds the {ACTIVITY_TYPE_HARD_LIMIT} hard limit.")
            )
        elif label_len > ACTIVITY_TYPE_SOFT_LIMIT:
            issues.append(
                _issue(row, "activity_type", "warning",
                       f"activity_type length {label_len} exceeds the legacy {ACTIVITY_TYPE_SOFT_LIMIT} cap.")
            )

        if not row.unit:
            issues.append(_issue(row, "unit", "warning", "Missing unit (UOM) for this factor."))

        if row.unit and len(row.unit) > UNIT_MAX_LEN:
            issues.append(
                _issue(row, "unit", "warning", f"unit length {len(row.unit)} exceeds {UNIT_MAX_LEN}.")
            )

        if row.scope and row.scope not in SCOPE_VOCABULARY:
            issues.append(
                _issue(row, "scope", "warning",
                       f"scope={row.scope!r} is outside the known vocabulary {SCOPE_VOCABULARY}.")
            )

        for issue in issues:
            report.issues.append(issue)

        if any(issue.severity == "error" for issue in issues):
            report.skipped.append(
                _skip(
                    row,
                    "validation_error",
                    "; ".join(i.message for i in issues if i.severity == "error"),
                )
            )
            continue

        key = row.natural_key
        if key in seen:
            first = seen[key]
            report.duplicates.append(
                DuplicateRow(
                    row_number=row.row_number,
                    sheet_name=row.sheet_name,
                    defra_id=row.defra_id,
                    natural_key=key,
                    activity_type=row.activity_type,
                    first_row_number=first.row_number,
                    first_defra_id=first.defra_id,
                )
            )
            report.issues.append(
                _issue(
                    row, "natural_key", "warning",
                    f"Duplicate natural key; first seen at row {first.row_number} "
                    f"(DEFRA ID {first.defra_id}). This row is skipped.",
                )
            )
            continue

        seen[key] = row
        report.factors.append(row)

    return report



def build_stats(
    report: ValidationReport,
    analysis: WorkbookAnalysis,
    parser_counters: dict[str, int],
) -> ImportStats:
    """Aggregate run statistics from the parser counters and validation report."""
    stats = ImportStats()
    stats.sheets_processed = len(analysis.worksheets)
    stats.data_sheets = sum(1 for w in analysis.worksheets if w.sheet_type == "data")
    stats.documentation_sheets = sum(
        1 for w in analysis.worksheets if w.sheet_type == "documentation"
    )
    stats.unsupported_sheets = sum(
        1 for w in analysis.worksheets if w.sheet_type == "unsupported"
    )
    stats.rows_scanned = parser_counters.get("rows_scanned", 0)
    stats.rows_parsed = parser_counters.get("rows_parsed", 0)
    stats.blank_rows = parser_counters.get("empty_rows", 0)
    stats.end_marker_rows = parser_counters.get("end_marker_rows", 0)
    stats.rows_with_id = parser_counters.get("rows_with_id", 0)
    stats.factors_with_value = parser_counters.get("factors_with_value", 0)

    for skipped in report.skipped:
        if skipped.reason == "no_factor_value":
            stats.skipped_no_factor += 1
        elif skipped.reason == "invalid_factor":
            stats.skipped_invalid_factor += 1
        elif skipped.reason == "no_activity_name":
            stats.skipped_no_activity_name += 1
        elif skipped.reason == "no_defra_id":
            stats.skipped_no_id += 1
        elif skipped.reason == "validation_error":
            stats.skipped_validation += 1

    stats.duplicates = len(report.duplicates)
    stats.imported = len(report.factors)
    stats.warnings = report.warnings
    stats.errors = report.errors
    return stats
