"""SEAI validator (CarbonTally SEAI 2025 provider).

Enforces the approved Implementation Gate v1.0 rules:

* provider = SEAI, country = IE, reporting_year = 2025, factor_set = SEAI-2025
* supported canonical units
* non-negative factor values
* exactly 20 canonical imported factors
* exactly 8 skipped source rows
* no duplicate canonical factors
* the electricity pair is present (consumption + gross supply)
* Biodiesel ME is present (it HAS a numeric factor)
* Natural gas (GCV) is skipped
* CO2-only semantics flag set on every factor
"""
from __future__ import annotations

from collections import Counter

from .models import (
    CANONICAL_UNITS,
    COUNTRY,
    EXPECTED_IMPORTED,
    EXPECTED_SKIPPED,
    FACTOR_SOURCE,
    FACTOR_SET,
    PROVIDER_KEY,
    REPORTING_YEAR,
    SeaiFactor,
    SeaiSkip,
    SeaiValidationIssue,
    SeaiValidationReport,
)

ELECTRICITY_CONSUMPTION = "Fuels > Electricity > Electricity consumption (kg CO2) [kWh]"
ELECTRICITY_GROSS_SUPPLY = "Fuels > Electricity > Gross electricity supply (kg CO2) [kWh]"
BIODIESEL_ME = "Biodiesel ME"
GAS_GCV = "Natural gas (GCV)"


def _issue(severity: str, message: str) -> SeaiValidationIssue:
    return SeaiValidationIssue(severity=severity, message=message)


def validate(
    factors: list[SeaiFactor],
    skipped: list[SeaiSkip],
) -> SeaiValidationReport:
    """Validate the mapped factors and skips against the approved spec."""
    report = SeaiValidationReport(factors=list(factors), skipped=list(skipped))

    # -- counts --------------------------------------------------------------
    if len(factors) != EXPECTED_IMPORTED:
        report.issues.append(
            _issue("error", f"expected {EXPECTED_IMPORTED} imported factors, got {len(factors)}")
        )
    if len(skipped) != EXPECTED_SKIPPED:
        report.issues.append(
            _issue("error", f"expected {EXPECTED_SKIPPED} skipped rows, got {len(skipped)}")
        )

    # -- per-factor field rules ----------------------------------------------
    for f in factors:
        if f.factor_source != FACTOR_SOURCE:
            report.issues.append(_issue("error", f"factor_source {f.factor_source!r} != SEAI"))
        if f.factor_set != FACTOR_SET:
            report.issues.append(_issue("error", f"factor_set {f.factor_set!r} != SEAI-2025"))
        if f.country != COUNTRY:
            report.issues.append(_issue("error", f"country {f.country!r} != IE"))
        if f.reporting_year != REPORTING_YEAR:
            report.issues.append(_issue("error", f"reporting_year {f.reporting_year} != 2025"))
        if f.provider_key != PROVIDER_KEY:
            report.issues.append(_issue("error", f"provider_key {f.provider_key!r} != seai"))
        if f.unit not in CANONICAL_UNITS:
            report.issues.append(_issue("error", f"unsupported unit {f.unit!r} on {f.activity_type}"))
        if f.co2e_multiplier < 0:
            report.issues.append(_issue("error", f"negative multiplier on {f.activity_type}"))
        if not f.co2_only:
            report.issues.append(_issue("error", f"CO2-only flag false on {f.activity_type}"))
        if not f.activity_type.endswith(f") [{f.unit}]") or "(kg CO2)" not in f.activity_type:
            report.issues.append(
                _issue("error", f"activity label convention violated: {f.activity_type!r}")
            )

    # -- duplicates by natural key -------------------------------------------
    seen: dict[tuple[str, ...], SeaiFactor] = {}
    for f in factors:
        key = f.natural_key or (
            str(f.reporting_year), f.activity_type, f.country, f.unit or "{no-unit}",
            f.scope or "{no-scope}",
        )
        if key in seen:
            report.duplicates.append(f)
            report.issues.append(
                _issue("error", f"duplicate natural key {key} for {f.activity_type}")
            )
        else:
            seen[key] = f

    # -- electricity pair -----------------------------------------------------
    labels = {f.activity_type for f in factors}
    if ELECTRICITY_CONSUMPTION not in labels:
        report.issues.append(_issue("error", "electricity consumption factor missing"))
    if ELECTRICITY_GROSS_SUPPLY not in labels:
        report.issues.append(_issue("error", "gross electricity supply factor missing"))

    # -- Biodiesel ME present, GCV skipped ------------------------------------
    names = {f.source_name for f in factors}
    if BIODIESEL_ME not in names:
        report.issues.append(_issue("error", "Biodiesel ME must be imported (it has a value)"))
    skipped_names = {s.name for s in skipped}
    if GAS_GCV not in skipped_names:
        report.issues.append(_issue("error", "Natural gas (GCV) must be skipped"))

    # -- skip reasons ---------------------------------------------------------
    reasons = Counter(s.reason for s in skipped)
    no_factor = reasons.get("no_factor_value", 0)
    if no_factor != 7:
        report.issues.append(
            _issue("error", f"expected 7 no_factor_value skips, got {no_factor}")
        )
    non_canonical = reasons.get("non_canonical_basis", 0)
    if non_canonical != 1:
        report.issues.append(
            _issue("error", f"expected 1 non_canonical_basis skip, got {non_canonical}")
        )

    return report
