"""CarbonTally — DEFRA 2025 emission-factor importer (CLI).

Usage (from the repository root)::

    python -m src.commands.import_defra --no-db        # artifacts only
    python -m src.commands.import_defra                # artifacts + DB sync
    python -m src.commands.import_defra --mode replace # exact, idempotent refresh

Pipeline: parse every worksheet -> map to emission_factors -> validate -> export
(SQL / JSON / reports) -> optional idempotent database load. Re-running the
importer never produces duplicate rows, duplicate SQL or duplicate JSON.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Allow ``python src/commands/import_defra.py`` and ``python -m ...`` alike.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from src.providers.defra import (
    analyze_workbook,
    build_stats,
    load_to_db,
    map_all,
    pandas_sheet_stats,
    parse_worksheet,
    validate_all,
    write_json,
    write_sql,
    write_statistics,
    write_summary,
)
from src.providers.defra.models import ImportResult

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
PROGRESS_INTERVAL = 500  # rows between progress log lines


class ProgressReporter:
    """Lightweight progress reporting: per-sheet and periodic row progress."""

    def __init__(self, log: logging.Logger, interval: int = PROGRESS_INTERVAL) -> None:
        self.log = log
        self.interval = interval
        self.sheet = ""

    def start_sheet(self, name: str, expected: int) -> None:
        self.sheet = name
        self.log.info("Parsing sheet %r (%d rows below header)...", name, expected)

    def rows_done(self, count: int) -> None:
        if count and count % self.interval == 0:
            self.log.info("  %s: %d rows parsed so far", self.sheet, count)

    def finish_sheet(self, parsed: int) -> None:
        self.log.info("  %s: %d rows parsed", self.sheet, parsed)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="import_defra",
        description="Import the DEFRA 2025 flat-format emission factors into "
        "the CarbonTally emission_factors table.",
    )
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK,
                        help="Path to the DEFRA flat-format workbook.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT,
                        help="Root directory for sql/json/reports/logs output.")
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
    stamp = time.strftime("%Y%m%d_%H%M%S")
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


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    started = time.monotonic()

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    load_dotenv()

    output_dir = args.output_dir.resolve()
    log_file = _setup_logging(output_dir, args.log_level)
    logger.info("DEFRA importer starting (workbook=%s)", args.workbook)

    try:
        # 1. Parse: read + analyse every worksheet ----------------------------
        wb, analysis = analyze_workbook(str(args.workbook))
        logger.info(
            "Workbook analysed: %d worksheet(s) — %d data, %d documentation, %d unsupported; "
            "reporting year=%s",
            len(analysis.worksheets),
            sum(1 for w in analysis.worksheets if w.sheet_type == "data"),
            sum(1 for w in analysis.worksheets if w.sheet_type == "documentation"),
            sum(1 for w in analysis.worksheets if w.sheet_type == "unsupported"),
            analysis.reporting_year,
        )

        reporting_year = args.year or analysis.reporting_year
        if reporting_year is None:
            logger.error(
                "Reporting year could not be determined. Pass --year explicitly."
            )
            wb.close()
            return 2

        factor_set = args.factor_set or f"DEFRA-{reporting_year}"

        parsed_rows: list = []
        counters: dict[str, int] = {
            "rows_scanned": 0, "empty_rows": 0, "end_marker_rows": 0,
            "rows_parsed": 0, "rows_with_id": 0, "factors_with_value": 0,
        }
        sheet_stats: dict[str, dict] = {}
        progress = ProgressReporter(logger)

        for ws in wb.worksheets:
            info = next((w for w in analysis.worksheets if w.name == ws.title), None)
            if info is None or info.sheet_type != "data":
                continue
            progress.start_sheet(ws.title, info.data_row_count or 0)
            rows, sheet_counters = parse_worksheet(ws, info)
            parsed_rows.extend(rows)
            for key, value in sheet_counters.items():
                counters[key] += value
            progress.rows_done(len(rows))
            progress.finish_sheet(len(rows))
            sheet_stats[ws.title] = pandas_sheet_stats(rows)
        wb.close()
        logger.info("Total parsed rows across all data sheets: %d", len(parsed_rows))

        # 2. Map: normalise + map onto emission_factors -----------------------
        mapped = map_all(
            parsed_rows,
            reporting_year=reporting_year,
            factor_source=args.source,
            factor_set=factor_set,
            country=args.country,
        )
        logger.info("Mapped %d rows (skipped rows carry a reason)", len(mapped))

        # 3. Validate: DB rules + duplicates -----------------------------------
        report = validate_all(mapped, country=args.country)
        stats = build_stats(report, analysis, counters)
        logger.info(
            "Validation: %d imported, %d skipped, %d duplicates, %d warnings",
            len(report.factors), len(report.skipped), len(report.duplicates), stats.warnings,
        )

        # 4. Export: SQL / JSON / reports ----------------------------------------
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
            sheet_stats=sheet_stats,
            execution_time_ms=int((time.monotonic() - started) * 1000),
        )
        write_sql(report.factors, output_dir)
        write_json(result, output_dir)
        logger.info("SQL + JSON artifacts written under %s", output_dir)

        # 5. Database load (unless --no-db) ----------------------------------------
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
                    db_result.get("backend"), db_result.get("inserted"),
                    db_result.get("updated"),
                )
            except Exception as exc:  # noqa: BLE001 — degrade gracefully, artifacts persist
                result.db = {"backend": "none", "error": str(exc)}
                logger.warning("Database load skipped: %s", exc)
        else:
            logger.info("--no-db set: skipping database load (SQL artifact available).")

        # 6. Final reports (after the DB step so they include its result + full time)
        result.execution_time_ms = int((time.monotonic() - started) * 1000)
        write_summary(result, output_dir)
        write_statistics(result, output_dir)
        logger.info(
            "DONE — sheets=%d imported=%d skipped=%d duplicates=%d warnings=%d errors=%d "
            "elapsed=%dms",
            stats.sheets_processed, stats.imported, len(report.skipped),
            stats.duplicates, stats.warnings, stats.errors, result.execution_time_ms,
        )
        return 0
    except Exception:
        logger.exception("Import failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

