"""Mapper: normalise DEFRA rows and map them onto ``public.emission_factors``.

Normalisation is conservative: text is whitespace-normalised, numbers become
exact decimals, and nothing is fabricated. DEFRA fields with no column in the
target table (defra_id, level hierarchy, column text, GHG/Unit breakdown) are
preserved in ``EmissionFactor.metadata`` so no information is ever lost.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from .models import EmissionFactor, ParsedRow

NBSP = "\u00a0"
MAX_ACTIVITY_TYPE_LEN = 150  # legacy varchar(150) compatibility
NO_UNIT = "{no-unit}"
NO_SCOPE = "{no-scope}"


# ---------------------------------------------------------------------------
# Text / number helpers
# ---------------------------------------------------------------------------
def clean_text(value: object) -> str:
    """Whitespace-normalised string (also folds non-breaking spaces)."""
    if value is None:
        return ""
    text = str(value).replace(NBSP, " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_decimal(value: object) -> Optional[Decimal]:
    """Parse a DEFRA factor value into an exact Decimal.

    Returns ``None`` for blank cells and for unparseable values. Handles
    integers, floats (including scientific notation), thousands separators
    and free-form text. Precision is never rounded.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = clean_text(value)
    if not text:
        return None
    text = text.replace(",", "")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


# ---------------------------------------------------------------------------
# Activity label construction
# ---------------------------------------------------------------------------
def build_activity_type(
    levels: tuple[str, str, str, str],
    column_text: str,
    ghg_unit: str,
    uom: str,
) -> str:
    """Build a deterministic activity label from the published row.

    Layout: ``Level 1 > Level 2 > Level 3 > Level 4 - Column Text (GHG/Unit) [UOM]``.
    Empty parts are omitted so the label stays compact and faithful.
    """
    parts = [clean_text(part) for part in levels if clean_text(part)]
    label = " > ".join(parts)

    column = clean_text(column_text)
    if column:
        label = f"{label} - {column}" if label else column

    ghg = clean_text(ghg_unit)
    if ghg:
        label = f"{label} ({ghg})" if label else ghg

    unit = clean_text(uom)
    if unit:
        label = f"{label} [{unit}]" if label else unit

    return label


def truncate_activity_type(label: str, defra_id: str, max_len: int = MAX_ACTIVITY_TYPE_LEN) -> str:
    """Truncate a label deterministically, disambiguating with the DEFRA id."""
    if len(label) <= max_len:
        return label
    suffix = f" [{defra_id}]"
    if len(suffix) >= max_len:
        return label[:max_len]
    head = label[: max_len - len(suffix)].rstrip()
    return f"{head}{suffix}"


# ---------------------------------------------------------------------------
# Natural key (mirrors the RC2 unique index semantics)
# ---------------------------------------------------------------------------
def natural_key(
    reporting_year: int,
    activity_type: str,
    country: str,
    unit: Optional[str],
    scope: Optional[str],
) -> tuple[str, ...]:
    """Natural key used for idempotency and duplicate detection."""
    return (
        str(reporting_year),
        activity_type,
        country or "GB",
        unit or NO_UNIT,
        scope or NO_SCOPE,
    )



# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------
def build_metadata(row: ParsedRow) -> dict[str, object]:
    """DEFRA fields with no column in ``emission_factors``, preserved as JSON."""
    return {
        "defra_id": row.defra_id,
        "level1": row.level1,
        "level2": row.level2,
        "level3": row.level3,
        "level4": row.level4,
        "column_text": row.column_text,
        "ghg_unit": row.ghg_unit,
        "uom": row.uom,
        "scope": row.scope,
        "sheet_name": row.sheet_name,
        "row_number": row.row_number,
        "raw_factor_value": clean_text(row.factor_raw),
    }


def map_row(
    row: ParsedRow,
    reporting_year: int,
    factor_source: str,
    factor_set: str,
    country: str,
) -> EmissionFactor:
    """Map one parsed row onto an ``EmissionFactor`` (skip_reason may be set)."""
    factor = parse_decimal(row.factor_raw)
    metadata = build_metadata(row)
    unit = clean_text(row.uom) or None
    scope = clean_text(row.scope) or None
    activity_label = build_activity_type(
        (row.level1, row.level2, row.level3, row.level4),
        row.column_text,
        row.ghg_unit,
        row.uom,
    )

    skip_reason: Optional[str] = None
    if not row.defra_id:
        skip_reason = "no_defra_id"
    elif not activity_label:
        skip_reason = "no_activity_name"
    elif factor is None:
        skip_reason = "invalid_factor" if clean_text(row.factor_raw) else "no_factor_value"
    elif factor < 0:
        skip_reason = "invalid_factor"

    activity_type = (
        truncate_activity_type(activity_label, row.defra_id) if activity_label else ""
    )
    return EmissionFactor(
        reporting_year=reporting_year,
        activity_type=activity_type,
        co2e_multiplier=factor if factor is not None else Decimal(0),
        unit=unit,
        scope=scope,
        factor_source=factor_source,
        factor_set=factor_set,
        country=country,
        defra_id=row.defra_id,
        level1=row.level1,
        level2=row.level2,
        level3=row.level3,
        level4=row.level4,
        column_text=row.column_text,
        uom=row.uom,
        ghg_unit=row.ghg_unit,
        row_number=row.row_number,
        sheet_name=row.sheet_name,
        natural_key=(
            natural_key(reporting_year, activity_type, country, unit, scope)
            if skip_reason is None
            else ()
        ),
        skip_reason=skip_reason,
        metadata=metadata,
    )


def map_all(
    parsed_rows: list[ParsedRow],
    reporting_year: int,
    factor_source: str,
    factor_set: str,
    country: str,
) -> list[EmissionFactor]:
    """Map every parsed row to an ``EmissionFactor`` (skipped rows carry a reason)."""
    return [
        map_row(row, reporting_year, factor_source, factor_set, country)
        for row in parsed_rows
    ]
