"""D33.1 — authorized evidence-record presentation for emission results.

Pure, unit-testable builders that turn persisted provenance into a human-readable
evidence record WITHOUT exposing the database. The record distinguishes ORIGINAL
source data from CarbonTally-derived data and classifies evidence completeness
honestly from the actual persisted fields (never fabricated).

Chain presented: source document -> extracted line -> mapping -> emission factor
-> calculation -> emission result, with an optional technical-details block of
stable record identifiers for auditors/advanced customers.
"""
from __future__ import annotations

from typing import Any, Optional

# ---------------------------------------------------------------------------
# Evidence completeness (derived from actual persisted provenance)
# ---------------------------------------------------------------------------


def classify_evidence_completeness(
    *,
    has_document: bool,
    has_item: bool,
    has_calculation: bool,
    has_factor: bool,
    has_page: bool,
) -> tuple[str, str]:
    """Classify evidence completeness as COMPLETE / PARTIAL / UNAVAILABLE.

    COMPLETE requires document + extracted line + calculation + factor AND an
    exact source location (page). PARTIAL covers a valid chain without an exact
    page/location. UNAVAILABLE means no reliable source provenance exists.
    """
    if has_document and has_item and has_calculation and has_factor:
        if has_page:
            return (
                "COMPLETE",
                "Document + extracted line + source page + calculation + factor.",
            )
        return (
            "PARTIAL",
            "Document + extracted line + calculation + factor "
            "(exact page/location not available).",
        )
    if has_document or has_item or has_calculation:
        return (
            "PARTIAL",
            "Some provenance is available but the evidence chain is incomplete.",
        )
    return "UNAVAILABLE", "No reliable source provenance."


def source_location_precision(
    *,
    has_document: bool,
    page: Optional[int],
    has_item: bool,
    sheet: Optional[str] = None,
    row: Optional[str] = None,
    column: Optional[str] = None,
    json_path: Optional[str] = None,
) -> dict[str, Any]:
    """Report source-location precision HONESTLY (never fabricate).

    Returns the available precision plus a human-readable display string.
    """
    present = []
    if has_document:
        present.append("document")
    if page is not None:
        present.append(f"page {page}")
    if sheet is not None:
        present.append(f"sheet {sheet}")
    if row is not None:
        present.append(f"row {row}")
    if column is not None:
        present.append(f"column {column}")
    if json_path is not None:
        present.append(f"JSON path {json_path}")

    if has_item:
        present.append("extracted line")
        if page is None and sheet is None and row is None:
            display = "Source line available; page/location not available."
        else:
            display = "Source document + line with location: " + ", ".join(present) + "."
    elif has_document:
        display = "Source document available; exact source location not available."
    else:
        display = "No source document available."

    return {
        "document_available": bool(has_document),
        "page": page,
        "sheet": sheet,
        "row": row,
        "column": column,
        "json_path": json_path,
        "line_available": bool(has_item),
        "precision": ", ".join(present) if present else "none",
        "display": display,
    }


def _calc_formula(
    quantity: Any,
    unit: Any,
    multiplier: Any,
    result: Any,
) -> str:
    """Human-readable formula, e.g. ``500 kWh × 0.00028 = 0.140 kg CO₂e``."""
    q = "" if quantity is None else str(quantity)
    u = "" if unit is None else f" {unit}"
    m = "" if multiplier is None else str(multiplier)
    r = "" if result is None else str(result)
    return f"{q}{u} × {m} = {r} kg CO₂e"
# ---------------------------------------------------------------------------
# Evidence record
# ---------------------------------------------------------------------------


