"""Processing-workflow validation rules (V3 Phase 3).

Pure, deterministic item-level validation for the manual-extraction pipeline
(Source → Extraction → Mapping → Validation → Calculation → Review → Approval).
The engine never touches the database: it consumes a
:class:`domain.partners.ManualExtractionItem` and returns a list of
:class:`ValidationFinding` records. The API layer decides what to do with the
findings (open ``issues`` rows for errors, route items back to ``mapping`` for
rework, or advance to ``validated``).

Dependency rules: imports only from ``domain`` and the standard library — no
``data``, no ``infra``, no API layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from domain.partners import ManualExtractionItem


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """A single item-level validation finding.

    Attributes:
        code: Stable machine-readable code (``EXTRACTION_*`` / ``MAPPING_*`` /
            ``CALCULATION_*`` / ``VALIDATION_*``).
        severity: ``error`` (blocks the pipeline) or ``warning`` (informational).
        message: Human-readable description.
        field: Optional affected field name.
    """

    code: str
    severity: str
    message: str
    field: Optional[str] = None


def _findings(
    *,
    missing_fields: Optional[list[str]] = None,
    quantity_error: Optional[str] = None,
    missing_unit: bool = False,
    mapping_missing: bool = False,
    factor_missing: bool = False,
    negative_result: bool = False,
) -> list[ValidationFinding]:
    """Build the finding list (keeps the rule function readable)."""
    out: list[ValidationFinding] = []
    for field in missing_fields or []:
        out.append(
            ValidationFinding(
                "EXTRACTION_MISSING_FIELD",
                "error",
                f"missing extracted field '{field}'",
                field,
            )
        )
    if quantity_error:
        code = "NEGATIVE_QUANTITY" if quantity_error == "negative" else "INVALID_QUANTITY"
        out.append(
            ValidationFinding(code, "error", quantity_error, "quantity")
        )
    if missing_unit:
        out.append(
            ValidationFinding("MISSING_UNIT", "error", "missing unit", "unit")
        )
    if mapping_missing:
        out.append(
            ValidationFinding(
                "MAPPING_MISSING", "error", "mapped_data not recorded", "mapped_data"
            )
        )
    if factor_missing:
        out.append(
            ValidationFinding(
                "FACTOR_MISSING",
                "error",
                "no emission factor selected (emission_factor_used or mapped_data.factor_id)",
                "emission_factor_used",
            )
        )
    if negative_result:
        out.append(
            ValidationFinding(
                "NEGATIVE_RESULT",
                "error",
                "calculated emissions must be >= 0",
                "calculated_emissions_kg_co2e",
            )
        )
    return out


def validate_processing_item(
    item: ManualExtractionItem, *, require_mapping: bool = True
) -> list[ValidationFinding]:
    """Validate one processing item against the pipeline invariants.

    Multi-line documents (``extracted_data.line_items`` list) are validated
    per line (quantity/unit/activity required on each line; supplier + invoice
    date on the header) — D23. Single-line extraction keeps the legacy
    top-level fields. ``error`` findings must be resolved (and ``issues``
    opened) before the item may advance past the validation stage.
    """
    data = item.extracted_data or {}
    line_items = data.get("line_items")
    if isinstance(line_items, list) and line_items:
        return _validate_line_items(item, line_items, require_mapping=require_mapping)

    missing: list[str] = []
    for field in ("supplier", "date", "activity"):
        if not str(data.get(field) or "").strip():
            missing.append(field)

    quantity_error: Optional[str] = None
    raw_qty = data.get("quantity")
    if raw_qty in (None, ""):
        quantity_error = "missing quantity"
    else:
        try:
            qty = Decimal(str(raw_qty))
            if qty < 0:
                quantity_error = "negative"
        except (InvalidOperation, ValueError, TypeError):
            quantity_error = "invalid"

    missing_unit = not str(data.get("unit") or "").strip()

    mapped = item.mapped_data or {}
    mapping_missing = require_mapping and not mapped
    factor_missing = require_mapping and not item.emission_factor_used and not mapped.get("factor_id")

    negative_result = (
        item.calculated_emissions_kg_co2e is not None
        and item.calculated_emissions_kg_co2e < 0
    )

    return _findings(
        missing_fields=missing,
        quantity_error=quantity_error,
        missing_unit=missing_unit,
        mapping_missing=mapping_missing,
        factor_missing=factor_missing,
        negative_result=negative_result,
    )



def _validate_line_items(
    item: ManualExtractionItem,
    line_items: list,
    *,
    require_mapping: bool,
) -> list[ValidationFinding]:
    """Validate a multi-line extraction (``extracted_data.line_items``).

    Header requirements: supplier + invoice date. Per-line requirements:
    activity, quantity (numeric >= 0), unit. Amount (numeric >= 0) and
    description are optional. Mapping requirements (when ``require_mapping``):
    every line must carry a ``factor_id`` in ``mapped_data.line_items``.
    """
    findings: list[ValidationFinding] = []
    data = item.extracted_data or {}

    if not str(data.get("supplier") or "").strip():
        findings.append(
            ValidationFinding(
                "EXTRACTION_MISSING_FIELD", "error",
                "missing extracted field 'supplier'", "supplier",
            )
        )

    header_date = str(data.get("invoice_date") or data.get("date") or "").strip()
    if not header_date:
        findings.append(
            ValidationFinding(
                "EXTRACTION_MISSING_FIELD", "error",
                "missing extracted field 'invoice_date'", "invoice_date",
            )
        )

    for idx, line in enumerate(line_items):
        if not isinstance(line, dict):
            findings.append(
                ValidationFinding(
                    "EXTRACTION_INVALID_LINE", "error",
                    f"line {idx + 1} is not an object", f"line_items[{idx}]",
                )
            )
            continue
        prefix = f"line_items[{idx}]"
        if not str(line.get("activity") or "").strip():
            findings.append(
                ValidationFinding(
                    "EXTRACTION_MISSING_FIELD", "error",
                    f"line {idx + 1} missing activity", f"{prefix}.activity",
                )
            )
        raw_qty = line.get("quantity")
        if raw_qty in (None, ""):
            findings.append(
                ValidationFinding(
                    "EXTRACTION_MISSING_FIELD", "error",
                    f"line {idx + 1} missing quantity", f"{prefix}.quantity",
                )
            )
        else:
            try:
                qty = Decimal(str(raw_qty))
                if qty < 0:
                    findings.append(
                        ValidationFinding(
                            "NEGATIVE_QUANTITY", "error",
                            f"line {idx + 1} quantity is negative", f"{prefix}.quantity",
                        )
                    )
            except (InvalidOperation, ValueError, TypeError):
                findings.append(
                    ValidationFinding(
                        "INVALID_QUANTITY", "error",
                        f"line {idx + 1} quantity is invalid", f"{prefix}.quantity",
                    )
                )
        if not str(line.get("unit") or "").strip():
            findings.append(
                ValidationFinding(
                    "MISSING_UNIT", "error",
                    f"line {idx + 1} missing unit", f"{prefix}.unit",
                )
            )
        raw_amount = line.get("amount")
        if raw_amount not in (None, ""):
            try:
                if Decimal(str(raw_amount)) < 0:
                    findings.append(
                        ValidationFinding(
                            "INVALID_AMOUNT", "error",
                            f"line {idx + 1} amount is negative", f"{prefix}.amount",
                        )
                    )
            except (InvalidOperation, ValueError, TypeError):
                findings.append(
                    ValidationFinding(
                        "INVALID_AMOUNT", "error",
                        f"line {idx + 1} amount is invalid", f"{prefix}.amount",
                    )
                )

    mapped = item.mapped_data or {}
    if require_mapping:
        if not mapped:
            findings.append(
                ValidationFinding(
                    "MAPPING_MISSING", "error", "mapped_data not recorded", "mapped_data"
                )
            )
        else:
            mapped_lines = mapped.get("line_items") or []
            for idx, line in enumerate(line_items):
                ml = (
                    mapped_lines[idx]
                    if idx < len(mapped_lines) and isinstance(mapped_lines[idx], dict)
                    else {}
                )
                if not ml.get("factor_id"):
                    findings.append(
                        ValidationFinding(
                            "FACTOR_MISSING", "error",
                            f"line {idx + 1} has no emission factor selected",
                            f"mapped_data.line_items[{idx}].factor_id",
                        )
                    )

    negative_result = (
        item.calculated_emissions_kg_co2e is not None
        and item.calculated_emissions_kg_co2e < 0
    )
    if negative_result:
        findings.append(
            ValidationFinding(
                "NEGATIVE_RESULT", "error",
                "calculated emissions must be >= 0", "calculated_emissions_kg_co2e",
            )
        )
    return findings



def has_blocking_findings(findings: list[ValidationFinding]) -> bool:
    """Return ``True`` when any finding is an ``error`` (blocks the pipeline)."""
    return any(f.severity == "error" for f in findings)
