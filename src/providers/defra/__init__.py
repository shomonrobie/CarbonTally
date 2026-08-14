"""CarbonTally — DEFRA 2025 emission-factor importer.

Pipeline: parser -> mapper -> validator -> exporter.

- ``parser`` reads every worksheet (openpyxl), classifies sheets and extracts
  factor tables (pandas used for sheet statistics).
- ``mapper`` normalises rows and maps them onto ``public.emission_factors``,
  preserving DEFRA-only fields in per-factor metadata.
- ``validator`` applies DB rules and reports duplicates, missing units,
  missing activity names, invalid factors, blank rows and unsupported sheets.
- ``exporter`` writes deterministic idempotent SQL, a full-fidelity JSON
  export, a summary report, statistics and (optionally) loads the database.
"""
from .models import (
    DuplicateRow,
    EmissionFactor,
    ImportResult,
    ImportStats,
    ParsedRow,
    SkippedRow,
    ValidationIssue,
    ValidationReport,
    WorkbookAnalysis,
    WorkbookMeta,
    WorksheetInfo,
)
from .parser import (
    analyze_workbook,
    open_workbook,
    pandas_sheet_stats,
    parse_worksheet,
    sheet_dataframe,
    workbook_sha256,
)
from .mapper import map_all, map_row
from .validator import build_stats, validate_all
from .exporter import (
    load_to_db,
    write_json,
    write_sql,
    write_statistics,
    write_summary,
)

__all__ = [
    "DuplicateRow",
    "EmissionFactor",
    "ImportResult",
    "ImportStats",
    "ParsedRow",
    "SkippedRow",
    "ValidationIssue",
    "ValidationReport",
    "WorkbookAnalysis",
    "WorkbookMeta",
    "WorksheetInfo",
    "analyze_workbook",
    "open_workbook",
    "pandas_sheet_stats",
    "parse_worksheet",
    "sheet_dataframe",
    "workbook_sha256",
    "map_all",
    "map_row",
    "build_stats",
    "validate_all",
    "load_to_db",
    "write_json",
    "write_sql",
    "write_statistics",
    "write_summary",
]
