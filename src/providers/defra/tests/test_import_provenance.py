"""DEMO-T2-B — DEFRA import provenance tests.

Covers the provenance enhancement on the **real** DEFRA 2025 workbook against a
**disposable** database (see ``conftest`` for the refusal guard):

* the batch checksum is the SHA-256 of the workbook bytes actually imported;
* the batch records the expected DEFRA metadata and the row accounting;
* imported factors are linked to the batch through ``import_batch_id``;
* a successful load ends ``completed`` + ``is_active``;
* a repeated import is deterministic and never leaves two active batches;
* ``replace`` mode keeps the provenance consistent;
* a failed load leaves no completed batch and no partial rows;
* the factor values and semantics produced by the importer are unchanged.

These tests write only the ``DEFRA-2025``/``GB`` slice the importer owns.
"""
from __future__ import annotations

import hashlib
from decimal import Decimal

import pytest

from src.providers.defra import (
    PROVIDER_KEY,
    BatchProvenance,
    load_to_db,
    provider_version_label,
    workbook_sha256,
)

EXPECTED_DEFRA_2025_FACTORS = 7029


def _count(db_conn, sql: str, params: tuple = ()) -> int:
    with db_conn.cursor() as cur:
        cur.execute(sql, params)
        return int(cur.fetchone()[0])


def _batch_row(db_conn, batch_id: str):
    with db_conn.cursor() as cur:
        cur.execute(
            """
            SELECT provider_key, provider_version, source_file, source_checksum,
                   reporting_year, status, rows_total, rows_imported,
                   rows_skipped, rows_duplicate, is_active
              FROM public.import_batches WHERE id = %s
            """,
            (batch_id,),
        )
        return cur.fetchone()


def _provenance(workbook_path, analysis, *, factors, skipped=0, duplicates=0):
    """Build the provenance the CLI builds for this workbook."""
    year = analysis.reporting_year or 2025
    return BatchProvenance(
        reporting_year=year,
        provider_key=PROVIDER_KEY,
        provider_version=provider_version_label(year, analysis.meta.version),
        source_file=str(workbook_path),
        source_checksum=analysis.meta.file_sha256,
        rows_total=len(factors) + skipped + duplicates,
        rows_skipped=skipped,
        rows_duplicate=duplicates,
    )


# ---------------------------------------------------------------------------
# A. Checksum
# ---------------------------------------------------------------------------
def test_source_checksum_is_the_sha256_of_the_workbook_bytes(
    workbook_path, defra_run, db_url, db_conn
):
    analysis, report = defra_run
    expected = hashlib.sha256(workbook_path.read_bytes()).hexdigest()

    # the mechanism computes the digest from the file; it is never hard-coded
    assert workbook_sha256(str(workbook_path)) == expected
    assert analysis.meta.file_sha256 == expected
    assert len(expected) == 64

    factors = report.factors[:10]
    result = load_to_db(
        factors, "sync", db_url,
        provenance=_provenance(workbook_path, analysis, factors=factors),
    )
    assert _batch_row(db_conn, result["batch_id"])[3] == expected
    assert result["source_checksum"] == expected


# ---------------------------------------------------------------------------
# B. Batch creation metadata
# ---------------------------------------------------------------------------
def test_batch_records_expected_defra_metadata(workbook_path, defra_run, db_url, db_conn):
    analysis, report = defra_run
    factors = report.factors[:10]
    result = load_to_db(
        factors, "sync", db_url,
        provenance=_provenance(workbook_path, analysis, factors=factors),
    )
    (provider_key, provider_version, source_file, checksum, reporting_year,
     status, rows_total, rows_imported, rows_skipped, rows_duplicate, is_active) = (
        _batch_row(db_conn, result["batch_id"])
    )

    assert provider_key == "defra"
    assert provider_version == provider_version_label(2025, analysis.meta.version)
    assert provider_version == "2025 (V1)"     # the workbook's own version field
    assert source_file == str(workbook_path)   # the artefact actually read
    assert reporting_year == 2025
    assert len(checksum) == 64
    assert status == "completed"
    assert is_active is True
    assert rows_imported == 10


