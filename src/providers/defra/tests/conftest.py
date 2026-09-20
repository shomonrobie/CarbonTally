"""Shared fixtures for the DEFRA provider test suite (DEMO-T2-B).

The DB-backed tests write real ``emission_factors`` rows and real
``import_batches`` rows, so they are **only** allowed to run against a
disposable database. Two safeguards apply:

* the usual override ``INTEGRATION_DATABASE_URL`` (the same variable the backend
  integration suite and the SEAI provider suite use), defaulting to the
  dedicated isolated test database;
* a **refusal guard**: a target whose database name looks persistent or
  authoritative (``demo``/``investor``/``prod``/``live``/``qa``, or the Supabase
  main ``postgres`` database) skips the DB-backed tests with an explicit reason,
  so an accidental run can never populate the Demo Lab or any authoritative
  database.

Cleanup is scoped to the slice this importer owns — ``factor_set='DEFRA-2025'``
with ``country='GB'`` (exactly what ``--mode replace`` deletes) plus
``provider_key='defra'`` batches. SEAI and other providers' rows are preserved.
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg2
import pytest

#: Test database URL — honours the same override used by the backend integration
#: suite and the existing SEAI provider suite.
TEST_DB_URL = os.getenv(
    "INTEGRATION_DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test",
)

WORKBOOK_NAME = "ghg-conversion-factors-2025-flat-format.xlsx"

#: Database names that must never be written to by these tests.
_FORBIDDEN_NAME_PARTS = ("demo", "investor", "prod", "live", "qa")


def _database_name(dsn: str) -> str:
    """Return the database name from a Postgres DSN."""
    tail = dsn.rsplit("/", 1)[-1]
    return tail.split("?", 1)[0].strip()


def _find_workbook() -> Path:
    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        repo_copy = parent / "tools" / "carbon_data_factory" / "docs" / WORKBOOK_NAME
        if repo_copy.exists():
            return repo_copy
        direct = parent / WORKBOOK_NAME
        if direct.exists():
            return direct
    raise FileNotFoundError(f"DEFRA workbook {WORKBOOK_NAME} not found under {here}")


@pytest.fixture(scope="session")
def workbook_path() -> Path:
    return _find_workbook()


@pytest.fixture(scope="session")
def defra_run(workbook_path):
    """Parse + map + validate the workbook once per session.

    Returns ``(analysis, report)`` — the importer's own output, so tests compare
    database rows against what the importer actually produced.
    """
    from src.providers.defra import analyze_workbook, map_all, validate_all

    wb, analysis = analyze_workbook(str(workbook_path))
    rows: list = []
    for ws in wb.worksheets:
        info = next((w for w in analysis.worksheets if w.name == ws.title), None)
        if info is None or info.sheet_type != "data":
            continue
        from src.providers.defra import parse_worksheet

        parsed, _counters = parse_worksheet(ws, info)
        rows.extend(parsed)
    wb.close()

    reporting_year = analysis.reporting_year or 2025
    mapped = map_all(
        rows,
        reporting_year=reporting_year,
        factor_source="DEFRA-DESNZ",
        factor_set=f"DEFRA-{reporting_year}",
        country="GB",
    )
    report = validate_all(mapped, country="GB")
    return analysis, report


@pytest.fixture(scope="session")
def db_url() -> str:
    return TEST_DB_URL


@pytest.fixture(scope="session")
def db_conn(db_url):
    """A direct connection to the disposable test database (skips if unusable)."""
    name = _database_name(db_url)
    if name == "postgres" or any(part in name.lower() for part in _FORBIDDEN_NAME_PARTS):
        pytest.skip(
            f"refusing to write to database {name!r}: not a disposable test database. "
            "Point INTEGRATION_DATABASE_URL at a disposable clone."
        )
    try:
        conn = psycopg2.connect(db_url, connect_timeout=5)
    except Exception as exc:  # noqa: BLE001 — unreachable DB → skip, never fail loudly
        pytest.skip(f"test database unavailable ({name}): {exc}")
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean_defra_slice(db_conn):
    """Remove only the DEFRA-2025/GB slice + defra batches around each test."""
    def _clean() -> None:
        with db_conn.cursor() as cur:
            cur.execute("DELETE FROM public.import_batches WHERE provider_key = 'defra'")
            cur.execute(
                "DELETE FROM public.emission_factors "
                "WHERE factor_set = 'DEFRA-2025' AND country = 'GB'"
            )

    _clean()
    yield
    _clean()