def build_evidence_record(
    *,
    emission: Any,
    snapshot: Optional[dict],
    item: Any,
    file_row: Any,
    factor: Any,
    customer_factor: Any,
) -> dict[str, Any]:
    """Build the authorized evidence record for one emission result.

    Sections carry an ``origin`` marker — ``original`` (customer source) vs
    ``derived`` (CarbonTally mapping/factor/calculation). The record exposes
    stable record identifiers in a scoped ``technical_details`` block.
    """
    extracted = (item.extracted_data or {}) if item is not None else {}
    mapped = (item.mapped_data or {}) if item is not None else {}

    # Defensive field access — callers may pass minimal item-like objects.
    def _ig(name: str, default=None):
        return getattr(item, name, default) if item is not None else default

    page = (snapshot or {}).get("source_page")
    sheet = None
    row = None
    column = None
    json_path = None
    loc = (snapshot or {}).get("source_location") or {}
    if isinstance(loc, dict):
        sheet = loc.get("sheet")
        row = loc.get("row")
        column = loc.get("column")
        json_path = loc.get("json_path")

    has_document = file_row is not None
    has_item = item is not None
    has_calculation = snapshot is not None
    has_factor = (factor is not None) or (customer_factor is not None)
    completeness, completeness_reason = classify_evidence_completeness(
        has_document=has_document,
        has_item=has_item,
        has_calculation=has_calculation,
        has_factor=has_factor,
        has_page=page is not None,
    )
    location = source_location_precision(
        has_document=has_document,
        page=page,
        has_item=has_item,
        sheet=sheet,
        row=row,
        column=column,
        json_path=json_path,
    )

    # --- SOURCE DOCUMENT (original) ---
    source_document: dict[str, Any] = {
        "origin": "original",
        "label": "SOURCE DOCUMENT",
        "fields": {
            "document_name": (file_row.name if file_row else None),
            "document_id": (file_row.id if file_row else None),
            "file_type": (file_row.file_type if file_row else None),
            "supplier": extracted.get("supplier"),
            "document_date": extracted.get("date") or (snapshot or {}).get("date"),
            "invoice_reference": (
                extracted.get("invoice_number")
                or extracted.get("reference")
                or (
                    (file_row.metadata or {}).get("invoice_number")
                    if file_row is not None
                    else None
                )
            ),
            "uploaded_at": (file_row.uploaded_at if file_row else None),
        },
    }

    # --- ORIGINAL EXTRACTED DATA (original) ---
    extraction: dict[str, Any] = {
        "origin": "original",
        "label": "ORIGINAL EXTRACTED DATA",
        "fields": {
            "extraction_item_id": (item.id if item else None),
            "activity": extracted.get("activity"),
            "quantity": extracted.get("quantity"),
            "unit": extracted.get("unit"),
            "original_value": (
                f"{extracted.get('quantity')} {extracted.get('unit') or ''}".strip()
                if extracted.get("quantity") is not None
                else None
            ),
            "extraction_status": _ig("status"),
            "extracted_by": _ig("extracted_by"),
            "extracted_at": _ig("extracted_at"),
        },
    }

    # --- MAPPING (derived) ---
    mapping: dict[str, Any] = {
        "origin": "derived",
        "label": "CARBONTALLY MAPPING",
        "fields": {
            "mapped_activity": (snapshot or {}).get("activity")
            or mapped.get("activity_type"),
            "activity_type": (snapshot or {}).get("activity_type")
            or mapped.get("activity_type"),
            "mapping_status": _ig("status"),
            "mapped_facility_id": _ig("mapped_facility_id"),
            "mapped_asset_id": _ig("mapped_asset_id"),
            "mapped_supplier_id": _ig("mapped_supplier_id"),
        },
    }
    # --- EMISSION FACTOR (derived) ---
    if customer_factor is not None:
        factor_id = customer_factor.id
        factor_name = customer_factor.name or customer_factor.activity_type
        factor_source = customer_factor.factor_source or "CUSTOMER"
        factor_set = None
        factor_year = customer_factor.reporting_year
        factor_unit = customer_factor.unit
        factor_value = customer_factor.co2e_multiplier
        factor_scope = customer_factor.scope
        factor_country = customer_factor.country
    elif factor is not None:
        factor_id = factor.id
        factor_name = factor.activity_type
        factor_source = factor.factor_source
        factor_set = factor.factor_set
        factor_year = factor.reporting_year
        factor_unit = factor.unit
        factor_value = factor.co2e_multiplier
        factor_scope = factor.scope
        factor_country = factor.country
    else:
        factor_id = None
        factor_name = (snapshot or {}).get("factor_source")
        factor_source = (snapshot or {}).get("factor_source")
        factor_set = (snapshot or {}).get("factor_set")
        factor_year = None
        factor_unit = (snapshot or {}).get("quantity_unit")
        factor_value = (snapshot or {}).get("co2e_multiplier")
        factor_scope = (snapshot or {}).get("scope")
        factor_country = None

    emission_factor: dict[str, Any] = {
        "origin": "derived",
        "label": "EMISSION FACTOR",
        "fields": {
            "factor_id": factor_id,
            "factor_name": factor_name,
            "factor_source": factor_source,
            "factor_set": factor_set,
            "reporting_year": factor_year,
            "factor_unit": factor_unit,
            "factor_value": factor_value,
            "scope": factor_scope,
            "country": factor_country,
        },
    }

    # --- CALCULATION (derived) ---
    calc = snapshot or {}
    calculation: dict[str, Any] = {
        "origin": "derived",
        "label": "CALCULATION",
        "fields": {
            "calculation_snapshot_id": calc.get("id"),
            "inputs": {
                "quantity": calc.get("quantity"),
                "unit": calc.get("quantity_unit"),
                "multiplier": calc.get("co2e_multiplier"),
            },
            "formula": _calc_formula(
                calc.get("quantity"),
                calc.get("quantity_unit"),
                calc.get("co2e_multiplier"),
                calc.get("co2e_kg"),
            ),
            "result_kg_co2e": calc.get("co2e_kg"),
            "methodology": calc.get("methodology"),
            "algorithm_version": calc.get("algorithm_version"),
            "calculated_at": calc.get("calculated_at"),
            "calculated_by": calc.get("calculated_by"),
        },
    }

    # --- EMISSION RESULT (derived) ---
    result: dict[str, Any] = {
        "origin": "derived",
        "label": "EMISSION RESULT",
        "fields": {
            "emission_log_id": emission.id,
            "co2e_kg": emission.calculated_kg_co2e,
            "scope": emission.scope,
            "date": emission.date,
            "snapshot_id": emission.snapshot_id,
        },
    }

    technical_details = {
        "emission_log_id": emission.id,
        "calculation_snapshot_id": calc.get("id"),
        "manual_extraction_item_id": (item.id if item else None),
        "organization_file_id": (file_row.id if file_row else None),
        "emission_factor_id": factor_id,
        "source_file": calc.get("source_file"),
        "source_page": page,
        "calculation": {
            "methodology": calc.get("methodology"),
            "algorithm_version": calc.get("algorithm_version"),
            "content_hash": calc.get("content_hash"),
            "calculated_at": calc.get("calculated_at"),
            "calculated_by": calc.get("calculated_by"),
            "request_id": calc.get("request_id"),
        },
    }

    return {
        "completeness": completeness,
        "completeness_reason": completeness_reason,
        "source_location": location,
        "sections": {
            "source_document": source_document,
            "extraction": extraction,
            "mapping": mapping,
            "emission_factor": emission_factor,
            "calculation": calculation,
            "result": result,
        },
        "technical_details": technical_details,
    }


