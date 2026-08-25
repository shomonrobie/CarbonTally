"""V3 RLS behaviour tests (authenticated role) — organisation / customer-factor /
processing-entity isolation.

These tests exercise the *behaviour* of the V3M-3/V3M-5/V3M-6 policies with a
real ``authenticated`` role, not just their existence. They run against the
dedicated ``carbontally_test`` database (see ``tests/integration/conftest.py``)
and emulate an authenticated session by setting ``request.jwt.claims``
(``auth.uid()`` reads the ``sub`` claim) and ``SET ROLE authenticated`` — the
same mechanism Supabase PostgREST uses.

No policy is weakened or bypassed; assertions verify the deny-by-default /
org-scoped / entity-scoped surfaces.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
import pytest

from tests.integration.conftest import make_org, new_id

pytestmark = pytest.mark.asyncio


@asynccontextmanager
async def _authenticated(
    pool: asyncpg.Pool, user_id: str
) -> AsyncIterator[asyncpg.Connection]:
    """Yield a connection in an ``authenticated`` session for ``user_id``.

    Emulates the Supabase PostgREST session (``SET ROLE authenticated`` +
    ``request.jwt.claims`` → ``auth.uid()``). The session state is reset on
    exit so pooled connections never leak the role or claims into other tests.
    """
    conn = await pool.acquire()
    try:
        await conn.execute("SET ROLE authenticated")
        claims = json.dumps({"sub": user_id, "role": "authenticated"})
        await conn.execute(
            "SELECT set_config('request.jwt.claims', $1, false)", claims
        )
        yield conn
    finally:
        await conn.execute("RESET ROLE")
        await conn.execute(
            "SELECT set_config('request.jwt.claims', '{}', false)"
        )
        await pool.release(conn)


async def _seed_org_member(pool, org_id: str, user_id: str, role: str = "member") -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"user-{user_id[:8]}@example.test",
        )
        await conn.execute(
            """
            INSERT INTO public.organization_members (
                id, organization_id, user_id, role, is_active, created_at
            ) VALUES ($1, $2, $3, $4, TRUE, NOW())
            """,
            new_id(),
            org_id,
            user_id,
            role,
        )


async def _seed_entity_staff(pool, user_id: str, entity_id: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"staff-{user_id[:8]}@example.test",
        )
        await conn.execute(
            """
            INSERT INTO public.staff_profiles (
                id, user_id, first_name, last_name, email, entity_id
            ) VALUES ($1, $2, 'Entity', 'Staff', $3, $4)
            """,
            new_id(),
            user_id,
            f"staff-{user_id[:8]}@example.test",
            entity_id,
        )


async def _count(conn: asyncpg.Connection, table: str, where: str, *args) -> int:
    return await conn.fetchval(
        f"SELECT count(*) FROM public.{table} WHERE {where}", *args
    )


# ---------------------------------------------------------------------------
# Organisation + customer-factor isolation (V3M-3 tenant policies)
# ---------------------------------------------------------------------------


class TestOrgAndCustomerFactorIsolation:
    async def test_org_member_sees_own_customer_factors(
        self, pool: asyncpg.Pool
    ) -> None:
        org_a = await make_org(pool)
        org_b = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.customer_factors (
                    id, organization_id, name, activity_type, co2e_multiplier,
                    country, reporting_year, factor_source, status, version
                ) VALUES ($1, $2, 'A', 'Electricity', 0.2, 'GB', 2025, 'CUSTOMER',
                          'draft', 1)
                """,
                new_id(),
                org_a,
            )
            await conn.execute(
                """
                INSERT INTO public.customer_factors (
                    id, organization_id, name, activity_type, co2e_multiplier,
                    country, reporting_year, factor_source, status, version
                ) VALUES ($1, $2, 'B', 'Gas', 0.1, 'GB', 2025, 'CUSTOMER',
                          'draft', 1)
                """,
                new_id(),
                org_b,
            )
        async with _authenticated(pool, member) as conn:
            # Own org rows are visible; the other org's rows are not.
            assert await _count(conn, "customer_factors", "organization_id = $1", org_a) == 1
            assert await _count(conn, "customer_factors", "organization_id = $1", org_b) == 0

    async def test_non_member_sees_nothing(self, pool: asyncpg.Pool) -> None:
        org_a = await make_org(pool)
        outsider = new_id()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.customer_factors (
                    id, organization_id, name, activity_type, co2e_multiplier,
                    country, reporting_year, factor_source, status, version
                ) VALUES ($1, $2, 'A', 'Electricity', 0.2, 'GB', 2025, 'CUSTOMER',
                          'draft', 1)
                """,
                new_id(),
                org_a,
            )
        async with _authenticated(pool, outsider) as conn:
            # No membership -> deny-by-default (no rows, no error).
            assert await _count(conn, "customer_factors", "organization_id = $1", org_a) == 0

    async def test_org_member_cannot_insert_into_other_org(
        self, pool: asyncpg.Pool
    ) -> None:
        org_a = await make_org(pool)
        org_b = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    """
                    INSERT INTO public.customer_factors (
                        id, organization_id, name, activity_type, co2e_multiplier,
                        country, reporting_year, factor_source, status, version
                    ) VALUES ($1, $2, 'x', 'Electricity', 0.2, 'GB', 2025,
                              'CUSTOMER', 'draft', 1)
                    """,
                    new_id(),
                    org_b,
                )


# ---------------------------------------------------------------------------
# Issues — org storey (V3M-5) + entity storey (V3M-6)
# ---------------------------------------------------------------------------


class TestIssueIsolation:
    async def test_org_member_sees_only_org_scoped_issues(
        self, pool: asyncpg.Pool
    ) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.issues (id, title, organization_id, status)
                VALUES ($1, 'customer issue', $2, 'open')
                """,
                new_id(),
                org_a,
            )
        async with _authenticated(pool, member) as conn:
            # Org-scoped (entity_id IS NULL) rows are visible to the member.
            assert await _count(conn, "issues", "organization_id = $1", org_a) == 1

    async def test_entity_scoped_issues_not_customer_visible(
        self, pool: asyncpg.Pool
    ) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with pool.acquire() as conn:
            entity_id = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'Babui', 'active')",
                entity_id,
            )
            await conn.execute(
                """
                INSERT INTO public.issues (id, title, organization_id, entity_id, status)
                VALUES ($1, 'entity issue', $2, $3, 'open')
                """,
                new_id(),
                org_a,
                entity_id,
            )
        async with _authenticated(pool, member) as conn:
            # The org storey excludes entity-scoped rows (never customer-visible).
            assert await _count(conn, "issues", "organization_id = $1", org_a) == 0

    async def test_entity_staff_sees_entity_scoped_issues(
        self, pool: asyncpg.Pool
    ) -> None:
        staff = new_id()
        async with pool.acquire() as conn:
            entity_id = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'Babui', 'active')",
                entity_id,
            )
            await conn.execute(
                """
                INSERT INTO public.issues (id, title, entity_id, status)
                VALUES ($1, 'entity issue', $2, 'open')
                """,
                new_id(),
                entity_id,
            )
        await _seed_entity_staff(pool, staff, entity_id)
        async with _authenticated(pool, staff) as conn:
            # V3M-6 entity storey: entity staff see their entity's issues.
            assert await _count(conn, "issues", "entity_id = $1", entity_id) == 1


