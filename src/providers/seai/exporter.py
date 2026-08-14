"""SEAI exporter: SQL/JSON artifacts and idempotent batch-linked DB load.

Unlike the legacy DEFRA loader, the SEAI loader **creates an ``import_batches``
record** and sets ``import_batch_id`` on every imported factor, so
``provider_key='seai'`` is correctly derived by the factor repository and full
provenance (provider, version, source file, checksum, counts) is recorded.

Idempotency: factor upserts use the RC2 natural-key ``ON CONFLICT`` path
(repeated runs never create duplicates); each run creates a new batch and
re-points the factors at it (batches are immutable provenance records, one
active batch per provider+year).
"""
from __future__ import annotations

import json
import logging
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from .models import (
    COUNTRY,
    EXPECTED_IMPORTED,
    EXPECTED_SKIPPED,
    FACTOR_SET,
    FACTOR_SOURCE,
    PROVIDER_KEY,
    PROVIDER_VERSION,
    REPORTING_YEAR,
    SeaiFactor,
    SeaiImportResult,
    SeaiSkip,
)

logger = logging.getLogger("seai_importer")

SCHEMA = "public"
TABLE = "emission_factors"
NO_UNIT = "{no-unit}"
NO_SCOPE = "{no-scope}"


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
# SQL generation (idempotent artifact)
# ---------------------------------------------------------------------------
def generate_sql(factors: list[SeaiFactor], schema: str = SCHEMA) -> str:
    """One idempotent ``INSERT ... WHERE NOT EXISTS`` per SEAI factor.

    Note: the static SQL artifact is batch-less (like the DEFRA artifact). The
    batch-linked import is performed by :func:`load_to_db` (the runtime loader).
    """
    lines: list[str] = [
        "-- ============================================================================",
        f"-- CarbonTally — SEAI {REPORTING_YEAR} emission factors import (idempotent)",
        "-- Target table: public.emission_factors",
        f"-- Factor set: {FACTOR_SET}  |  Source: {FACTOR_SOURCE}  |  Country: {COUNTRY}",
        "-- CO2-only factors. Re-running never creates duplicates.",
        "-- ============================================================================",
        "",
        "BEGIN;",
        "",
    ]
    for f in factors:
        lines.extend(_insert_statement(f, schema))
    lines.append("")
    lines.append("COMMIT;")
    return "\n".join(lines)


def _insert_statement(f: SeaiFactor, schema: str) -> list[str]:
    unit_lit = f.unit or NO_UNIT
    scope_lit = f.scope or NO_SCOPE
    where = (
        "    SELECT 1 FROM {schema}.{table}\n"
        "     WHERE reporting_year = {year}\n"
        "       AND activity_type = {label}\n"
        "       AND COALESCE(country, 'GB') = {country}\n"
        "       AND COALESCE(unit, '{no_unit}') = {unit}\n"
        "       AND COALESCE(scope, '{no_scope}') = {scope}"
    ).format(
        schema=schema, table=TABLE, year=f.reporting_year,
        label=_sql_str(f.activity_type), country=_sql_str(f.country or "GB"),
        no_unit=NO_UNIT, unit=_sql_str(unit_lit),
        no_scope=NO_SCOPE, scope=_sql_str(scope_lit),
    )
    insert = (
        "INSERT INTO {schema}.{table}\n"
        "    (reporting_year, activity_type, co2e_multiplier, unit, scope,\n"
        "     factor_source, factor_set, country, updated_at)\n"
        "SELECT {year}, {label}, {multiplier}, {unit}, {scope},\n"
        "       {source}, {factor_set}, {country}, NOW()\n"
        "WHERE NOT EXISTS (\n{where}\n);"
    ).format(
        schema=schema, table=TABLE, year=f.reporting_year,
        label=_sql_str(f.activity_type), multiplier=_sql_decimal(f.co2e_multiplier),
        unit=_sql_nullable(f.unit), scope=_sql_nullable(f.scope),
        source=_sql_str(f.factor_source), factor_set=_sql_str(f.factor_set),
        country=_sql_str(f.country or "GB"), where=where,
    )
    return [
        f"-- SEAI source row {f.source_row} | {f.source_name} | basis {f.basis}",
        insert,
        "",
    ]


def write_sql(factors: list[SeaiFactor], output_dir: Path) -> str:
    sql_dir = output_dir / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    path = sql_dir / "emission_factors_seai_2025.sql"
    path.write_text(generate_sql(factors), encoding="utf-8")
    return str(path)


