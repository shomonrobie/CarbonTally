"""Integration tests for V3M-3 — Customer-Owned Emission Factors (O1 snapshot
FK relaxation).

These tests run against the dedicated test database ``carbontally_test`` (see
``tests/integration/conftest.py``) — never the authoritative development
database. They verify the schema and invariants established by:

  * ``supabase/migrations/20260810020000_v3m3_customer_factors.sql``

Covered invariants:
  1. ``customer_factors`` exists with the approved org-scoped columns and
     lifecycle CHECK (draft/active/inactive/archived).
  2. Per-version family UNIQUE index rejects a duplicate version.
  3. co2e_multiplier >= 0 and country GB/IE CHECKs.
  4. RLS enabled; select/insert/update policies present; NO delete policy
     (delete restricted — soft-deactivate).
  5. O1 snapshot relaxation: ``factor_id`` nullable, ``factor_kind`` NOT NULL
     DEFAULT 'emission_factor', ``customer_factor_id`` optional FK.
  6. Exactly-one-source CHECK: emission-only and customer-only rows are valid;
     both-NULL and both-set rows are rejected.
  7. ``customer_factor_id`` FK is ON DELETE RESTRICT (provenance protected).
  8. ``emission_factors`` is untouched (no org/customer columns added).
"""
from __future__ import annotations

import asyncpg
import pytest

from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_customer_factor(
    conn: asyncpg.Connection,
    org_id: str,
    *,
    activity_type: str = "Fuels > Petrol",
    multiplier: str = "2.30",
    status: str = "draft",
    version: int = 1,
    name: str = "My Electricity Factor",
) -> str:
    factor_id = new_id()
    await conn.execute(
        """
        INSERT INTO public.customer_factors (
            id, organization_id, name, activity_type, co2e_multiplier,
            country, reporting_year, factor_source, status, version
        ) VALUES ($1, $2, $3, $4, $5, 'GB', 2025, 'CUSTOMER', $6, $7)
        """,
        factor_id,
        org_id,
        name,
        activity_type,
        multiplier,
        status,
        version,
    )
    return factor_id


async def _create_emission_factor(conn: asyncpg.Connection) -> str:
    """Insert a minimal emission_factors row (natural key unique per test)."""
    factor_id = new_id()
    await conn.execute(
        """
        INSERT INTO public.emission_factors (
            id, reporting_year, activity_type, co2e_multiplier, country,
            factor_source
        ) VALUES ($1, 2025, $2, 0.20, 'GB', 'DEFRA-DESNZ')
        """,
        factor_id,
        f"V3M3 test factor {factor_id[:8]}",
    )
    return factor_id


async def _insert_snapshot(
    conn: asyncpg.Connection,
    org_id: str,
    *,
    factor_id: str | None,
    factor_kind: str = "emission_factor",
    customer_factor_id: str | None = None,
) -> str:
    snapshot_id = new_id()
    await conn.execute(
        """
        INSERT INTO public.calculation_snapshots (
            id, organization_id, activity, activity_type, quantity,
            quantity_unit, co2e_multiplier, co2e_kg, date, factor_id,
            factor_kind, customer_factor_id, reporting_year, methodology,
            algorithm_version, content_hash
        ) VALUES ($1, $2, 'Electricity', 'Electricity', 100, 'kWh', 0.20,
                  20, '2025-06-01', $3, $4, $5, 2025, 'activity_based',
                  'v1.0', $6)
        """,
        snapshot_id,
        org_id,
        factor_id,
        factor_kind,
        customer_factor_id,
        "0" * 64,
    )
    return snapshot_id


# ---------------------------------------------------------------------------
# 1. customer_factors schema (columns + status lifecycle)
# ---------------------------------------------------------------------------


async def test_customer_factors_table_exists(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'customer_factors'"
        )
        names = {c["column_name"] for c in cols}
        for required in (
            "id",
            "organization_id",
            "name",
            "activity_type",
            "co2e_multiplier",
            "unit",
            "scope",
            "country",
            "reporting_year",
            "factor_source",
            "source_reference",
            "status",
            "version",
            "effective_from",
            "effective_to",
            "metadata",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ):
            assert required in names, f"missing customer_factors.{required}"