# ---------------------------------------------------------------------------
# Processing Entity isolation (V3M-1 deny-by-default + V3M-6 is_entity_member)
# ---------------------------------------------------------------------------


class TestProcessingEntityIsolation:
    async def test_entity_deny_by_default_for_authenticated(
        self, pool: asyncpg.Pool
    ) -> None:
        async with pool.acquire() as conn:
            entity_id = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'Babui', 'active')",
                entity_id,
            )
        async with _authenticated(pool, new_id()) as conn:
            # No entity staff membership -> deny-by-default.
            assert await _count(conn, "processing_entities", "id = $1", entity_id) == 0

    async def test_entity_staff_sees_own_entity(self, pool: asyncpg.Pool) -> None:
        async with pool.acquire() as conn:
            entity_id = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'Babui', 'active')",
                entity_id,
            )
            staff = new_id()
        await _seed_entity_staff(pool, staff, entity_id)
        async with _authenticated(pool, staff) as conn:
            # is_entity_member(entity_id) resolves via staff_profiles.entity_id.
            assert await _count(conn, "processing_entities", "id = $1", entity_id) == 1

    async def test_entity_staff_does_not_see_other_entity(
        self, pool: asyncpg.Pool
    ) -> None:
        async with pool.acquire() as conn:
            entity_a = new_id()
            entity_b = new_id()
            await conn.execute(
                "INSERT INTO public.processing_entities (id, name, status) "
                "VALUES ($1, 'A', 'active'), ($2, 'B', 'active')",
                entity_a,
                entity_b,
            )
            staff = new_id()
        await _seed_entity_staff(pool, staff, entity_a)
        async with _authenticated(pool, staff) as conn:
            assert await _count(conn, "processing_entities", "id = $1", entity_a) == 1
            assert await _count(conn, "processing_entities", "id = $1", entity_b) == 0


