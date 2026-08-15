"""Shared fixtures for the repository integration suite.

The tests run against the **local Supabase PostgreSQL database**
(``postgresql://postgres:postgres@127.0.0.1:54326/postgres``). For the current
V3 verification phase this local database is intentionally the integration-test
database: it is disposable and rebuildable (``supabase db reset`` replays the
migration chain; the factor baseline is re-imported), and the remote Supabase
project is never touched.

The session fixture truncates the tables under test (with CASCADE) inside the
local database so every assertion is deterministic. Override
``INTEGRATION_DATABASE_URL`` to target any other database (e.g. a CI sandbox).
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

TEST_DB_URL = os.getenv(
    "INTEGRATION_DATABASE_URL",
    "postgresql://postgres:postgres@127.0.0.1:54326/postgres",
)

#: Environment used by infra/supabase.py inside the test process.
#: ``DATABASE_URL`` is *forced* (not ``setdefault``) so a stale ``DATABASE_URL``
#: exported in the outer shell can never redirect repository pools at the
#: authoritative database; the test process always talks to the test database.
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54325")
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
    """A connection pool to the test database, reset before the suite runs."""
    p = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=5)
    try:
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
