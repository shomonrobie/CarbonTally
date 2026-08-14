"""Integration tests: SEAI import into the isolated test database.

These tests run against ``carbontally_test`` (never the development
database). They verify batch creation, ``import_batch_id`` linkage, exact
counts, idempotent re-import, and that existing DEFRA rows are untouched.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.providers.seai import analyze_workbook, load_to_db, map_all, validate

SEAI_WHERE = (
    "factor_source = 'SEAI' AND factor_set = 'SEAI-2025' AND country = 'IE'"
)


def _count(cur, where, params=()):
    cur.execute(f"SELECT count(*) FROM public.emission_factors WHERE {where}", params)
    return cur.fetchone()[0]


def test_import_creates_batch_and_20_factors(db_url, db_conn, seai_data):
    factors, skipped = map_all(list(seai_data.rows))
    report = validate(factors, skipped)
    assert report.ok, [i.message for i in report.issues]

    with db_conn.cursor() as cur:
        defra_before = _count(cur, "country = 'GB'")
        total_before = _count(cur, "1 = 1")

    db = load_to_db(
        factors, skipped, db_url,
        source_file=seai_data.meta.source_path,
        source_checksum=seai_data.meta.file_sha256,
    )
    assert db["inserted"] == 20
    assert db["updated"] == 0
    assert db["total_processed"] == 20
    assert db["skipped_count"] == 8

    with db_conn.cursor() as cur:
        assert _count(cur, SEAI_WHERE) == 20
        assert _count(cur, "import_batch_id = %s", (db["batch_id"],)) == 20
        defra_after = _count(cur, "country = 'GB'")
        total_after = _count(cur, "1 = 1")
        assert defra_after == defra_before
        assert total_after == total_before + 20

        cur.execute(
            "SELECT provider_key, provider_version, source_file, "
            "source_checksum, reporting_year, status, rows_total, "
            "rows_imported, rows_skipped, rows_duplicate, is_active "
            "FROM public.import_batches WHERE id = %s",
            (db["batch_id"],),
        )
        batch = cur.fetchone()
        assert batch is not None
        provider_key, provider_version, source_file, checksum, year, status = batch[:6]
        rows_total, rows_imported, rows_skipped, rows_duplicate, is_active = batch[6:]
        assert provider_key == "seai"
        assert year == 2025
        assert status == "completed"
        assert rows_total == 28
        assert rows_imported == 20
        assert rows_skipped == 8
        assert rows_duplicate == 0
        assert is_active is True
        assert checksum == seai_data.meta.file_sha256
        assert seai_data.meta.source_path in source_file

def test_every_factor_linked_to_batch(db_url, db_conn, seai_data):
    factors, skipped = map_all(list(seai_data.rows))
    db = load_to_db(factors, skipped, db_url,
                    source_checksum=seai_data.meta.file_sha256)
    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM public.emission_factors "
            f"WHERE {SEAI_WHERE} AND import_batch_id IS NULL"
        )
        assert cur.fetchone()[0] == 0


def test_import_is_idempotent(db_url, db_conn, seai_data):
    factors, skipped = map_all(list(seai_data.rows))
    first = load_to_db(factors, skipped, db_url,
                       source_checksum=seai_data.meta.file_sha256)
    second = load_to_db(factors, skipped, db_url,
                        source_checksum=seai_data.meta.file_sha256)

    assert second["inserted"] == 0
    assert second["updated"] == 20
    assert second["batch_id"] != first["batch_id"]

    with db_conn.cursor() as cur:
        assert _count(cur, SEAI_WHERE) == 20
        # every SEAI factor now points at the newest batch
        assert _count(cur, "import_batch_id = %s", (second["batch_id"],)) == 20
        assert _count(cur, "import_batch_id = %s", (first["batch_id"],)) == 0
        # exactly one active SEAI 2025 batch
        cur.execute(
            "SELECT count(*) FROM public.import_batches "
            "WHERE provider_key = 'seai' AND reporting_year = 2025 AND is_active"
        )
        assert cur.fetchone()[0] == 1


def test_import_does_not_modify_existing_defra_rows(db_url, db_conn, seai_data):
    factors, skipped = map_all(list(seai_data.rows))
    with db_conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.emission_factors WHERE country = 'GB'")
        defra_before = cur.fetchone()[0]
        cur.execute(
            "SELECT id, co2e_multiplier FROM public.emission_factors "
            "WHERE country = 'GB' ORDER BY id LIMIT 5"
        )
        defra_rows_before = cur.fetchall()

    load_to_db(factors, skipped, db_url, source_checksum=seai_data.meta.file_sha256)

    with db_conn.cursor() as cur:
        assert _count(cur, "country = 'GB'") == defra_before
        cur.execute(
            "SELECT id, co2e_multiplier FROM public.emission_factors "
            "WHERE country = 'GB' ORDER BY id LIMIT 5"
        )
        assert cur.fetchall() == defra_rows_before


def test_imported_multipliers_match_approved_spec(db_url, db_conn, seai_data):
    factors, skipped = map_all(list(seai_data.rows))
    load_to_db(factors, skipped, db_url, source_checksum=seai_data.meta.file_sha256)
    spot = {
        "Diesel / gasoil (100% petroleum)": Decimal("2.682327"),
        "Electricity consumption": Decimal("0.197803384"),
        "Gross electricity supply": Decimal("0.178327674"),
    }
    with db_conn.cursor() as cur:
        for name, expected in spot.items():
            cur.execute(
                "SELECT ef.co2e_multiplier FROM public.emission_factors ef "
                "WHERE ef.factor_source = 'SEAI' AND ef.factor_set = 'SEAI-2025' "
                "AND ef.country = 'IE' AND ef.activity_type LIKE %s",
                (f"Fuels > % > {name} (kg CO2) [%]",),
            )
            row = cur.fetchone()
            assert row is not None, name
            assert abs(float(row[0]) - float(expected)) < 1e-6, name