# ---------------------------------------------------------------------------
# Consultant active-grant isolation (D15, APPROVED 2026-08-20)
# ---------------------------------------------------------------------------


async def _seed_consultant(pool, user_id: str, org_id: str, *, status: str) -> None:
    """Seed a consultant firm + owner member + client grant for ``org_id``."""
    profile_id = new_id()
    member_id = new_id()
    client_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"cons-{user_id[:8]}@example.test",
        )
        await conn.execute(
            "INSERT INTO public.consultant_profiles "
            "(id, user_id, company_name, is_active, created_at, updated_at) "
            "VALUES ($1, $2, 'RLS Test Firm', TRUE, NOW(), NOW())",
            profile_id,
            user_id,
        )
        await conn.execute(
            "INSERT INTO public.consultant_firm_members "
            "(id, firm_id, user_id, role, is_active, created_at, updated_at) "
            "VALUES ($1, $2, $3, 'owner', TRUE, NOW(), NOW())",
            member_id,
            profile_id,
            user_id,
        )
        await conn.execute(
            "INSERT INTO public.consultant_clients "
            "(id, consultant_id, organization_id, client_name, status, "
            "created_at, updated_at) VALUES ($1, $2, $3, 'RLS Client', $4, NOW(), NOW())",
            client_id,
            profile_id,
            org_id,
            status,
        )


class TestConsultantActiveGrantIsolation:
    """D15 — ``is_org_consultant`` requires an ACTIVE consultant-client grant."""

    async def test_consultant_active_grant_sees_org_tenant_rows(
        self, pool: asyncpg.Pool
    ) -> None:
        org = await make_org(pool)
        user = new_id()
        await _seed_consultant(pool, user, org, status="active")
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.customer_factors ("
                " id, organization_id, name, activity_type, co2e_multiplier,"
                " country, reporting_year, factor_source, status, version"
                ") VALUES ($1, $2, 'A', 'Electricity', 0.2, 'GB', 2025, "
                " 'CUSTOMER', 'draft', 1)",
                new_id(),
                org,
            )
        async with _authenticated(pool, user) as conn:
            assert (
                await _count(conn, "customer_factors", "organization_id = $1", org)
                == 1
            )

    async def test_consultant_inactive_grant_denied_org_tenant_rows(
        self, pool: asyncpg.Pool
    ) -> None:
        org = await make_org(pool)
        user = new_id()
        await _seed_consultant(pool, user, org, status="inactive")
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.customer_factors ("
                " id, organization_id, name, activity_type, co2e_multiplier,"
                " country, reporting_year, factor_source, status, version"
                ") VALUES ($1, $2, 'A', 'Electricity', 0.2, 'GB', 2025, "
                " 'CUSTOMER', 'draft', 1)",
                new_id(),
                org,
            )
        async with _authenticated(pool, user) as conn:
            # D15: relationship ended → RLS denies the org tenant rows.
            assert (
                await _count(conn, "customer_factors", "organization_id = $1", org)
                == 0
            )



