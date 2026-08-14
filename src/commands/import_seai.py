"""CarbonTally — SEAI 2025 emission-factor importer (CLI).

Usage (from the repository root)::

    python -m src.commands.import_seai --no-db        # artifacts only
    python -m src.commands.import_seai --db-url <dsn>  # artifacts + DB load
    python -m src.commands.import_seai --db-url <dsn> --mode replace

The importer reads the authoritative sheet ``Conversion and emission factors``
(2025), maps the 28 published rows onto the 20 canonical factors, skips the 8
non-importable rows, and (unless ``--no-db``) loads them through a
batch-linked, idempotent upsert that creates an ``import_batches`` record and
sets ``import_batch_id`` on every imported factor.

Unlike the legacy DEFRA CLI, the SEAI importer REQUIRES an explicit database
URL for any DB load (``--db-url`` or the ``SEAI_DATABASE_URL`` environment
variable) so an accidental load against the wrong database is avoided.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.providers.seai import (
    analyze_workbook,
    load_to_db,
    map_all,
    validate,
    write_json,
    write_sql,
    write_statistics,
    write_summary,
)
from src.providers.seai.models import SeaiImportResult

logger = logging.getLogger("seai_importer")

DEFAULT_WORKBOOK = (
    Path(__file__).resolve().parents[2]
    / "tools"
    / "carbon_data_factory"
    / "docs"
    / "SEAI-conversion-and-emission-factors.xlsx"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "output" / "seai_2025"
DB_URL_ENV_NAMES = ("SEAI_DATABASE_URL", "DATABASE_URL", "SUPABASE_DB_URL")

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="import_seai",
        description="Import the SEAI 2025 energy conversion and emission "
        "factors into the CarbonTally emission_factors table.",
    )
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK,
                        help="Path to the SEAI workbook.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT,
                        help="Root directory for sql/json/reports output.")
    parser.add_argument("--mode", choices=("sync", "replace"), default="sync",
                        help="DB write mode: sync = natural-key upsert; "
                             "replace = delete SEAI-2025/IE rows then insert.")
    parser.add_argument("--db-url", type=str, default=None,
                        help="Postgres DSN (default: $SEAI_DATABASE_URL / "
                             "$DATABASE_URL / $SUPABASE_DB_URL).")
    parser.add_argument("--no-db", action="store_true",
                        help="Generate artifacts only; do not touch the database.")
    parser.add_argument("--source-file", type=str, default="",
                        help="Override the source_file recorded on the batch "
                             "(defaults to the workbook path).")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    started = time.monotonic()
    try:
        workbook = analyze_workbook(args.workbook)
        factors, skipped = map_all(list(workbook.rows))
        report = validate(factors, skipped)
        if not report.ok:
            for issue in report.issues:
                logger.error("validation: %s — %s", issue.severity, issue.message)
            return 1

        result = SeaiImportResult(
            workbook=workbook,
            validation=report,
            config={
                "workbook": str(args.workbook),
                "reporting_year": workbook.meta.reporting_year or 2025,
                "factor_source": "SEAI",
                "factor_set": "SEAI-2025",
                "country": "IE",
                "mode": args.mode,
                "no_db": args.no_db,
                "output_dir": str(args.output_dir),
            },
        )

        write_sql(report.factors, args.output_dir)
        write_json(result, args.output_dir)
        logger.info(
            "SEAI mapping: %d imported, %d skipped, %d duplicates, %d errors",
            len(report.factors), len(report.skipped),
            len(report.duplicates), report.errors,
        )

        if not args.no_db:
            db_url = args.db_url or next(
                (os.getenv(name) for name in DB_URL_ENV_NAMES if os.getenv(name)), None
            )
            if not db_url:
                logger.error(
                    "no database URL provided: pass --db-url or set "
                    "SEAI_DATABASE_URL / DATABASE_URL / SUPABASE_DB_URL"
                )
                return 2
            source_file = args.source_file or str(args.workbook)
            db_result = load_to_db(
                report.factors,
                report.skipped,
                db_url,
                source_file=source_file,
                source_checksum=workbook.meta.file_sha256,
                mode=args.mode,
            )
            result.db = db_result
            logger.info(
                "Database load complete (batch %s): %d inserted, %d updated, "
                "%d deleted",
                db_result.get("batch_id"), db_result.get("inserted"),
                db_result.get("updated"), db_result.get("deleted_before_insert"),
            )
        else:
            logger.info("--no-db set: skipping database load (SQL artifact available).")

        result.execution_time_ms = int((time.monotonic() - started) * 1000)
        write_summary(result, args.output_dir)
        write_statistics(result, args.output_dir)
        logger.info(
            "DONE — imported=%d skipped=%d duplicates=%d errors=%d elapsed=%dms",
            len(report.factors), len(report.skipped),
            len(report.duplicates), report.errors, result.execution_time_ms,
        )
        return 0
    except Exception:
        logger.exception("SEAI import failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