# ---------------------------------------------------------------------------
# C. Factor linkage
# ---------------------------------------------------------------------------
def test_imported_factors_are_linked_to_the_batch(workbook_path, defra_run, db_url, db_conn):
    analysis, report = defra_run
    factors = report.factors[:25]
    result = load_to_db(
        factors, "sync", db_url,
        provenance=_provenance(workbook_path, analysis, factors=factors),
    )
    assert _count(
        db_conn,
        "SELECT count(*) FROM public.emission_factors WHERE import_batch_id = %s",
        (result["batch_id"],),
    ) == 25
    assert _count(
        db_conn,
        "SELECT count(*) FROM public.emission_factors "
        "WHERE factor_set = 'DEFRA-2025' AND import_batch_id IS NULL",
    ) == 0


# ---------------------------------------------------------------------------
# D. Counts
# ---------------------------------------------------------------------------
def test_counters_match_the_importer_results(workbook_path, defra_run, db_url, db_conn):
    analysis, report = defra_run
    factors = report.factors[:25]
    skipped, duplicates = len(report.skipped), len(report.duplicates)
    result = load_to_db(
        factors, "sync", db_url,
        provenance=_provenance(workbook_path, analysis, factors=factors,
                               skipped=skipped, duplicates=duplicates),
    )
    row = _batch_row(db_conn, result["batch_id"])
    assert row[6] == len(factors) + skipped + duplicates   # rows_total
    assert row[7] == len(factors)                          # rows_imported
    assert row[8] == skipped                               # rows_skipped
    assert row[9] == duplicates                            # rows_duplicate
    # rows_total recounts every resolved source row exactly once (the full-set
    # invariant is asserted in test_full_dataset_expected_counts_and_linkage)
    assert row[6] == row[7] + row[8] + row[9]



# ---------------------------------------------------------------------------
# E. Successful completion
# ---------------------------------------------------------------------------
def test_successful_load_completes_and_activates_the_batch(workbook_path, defra_run,
                                                           db_url, db_conn):
    analysis, report = defra_run
    factors = report.factors[:10]
    result = load_to_db(
        factors, "sync", db_url,
        provenance=_provenance(workbook_path, analysis, factors=factors),
    )
    row = _batch_row(db_conn, result["batch_id"])
    assert row[5] == "completed"
    assert row[10] is True
    assert result["backend"] == "psycopg2"


# ---------------------------------------------------------------------------
# Full dataset: the expected 2025 result is unchanged
# ---------------------------------------------------------------------------
def test_full_dataset_expected_counts_and_linkage(workbook_path, defra_run, db_url, db_conn):
    analysis, report = defra_run
    factors = report.factors
    assert len(factors) == EXPECTED_DEFRA_2025_FACTORS, "importer result changed"
    assert len(report.duplicates) == 0

    result = load_to_db(
        factors, "sync", db_url,
        provenance=_provenance(workbook_path, analysis, factors=factors,
                               skipped=len(report.skipped),
                               duplicates=len(report.duplicates)),
    )
    assert result["inserted"] == EXPECTED_DEFRA_2025_FACTORS
    assert result["updated"] == 0
    assert _count(
        db_conn,
        "SELECT count(*) FROM public.emission_factors "
        "WHERE factor_set = 'DEFRA-2025' AND country = 'GB'",
    ) == EXPECTED_DEFRA_2025_FACTORS
    assert _count(
        db_conn,
        "SELECT count(*) FROM public.emission_factors WHERE import_batch_id = %s",
        (result["batch_id"],),
    ) == EXPECTED_DEFRA_2025_FACTORS
    row = _batch_row(db_conn, result["batch_id"])
    assert row[6] == EXPECTED_DEFRA_2025_FACTORS + len(report.skipped)  # rows_total
    assert row[5] == "completed" and row[10] is True