def write_json(result: SeaiImportResult, output_dir: Path) -> str:
    json_dir = output_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    path = json_dir / "emission_factors_seai_2025.json"
    path.write_text(
        json.dumps(result.as_dict(), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return str(path)


def write_summary(result: SeaiImportResult, output_dir: Path) -> str:
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "import_summary_seai_2025.md"
    meta = result.workbook.meta
    lines = [
        "# CarbonTally — SEAI Import Summary (2025)",
        "",
        f"- Workbook: `{meta.source_path}`",
        f"- SHA-256: `{meta.file_sha256}`",
        f"- Reporting year: {REPORTING_YEAR}",
        f"- Factor set: `{FACTOR_SET}`  |  Source: `{FACTOR_SOURCE}`  |  Country: `{COUNTRY}`",
        f"- Import batch: {result.db.get('batch_id', 'n/a')}",
        "",
        "| Metric | Count |",
        "|---|---|",
        f"| Source rows (authoritative sheet) | {len(result.workbook.rows)} |",
        f"| **Imported factors** | **{len(result.validation.factors)}** |",
        f"| Skipped rows | {len(result.validation.skipped)} |",
        f"| Duplicates | {len(result.validation.duplicates)} |",
        f"| Validation errors | {result.validation.errors} |",
        "",
        "## Skipped rows",
        "",
        "| Row | Name | Reason |",
        "|---|---|---|",
    ]
    for s in result.validation.skipped:
        lines.append(f"| {s.row_number} | {s.name} | {s.reason} |")
    lines.append("")
    if result.db:
        lines.append("## Database load")
        lines.append("")
        lines.append("| Key | Value |")
        lines.append("|---|---|")
        for k, v in result.db.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def write_statistics(result: SeaiImportResult, output_dir: Path) -> str:
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "import_statistics_seai_2025.json"
    payload = {
        "reporting_year": REPORTING_YEAR,
        "factor_source": FACTOR_SOURCE,
        "factor_set": FACTOR_SET,
        "source_rows": len(result.workbook.rows),
        "imported": len(result.validation.factors),
        "skipped": len(result.validation.skipped),
        "duplicates": len(result.validation.duplicates),
        "errors": result.validation.errors,
        "warnings": result.validation.warnings,
        "db": result.db,
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return str(path)


# ---------------------------------------------------------------------------
# Database load (batch-linked, idempotent)
# ---------------------------------------------------------------------------


def _sanitize_dsn(dsn: str) -> str:
    """Return a psycopg2-compatible DSN (drops non-standard URI query params)."""
    allowed = {
        "sslmode", "sslrootcert", "sslcert", "sslkey", "sslpassword",
        "connect_timeout", "application_name", "options", "keepalives",
        "keepalives_idle", "target_session_attrs",
    }
    if "?" not in dsn:
        return dsn
    base, _, query = dsn.partition("?")
    pairs = [
        item for item in query.split("&")
        if "=" in item and item.partition("=")[0] in allowed
    ]
    return base + ("?" + "&".join(pairs) if pairs else "")


def load_to_db(
    factors: list[SeaiFactor],
    skipped: list[SeaiSkip],
    db_url: str,
    *,
    source_file: str = "",
    source_checksum: str = "",
    provider_version: str = PROVIDER_VERSION,
    mode: str = "sync",
) -> dict[str, Any]:
    """Import the SEAI factors into the target database.

    * Creates one ``import_batches`` row (provider_key='seai').
    * Deactivates any previously active SEAI 2025 batch (one active per provider
      + year) and activates the new batch.
    * Upserts every factor by RC2 natural key with ``import_batch_id`` set —
      repeated runs never create duplicate factors.
    * ``mode='replace'`` first deletes the existing SEAI-2025/IE rows.
    """
    import psycopg2

    if not factors:
        raise ValueError("no factors to load")

    dsn = _sanitize_dsn(db_url)
    conn = psycopg2.connect(dsn, connect_timeout=10)
    conn.autocommit = False
    inserted = 0
    updated = 0
    deleted = 0
    batch_id: Optional[str] = None
    try:
        with conn.cursor() as cur:
            if mode == "replace":
                cur.execute(
                    "DELETE FROM public.emission_factors "
                    "WHERE factor_source = %s AND factor_set = %s AND country = %s",
                    (FACTOR_SOURCE, FACTOR_SET, COUNTRY),
                )
                deleted = cur.rowcount

            cur.execute(
                """
                INSERT INTO public.import_batches (
                    provider_key, provider_version, source_file, source_checksum,
                    reporting_year, status, rows_total, rows_imported,
                    rows_skipped, rows_duplicate, errors, is_active,
                    created_at, created_by, updated_at
                ) VALUES (%s, %s, %s, %s, %s, 'importing',
                          %s, 0, 0, 0, NULL, FALSE, NOW(), NULL, NOW())
                RETURNING id
                """,
                (
                    PROVIDER_KEY, provider_version, source_file, source_checksum,
                    REPORTING_YEAR, len(factors) + len(skipped),
                ),
            )
            batch_id = str(cur.fetchone()[0])

            cur.execute(
                """
                UPDATE public.import_batches
                   SET is_active = FALSE, updated_at = NOW()
                 WHERE provider_key = %s AND reporting_year = %s
                   AND is_active = TRUE AND id <> %s
                """,
                (PROVIDER_KEY, REPORTING_YEAR, batch_id),
            )


            for f in factors:
                cur.execute(
                    """
                    INSERT INTO public.emission_factors (
                        id, reporting_year, activity_type, co2e_multiplier,
                        unit, scope, factor_source, factor_set, country,
                        import_batch_id, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (
                        reporting_year, activity_type,
                        COALESCE(country, 'GB'),
                        COALESCE(unit, '{no-unit}'),
                        COALESCE(scope, '{no-scope}')
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
                        str(uuid.uuid4()), f.reporting_year, f.activity_type,
                        f.co2e_multiplier, f.unit, f.scope, f.factor_source,
                        f.factor_set, f.country, batch_id,
                    ),
                )
                was_inserted = cur.fetchone()[0]
                if was_inserted:
                    inserted += 1
                else:
                    updated += 1

            cur.execute(
                """
                UPDATE public.import_batches
                   SET status = 'completed',
                       rows_imported = %s,
                       rows_skipped = %s,
                       rows_duplicate = %s,
                       is_active = TRUE,
                       updated_at = NOW()
                 WHERE id = %s
                """,
                (len(factors), len(skipped), 0, batch_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "backend": "psycopg2",
        "mode": mode,
        "batch_id": batch_id,
        "inserted": inserted,
        "updated": updated,
        "deleted_before_insert": deleted,
        "total_processed": len(factors),
        "skipped_count": len(skipped),
        "provider_key": PROVIDER_KEY,
        "provider_version": provider_version,
        "source_checksum": source_checksum,
        "expected_imported": EXPECTED_IMPORTED,
        "expected_skipped": EXPECTED_SKIPPED,
    }

