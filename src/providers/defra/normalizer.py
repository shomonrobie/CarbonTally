"""Normalisation of parsed DEFRA rows into DB-facing emission factors.

Normalisation is deliberately conservative: text is whitespace-normalised and
numbers are parsed as exact decimals. Nothing is fabricated — rows without a
published factor value are reported as skipped, never invented.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from .models import EmissionFactor, ParsedRow, SkippedRow

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
    and free-form text.
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
    """Build a deterministic, unique activity label from the published row.

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
    """Truncate a label deterministically, disambiguating with the DEFRA id.

    The published DEFRA id is appended when truncation is required so the
    activity_type remains unique and traceable to the source row.
    """
    if len(label) <= max_len:
        return label
    suffix = f" [{defra_id}]"
    if len(suffix) >= max_len:
        return label[:max_len]
    head = label[: max_len - len(suffix)].rstrip()
    return f"{head}{suffix}"


# ---------------------------------------------------------------------------
# Row normalisation
# ---------------------------------------------------------------------------
def _make_skipped(row: ParsedRow, reason: str, detail: str, activity_type: str = "") -> SkippedRow:
    return SkippedRow(
        row_number=row.row_number,
        sheet_name=row.sheet_name,
        defra_id=row.defra_id,
        reason=reason,
        detail=detail,
        activity_type=activity_type or None,
    )


def normalise_all(
    parsed_rows: list[ParsedRow],
    reporting_year: int,
    factor_source: str,
    factor_set: str,
    country: str,
) -> tuple[list[EmissionFactor], list[SkippedRow]]:
    """Convert parsed rows into normalised emission factors (or skip records)."""
    factors: list[EmissionFactor] = []
    skipped: list[SkippedRow] = []

    for row in parsed_rows:
        activity_label = build_activity_type(
            (row.level1, row.level2, row.level3, row.level4),
            row.column_text,
            row.ghg_unit,
            row.uom,
        )

        if not row.defra_id:
            skipped.append(_make_skipped(row, "no_defra_id", "Row has no DEFRA ID."))
            continue

        if not activity_label:
            skipped.append(_make_skipped(row, "no_activity_label", "Row has no level/unit labels."))
            continue

        factor = parse_decimal(row.factor_raw)
        if factor is None:
            raw_present = row.factor_raw is not None and clean_text(row.factor_raw) != ""
            if raw_present:
                skipped.append(
                    _make_skipped(
                        row,
                        "unparseable_factor",
                        f"Factor value {row.factor_raw!r} is not a valid number.",
                        activity_label,
                    )
                )
            else:
                skipped.append(
                    _make_skipped(
                        row,
                        "no_factor_value",
                        "DEFRA published no conversion factor for this row.",
                        activity_label,
                    )
                )
            continue

        activity_type = truncate_activity_type(activity_label, row.defra_id)
        unit = clean_text(row.uom) or None
        scope = clean_text(row.scope) or None

        factors.append(
            EmissionFactor(
                reporting_year=reporting_year,
                activity_type=activity_type,
                co2e_multiplier=factor,
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
                natural_key=natural_key(reporting_year, activity_type, country, unit, scope),
            )
        )

    return factors, skipped


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