# ---------------------------------------------------------------------------
# F. Repeat import
# ---------------------------------------------------------------------------
def test_repeat_import_is_deterministic_with_one_active_batch(workbook_path, defra_run,
                                                              db_url, db_conn):
    analysis, report = defra_run
    factors = report.factors[:20]

    first = load_to_db(factors, "sync", db_url,
                       provenance=_provenance(workbook_path, analysis, factors=factors))
    second = load_to_db(factors, "sync", db_url,
                        provenance=_provenance(workbook_path, analysis, factors=factors))

    assert second["batch_id"] != first["batch_id"]
    assert second["inserted"] == 0 and second["updated"] == 20, "re-import must upsert"
    # every factor now points at the newest batch; the old batch keeps its record
    assert _count(db_conn, "SELECT count(*) FROM public.emission_factors "
                           "WHERE import_batch_id = %s", (second["batch_id"],)) == 20
    assert _count(db_conn, "SELECT count(*) FROM public.emission_factors "
                           "WHERE import_batch_id = %s", (first["batch_id"],)) == 0
    assert _count(db_conn, "SELECT count(*) FROM public.emission_factors "
                           "WHERE factor_set = 'DEFRA-2025'") == 20
    # exactly one active DEFRA 2025 batch, and no active batch other than the newest
    assert _count(db_conn, "SELECT count(*) FROM public.import_batches "
                           "WHERE provider_key = 'defra' AND reporting_year = 2025 "
                           "AND is_active") == 1
    assert _batch_row(db_conn, second["batch_id"])[10] is True
    assert _batch_row(db_conn, first["batch_id"])[10] is False


# ---------------------------------------------------------------------------
# Replace mode
# ---------------------------------------------------------------------------
def test_replace_mode_keeps_provenance_consistent(workbook_path, defra_run, db_url, db_conn):
    analysis, report = defra_run
    factors = report.factors[:15]

    first = load_to_db(factors, "sync", db_url,
                       provenance=_provenance(workbook_path, analysis, factors=factors))
    replaced = load_to_db(factors, "replace", db_url,
                          provenance=_provenance(workbook_path, analysis, factors=factors))

    assert replaced["batch_id"] != first["batch_id"]
    assert replaced["deleted_before_insert"] == 15
    assert replaced["inserted"] == 15
    # no row is left pointing at the replaced batch and no orphaned provenance
    assert _count(db_conn, "SELECT count(*) FROM public.emission_factors "
                           "WHERE import_batch_id = %s", (first["batch_id"],)) == 0
    assert _count(db_conn, "SELECT count(*) FROM public.emission_factors "
                           "WHERE import_batch_id = %s", (replaced["batch_id"],)) == 15
    # the replaced batch is retained for provenance but deactivated: no ACTIVE
    # batch points at deleted rows
    assert _batch_row(db_conn, first["batch_id"])[10] is False
    assert _count(db_conn, "SELECT count(*) FROM public.import_batches "
                           "WHERE provider_key = 'defra' AND is_active") == 1



# ---------------------------------------------------------------------------
# G. Failure / rollback
# ---------------------------------------------------------------------------
def test_failed_load_leaves_no_completed_batch_and_no_rows(workbook_path, defra_run,
                                                           db_url, db_conn):
    """A database failure must roll the factors AND the batch back together."""
    from dataclasses import replace as dc_replace

    analysis, report = defra_run
    good = report.factors[:3]
    # a negative multiplier violates the DB CHECK constraint (emission_factors_
    # co2e_multiplier_check) → the transaction must fail as a whole
    bad = dc_replace(
        good[-1],
        activity_type="F-T2B invalid factor (must roll back)",
        co2e_multiplier=Decimal("-1"),
    )
    batch = [*good, bad]

    with pytest.raises(Exception):
        load_to_db(batch, "sync", db_url,
                   provenance=_provenance(workbook_path, analysis, factors=batch))

    assert _count(db_conn, "SELECT count(*) FROM public.import_batches "
                           "WHERE provider_key = 'defra'") == 0
    assert _count(db_conn, "SELECT count(*) FROM public.emission_factors "
                           "WHERE activity_type = 'F-T2B invalid factor (must roll back)'") == 0
    assert _count(db_conn, "SELECT count(*) FROM public.emission_factors "
                           "WHERE factor_set = 'DEFRA-2025'") == 0


