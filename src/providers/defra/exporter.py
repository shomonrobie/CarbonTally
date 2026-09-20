"""Exporter: deterministic SQL/JSON/report artifacts and idempotent DB load.

The SQL file is the portable deliverable: one idempotent
``INSERT ... SELECT ... WHERE NOT EXISTS`` per factor, matching the RC2
natural-key unique index ``(reporting_year, activity_type, COALESCE(country,
'GB'), COALESCE(unit,'{no-unit}'), COALESCE(scope,'{no-scope}'))``. Re-running
the file never creates duplicates. The JSON export preserves the full published
row (including per-factor metadata) so no DEFRA information is lost.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from .models import EmissionFactor, ImportResult

logger = logging.getLogger(__name__)

SCHEMA = "public"
TABLE = "emission_factors"
BATCH_TABLE = "import_batches"
NO_UNIT = "{no-unit}"
NO_SCOPE = "{no-scope}"

#: Provider key recorded on ``import_batches.provider_key`` for this importer
#: (lower-case, matching the existing ``provider_key`` vocabulary: defra, seai, …).
PROVIDER_KEY = "defra"

#: Status written on a batch that is still being loaded / has finished loading.
BATCH_STATUS_IMPORTING = "importing"
BATCH_STATUS_COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class BatchProvenance:
    """Provenance for one DEFRA import batch (DEMO-T2-B).

    Mirrors the provenance the SEAI importer records, using the same
    ``import_batches`` model: provider identity + dataset version + the source
    artefact and its SHA-256 + the row accounting.

    ``rows_total`` is the number of source rows the importer resolved
    (imported + skipped + duplicates).
    """

    reporting_year: int
    provider_key: str = PROVIDER_KEY
    provider_version: str = ""
    source_file: str = ""
    source_checksum: str = ""
    rows_total: int = 0
    rows_skipped: int = 0
    rows_duplicate: int = 0


def provider_version_label(reporting_year: int, workbook_version: str = "") -> str:
    """Dataset-version label in the shape the SEAI provider already uses.

    ``"2025 (V1.7)"`` is the established form; the DEFRA flat file reports its
    own version on the front page (currently ``"1"``), so the label is derived
    from the workbook rather than invented. Falls back to the reporting year
    alone when the workbook carries no version.
    """
    version = (workbook_version or "").strip()
    if not version:
        return str(reporting_year)
    if version.upper().startswith("V"):
        return f"{reporting_year} ({version})"
    return f"{reporting_year} (V{version})"

# Query parameters psycopg2 understands; anything else (e.g. Supabase pooler's
# ``?schema=public``) is dropped so the DSN connects cleanly.
_PSYCOPG2_URI_PARAMS = {
    "sslmode", "sslrootcert", "sslcert", "sslkey", "sslpassword",
    "connect_timeout", "application_name", "options", "keepalives",
    "keepalives_idle", "target_session_attrs",
}


def _sanitize_dsn(dsn: str) -> str:
    """Return a psycopg2-compatible DSN (drops non-standard URI query params)."""
    if "?" not in dsn:
        return dsn
    base, _, query = dsn.partition("?")
    pairs = [
        item
        for item in query.split("&")
        if "=" in item and item.partition("=")[0] in _PSYCOPG2_URI_PARAMS
    ]
    return base + ("?" + "&".join(pairs) if pairs else "")


# ---------------------------------------------------------------------------
# SQL literal helpers
# ---------------------------------------------------------------------------
def _sql_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_nullable(value: Optional[str]) -> str:
    return "NULL" if value is None else _sql_str(value)


def _sql_decimal(value: Decimal) -> str:
    return format(value, "f")


# ---------------------------------------------------------------------------
# SQL generation
# ---------------------------------------------------------------------------
def generate_sql(factors: list[EmissionFactor], schema: str = SCHEMA) -> str:
    """Generate one idempotent INSERT statement per emission factor."""
    if not factors:
        return "-- No factors to import.\n"

    year = factors[0].reporting_year
    lines: list[str] = [
        "-- ============================================================================",
        f"-- CarbonTally — DEFRA {year} emission factors import (idempotent)",
        "-- Target table: public.emission_factors",
        f"-- Factor set: {factors[0].factor_set}  |  Source: {factors[0].factor_source}",
        "-- Re-running this file never creates duplicate rows: each INSERT only",
        "-- fires when no row with the same natural key already exists.",
        "-- ============================================================================",
        "",
        "BEGIN;",
        "",
    ]

    for factor in factors:
        lines.extend(_insert_statement(factor, schema))

    lines.append("")
    lines.append("COMMIT;")
    return "\n".join(lines)


def _insert_statement(factor: EmissionFactor, schema: str) -> list[str]:
    year = factor.reporting_year
    unit_lit = factor.unit or NO_UNIT
    scope_lit = factor.scope or NO_SCOPE

    where = (
        "    SELECT 1 FROM {schema}.{table}\n"
        "     WHERE reporting_year = {year}\n"
        "       AND activity_type = {label}\n"
        "       AND COALESCE(country, 'GB') = {country}\n"
        "       AND COALESCE(unit, '{no_unit}') = {unit}\n"
        "       AND COALESCE(scope, '{no_scope}') = {scope}"
    ).format(
        schema=schema,
        table=TABLE,
        year=year,
        label=_sql_str(factor.activity_type),
        country=_sql_str(factor.country or "GB"),
        no_unit=NO_UNIT,
        unit=_sql_str(unit_lit),
        no_scope=NO_SCOPE,
        scope=_sql_str(scope_lit),
    )

    insert = (
        "INSERT INTO {schema}.{table}\n"
        "    (reporting_year, activity_type, co2e_multiplier, unit, scope,\n"
        "     factor_source, factor_set, country, updated_at)\n"
        "SELECT {year}, {label}, {multiplier}, {unit}, {scope},\n"
        "       {source}, {factor_set}, {country}, NOW()\n"
        "WHERE NOT EXISTS (\n{where}\n);"
    ).format(
        schema=schema,
        table=TABLE,
        year=year,
        label=_sql_str(factor.activity_type),
        multiplier=_sql_decimal(factor.co2e_multiplier),
        unit=_sql_nullable(factor.unit),
        scope=_sql_nullable(factor.scope),
        source=_sql_str(factor.factor_source),
        factor_set=_sql_str(factor.factor_set),
        country=_sql_str(factor.country or "GB"),
        where=where,
    )

    return [
        "-- DEFRA ID {id} | source row {row} | sheet {sheet}".format(
            id=factor.defra_id, row=factor.row_number, sheet=factor.sheet_name
        ),
        insert,
        "",
    ]


def write_sql(factors: list[EmissionFactor], output_dir: Path) -> str:
    """Write ``output/sql/emission_factors.sql``; returns the written path."""
    sql_dir = output_dir / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    path = sql_dir / "emission_factors.sql"
    path.write_text(generate_sql(factors), encoding="utf-8")
    logger.info("SQL artifact written: %s", path)
    return str(path)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------
def write_json(result: ImportResult, output_dir: Path) -> str:
    """Write ``output/json/emission_factors.json`` (deterministic, full fidelity)."""
    json_dir = output_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    path = json_dir / "emission_factors.json"

    payload = {
        "source": {
            "file": result.analysis.meta.source_path,
            "sha256": result.analysis.meta.file_sha256,
            "title": result.analysis.meta.title,
            "version": result.analysis.meta.version,
            "status": result.analysis.meta.status,
            "year": result.analysis.meta.year,
        },
        "reporting_year": result.analysis.reporting_year,
        "factor_source": result.config.get("factor_source"),
        "factor_set": result.config.get("factor_set"),
        "country": result.config.get("country"),
        "count": len(result.validation.factors),
        "factors": [factor.as_dict() for factor in result.validation.factors],
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    logger.info("JSON export written: %s", path)
    return str(path)


# ---------------------------------------------------------------------------
# Markdown summary / statistics report
# ---------------------------------------------------------------------------
def _format_seconds(ms: int) -> str:
    total = max(0, ms) / 1000.0
    if total < 60:
        return f"{total:.2f}s"
    return f"{int(total // 60)}m {total % 60:.1f}s"


def write_summary(result: ImportResult, output_dir: Path) -> str:
    """Write ``output/reports/import_summary.md`` (the final report)."""
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "import_summary.md"

    stats = result.stats
    lines = [
        "# CarbonTally — DEFRA Import Summary",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"- Execution time: {_format_seconds(result.execution_time_ms)}",
        f"- Workbook: `{result.analysis.meta.source_path}`",
        f"- SHA-256: `{result.analysis.meta.file_sha256}`",
        f"- Reporting year: {result.analysis.reporting_year}",
        f"- Factor set: `{result.config.get('factor_set')}`",
        "",
        "## Sheets",
        "",
        "| Metric | Count |",
        "|---|---|",
        f"| Sheets processed | {stats.sheets_processed} |",
        f"| Data sheets | {stats.data_sheets} |",
        f"| Documentation sheets | {stats.documentation_sheets} |",
        f"| Unsupported sheets | {stats.unsupported_sheets} |",
        "",
        "## Rows",
        "",
        "| Metric | Count |",
        "|---|---|",
        f"| Rows scanned (data sheets) | {stats.rows_scanned} |",
        f"| Rows parsed | {stats.rows_parsed} |",
        f"| Blank rows | {stats.blank_rows} |",
        f"| End markers | {stats.end_marker_rows} |",
        f"| Rows with a DEFRA ID | {stats.rows_with_id} |",
        f"| Rows with a factor value | {stats.factors_with_value} |",
        "",
        "## Outcome",
        "",
        "| Metric | Count |",
        "|---|---|",
        f"| **Rows imported** | **{stats.imported}** |",
        f"| Rows skipped | {len(result.validation.skipped)} |",
        f"| Duplicates | {stats.duplicates} |",
        f"| Warnings | {stats.warnings} |",
        f"| Errors | {stats.errors} |",
        "",
    ]

    if result.validation.skipped:
        from collections import Counter

        lines.append("## Skipped rows by reason")
        lines.append("")
        lines.append("| Reason | Count |")
        lines.append("|---|---|")
        for reason, count in Counter(s.reason for s in result.validation.skipped).most_common():
            lines.append(f"| `{reason}` | {count} |")
        lines.append("")

    if result.db:
        lines.append("## Database load")
        lines.append("")
        lines.append("| Key | Value |")
        lines.append("|---|---|")
        for key, value in result.db.items():
            lines.append(f"| {key} | `{value}` |")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Summary report written: %s", path)
    return str(path)


def write_statistics(result: ImportResult, output_dir: Path) -> str:
    """Write ``output/reports/import_statistics.json`` (machine-readable)."""
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "import_statistics.json"

    payload = {
        "execution_time_ms": result.execution_time_ms,
        "sheets_processed": result.stats.sheets_processed,
        "sheets": [w.as_dict() for w in result.analysis.worksheets],
        "sheet_stats": result.sheet_stats,
        "rows_imported": result.stats.imported,
        "rows_skipped": len(result.validation.skipped),
        "skipped": [s.as_dict() for s in result.validation.skipped],
        "duplicates": result.stats.duplicates,
        "duplicate_details": [d.as_dict() for d in result.validation.duplicates],
        "warnings": result.stats.warnings,
        "errors": result.stats.errors,
        "issues": [i.as_dict() for i in result.validation.issues],
        "stats": result.stats.as_dict(),
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    logger.info("Statistics report written: %s", path)
    return str(path)



# ---------------------------------------------------------------------------
# Database loader (idempotent upsert by natural key)
#
# Provenance (DEMO-T2-B): when a :class:`BatchProvenance` is supplied, one
# ``import_batches`` row is created for the load, the factors are linked to it
# through ``import_batch_id``, the row accounting is recorded and the batch is
# activated — the same model the SEAI importer already uses. Every statement runs
# in the loader's single transaction, so a failure leaves neither factors nor a
# completed batch behind.
# ---------------------------------------------------------------------------


def _create_batch(cur: Any, provenance: BatchProvenance, schema: str) -> str:
    """Insert the batch in the ``importing`` state and return its id."""
    cur.execute(
        f"""
        INSERT INTO {schema}.{BATCH_TABLE} (
            provider_key, provider_version, source_file, source_checksum,
            reporting_year, status, rows_total, rows_imported,
            rows_skipped, rows_duplicate, errors, is_active,
            created_at, created_by, updated_at
        ) VALUES (%s, %s, %s, %s, %s, '{BATCH_STATUS_IMPORTING}',
                  %s, 0, 0, 0, NULL, FALSE, NOW(), NULL, NOW())
        RETURNING id
        """,
        (
            provenance.provider_key,
            provenance.provider_version,
            provenance.source_file,
            provenance.source_checksum,
            provenance.reporting_year,
            provenance.rows_total,
        ),
    )
    return str(cur.fetchone()[0])


def _deactivate_other_batches(
    cur: Any, provenance: BatchProvenance, batch_id: str, schema: str
) -> int:
    """Enforce the existing one-active-batch-per-provider+year rule."""
    cur.execute(
        f"""
        UPDATE {schema}.{BATCH_TABLE}
           SET is_active = FALSE, updated_at = NOW()
         WHERE provider_key = %s
           AND reporting_year = %s
           AND is_active = TRUE
           AND id <> %s
        """,
        (provenance.provider_key, provenance.reporting_year, batch_id),
    )
    return cur.rowcount


def _upsert_factor_with_batch(
    cur: Any, factor: EmissionFactor, table: str, batch_id: str
) -> bool:
    """Natural-key upsert that records the batch link; ``True`` when inserted."""
    cur.execute(
        f"""
        INSERT INTO {table} (
            reporting_year, activity_type, co2e_multiplier,
            unit, scope, factor_source, factor_set, country,
            import_batch_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (
            reporting_year, activity_type,
            COALESCE(country, 'GB'),
            COALESCE(unit, '{NO_UNIT}'),
            COALESCE(scope, '{NO_SCOPE}')
        )
        DO UPDATE SET
            co2e_multiplier = EXCLUDED.co2e_multiplier,
            unit = EXCLUDED.unit,
            scope = EXCLUDED.scope,
            factor_source = EXCLUDED.factor_source,
            factor_set = EXCLUDED.factor_set,
            import_batch_id = EXCLUDED.import_batch_id,
            updated_at = NOW()
        RETURNING (xmax = 0) AS was_inserted
        """,
        (
            factor.reporting_year,
            factor.activity_type,
            factor.co2e_multiplier,
            factor.unit,
            factor.scope,
            factor.factor_source,
            factor.factor_set,
            factor.country,
            batch_id,
        ),
    )
    return bool(cur.fetchone()[0])


def _complete_batch(
    cur: Any, provenance: BatchProvenance, batch_id: str, *, rows_imported: int, schema: str
) -> None:
    """Record the counts and activate the batch."""
    cur.execute(
        f"""
        UPDATE {schema}.{BATCH_TABLE}
           SET status = '{BATCH_STATUS_COMPLETED}',
               rows_imported = %s,
               rows_skipped = %s,
               rows_duplicate = %s,
               is_active = TRUE,
               updated_at = NOW()
         WHERE id = %s
        """,
        (rows_imported, provenance.rows_skipped, provenance.rows_duplicate, batch_id),
    )


def load_to_db(
    factors: list[EmissionFactor],
    mode: str,
    db_url: Optional[str] = None,
    schema: str = SCHEMA,
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    *,
    provenance: Optional[BatchProvenance] = None,
) -> dict[str, Any]:
    """Write factors to the database using the best available backend.

    Prefers a direct Postgres connection (psycopg2) when a DSN is supplied;
    falls back to the Supabase client (service role) when only
    ``SUPABASE_URL`` + ``SUPABASE_SERVICE_KEY`` are available.

    ``mode`` is ``sync`` (upsert by natural key) or ``replace`` (delete the
    factor set first, then insert — an exact, idempotent refresh).

    ``provenance`` (DEMO-T2-B) turns the load into a provenance-recorded import:
    one ``import_batches`` row for this dataset, every factor linked through
    ``import_batch_id``, and the row accounting recorded. Provenance requires the
    psycopg2 backend because it must share a single transaction with the factor
    writes; without a DSN the Supabase fallback is refused rather than loading
    factors with no provenance.
    """
    if db_url:
        return load_with_psycopg2(factors, mode, db_url, schema, provenance=provenance)
    if provenance is not None:
        raise RuntimeError(
            "DEFRA import provenance requires a direct Postgres connection: pass "
            "--db-url or set DATABASE_URL / SUPABASE_DB_URL / POSTGRES_URL. The "
            "Supabase client path cannot create the import_batches row in the same "
            "transaction as the factor writes."
        )
    if supabase_url and supabase_key:
        return load_with_supabase(factors, mode, supabase_url, supabase_key)
    raise RuntimeError(
        "No database credentials available. Set DATABASE_URL (or SUPABASE_DB_URL/"
        "POSTGRES_URL) for a direct connection, or SUPABASE_URL + "
        "SUPABASE_SERVICE_KEY for the Supabase client."
    )


def load_with_psycopg2(
    factors: list[EmissionFactor],
    mode: str,
    dsn: str,
    schema: str = SCHEMA,
    *,
    provenance: Optional[BatchProvenance] = None,
) -> dict[str, Any]:
    """Upsert factors through a direct Postgres connection in one transaction.

    With ``provenance`` the load is batch-recorded: the ``import_batches`` row is
    created (status ``importing``), any other active batch for the same provider +
    reporting year is deactivated, every factor is linked to the new batch, and the
    batch is completed and activated — all inside this single transaction, so a
    failure rolls the factors and the batch back together.
    """
    import psycopg2

    inserts = 0
    updates = 0
    deleted = 0
    batch_id: Optional[str] = None
    table = f"{schema}.{TABLE}"
    conn = psycopg2.connect(_sanitize_dsn(dsn), connect_timeout=15)
    try:
        with conn:
            with conn.cursor() as cur:
                if mode == "replace" and factors:
                    cur.execute(
                        f"DELETE FROM {table} WHERE factor_set = %s",
                        (factors[0].factor_set,),
                    )
                    deleted = cur.rowcount
                if provenance is not None:
                    batch_id = _create_batch(cur, provenance, schema)
                    _deactivate_other_batches(cur, provenance, batch_id, schema)
                for factor in factors:
                    if batch_id is not None:
                        if _upsert_factor_with_batch(cur, factor, table, batch_id):
                            inserts += 1
                        else:
                            updates += 1
                        continue
                    cur.execute(
                        "SELECT id FROM {table} WHERE "
                        "reporting_year = %s AND activity_type = %s AND "
                        "COALESCE(country, 'GB') = %s AND "
                        "COALESCE(unit, '{no_unit}') = %s AND "
                        "COALESCE(scope, '{no_scope}') = %s".format(
                            table=table, no_unit=NO_UNIT, no_scope=NO_SCOPE
                        ),
                        (
                            factor.reporting_year,
                            factor.activity_type,
                            factor.country or "GB",
                            factor.unit or NO_UNIT,
                            factor.scope or NO_SCOPE,
                        ),
                    )
                    existing = cur.fetchone()
                    if existing is not None:
                        cur.execute(
                            "UPDATE {table} SET co2e_multiplier = %s, unit = %s, "
                            "scope = %s, factor_source = %s, factor_set = %s, "
                            "country = %s, updated_at = NOW() WHERE id = %s".format(
                                table=table
                            ),
                            (
                                factor.co2e_multiplier,
                                factor.unit,
                                factor.scope,
                                factor.factor_source,
                                factor.factor_set,
                                factor.country,
                                existing[0],
                            ),
                        )
                        updates += 1
                    else:
                        cur.execute(
                            "INSERT INTO {table} (reporting_year, activity_type, "
                            "co2e_multiplier, unit, scope, factor_source, factor_set, "
                            "country) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)".format(
                                table=table
                            ),
                            (
                                factor.reporting_year,
                                factor.activity_type,
                                factor.co2e_multiplier,
                                factor.unit,
                                factor.scope,
                                factor.factor_source,
                                factor.factor_set,
                                factor.country,
                            ),
                        )
                        inserts += 1
                if batch_id is not None:
                    _complete_batch(
                        cur, provenance, batch_id, rows_imported=inserts, schema=schema
                    )
    finally:
        conn.close()
    result: dict[str, Any] = {
        "backend": "psycopg2",
        "mode": mode,
        "inserted": inserts,
        "updated": updates,
        "deleted_before_insert": deleted,
        "total_processed": len(factors),
    }
    if provenance is not None and batch_id is not None:
        result.update(
            {
                "batch_id": batch_id,
                "provider_key": provenance.provider_key,
                "provider_version": provenance.provider_version,
                "source_file": provenance.source_file,
                "source_checksum": provenance.source_checksum,
                "rows_total": provenance.rows_total,
                "rows_skipped": provenance.rows_skipped,
                "rows_duplicate": provenance.rows_duplicate,
            }
        )
    return result



def load_with_supabase(
    factors: list[EmissionFactor],
    mode: str,
    url: str,
    key: str,
) -> dict[str, Any]:
    """Upsert factors through the Supabase client (service role)."""
    from supabase import create_client

    client = create_client(url.strip(), key.strip())
    table = client.table(TABLE)
    inserts = 0
    updates = 0
    deleted = 0

    if mode == "replace" and factors:
        result = table.delete().eq("factor_set", factors[0].factor_set).execute()
        deleted = len(result.data or [])

    for factor in factors:
        query = (
            table.select("id")
            .eq("reporting_year", factor.reporting_year)
            .eq("activity_type", factor.activity_type)
            .eq("country", factor.country or "GB")
        )
        if factor.unit is None:
            query = query.is_("unit", None)
        else:
            query = query.eq("unit", factor.unit)
        if factor.scope is None:
            query = query.is_("scope", None)
        else:
            query = query.eq("scope", factor.scope)

        result = query.maybe_single().execute()
        existing = result.data

        multiplier = format(factor.co2e_multiplier, "f")
        if existing:
            table.update(
                {
                    "co2e_multiplier": multiplier,
                    "unit": factor.unit,
                    "scope": factor.scope,
                    "factor_source": factor.factor_source,
                    "factor_set": factor.factor_set,
                    "country": factor.country,
                    "updated_at": datetime.now().isoformat(),
                }
            ).eq("id", existing["id"]).execute()
            updates += 1
        else:
            table.insert(
                {
                    "reporting_year": factor.reporting_year,
                    "activity_type": factor.activity_type,
                    "co2e_multiplier": multiplier,
                    "unit": factor.unit,
                    "scope": factor.scope,
                    "factor_source": factor.factor_source,
                    "factor_set": factor.factor_set,
                    "country": factor.country,
                }
            ).execute()
            inserts += 1

    return {
        "backend": "supabase",
        "mode": mode,
        "inserted": inserts,
        "updated": updates,
        "deleted_before_insert": deleted,
        "total_processed": len(factors),
    }

