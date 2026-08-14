"""Shared fixtures for the SEAI provider test suite.

The DB-backed tests run against the **dedicated integration-test database**
(``carbontally_test``) — never the authoritative/development database. Only
SEAI-created rows (``factor_source='SEAI'`` / ``provider_key='seai'``) are
cleaned between tests; DEFRA and other rows are preserved.
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg2
import pytest

#: Test database URL — honours the same override used by the backend
#: integration suite, defaulting to the dedicated isolated test database.
TEST_DB_URL = os.getenv(
    "INTEGRATION_DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:54326/carbontally_test",
)

_WORKBOOK_NAMES = ("SEAI-conversion-and-emission-factors.xlsx",)


def _find_workbook() -> Path:
    """Locate the SEAI workbook in the repository (any of the known copies)."""
    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        for name in _WORKBOOK_NAMES:
            candidate = parent / name
            if candidate.exists():
                return candidate
            repo_copy = parent / "tools" / "carbon_data_factory" / "docs" / name
            if repo_copy.exists():
                return repo_copy
    raise FileNotFoundError(f"SEAI workbook not found under {here}")



@pytest.fixture(scope="session")
def workbook_path() -> Path:
    return _find_workbook()


@pytest.fixture(scope="session")
def seai_data(workbook_path):
    """Parse the workbook exactly once per session (the workbook is large)."""
    from src.providers.seai import analyze_workbook

    return analyze_workbook(workbook_path)


@pytest.fixture(scope="session")
def db_url() -> str:
    return TEST_DB_URL


@pytest.fixture(scope="session")
def db_conn(db_url):
    """A read/write psycopg2 connection to the test database."""
    conn = psycopg2.connect(db_url, connect_timeout=10)
    conn.autocommit = True
    yield conn
    conn.close()


def clean_seai(db_conn) -> None:
    """Remove SEAI-created rows so DB tests are deterministic.

    Deletes only SEAI factors (IE / SEAI-2025) and SEAI import batches.
    DEFRA rows and all other data are left untouched.
    """
    with db_conn.cursor() as cur:
        cur.execute(
            "DELETE FROM public.emission_factors "
            "WHERE factor_source = 'SEAI' AND factor_set = 'SEAI-2025' "
            "AND country = 'IE'"
        )
        cur.execute("DELETE FROM public.import_batches WHERE provider_key = 'seai'")


@pytest.fixture(autouse=True)
def _isolate_seai(db_conn):
    """Clean SEAI state before and after every DB test."""
    clean_seai(db_conn)
    yield
    clean_seai(db_conn)