# ---------------------------------------------------------------------------
# D35 — self-service onboarding RLS behaviour
# ---------------------------------------------------------------------------


async def _seed_user_only(pool: asyncpg.Pool, user_id: str) -> None:
    """Seed a real user row with NO organization membership (brand-new
    customer)."""
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id, email) VALUES ($1, $2)",
            user_id,
            f"new-{user_id[:8]}@example.test",
        )


class TestD35SelfServiceOnboardingRLS:
    """D35 — the new onboarding surfaces never weaken RLS.

    * ``data_discovery_requests`` (now with the nullable ``organization_id``
      onboarding variant + ``created_by``) stays deny-by-default for the
      ``authenticated`` role.
    * A brand-new customer with NO membership sees no organisation rows.
    * The D35 columns are present and ``organization_id`` is nullable.
    * The owner role remains part of the real ``organization_members`` CHECK.
    """

    async def test_onboarding_requests_deny_by_default(
        self, pool: asyncpg.Pool
    ) -> None:
        org = await make_org(pool, name="D35 Candidate Org")
        user = new_id()
        # Service-role seed of a PRE-ORG-CREATION onboarding request owned by
        # ``user`` — RLS must still deny the authenticated read.
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO public.data_discovery_requests ("
                " id, candidate_organization_id, status, verification_method,"
                " created_by, created_at, updated_at"
                ") VALUES ($1, $2, 'pending_verification', 'email', $3, NOW(), NOW())",
                new_id(),
                org,
                user,
            )
        async with _authenticated(pool, user) as conn:
            assert (
                await _count(conn, "data_discovery_requests", "created_by = $1", user)
                == 0
            )

    async def test_new_customer_sees_no_org_rows(self, pool: asyncpg.Pool) -> None:
        org = await make_org(pool, name="D35 Private Org")
        user = new_id()
        await _seed_user_only(pool, user)
        async with _authenticated(pool, user) as conn:
            assert await _count(conn, "organizations", "id = $1", org) == 0

    async def test_d35_columns_present_and_org_nullable(self, pool: asyncpg.Pool) -> None:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT column_name, is_nullable FROM information_schema.columns "
                "WHERE table_name = 'data_discovery_requests' "
                "AND column_name IN ('created_by', 'organization_id')"
            )
            by_name = {r["column_name"]: r["is_nullable"] for r in rows}
            assert "created_by" in by_name
            assert by_name.get("organization_id") == "YES"

    async def test_owner_role_still_in_membership_check(self, pool: asyncpg.Pool) -> None:
        async with pool.acquire() as conn:
            check = await conn.fetchval(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid = 'public.organization_members'::regclass "
                "AND contype = 'c' AND conname = 'organization_members_role_check'"
            )
        assert check is not None and "owner" in check


# ---------------------------------------------------------------------------
# D37-0 — P0 billing security lockdown (authenticated write denial)
# ---------------------------------------------------------------------------