# ---------------------------------------------------------------------------
# H. Existing DEFRA semantics unchanged
# ---------------------------------------------------------------------------
def test_factor_values_and_mapping_are_unchanged(workbook_path, defra_run, db_url, db_conn):
    analysis, report = defra_run
    factors = report.factors[:5]
    load_to_db(factors, "sync", db_url,
               provenance=_provenance(workbook_path, analysis, factors=factors))

    for factor in factors:
        with db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT reporting_year, activity_type, co2e_multiplier::text, unit, scope,
                       factor_source, factor_set, country
                  FROM public.emission_factors
                 WHERE reporting_year = %s
                   AND activity_type = %s
                   AND COALESCE(country, 'GB') = %s
                   AND COALESCE(unit, '{no-unit}') = %s
                   AND COALESCE(scope, '{no-scope}') = %s
                """,
                (factor.reporting_year, factor.activity_type, factor.country or "GB",
                 factor.unit or "{no-unit}", factor.scope or "{no-scope}"),
            )
            row = cur.fetchone()
        assert row is not None, f"factor not stored: {factor.activity_type}"
        assert row[0] == factor.reporting_year
        assert row[1] == factor.activity_type
        assert Decimal(row[2]) == Decimal(str(factor.co2e_multiplier))
        assert row[3] == factor.unit
        assert row[4] == factor.scope
        assert row[5] == "DEFRA-DESNZ"
        assert row[6] == "DEFRA-2025"
        assert row[7] == "GB"


def test_legacy_load_without_provenance_still_works(workbook_path, defra_run, db_url, db_conn):
    """The pre-existing (batch-less) loader path must remain available."""
    _analysis, report = defra_run
    factors = report.factors[:5]
    result = load_to_db(factors, "sync", db_url)      # no provenance
    assert result["inserted"] == 5
    assert "batch_id" not in result
    assert _count(db_conn, "SELECT count(*) FROM public.emission_factors "
                           "WHERE factor_set = 'DEFRA-2025' "
                           "AND import_batch_id IS NULL") == 5


def test_provenance_requires_a_direct_connection(workbook_path, defra_run):
    """Without a DSN the Supabase fallback is refused rather than loading silently."""
    analysis, report = defra_run
    factors = report.factors[:1]
    with pytest.raises(RuntimeError, match="requires a direct Postgres connection"):
        load_to_db(
            factors, "sync", None,
            supabase_url="http://127.0.0.1:1",
            supabase_key="not-a-real-key",
            provenance=_provenance(workbook_path, analysis, factors=factors),
        )


# ---------------------------------------------------------------------------
# Dry run: --no-db must stay genuinely database-free
# ---------------------------------------------------------------------------
def test_no_db_dry_run_never_reaches_the_database(tmp_path, monkeypatch, workbook_path):
    from src.commands import import_defra as cli

    calls: list = []

    def _forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("load_to_db must never be called with --no-db")

    monkeypatch.setattr(cli, "load_to_db", _forbidden)

    rc = cli.main([
        "--no-db",
        "--workbook", str(workbook_path),
        "--output-dir", str(tmp_path),
    ])

    assert rc == 0
    assert calls == [], "--no-db attempted a database load"
    # the dry run still produces its artifacts
    assert (tmp_path / "sql" / "emission_factors.sql").exists()
    assert (tmp_path / "json" / "emission_factors.json").exists()
    assert (tmp_path / "reports" / "import_summary.md").exists()

