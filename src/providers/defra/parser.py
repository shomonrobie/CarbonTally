"""Parse raw worksheet rows into typed ``ParsedRow`` records.

The parser only *extracts*; it performs no decimal parsing (that is the
normaliser's job) so the published factor values are preserved verbatim.
"""
from __future__ import annotations

from typing import Any, Optional

from .models import ParsedRow, RawRow, WorksheetInfo
from .reader import FACTOR_HEADER_RE, clean_cell, iter_data_rows


def _cell_text(column_map: dict[str, int], label: str, cells: tuple[Any, ...]) -> str:
    idx = column_map.get(label)
    if idx is None:
        return ""
    value = cells[idx - 1] if idx - 1 < len(cells) else None
    return clean_cell(value)


def _raw_cell(column_map: dict[str, int], label: str, cells: tuple[Any, ...]) -> Any:
    idx = column_map.get(label)
    if idx is None:
        return None
    return cells[idx - 1] if idx - 1 < len(cells) else None


def _factor_column_label(column_map: dict[str, int]) -> Optional[str]:
    for label in column_map:
        if FACTOR_HEADER_RE.match(label):
            return label
    return None


def _build_parsed_row(raw: RawRow, column_map: dict[str, int], factor_label: str) -> ParsedRow:
    cells = raw.cells
    return ParsedRow(
        sheet_name=raw.sheet_name,
        row_number=raw.row_number,
        defra_id=_cell_text(column_map, "ID", cells),
        scope=_cell_text(column_map, "Scope", cells),
        level1=_cell_text(column_map, "Level 1", cells),
        level2=_cell_text(column_map, "Level 2", cells),
        level3=_cell_text(column_map, "Level 3", cells),
        level4=_cell_text(column_map, "Level 4", cells),
        column_text=_cell_text(column_map, "Column Text", cells),
        uom=_cell_text(column_map, "UOM", cells),
        ghg_unit=_cell_text(column_map, "GHG/Unit", cells),
        factor_raw=_raw_cell(column_map, factor_label, cells),
    )


def parse_worksheet(ws: Any, info: WorksheetInfo) -> tuple[list[ParsedRow], dict[str, int]]:
    """Parse every usable data row of one data worksheet.

    Returns ``(parsed_rows, counters)`` where counters covers rows scanned,
    empty rows, end markers, rows with an ID and rows with a factor value.
    """
    column_map = dict(info.columns)
    factor_label = _factor_column_label(column_map)
    if factor_label is None:
        raise ValueError(
            f"Worksheet {info.name!r} has no 'GHG Conversion Factor <year>' column; "
            "cannot determine the factor column."
        )

    rows: list[ParsedRow] = []
    counters: dict[str, int] = {
        "rows_scanned": 0,
        "empty_rows": 0,
        "end_marker_rows": 0,
        "rows_parsed": 0,
        "rows_with_id": 0,
        "factors_with_value": 0,
    }

    for raw in iter_data_rows(ws, info):
        counters["rows_scanned"] += 1
        if not any(c is not None and str(c).strip() for c in raw.cells):
            counters["empty_rows"] += 1
            continue
        # DEFRA terminates data sheets with a row whose scope cell reads END.
        scope_idx = column_map.get("Scope")
        if scope_idx is not None and clean_cell(raw.cells[scope_idx - 1]).upper() == "END":
            counters["end_marker_rows"] += 1
            continue

        parsed = _build_parsed_row(raw, column_map, factor_label)
        rows.append(parsed)
        counters["rows_parsed"] += 1
        if parsed.defra_id:
            counters["rows_with_id"] += 1
        if parsed.factor_raw is not None and str(parsed.factor_raw).strip():
            counters["factors_with_value"] += 1

    return rows, counters