class TestBillingSecurityLockdown:
    """The D36 P0 defect, closed: authenticated customers cannot mutate
    authoritative billing state through PostgREST.

    Twelve denial checks (D37-0 §5) + the trusted/server-side path.
    """

    async def test_authenticated_cannot_write_usage_tracking(self, pool) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO public.usage_tracking "
                    "(organization_id, usage_date, ai_files_processed) "
                    "VALUES ($1, NOW(), 999)",
                    org_a,
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.usage_tracking SET ai_files_processed = 9999 "
                    "WHERE organization_id = $1",
                    org_a,
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "DELETE FROM public.usage_tracking WHERE organization_id = $1",
                    org_a,
                )

    async def test_authenticated_cannot_write_customer_subscriptions(self, pool) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            # Create an unauthorized subscription.
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO public.customer_subscriptions (organization_id) "
                    "VALUES ($1)",
                    org_a,
                )
            # Modify plan / status / limits.
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.customer_subscriptions SET status = 'active' "
                    "WHERE organization_id = $1",
                    org_a,
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "DELETE FROM public.customer_subscriptions "
                    "WHERE organization_id = $1",
                    org_a,
                )

    async def test_authenticated_cannot_write_consultant_billing(self, pool) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO public.consultant_billing "
                    "(consultant_id, plan) VALUES ($1, 'enterprise')",
                    member,
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.consultant_billing "
                    "SET plan = 'enterprise' WHERE consultant_id = $1",
                    member,
                )



    async def test_authenticated_cannot_modify_org_billing_trial_tax(self, pool) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            # Subscription state, trial state, tax authority fields + billing mode.
            for column, value in [
                ("subscription_status", "'active'"),
                ("subscription_tier", "'enterprise'"),
                ("trial_end_date", "NOW() + interval '1 year'"),
                ("tax_rate", "0"),
                ("billing_mode", "'STANDARD'"),
            ]:
                with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                    await conn.execute(
                        f"UPDATE public.organizations SET {column} = {value} "
                        "WHERE id = $1",
                        org_a,
                    )
            # Any direct org write is denied (no UPDATE grant at all).
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.organizations SET name = 'Hacked' WHERE id = $1",
                    org_a,
                )

    async def test_authenticated_cannot_grant_credit_entitlement(self, pool) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            # billing_plans / billing_commercial_config / billing_credit_ledger
            # are deny-by-default with no authenticated grants.
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO public.billing_credit_ledger "
                    "(organization_id, entry_type, credit_delta, source) "
                    "VALUES ($1, 'grant', 100000, 'hacked')",
                    org_a,
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO public.billing_plans (plan_code, name) "
                    "VALUES ('hacked', 'Hacked')"
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.billing_commercial_config SET config_value = '{}'"
                )


    async def test_d37_0_schema_foundation_present(self, pool) -> None:
        async with pool.acquire() as conn:
            for table in (
                "billing_plans",
                "billing_commercial_config",
                "billing_credit_ledger",
            ):
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' "
                    "AND tablename = $1)",
                    table,
                )
                assert exists, f"missing D37-0 table {table}"
            mode_col = await conn.fetchval(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'organizations' AND column_name = 'billing_mode'"
            )
            assert mode_col == "text"
            # No authenticated write policies remain on the legacy billing tables.
            policies = await conn.fetch(
                "SELECT tablename, cmd FROM pg_policies "
                "WHERE schemaname = 'public' "
                "AND tablename IN ('usage_tracking', 'customer_subscriptions') "
                "AND cmd IN ('INSERT', 'UPDATE', 'DELETE')"
            )
            assert policies == []