async def test_customer_factor_create_and_fetch(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        factor_id = await _create_customer_factor(
            conn, org_id, multiplier="1.75", status="draft"
        )
        row = await conn.fetchrow(
            "SELECT organization_id, co2e_multiplier, status, factor_source, version "
            "FROM public.customer_factors WHERE id = $1",
            factor_id,
        )
        assert row is not None
        assert row["organization_id"] == org_id
        assert str(row["co2e_multiplier"]) == "1.75"
        assert row["status"] == "draft"
        assert row["factor_source"] == "CUSTOMER"
        assert row["version"] == 1


async def test_customer_factor_status_check(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _create_customer_factor(conn, org_id, status="bogus_status")


async def test_customer_factor_multiplier_check(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _create_customer_factor(conn, org_id, multiplier="-1.0")


async def test_customer_factor_country_check(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await conn.execute(
                """
                INSERT INTO public.customer_factors (
                    id, organization_id, name, activity_type, co2e_multiplier,
                    country, reporting_year, factor_source, status, version
                ) VALUES ($1, $2, 'X', 'Fuels > Petrol', 1.0, 'FR', 2025,
                          'CUSTOMER', 'draft', 1)
                """,
                new_id(),
                org_id,
            )


async def test_customer_factor_org_fk(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await _create_customer_factor(conn, new_id())


async def test_customer_factor_version_unique(pool: asyncpg.Pool) -> None:
    """Per-version family UNIQUE index rejects a duplicate (same family, v1)."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        await _create_customer_factor(
            conn, org_id, activity_type="Fuels > Petrol", version=1
        )
        with pytest.raises(asyncpg.exceptions.UniqueViolationError):
            await _create_customer_factor(
                conn, org_id, activity_type="Fuels > Petrol", version=1
            )
        # A new version of the same family is allowed.
        await _create_customer_factor(
            conn, org_id, activity_type="Fuels > Petrol", version=2
        )


# ---------------------------------------------------------------------------
# 2. RLS posture (M8 conventions + consultant read)
# ---------------------------------------------------------------------------


async def test_customer_factors_rls_enabled_no_delete(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        rls_on = await conn.fetchval(
            "SELECT relrowsecurity FROM pg_class WHERE relname = 'customer_factors'"
        )
        assert rls_on is True

        policies = await conn.fetch(
            "SELECT policyname, cmd FROM pg_policies "
            "WHERE schemaname = 'public' AND tablename = 'customer_factors'"
        )
        by_cmd = {p["cmd"]: p["policyname"] for p in policies}
        assert by_cmd.get("SELECT") == "customer_factors_select_own"
        assert by_cmd.get("INSERT") == "customer_factors_insert_own"
        assert by_cmd.get("UPDATE") == "customer_factors_update_own"
        assert "DELETE" not in by_cmd, "customer_factors must have NO delete policy"


async def test_customer_factors_updated_at_trigger(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        trigger = await conn.fetchrow(
            "SELECT tgname FROM pg_trigger "
            "WHERE tgrelid = 'public.customer_factors'::regclass "
            "AND tgname = 'trg_set_updated_at_customer_factors'"
        )
        assert trigger is not None


# ---------------------------------------------------------------------------
# 3. O1 snapshot-FK relaxation
# ---------------------------------------------------------------------------


async def test_snapshot_o1_columns(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        cols = await conn.fetch(
            "SELECT column_name, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'calculation_snapshots' "
            "AND column_name IN ('factor_id', 'factor_kind', 'customer_factor_id')"
        )
        by_name = {c["column_name"]: c for c in cols}
        # factor_id is now nullable (O1).
        assert by_name["factor_id"]["is_nullable"] == "YES"
        # factor_kind NOT NULL with DEFAULT emission_factor.
        assert by_name["factor_kind"]["is_nullable"] == "NO"
        assert "emission_factor" in by_name["factor_kind"]["column_default"]
        # customer_factor_id optional.
        assert by_name["customer_factor_id"]["is_nullable"] == "YES"


async def test_snapshot_emission_factor_provenance(pool: asyncpg.Pool) -> None:
    """O1: a snapshot referencing emission_factors stays valid."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        factor_id = await _create_emission_factor(conn)
        snapshot_id = await _insert_snapshot(
            conn, org_id, factor_id=factor_id, factor_kind="emission_factor"
        )
        row = await conn.fetchrow(
            "SELECT factor_id, factor_kind, customer_factor_id "
            "FROM public.calculation_snapshots WHERE id = $1",
            snapshot_id,
        )
        assert row["factor_id"] == factor_id
        assert row["factor_kind"] == "emission_factor"
        assert row["customer_factor_id"] is None


async def test_snapshot_customer_factor_provenance(pool: asyncpg.Pool) -> None:
    """O1: a snapshot referencing customer_factors is valid."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        cf_id = await _create_customer_factor(conn, org_id, status="active")
        snapshot_id = await _insert_snapshot(
            conn,
            org_id,
            factor_id=None,
            factor_kind="customer_factor",
            customer_factor_id=cf_id,
        )
        row = await conn.fetchrow(
            "SELECT factor_id, factor_kind, customer_factor_id "
            "FROM public.calculation_snapshots WHERE id = $1",
            snapshot_id,
        )
        assert row["factor_id"] is None
        assert row["factor_kind"] == "customer_factor"
        assert row["customer_factor_id"] == cf_id


async def test_snapshot_exactly_one_source_both_null(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _insert_snapshot(conn, org_id, factor_id=None)


async def test_snapshot_exactly_one_source_both_set(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        cf_id = await _create_customer_factor(conn, org_id, status="active")
        factor_id = await _create_emission_factor(conn)
        with pytest.raises(asyncpg.exceptions.CheckViolationError):
            await _insert_snapshot(
                conn,
                org_id,
                factor_id=factor_id,
                factor_kind="customer_factor",
                customer_factor_id=cf_id,
            )


async def test_customer_factor_fk_restrict(pool: asyncpg.Pool) -> None:
    """ON DELETE RESTRICT: an approved factor referenced by a snapshot cannot
    be deleted (immutable provenance)."""
    async with pool.acquire() as conn:
        org_id = await make_org(pool)
        cf_id = await _create_customer_factor(conn, org_id, status="active")
        await _insert_snapshot(
            conn,
            org_id,
            factor_id=None,
            factor_kind="customer_factor",
            customer_factor_id=cf_id,
        )
        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await conn.execute(
                "DELETE FROM public.customer_factors WHERE id = $1", cf_id
            )


# ---------------------------------------------------------------------------
# 4. emission_factors untouched
# ---------------------------------------------------------------------------


async def test_emission_factors_untouched(pool: asyncpg.Pool) -> None:
    """No org/customer columns were added to global emission_factors."""
    async with pool.acquire() as conn:
        cols = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'emission_factors'"
        )
        names = {c["column_name"] for c in cols}
        assert "organization_id" not in names
        assert "customer_factor_id" not in names
        assert "factor_kind" not in names
