"""CarbonTally — DEFRA 2025 emission-factor importer (CLI).

Usage (from the repository root)::

    python -m src.commands.import_defra --no-db
    python -m src.commands.import_defra                 # write to the DB (sync)
    python -m src.commands.import_defra --mode replace  # exact, idempotent refresh

The pipeline is: read -> analyse -> parse -> normalise -> validate -> artifacts
(JSON/SQL/reports/logs) -> optional database load. Every stage is logged; the
database load is idempotent (upsert by natural key) in both ``sync`` and
``replace`` modes.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Allow ``python src/commands/import_defra.py`` and ``python -m ...`` alike.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from src.providers.defra.loader import (
    load_to_db,
    write_json_artifacts,
    write_reports,
    write_sql_artifact,
)
from src.providers.defra.models import (
    ImportResult,
    ImportStats,
    SkippedRow,
)
from src.providers.defra.normalizer import normalise_all
from src.providers.defra.parser import parse_worksheet
from src.providers.defra.reader import analyze_workbook
from src.providers.defra.validator import validate_all

logger = logging.getLogger("defra_importer")

DEFAULT_WORKBOOK = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "carbon_data_factory"
    / "docs"
    / "ghg-conversion-factors-2025-flat-format.xlsx"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "output"
DB_URL_ENV_NAMES = ("DATABASE_URL", "SUPABASE_DB_URL", "POSTGRES_URL")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="import_defra",
        description="Import the DEFRA 2025 flat-format emission factors into "
        "the CarbonTally emission_factors table.",
    )
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK,
                        help="Path to the DEFRA flat-format workbook.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT,
                        help="Root directory for json/sql/reports/logs output.")
    parser.add_argument("--year", type=int, default=None,
                        help="Override the reporting year (default: parsed from the workbook).")
    parser.add_argument("--mode", choices=("sync", "replace"), default="sync",
                        help="DB write mode: sync = upsert by natural key; "
                             "replace = delete factor set then insert.")
    parser.add_argument("--db-url", type=str, default=None,
                        help="Postgres DSN (default: $DATABASE_URL / $SUPABASE_DB_URL / $POSTGRES_URL).")
    parser.add_argument("--no-db", action="store_true",
                        help="Do not write to the database (artifacts only).")
    parser.add_argument("--country", default="GB", help="Jurisdiction for the factors (default GB).")
    parser.add_argument("--source", default="DEFRA-DESNZ",
                        help="factor_source value (default DEFRA-DESNZ).")
    parser.add_argument("--factor-set", default=None,
                        help="factor_set value (default DEFRA-<year>).")
    parser.add_argument("--log-level", default="INFO",
                        choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    return parser.parse_args(argv)


def _setup_logging(output_dir: Path, level: str) -> Path:
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"import_defra_{stamp}.log"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
    logger.info("Log file: %s", log_file)
    return log_file


def _count_skipped(skipped: list[SkippedRow], reason: str) -> int:
    return sum(1 for row in skipped if row.reason == reason)


def _build_stats(
    counters: dict[str, int],
    report_skipped: list[SkippedRow],
    duplicates: int,
    imported: int,
) -> ImportStats:
    stats = ImportStats()
    stats.rows_scanned = counters.get("rows_scanned", 0)
    stats.rows_parsed = counters.get("rows_parsed", 0)
    stats.empty_rows = counters.get("empty_rows", 0)
    stats.end_marker_rows = counters.get("end_marker_rows", 0)
    stats.rows_with_id = counters.get("rows_with_id", 0)
    stats.factors_with_value = counters.get("factors_with_value", 0)
    stats.skipped_no_factor = _count_skipped(report_skipped, "no_factor_value")
    stats.skipped_unparseable = _count_skipped(report_skipped, "unparseable_factor")
    stats.skipped_no_label = _count_skipped(report_skipped, "no_activity_label")
    stats.skipped_no_id = _count_skipped(report_skipped, "no_defra_id")
    stats.skipped_validation = _count_skipped(report_skipped, "validation_error")
    stats.duplicates = duplicates
    stats.imported = imported
    return stats



def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    load_dotenv()

    output_dir = args.output_dir.resolve()
    log_file = _setup_logging(output_dir, args.log_level)
    logger.info("DEFRA importer starting (workbook=%s)", args.workbook)

    try:
        # 1. Read + analyse ----------------------------------------------------
        wb, analysis = analyze_workbook(str(args.workbook))
        if not analysis.data_sheet_names:
            logger.error("No data worksheet found in %s; nothing to import.", args.workbook)
            wb.close()
            return 2
        logger.info(
            "Workbook analysed: %d worksheet(s), %d data sheet(s), reporting year=%s",
            len(analysis.worksheets),
            len(analysis.data_sheet_names),
            analysis.reporting_year,
        )

        reporting_year = args.year or analysis.reporting_year
        if reporting_year is None:
            logger.error(
                "Reporting year could not be determined (no factor-column header "
                "and no front-page year). Pass --year explicitly."
            )
            wb.close()
            return 2

        factor_set = args.factor_set or f"DEFRA-{reporting_year}"

        # 2. Parse every data worksheet ---------------------------------------
        parsed_rows: list = []
        counters: dict[str, int] = {
            "rows_scanned": 0, "empty_rows": 0, "end_marker_rows": 0,
            "rows_parsed": 0, "rows_with_id": 0, "factors_with_value": 0,
        }
        for ws in wb.worksheets:
            info = next((w for w in analysis.worksheets if w.name == ws.title), None)
            if info is None or info.sheet_type != "data":
                continue
            rows, sheet_counters = parse_worksheet(ws, info)
            parsed_rows.extend(rows)
            for key, value in sheet_counters.items():
                counters[key] += value
            logger.info(
                "Worksheet %r: %d rows parsed (%d scanned)",
                ws.title, sheet_counters["rows_parsed"], sheet_counters["rows_scanned"],
            )
        wb.close()
        logger.info("Total parsed rows: %d", len(parsed_rows))

        # 3. Normalise ----------------------------------------------------------
        factors, skipped = normalise_all(
            parsed_rows,
            reporting_year=reporting_year,
            factor_source=args.source,
            factor_set=factor_set,
            country=args.country,
        )
        logger.info("Normalised: %d factors, %d skipped", len(factors), len(skipped))

        # 4. Validate -------------------------------------------------------------
        report = validate_all(factors, skipped, country=args.country)
        stats = _build_stats(
            counters, report.skipped, len(report.duplicates), len(report.factors)
        )
        logger.info(
            "Validation: %d imported, %d skipped, %d duplicates",
            len(report.factors), len(report.skipped), len(report.duplicates),
        )

        # 5. Artifacts ---------------------------------------------------------------
        result = ImportResult(
            analysis=analysis,
            validation=report,
            stats=stats,
            config={
                "workbook": str(args.workbook),
                "reporting_year": reporting_year,
                "mode": args.mode,
                "no_db": args.no_db,
                "factor_source": args.source,
                "factor_set": factor_set,
                "country": args.country,
                "output_dir": str(output_dir),
                "log_file": str(log_file),
            },
        )
        write_json_artifacts(result, output_dir)
        write_sql_artifact(report.factors, output_dir)
        write_reports(result, output_dir)
        logger.info("Artifacts written under %s", output_dir)

        # 6. Database load (unless --no-db) ------------------------------------------
        if not args.no_db:
            db_url = args.db_url or next(
                (os.getenv(name) for name in DB_URL_ENV_NAMES if os.getenv(name)), None
            )
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
            try:
                db_result = load_to_db(
                    report.factors,
                    mode=args.mode,
                    db_url=db_url,
                    supabase_url=supabase_url,
                    supabase_key=supabase_key,
                )
                result.db = db_result
                logger.info(
                    "Database load complete (%s): %d inserted, %d updated",
                    db_result.get("backend"), db_result.get("inserted"), db_result.get("updated"),
                )
            except Exception as exc:  # noqa: BLE001 — degrade gracefully, artifacts persist
                result.db = {"backend": "none", "error": str(exc)}
                logger.warning("Database load skipped: %s", exc)
        else:
            logger.info("--no-db set: skipping database load (SQL artifact available).")

        # 7. Summary --------------------------------------------------------------------
        logger.info(
            "DONE — rows scanned=%d parsed=%d imported=%d skipped=%d duplicates=%d",
            stats.rows_scanned, stats.rows_parsed, stats.imported,
            len(report.skipped), len(report.duplicates),
        )
        return 0
    except Exception:
        logger.exception("Import failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