class TestBillingDenyByDefault:
    """D37 — the new commercial tables are deny-by-default for authenticated.

    Customers (and consultants / entity staff / anyone not on the trusted
    service path) must never mutate orders, payment records, storage metering,
    idempotency keys or the subscription lifecycle through PostgREST.
    """

    async def test_authenticated_cannot_write_d37_tables(self, pool) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            for table, body in (
                ("billing_orders", {"organization_id": org_a, "order_type": "assisted",
                                    "status": "approved", "items": "[]", "total_amount": 0}),
                ("billing_storage_usage", {"organization_id": org_a, "usage_bytes": 0}),
                ("billing_payment_records", {"organization_id": org_a, "provider": "x", "amount": 1}),
                ("billing_idempotency_keys", {"key": "x", "operation": "y"}),
            ):
                with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                    await conn.execute(
                        f"INSERT INTO public.{table} "
                        f"({', '.join(body.keys())}) VALUES ({', '.join('$'+str(i+1) for i in range(len(body)))})",
                        *body.values(),
                    )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.billing_orders SET status = 'completed'"
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "DELETE FROM public.billing_payment_records"
                )

    async def test_authenticated_cannot_write_subscription_lifecycle(self, pool) -> None:
        org_a = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO public.customer_subscriptions "
                    "(organization_id, plan_code, plan_version, lifecycle_status, billing_mode) "
                    "VALUES ($1, 'starter', 2, 'active', 'CREDIT')",
                    org_a,
                )

    async def test_trusted_service_writes_d37_tables(self, pool) -> None:
        """The trusted service path (owner) can write the D37 tables."""
        org_a = await make_org(pool)
        async with pool.acquire() as conn:
            order = await conn.fetchrow(
                "INSERT INTO public.billing_orders "
                "(organization_id, order_type, status, items, total_amount) "
                "VALUES ($1, 'assisted', 'estimated', '[{\"q\":1}]'::jsonb, 9.99) RETURNING id",
                org_a,
            )
            assert order is not None
            sub = await conn.fetchrow(
                "INSERT INTO public.customer_subscriptions "
                "(organization_id, plan, plan_code, plan_version, lifecycle_status, billing_mode) "
                "VALUES ($1, 'starter', 'starter', 2, 'active', 'CREDIT') RETURNING id",
                org_a,
            )
            assert sub is not None
            # Cleanup (test DB only).
            await conn.execute("DELETE FROM public.billing_orders WHERE id = $1", order["id"])
            await conn.execute("DELETE FROM public.customer_subscriptions WHERE id = $1", sub["id"])

    async def test_authenticated_cannot_modify_another_orgs_billing(self, pool) -> None:
        org_a = await make_org(pool)
        org_b = await make_org(pool)
        member = new_id()
        await _seed_org_member(pool, org_a, member)
        async with _authenticated(pool, member) as conn:
            # Cross-organisation writes denied on the legacy billing tables
            # (and the org row itself).
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.customer_subscriptions SET status = 'active' "
                    "WHERE organization_id = $1",
                    org_b,
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.usage_tracking SET ai_files_processed = 1 "
                    "WHERE organization_id = $1",
                    org_b,
                )
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "UPDATE public.organizations SET billing_mode = 'STANDARD' "
                    "WHERE id = $1",
                    org_b,
                )

    async def test_trusted_service_path_still_writes(self, pool) -> None:
        """The trusted/server-side path (service role / owner) is unaffected."""
        org_a = await make_org(pool)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO public.usage_tracking "
                "(organization_id, usage_date, ai_files_processed) "
                "VALUES ($1, NOW(), 1) RETURNING id",
                org_a,
            )
            assert row is not None
            await conn.execute("DELETE FROM public.usage_tracking WHERE id = $1", row["id"])

            sub = await conn.fetchrow(
                "INSERT INTO public.customer_subscriptions "
                "(organization_id, status, plan) VALUES ($1, 'active', 'starter') "
                "RETURNING id",
                org_a,
            )
            assert sub is not None
            await conn.execute(
                "DELETE FROM public.customer_subscriptions WHERE id = $1", sub["id"]
            )

            await conn.execute(
                "UPDATE public.organizations SET trial_end_date = NULL WHERE id = $1",
                org_a,
            )

    async def test_d37_0_schema_foundation_present(self, pool) -> None:
        async with pool.acquire() as conn:
            for table in (
                "billing_plans",
                "billing_commercial_config",
                "billing_credit_ledger",
            ):
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' "
                    "AND tablename = $1)",
                    table,
                )
                assert exists, f"missing D37-0 table {table}"
            mode_col = await conn.fetchval(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'organizations' AND column_name = 'billing_mode'"
            )
            assert mode_col == "text"
            # No authenticated write policies remain on the legacy billing tables.
            policies = await conn.fetch(
                "SELECT tablename, cmd FROM pg_policies "
                "WHERE schemaname = 'public' "
                "AND tablename IN ('usage_tracking', 'customer_subscriptions') "
                "AND cmd IN ('INSERT', 'UPDATE', 'DELETE')"
            )
            assert policies == []
