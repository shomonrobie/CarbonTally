"""Shared fixtures for the repository integration suite.

**D31 fix (test-infrastructure footgun):** the integration suite previously
defaulted ``INTEGRATION_DATABASE_URL`` to the LOCAL SUPABASE MAIN database
(``...:54326/postgres``) and TRUNCATEd ~22 tables there — which wiped the
local demo data (see D30 report §12). The suite now defaults to a DEDICATED
test database (``carbontally_test``) and refuses to run against the main
application database:

- if the connected database is the main app database (``postgres`` /
  ``supabase_db_carbon_ledger``), the session fixture RAISES and no truncation
  happens;
- if the dedicated ``carbontally_test`` database is unreachable, the session
  fixture SKIPS the suite (fail-safe — integration tests never silently fall
  back to the application database).

Create the dedicated test database with:
``createdb -h 127.0.0.1 -p 54326 -U postgres carbontally_test`` and restore the
schema (``pg_dump --schema-only`` from the main DB) so the RLS policies exist.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime

import asyncpg
import pytest

from data.organizations import OrganizationsRepository
from domain.organization import Organization

# ---------------------------------------------------------------------------
# Test database configuration
# ---------------------------------------------------------------------------

#: DEDICATED integration-test database (never the main app database).
TEST_DB_URL = os.getenv(
    "INTEGRATION_DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test",
)

#: Database names that are OFF-LIMITS — the suite must never TRUNCATE them.
FORBIDDEN_MAIN_DB_NAMES = ("postgres", "supabase_db_carbon_ledger")

#: Environment used by infra/supabase.py inside the test process.
#: ``DATABASE_URL`` is *forced* (not ``setdefault``) so a stale ``DATABASE_URL``
#: exported in the outer shell can never redirect repository pools at the
#: authoritative database; the test process always talks to the test database.
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54425")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

#: Service-role placeholder referenced by repository NOT NULL actor/user
#: columns (mirrors ``data.documents._SYSTEM_UUID`` / ``data.emissions_logs``).
_SYSTEM_UUID = "00000000-0000-0000-0000-000000000000"

#: Tables under test, listed so child rows are removed before parents.
_TRUNCATE_TABLES = [
    "emissions_logs",
    "calculation_snapshots",
    "factor_aliases",
    "domain_events",
    "audit_trail",
    "customer_documents",
    "consultant_tasks",
    "consultant_clients",
    "consultant_firm_members",
    "consultant_profiles",
    "user_invitations",
    "report_versions",
    "report_generation_queue",
    "import_batches",
    "emission_factors",
    "organization_metadata",
    "assets",
    "facilities",
    "organization_members",
    "organizations",
    "issues",
    "customer_factors",
    "processing_entities",
]


@pytest.fixture(scope="session")
async def pool() -> asyncpg.Pool:
    """A connection pool to the DEDICATED test database, reset before the suite.

    Fail-safe (D31): the suite never runs against the main application database.
    - If the database cannot be reached -> pytest.skip (unavailable).
    - If it resolves to a FORBIDDEN main app database -> RuntimeError, no TRUNCATE.
    - If the schema is absent -> pytest.skip (schema not provisioned).
    """
    try:
        p = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=5)
    except Exception as exc:  # noqa: BLE001 - connection refused / unknown db
        pytest.skip(f"dedicated integration database unavailable: {exc}")
    try:
        async with p.acquire() as conn:
            db_name = await conn.fetchval("SELECT current_database()")
            if db_name in FORBIDDEN_MAIN_DB_NAMES:
                raise RuntimeError(
                    f"refusing to run integration suite against the main application "
                    f"database ({db_name!r}). Point INTEGRATION_DATABASE_URL at the "
                    f"dedicated test database (carbontally_test)."
                )
            has_schema = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name='organizations')"
            )
            if not has_schema:
                pytest.skip(
                    "dedicated integration database has no public schema; "
                    "restore it (pg_dump --schema-only) before running the suite"
                )
        tables = ", ".join(f"public.{t}" for t in _TRUNCATE_TABLES)
        async with p.acquire() as conn:
            await conn.execute(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")
        await _seed_system_member(p)
        yield p
    finally:
        await p.close()


def new_id() -> str:
    """Return a fresh UUID string for test rows."""
    return str(uuid.uuid4())


async def _seed_system_member(pool: asyncpg.Pool) -> None:
    """Insert the service-role member referenced by repository ``_SYSTEM_UUID``
    columns (``customer_documents.organization_member_id``), once per session.

    The foreign key only checks that the member row exists; it does not require
    the member to belong to the document's organisation.
    """
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM public.organization_members WHERE id = $1", _SYSTEM_UUID
        )
        if exists:
            return
        org_id = new_id()
        user_id = new_id()
        await conn.execute(
            "INSERT INTO public.organizations (id, name, country, is_active, created_at, updated_at) "
            "VALUES ($1, 'System', 'GB', TRUE, NOW(), NOW())",
            org_id,
        )
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"system-{user_id}@example.test",
        )
        await conn.execute(
            "INSERT INTO public.organization_members "
            "(id, organization_id, user_id, role, is_active, created_at) "
            "VALUES ($1, $2, $3, 'member', TRUE, NOW())",
            _SYSTEM_UUID,
            org_id,
            user_id,
        )


async def make_org(pool: asyncpg.Pool, name: str = "Test Co") -> str:
    """Create a real organisation row and return its id.

    Several tables under test (``customer_documents``, ``report_generation_queue``,
    ``factor_aliases``, ``emissions_logs``, ``organization_members``) hold
    ``organization_id`` foreign keys, so tests must seed the parent row instead
    of passing a random UUID.
    """
    org = Organization(
        id=new_id(),
        name=name,
        country="GB",
        is_active=True,
        created_at=datetime.now(),
    )
    await OrganizationsRepository(pool).save(org)
    return org.id


async def make_user(pool: asyncpg.Pool) -> str:
    """Create a real user row (``organization_members.user_id`` FK) and return id."""
    user_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"user-{user_id}@example.test",
        )
    return user_id


async def make_snapshot(
    pool: asyncpg.Pool, org_id: str, factor_id: str
) -> str:
    """Create a minimal calculation_snapshots row (``emissions_logs.snapshot_id``
    FK) and return its id."""
    snapshot_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.calculation_snapshots (
                id, organization_id, activity, activity_type, quantity,
                quantity_unit, co2e_multiplier, co2e_kg, date, factor_id,
                reporting_year, methodology, algorithm_version, content_hash
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
            snapshot_id,
            org_id,
            "Electricity",
            "Electricity",
            "100.00",
            "kWh",
            "0.20000",
            "20.00000",
            date(2025, 6, 1),
            factor_id,
            2025,
            "activity_based",
            "v1.0",
            "0" * 64,
        )
    return snapshot_id
