"""CarbonTally Insight P3 — bounded data-quality and reproducibility contract.

Authorization: PO P3 implementation authorization (2026-09-23), bounded by the
P1 capability coverage matrix (family 14 Data Quality / family 16 Evidence and
Audit) and the master preflight.

Design rule (the whole point of this module): **P3 invents no quality rule.**

Every deficiency P3 can report is produced by the *existing* authoritative
machinery, and P3 only aggregates and projects what that machinery emits:

* ``engines.validation.ValidationEngine.validate_input`` — A1 completeness
  (empty activity, negative quantity, year out of range, missing unit);
* ``engines.validation.ValidationEngine.validate_snapshot`` — A2 reproducibility
  (recomputed ``quantity * co2e_multiplier``) + content-hash tamper evidence +
  A5 factor-provenance consistency;
* ``engines.validation.ValidationEngine.verify_snapshots`` — the existing A9 batch
  entry point over a set of snapshots;
* ``engines.calculation.CalculationEngine.verify`` — the existing audit-time
  reproducibility check returning ``VerificationResult(match, discrepancy,
  tampered)`` (Backend v2.1 §13).

The issue vocabulary is ``engines.validation``'s stable ``VAL_*`` codes. P3 adds
no code, no severity, no weight and **no composite score** — a single
"data quality = 87%" figure is exactly the kind of invented methodology the
authorization forbids.

Pure contract/typing + pure helpers: no I/O, no database, no provider, no
authorization decision, no SQL. Execution lives in ``services.insight_tools``.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Sequence

#: The two authorized P3 tool names (defined once, here).
TOOL_INSIGHT_DATA_QUALITY = "insight_data_quality"
TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY = "insight_calculation_reproducibility"

#: Tool name → authorized operation.
QUALITY_OPERATIONS: dict[str, str] = {
    TOOL_INSIGHT_DATA_QUALITY: "data_quality",
    TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY: "calculation_reproducibility",
}

#: Hard bound on the number of stored records one quality scan may check.
#:
#: Deliberately the *existing* I3 result bound (``MAX_RESULT_ITEMS`` = 200) rather
#: than a new product limit: a scan that could not be bounded would be an
#: unbounded analytics query, which P3 is not authorized to create. A period with
#: more records than this is reported as truncated, and every count describes the
#: records actually checked — never a fabricated population total.
MAX_QUALITY_RECORDS = 200

#: The deterministic condition names the record-level reproducibility check
#: reports. Each is a *structural presence* question about data CarbonTally
#: already retains — not an accounting rule and not a judgement.
CONDITION_SNAPSHOT_RETAINED = "calculation_snapshot_retained"
CONDITION_RESULT_RETAINED = "calculation_result_retained"
CONDITION_INPUTS_RETAINED = "calculation_inputs_retained"
CONDITION_FACTOR_REFERENCE = "factor_reference_retained"
CONDITION_METHODOLOGY_RETAINED = "methodology_and_algorithm_retained"
CONDITION_SOURCE_LINEAGE = "source_lineage_retained"
CONDITION_EVIDENCE_RESOLVABLE = "evidence_resolvable"
CONDITION_RECOMPUTATION_MATCHES = "recomputation_matches"
CONDITION_CONTENT_HASH_MATCHES = "content_hash_matches"
CONDITION_PROVENANCE_CONSISTENT = "factor_provenance_consistent"

#: Deterministic report order for the conditions above.
REPRODUCIBILITY_CONDITIONS: tuple[str, ...] = (
    CONDITION_SNAPSHOT_RETAINED,
    CONDITION_RESULT_RETAINED,
    CONDITION_INPUTS_RETAINED,
    CONDITION_FACTOR_REFERENCE,
    CONDITION_METHODOLOGY_RETAINED,
    CONDITION_SOURCE_LINEAGE,
    CONDITION_EVIDENCE_RESOLVABLE,
    CONDITION_RECOMPUTATION_MATCHES,
    CONDITION_CONTENT_HASH_MATCHES,
    CONDITION_PROVENANCE_CONSISTENT,
)

#: The stated basis strings (a figure is never presented without its basis).
QUALITY_SCAN_BASIS = (
    "stored calculation_snapshots validated by the existing ValidationEngine "
    "(A1 input completeness, A2 recomputation + content hash, A5 factor "
    "provenance), organization-scoped"
)
REPRODUCIBILITY_BASIS = (
    "stored calculation_snapshots re-checked by the existing "
    "CalculationEngine.verify and ValidationEngine.validate_snapshot (no second "
    "calculation engine, no reimplemented formula)"
)
QC_STATE_BASIS = "open Issue rows for the organization (existing QC vocabulary)"


@dataclass(frozen=True, slots=True)
class ReproducibilityCondition:
    """One deterministic reproducibility/traceability condition."""

    name: str
    satisfied: bool
    detail: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "satisfied": self.satisfied, "detail": self.detail}


def order_issue_codes(codes: Sequence[str]) -> list[str]:
    """Deterministic ordering for reported issue codes (stable, sorted).

    Sorting is deliberate: the result is a *set of findings*, and a caller must
    see the same order on every identical request.
    """
    return sorted({str(code) for code in codes})


def _decimal_or_none(value: Any) -> Optional[Decimal]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _date_or_none(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def snapshot_from_row(row: Mapping[str, Any]) -> Any:
    """Map one stored ``calculation_snapshots`` row onto the domain snapshot.

    A *field mapping* over data CarbonTally already retains, not a new rule:
    ``match_request_id`` is the stored ``request_id`` and ``created_at`` is the
    stored ``calculated_at`` (exactly what the calculation engine writes). Returns
    ``None`` when a field the domain object requires is absent, so the caller can
    report an honest "not checkable" result rather than guessing.
    """
    from domain.calculation import CalculationSnapshot

    quantity = _decimal_or_none(row.get("quantity"))
    multiplier = _decimal_or_none(row.get("co2e_multiplier"))
    co2e_kg = _decimal_or_none(row.get("co2e_kg"))
    snapshot_date = _date_or_none(row.get("date"))
    created_at = _date_or_none(row.get("calculated_at"))
    reporting_year = row.get("reporting_year")
    if (
        quantity is None
        or multiplier is None
        or co2e_kg is None
        or snapshot_date is None
        or created_at is None
        or reporting_year is None
    ):
        return None
    return CalculationSnapshot(
        id=str(row.get("id")),
        match_request_id=str(row.get("request_id") or row.get("id")),
        organization_id=str(row.get("organization_id")),
        factor_id=str(row["factor_id"]) if row.get("factor_id") else None,
        quantity=quantity,
        quantity_unit=str(row.get("quantity_unit") or ""),
        co2e_multiplier=multiplier,
        co2e_kg=co2e_kg,
        scope=str(row["scope"]) if row.get("scope") else None,
        date=snapshot_date,
        reporting_year=int(reporting_year),
        methodology=str(row.get("methodology") or ""),
        algorithm_version=str(row.get("algorithm_version") or ""),
        created_at=created_at,
        content_hash=str(row.get("content_hash") or ""),
        factor_kind=str(row.get("factor_kind") or "emission_factor"),
        customer_factor_id=(
            str(row["customer_factor_id"]) if row.get("customer_factor_id") else None
        ),
        source_file=row.get("source_file") or None,
        source_page=(
            int(row["source_page"]) if row.get("source_page") is not None else None
        ),
        source_item_id=row.get("source_item_id") or None,
        source_line_item_id=row.get("source_line_item_id") or None,
    )


def summarise_report(
    issues: Sequence[Mapping[str, Any]],
    *,
    records_checked: int,
    records_with_findings: int,
) -> dict[str, Any]:
    """Aggregate authoritative validation issues into a truthful summary.

    For every distinct code the summary states how many *records* it affects and
    the severity the validation engine assigned to it. There is deliberately no
    weighting, no ranking and no combined score, and ``records_passing`` counts
    records for which the engine reported nothing at all.
    """
    by_code: dict[str, dict[str, Any]] = {}
    for issue in issues:
        code = str(issue.get("code"))
        entry = by_code.get(code)
        if entry is None:
            entry = {
                "code": code,
                "severity": str(issue.get("severity") or ""),
                "field": str(issue.get("field") or "") or None,
                "record_count": 0,
                "entity_ids": set(),
            }
            by_code[code] = entry
        entry["record_count"] = int(entry["record_count"]) + 1
        # Attribute the finding to the stored calculation it belongs to; the
        # engine's own subject is the fallback when no record id was supplied.
        entity = issue.get("record_id") or issue.get("entity_id")
        if entity:
            entry["entity_ids"].add(str(entity))
    findings: list[dict[str, Any]] = []
    for code in order_issue_codes(list(by_code)):
        entry = by_code[code]
        entities = sorted(entry.pop("entity_ids"))
        findings.append({**entry, "affected_records": entities})
    return {
        "records_checked": int(records_checked),
        "records_with_findings": int(records_with_findings),
        "records_passing": max(0, int(records_checked) - int(records_with_findings)),
        "finding_count": len(issues),
        "distinct_finding_codes": len(findings),
        "findings": findings,
    }
