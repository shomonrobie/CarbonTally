"""CarbonTally — SEAI 2025 emission-factor provider.

Pipeline: parser -> mapper -> validator -> exporter -> loader.

* ``parser`` reads the authoritative sheet ``Conversion and emission factors``
  (single source of truth) using cached formula values.
* ``mapper`` maps the 28 published rows onto 20 canonical factors (8 skipped
  rows: 7 biogenic net-zero biofuel/biomass + Natural gas (GCV) variant).
* ``validator`` enforces the approved Implementation Gate rules (counts,
  units, scopes, electricity pair, Biodiesel ME, GCV skip, duplicates).
* ``exporter`` writes idempotent SQL/JSON artifacts and a batch-linked DB
  loader (``import_batches`` + ``import_batch_id`` per factor).

SEAI factors are CO2-only; they are stored in the existing ``co2e_multiplier``
column (the calculation contract) with CO2-only semantics preserved through
``factor_source``/``factor_set``/``(kg CO2)`` labels and batch provenance.
"""
from .models import (
    SeaiFactor,
    SeaiImportResult,
    SeaiParsedRow,
    SeaiSkip,
    SeaiValidationIssue,
    SeaiValidationReport,
    SeaiWorkbookData,
    SeaiWorkbookMeta,
    SeaiWorksheetInfo,
)
from .parser import analyze_workbook, open_workbook, parse_worksheet, workbook_sha256
from .mapper import map_all, map_row
from .validator import validate
from .exporter import (
    generate_sql,
    load_to_db,
    write_json,
    write_sql,
    write_statistics,
    write_summary,
)

__all__ = [
    "SeaiFactor",
    "SeaiImportResult",
    "SeaiParsedRow",
    "SeaiSkip",
    "SeaiValidationIssue",
    "SeaiValidationReport",
    "SeaiWorkbookData",
    "SeaiWorkbookMeta",
    "SeaiWorksheetInfo",
    "analyze_workbook",
    "open_workbook",
    "parse_worksheet",
    "workbook_sha256",
    "map_all",
    "map_row",
    "validate",
    "generate_sql",
    "load_to_db",
    "write_json",
    "write_sql",
    "write_statistics",
    "write_summary",
]
