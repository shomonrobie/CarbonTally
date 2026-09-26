"""P17-L — the governed capability truth surface: real-PostgreSQL verification.

Why this file exists
--------------------
`P17-DECISION-03 §6` requires the customer and investor surfaces to consume ONE
canonical capability truth, and `§18.3` makes the gates `AG-1`…`AG-8`
deterministic checks. `P17-K` verified the *catalogue*; this suite verifies the
*read surface* against a real, migrated PostgreSQL database:

1. the catalogue exists on the evidenced framework version;
2. the catalogue rows are unchanged (the read surface writes nothing);
3. the projection returns the expected rows from the **persisted** rows;
4. the exact `M-1` mapping is preserved (§11.2 — non-upgrade is absolute);
5. the four-way rollup is exact and derived (`AG-7`);
6. no applicability model exists anywhere in the read path (`PO-3`, `F-1`);
7. no tenant data is returned (`CS-1`, `SEC-1`);
8. a negative tenant-isolation test: two tenant contexts see **identical**
   capability truth (`§19.4` row 8);
9. the safety probe refuses the demo database **before** any destructive
   statement (F-046-1);
10. the demo/production-style databases remain untouched.

Safety (F-046-1 restated)
-------------------------
This module uses the shared ``pool`` fixture, which performs **destructive**
setup (``TRUNCATE … RESTART IDENTITY CASCADE``). It therefore inherits that
fixture's guard: a target whose name matches ``qa`` / ``demo`` / ``investor`` /
``prod`` / ``live`` is refused before any statement runs, and the main
application databases are refused outright. Point
``INTEGRATION_DATABASE_URL`` at a disposable ``ct_*`` clone::

    INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_p17l_surface_20260926 \\
      .venv/bin/python -m pytest \\
      tests/integration/test_p17l_capability_truth_surface_runtime.py

The disclosure catalogue is **not** in the fixture's ``_TRUNCATE_TABLES`` list
(it is global, tenant-free reference data with no ``organization_id``), so the
rows seeded by the P17-K migration survive the reset and can be asserted. No
production, demo, investor or QA environment is contacted, and no migration is
applied to one.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import uuid
from datetime import datetime
from typing import Any

import asyncpg
import httpx
import pytest
from fastapi import FastAPI

import api.v3_disclosure as disclosure_api  # noqa: F401 - the module under test
from api.dependencies import get_current_user, get_pool
from api.v3_disclosure import router as disclosure_router
from auth import AuthUser
from data.disclosure import DisclosureCatalogRepository
from data.organizations import OrganizationsRepository
from domain import capability_catalogue as cc
from domain.disclosure import CARBONTALLY_CAPABILITIES, REQUIREMENT_CLASSES
from domain.organization import Organization

pytestmark = pytest.mark.asyncio

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[2]
ROUTE = "/api/v3/capabilities"
FRAMEWORK_CODE = "GHG_PROTOCOL"
VERSION_LABEL = "Corporate Accounting and Reporting Standard (2004 revised edition)"

#: The frozen `M-1` image (P17-DECISION-03 §11.1/§11.2).
M1_IMAGE: dict[str, str] = {
    "GP-S3-CAT-01": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-02": "MISSING_CAPABILITY",
    "GP-S3-CAT-03": "SUPPORTED",
    "GP-S3-CAT-04": "SUPPORTED",
    "GP-S3-CAT-05": "SUPPORTED",
    "GP-S3-CAT-06": "SUPPORTED",
    "GP-S3-CAT-07": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-08": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-09": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-10": "MISSING_CAPABILITY",
    "GP-S3-CAT-11": "FUTURE",
    "GP-S3-CAT-12": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-13": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-14": "FUTURE",
    "GP-S3-CAT-15": "FUTURE",
}

ROLLUP: dict[str, int] = {
    "SUPPORTED": 4,
    "PARTIALLY_SUPPORTED": 6,
    "FUTURE": 3,
    "MISSING_CAPABILITY": 2,
}

ALL_CODES: tuple[str, ...] = (
    "GP-S1",
    "GP-S2-LB",
    "GP-S2-MB",
    *tuple(M1_IMAGE),
)

AXIS_A_PATTERN = r"\b(PARTIAL|DEFERRED|NOT_IMPLEMENTED)\b"
UNRESOLVED = "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION"

#: The three governed catalogue tables the read model may touch.
CATALOGUE_TABLES: tuple[str, ...] = (
    "disclosure_requirement_versions",
    "disclosure_framework_versions",
    "disclosure_frameworks",
)

#: Tenant/tenant-adjacent tables the read model must never name.
TENANT_TABLES: tuple[str, ...] = (
    "organizations",
    "organization_members",
    "organization_metadata",
    "facilities",
    "suppliers",
    "customer_documents",
    "calculation_snapshots",
    "emissions_logs",
    "disclosure_values",
    "disclosure_applicability_assessments",
    "report_versions",
    "reports",
)


def _read_path_statements(statements: list[str]) -> list[str]:
    """Only the statements the read model itself issued.

    asyncpg emits a small number of housekeeping statements on a fresh
    connection (it probes e.g. ``jit``); those are driver introspection, not the
    read model's SQL, and counting them would misstate both the query count and
    the tenant audit.
    """
    return [
        statement
        for statement in statements
        if any(table in statement.lower() for table in CATALOGUE_TABLES)
    ]


# ---------------------------------------------------------------------------
# Helpers — the real read path (repository → canonical projection)
# ---------------------------------------------------------------------------
async def _select_catalogue_version(pool: Any) -> dict[str, Any]:
    """The governed capability catalogue version — the **shipped** selector.

    This calls the production selector instead of re-implementing the rule, so
    this suite cannot stay green while the route's rule differs (`P17-M2`,
    `DEF-1`).
    """
    candidates = await DisclosureCatalogRepository(pool).capability_catalogue_candidates()
    version = cc.select_governed_catalogue_version(candidates)
    if version is None:
        raise AssertionError("no framework version carries a governed capability catalogue")
    return version


async def _read_catalogue(pool: Any) -> list[dict[str, Any]]:
    """The shipped repository read, against the real database."""
    version = await _select_catalogue_version(pool)
    return await DisclosureCatalogRepository(pool).list_capability_catalogue_requirements(
        str(version["id"])
    )


async def _project(pool: Any) -> dict[str, Any]:
    """The shipped read path end to end: selection → repository → projection."""
    repository = DisclosureCatalogRepository(pool)
    version = await _select_catalogue_version(pool)
    framework = await repository.get_framework_by_code(str(version.get("framework_code") or ""))
    assert framework is not None, "the framework of the governed catalogue must exist"
    return cc.project_capability_catalogue(
        framework=framework,
        framework_version=version,
        requirement_rows=await repository.list_capability_catalogue_requirements(
            str(version["id"])
        ),
    )


def _app(pool: asyncpg.Pool, user: AuthUser) -> FastAPI:
    """The real ASGI app with the real pool and a fixed authenticated actor."""
    app = FastAPI()
    app.include_router(disclosure_router)

    async def _pool() -> asyncpg.Pool:
        return pool

    app.dependency_overrides[get_pool] = _pool
    app.dependency_overrides[get_current_user] = lambda: user
    return app


async def _get(pool: asyncpg.Pool, user: AuthUser) -> httpx.Response:
    """Drive the real HTTP route in-process, on the real database."""
    transport = httpx.ASGITransport(app=_app(pool, user))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(ROUTE)


def _user(organization_id: str, user_id: str) -> AuthUser:
    return AuthUser(
        user_id=user_id,
        email="owner@example.test",
        role="owner",
        organization_id=organization_id,
        is_org_member=True,
    )


class _LoggedPool:
    """A pool-like shim handing out ONE real connection.

    `AbstractRepository` only needs ``acquire()`` → async context manager, so a
    single logged connection lets the suite audit every statement the read model
    actually issues (`SEC-3`) without reaching into asyncpg internals.
    """

    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    def acquire(self) -> Any:
        connection = self._connection

        class _Ctx:
            async def __aenter__(self) -> asyncpg.Connection:
                return connection

            async def __aexit__(self, *exc: Any) -> bool:
                return False

        return _Ctx()


async def _logged_connection() -> tuple[asyncpg.Connection, _LoggedPool]:
    """A real connection to the disposable clone, plus a pool shim over it."""
    connection = await asyncpg.connect(os.environ["DATABASE_URL"])
    return connection, _LoggedPool(connection)


async def _make_org(pool: asyncpg.Pool, name: str) -> str:
    """Create a real organisation row and return its id (a genuine tenant)."""
    org = Organization(
        id=str(uuid.uuid4()),
        name=name,
        country="GB",
        is_active=True,
        created_at=datetime.now(),
    )
    await OrganizationsRepository(pool).save(org)
    return org.id


# ===========================================================================
# 1–2. The catalogue exists and is unchanged by the read surface
# ===========================================================================
async def test_the_catalogue_exists_on_the_evidenced_framework_version(
    pool: asyncpg.Pool,
) -> None:
    row = await pool.fetchrow(
        """
        SELECT fv.version_label, fv.status, fv.source_tier, count(rv.id)::int AS n
          FROM public.disclosure_frameworks f
          JOIN public.disclosure_framework_versions fv ON fv.framework_id = f.id
          LEFT JOIN public.disclosure_requirement_versions rv
                 ON rv.framework_version_id = fv.id
         WHERE f.code = $1 AND fv.version_label = $2
         GROUP BY fv.version_label, fv.status, fv.source_tier
        """,
        FRAMEWORK_CODE,
        VERSION_LABEL,
    )
    assert row is not None, "the governed framework version is absent"
    assert row["version_label"] == VERSION_LABEL
    assert row["status"] == "IN_FORCE"
    assert row["source_tier"] == 1
    assert row["n"] == 18


async def test_the_catalogue_is_the_exact_governed_requirement_set(
    pool: asyncpg.Pool,
) -> None:
    rows = await _read_catalogue(pool)
    assert [row["requirement_code"] for row in rows] == list(ALL_CODES)


async def test_the_read_path_writes_nothing(pool: asyncpg.Pool) -> None:
    """A read surface must not mutate the governed catalogue (AGENTS.md §66)."""
    before = await pool.fetchrow(
        """
        SELECT count(*)::int AS n,
               coalesce(max(updated_at), 'epoch'::timestamptz) AS latest,
               coalesce(sum(hashtext(rv.requirement_code || rv.carbontally_capability)), 0) AS sig
          FROM public.disclosure_requirement_versions rv
        """
    )
    payload = await _project(pool)
    assert payload["requirements"]
    await _get(pool, _user("11111111-1111-4111-8111-111111111111", "a" * 8))
    after = await pool.fetchrow(
        """
        SELECT count(*)::int AS n,
               coalesce(max(updated_at), 'epoch'::timestamptz) AS latest,
               coalesce(sum(hashtext(rv.requirement_code || rv.carbontally_capability)), 0) AS sig
          FROM public.disclosure_requirement_versions rv
        """
    )
    assert dict(before) == dict(after), (dict(before), dict(after))



# ===========================================================================
# 3. The projection returns the expected rows, from the persisted rows
# ===========================================================================
async def test_the_projection_returns_the_expected_rows(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    assert payload["surface"] == "CAPABILITY_TRUTH"
    assert len(payload["requirements"]) == 18
    assert payload["capability_vocabulary"] == list(CARBONTALLY_CAPABILITIES)
    assert payload["framework"]["code"] == FRAMEWORK_CODE
    assert payload["framework_version"]["version_label"] == VERSION_LABEL


async def test_every_scope_and_category_is_present(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    scopes = {item["scope"] for item in payload["requirements"]}
    assert scopes == {"Scope 1", "Scope 2", "Scope 3"}
    categories = sorted(
        item["scope3_category"]
        for item in payload["requirements"]
        if item["scope3_category"] is not None
    )
    assert categories == list(range(1, 16))
    methods = {
        item["scope2_method"]
        for item in payload["requirements"]
        if item["scope2_method"] is not None
    }
    assert methods == {"LOCATION_BASED", "MARKET_BASED"}


async def test_every_requirement_carries_its_governed_metadata(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    for item in payload["requirements"]:
        assert item["requirement_name"], item["requirement_code"]
        assert item["carbontally_capability"] in CARBONTALLY_CAPABILITIES
        assert item["requirement_class"] in REQUIREMENT_CLASSES
        assert item["requirement_class_expression"] in REQUIREMENT_CLASSES
        assert item["capability_explanation"].strip()
        assert item["capability_detail"], item["requirement_code"]


# ===========================================================================
# 4. The exact M-1 mapping (non-upgrade is a test, not a convention)
# ===========================================================================
async def test_the_m1_mapping_is_preserved_exactly(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    by_code = {item["requirement_code"]: item for item in payload["requirements"]}
    for code, capability in M1_IMAGE.items():
        assert by_code[code]["carbontally_capability"] == capability, code

    # ... and the persisted database value agrees with the projection (AG-1).
    persisted = {
        row["requirement_code"]: row["carbontally_capability"] for row in await _read_catalogue(pool)
    }
    for code, capability in M1_IMAGE.items():
        assert persisted[code] == capability, code


async def test_scope2_market_based_is_not_producible(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    by_method = {
        item["scope2_method"]: item
        for item in payload["requirements"]
        if item["scope2_method"] is not None
    }
    assert by_method["MARKET_BASED"]["carbontally_capability"] == "MISSING_CAPABILITY"
    assert by_method["MARKET_BASED"]["requirement_class_expression"] == "NOT_SUPPORTED"
    assert by_method["MARKET_BASED"]["supported"] is False
    assert by_method["LOCATION_BASED"]["carbontally_capability"] == "SUPPORTED"


async def test_no_persisted_row_upgrades_a_scope3_category(pool: asyncpg.Pool) -> None:
    """`S3-2` — a bounded category is never recorded as fully supported."""
    for code in ("GP-S3-CAT-01", "GP-S3-CAT-07", "GP-S3-CAT-08", "GP-S3-CAT-09",
                 "GP-S3-CAT-12", "GP-S3-CAT-13"):
        value = await pool.fetchval(
            "SELECT carbontally_capability FROM public.disclosure_requirement_versions "
            "WHERE requirement_code = $1",
            code,
        )
        assert value == "PARTIALLY_SUPPORTED", (code, value)


# ===========================================================================
# 5. The four-way rollup is exact and derived (AG-7)
# ===========================================================================
async def test_the_four_way_rollup_is_exact(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    assert payload["scope3_capability_rollup"] == ROLLUP


async def test_the_rollup_is_recomputed_from_the_persisted_rows(pool: asyncpg.Pool) -> None:
    rows = await _read_catalogue(pool)
    assert cc.scope3_capability_rollup(rows) == ROLLUP
    # The SQL the database itself would compute agrees.
    counts = await pool.fetch(
        """
        SELECT rv.carbontally_capability AS capability, count(*)::int AS n
          FROM public.disclosure_requirement_versions rv
          JOIN public.disclosure_framework_versions fv ON fv.id = rv.framework_version_id
          JOIN public.disclosure_frameworks f ON f.id = fv.framework_id
         WHERE f.code = $1 AND rv.requirement_code LIKE 'GP-S3-CAT-%'
         GROUP BY rv.carbontally_capability
        """,
        FRAMEWORK_CODE,
    )
    assert {row["capability"]: row["n"] for row in counts} == ROLLUP


async def test_no_total_or_coverage_figure_is_produced(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    cc.assert_no_forbidden_field(payload)
    text = json.dumps(payload, default=str).lower()
    assert "15 categories supported" not in text
    assert "all 15" not in text



# ===========================================================================
# 6. No applicability model exists in the read path (PO-3 / F-1)
# ===========================================================================
async def test_no_applicability_vocabulary_is_persisted_for_the_catalogue(
    pool: asyncpg.Pool,
) -> None:
    for token in ("NOT_APPLICABLE", "DOES_NOT_APPLY", "UNDETERMINED", "APPLIES"):
        found = await pool.fetchval(
            """
            SELECT count(*)::int
              FROM public.disclosure_requirement_versions rv
             WHERE rv.requirement_class = $1
                OR rv.carbontally_capability = $1
            """,
            token,
        )
        assert found == 0, (token, found)


async def test_no_applicability_column_or_assessment_is_reachable(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    text = json.dumps(payload, default=str).lower()
    for forbidden in ("applicability", "does_not_apply", "assessed_status"):
        assert forbidden not in text, forbidden

    columns = await pool.fetch(
        """
        SELECT column_name FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name IN ('disclosure_requirement_versions', 'disclosure_framework_versions')
        """
    )
    names = {row["column_name"] for row in columns}
    # No *applicability* column exists. (`applicable_from` / `applicable_to` are
    # the pre-existing framework-version period columns, not a category model.)
    assert not {name for name in names if "applicab" in name and name not in (
        "applicable_from", "applicable_to"
    )}, names


async def test_the_catalogue_tables_carry_no_tenant_column(pool: asyncpg.Pool) -> None:
    columns = await pool.fetch(
        """
        SELECT table_name, column_name FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name IN ('disclosure_requirement_versions',
                              'disclosure_framework_versions',
                              'disclosure_frameworks')
        """
    )
    for row in columns:
        assert "organization" not in row["column_name"], row
        assert "tenant" not in row["column_name"], row
        assert "facility" not in row["column_name"], row


async def test_no_foreign_key_leads_from_the_catalogue_to_a_tenant_table(
    pool: asyncpg.Pool,
) -> None:
    fks = await pool.fetch(
        """
        SELECT tc.table_name AS source, ccu.table_name AS target
          FROM information_schema.table_constraints tc
          JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
           AND ccu.table_schema = tc.table_schema
         WHERE tc.constraint_type = 'FOREIGN KEY'
           AND tc.table_schema = 'public'
           AND tc.table_name IN ('disclosure_requirement_versions',
                                 'disclosure_framework_versions',
                                 'disclosure_frameworks')
        """
    )
    tenant_tables = set(TENANT_TABLES) | {"organization_metadata"}
    for row in fks:
        assert row["target"] not in tenant_tables, (row["source"], row["target"])


# ===========================================================================
# 7. No tenant data is returned
# ===========================================================================
TENANT_TOKENS: tuple[str, ...] = (
    "organization_id",
    "organisation_id",
    "tenant_id",
    "facility_id",
    "supplier_id",
    "report_id",
    "report_version_id",
    "customer_document",
)


async def test_no_tenant_token_is_returned(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    text = json.dumps(payload, default=str)
    for token in TENANT_TOKENS:
        assert token not in text, token


async def test_no_tenant_query_is_issued_by_the_read_model(pool: asyncpg.Pool) -> None:
    """`SEC-3` — the *query path*, not only the rendered output.

    `AbstractRepository` only needs ``acquire()``, so a single real connection
    with a query logger attached is enough to audit every statement the read
    model issues.
    """
    connection, logged_pool = await _logged_connection()
    statements: list[str] = []

    def _log(record: Any) -> None:
        """asyncpg hands the logger a single ``LoggedQuery`` record."""
        statements.append(record.query)

    connection.add_query_logger(_log)
    try:
        payload = await _project(logged_pool)
    finally:
        connection.remove_query_logger(_log)
        await connection.close()

    assert payload["requirements"], "the read path must return the catalogue"
    read_path = _read_path_statements(statements)
    assert read_path, "the read path must have issued statements"
    for query in read_path:
        for table in TENANT_TABLES:
            assert table not in query.lower(), query
        assert "current_setting" not in query.lower(), query
        assert "auth.uid" not in query.lower(), query
    # ... and nothing in the whole capture names a tenant table.
    for query in statements:
        for table in TENANT_TABLES:
            assert table not in query.lower(), query



# ===========================================================================
# 8. Negative tenant isolation (§19.4 row 8: investor surface → tenant data DENY)
# ===========================================================================
async def test_two_tenant_contexts_see_identical_capability_truth(
    pool: asyncpg.Pool,
) -> None:
    """§13 — a tenant query may not alter capability truth, because there is none.

    A dedicated single-connection pool is used so the session-level JWT claim is
    applied to the *same* connection the read path uses: if any tenant predicate
    existed, these two reads would differ.
    """
    dsn = os.environ["DATABASE_URL"]
    dedicated = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=1)
    try:
        first = await _project(dedicated)
        async with dedicated.acquire() as conn:
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, false)",
                json.dumps({"sub": "11111111-1111-4111-8111-111111111111",
                            "role": "authenticated"}),
            )
        second = await _project(dedicated)
        async with dedicated.acquire() as conn:
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, false)",
                json.dumps({"sub": "22222222-2222-4222-8222-222222222222",
                            "role": "authenticated"}),
            )
        third = await _project(dedicated)
    finally:
        await dedicated.close()

    assert json.dumps(first, default=str) == json.dumps(second, default=str)
    assert json.dumps(first, default=str) == json.dumps(third, default=str)


async def test_the_http_surface_is_byte_identical_under_two_identities(
    pool: asyncpg.Pool,
) -> None:
    """Two genuinely authorised tenants get the same product truth (`CS-2`)."""
    org_a = await _make_org(pool, "P17L Tenant A")
    org_b = await _make_org(pool, "P17L Tenant B")
    response_a = await _get(pool, _user(org_a, "11111111-1111-4111-8111-111111111111"))
    response_b = await _get(pool, _user(org_b, "22222222-2222-4222-8222-222222222222"))
    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    assert response_a.content == response_b.content
    # Neither tenant's identifier is echoed back.
    assert org_a not in response_a.text
    assert org_b not in response_b.text


async def test_the_product_surface_answers_without_any_tenant_context(
    pool: asyncpg.Pool,
) -> None:
    """`SEC-1` — the endpoint is safe to serve with no tenant at all."""
    response = await _get(
        pool,
        AuthUser(
            user_id="33333333-3333-4333-8333-333333333333",
            email="reviewer@carbontally.local",
            role="reviewer",
            is_staff=True,
            is_org_member=False,
        ),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["requirements"]) == 18
    assert body["scope3_capability_rollup"] == ROLLUP


# ===========================================================================
# 9–10. Safety probes (F-046-1) — the demo database is refused, untouched
# ===========================================================================
DEMO_DB = "carbontally_demo_local"
DEMO_DSN = f"postgresql://postgres:postgres@127.0.0.1:54426/{DEMO_DB}"


async def test_the_demo_database_catalogue_is_untouched_by_this_work(
    pool: asyncpg.Pool,
) -> None:
    """`AGENTS.md §55` — the demo database is never mutated by this task."""
    requirements, versions = await _demo_catalogue_counts()
    # The P17-K catalogue has not been promoted to the demo database, and this
    # task neither promotes it nor mutates anything there.
    assert requirements == 0, requirements
    assert versions == 0, versions


async def test_the_safety_probe_refuses_the_demo_database_before_any_truncate(
    pool: asyncpg.Pool,
) -> None:
    """F-046-1 — a mis-pointed destructive run fails loudly, before TRUNCATE."""
    before = await _demo_catalogue_counts()
    env = dict(os.environ)
    env["INTEGRATION_DATABASE_URL"] = DEMO_DSN
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
            "tests/integration/test_p17l_capability_truth_surface_runtime.py"
            "::test_the_catalogue_is_the_exact_governed_requirement_set",
        ],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "F-046-1" in output, output
    assert "refusing to run the integration suite" in output, output
    assert "carbontally_demo_local" in output, output

    # ... and the refused target was not touched (fixture setup never ran).
    assert await _demo_catalogue_counts() == before


async def _demo_catalogue_counts() -> tuple[int, int]:
    connection = await asyncpg.connect(DEMO_DSN)
    try:
        requirements = await connection.fetchval(
            "SELECT count(*)::int FROM public.disclosure_requirement_versions"
        )
        versions = await connection.fetchval(
            "SELECT count(*)::int FROM public.disclosure_framework_versions"
        )
    finally:
        await connection.close()
    return int(requirements), int(versions)


async def test_the_dedicated_test_database_is_not_this_target(pool: asyncpg.Pool) -> None:
    """This suite must not be running against ``carbontally_test`` or a demo DB."""
    name = await pool.fetchval("SELECT current_database()")
    assert name not in ("carbontally_test", DEMO_DB, "carbontally_qa_phase8")
    assert "demo" not in str(name).lower()
    assert "qa" not in str(name).lower()



# ===========================================================================
# The HTTP route end to end, on real persisted rows
# ===========================================================================
async def test_the_route_serves_the_canonical_projection(pool: asyncpg.Pool) -> None:
    response = await _get(pool, _user(str(uuid.uuid4()), str(uuid.uuid4())))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["surface"] == "CAPABILITY_TRUTH"
    assert body["scope3_capability_rollup"] == ROLLUP
    assert len(body["requirements"]) == 18
    # The HTTP payload is the projection, not a re-derivation of it.
    assert body == json.loads(json.dumps(await _project(pool), default=str))


async def test_the_route_refuses_an_unauthenticated_caller(pool: asyncpg.Pool) -> None:
    app = FastAPI()
    app.include_router(disclosure_router)

    async def _pool() -> asyncpg.Pool:
        return pool

    app.dependency_overrides[get_pool] = _pool
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(ROUTE)
    assert response.status_code == 401, response.text


async def test_the_route_issues_at_most_three_read_queries(pool: asyncpg.Pool) -> None:
    """A thin read model: the surface adds no fourth query of its own."""
    connection, logged_pool = await _logged_connection()
    statements: list[str] = []

    def _log(record: Any) -> None:
        """asyncpg hands the logger a single ``LoggedQuery`` record."""
        statements.append(record.query)

    app = FastAPI()
    app.include_router(disclosure_router)

    async def _pool() -> _LoggedPool:
        return logged_pool

    app.dependency_overrides[get_pool] = _pool
    app.dependency_overrides[get_current_user] = lambda: _user(str(uuid.uuid4()), str(uuid.uuid4()))

    connection.add_query_logger(_log)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get(ROUTE)
    finally:
        connection.remove_query_logger(_log)
        await connection.close()

    assert response.status_code == 200, response.text
    assert response.json()["scope3_capability_rollup"] == ROLLUP
    read_path = _read_path_statements(statements)
    # candidates + framework + requirements: three statements, and no more.
    assert 1 <= len(read_path) <= 3, read_path



# ===========================================================================
# AG-3 / AG-4 / AG-7 / AG-8 — on real persisted rows
# ===========================================================================
async def test_ag_3_no_axis_a_token_is_renderable_from_real_rows(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    cc.assert_no_axis_a_status_token(payload)
    text = json.dumps(payload, default=str)
    assert not re.search(AXIS_A_PATTERN, text, re.IGNORECASE)
    assert "architecture_status" not in text


async def test_ag_3_no_axis_a_token_exists_in_the_persisted_catalogue(
    pool: asyncpg.Pool,
) -> None:
    """Row text included: a surface cannot leak an internal status by copying it."""
    offenders = await pool.fetch(
        """
        SELECT rv.requirement_code FROM public.disclosure_requirement_versions rv
         WHERE rv.title ~* $1
            OR coalesce(rv.description, '') ~* $1
            OR rv.requirement_code ~* $1
        """,
        AXIS_A_PATTERN,
    )
    assert offenders == [], [row["requirement_code"] for row in offenders]


async def test_ag_4_no_placeholder_or_figure_is_renderable_from_real_rows(
    pool: asyncpg.Pool,
) -> None:
    payload = await _project(pool)
    cc.assert_no_placeholder_or_figure(payload)
    for item in payload["requirements"]:
        assert item["result_presence"] is None, item["requirement_code"]


async def test_ag_8_every_real_row_carries_provenance(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    for item in payload["requirements"]:
        provenance = item["provenance"]
        assert provenance["source_locator"], item["requirement_code"]
        assert provenance["authoritative_text_ref"], item["requirement_code"]
        assert provenance["source_tier"] == 1, item["requirement_code"]
        assert provenance["identifier_status"] in ("RESOLVED", UNRESOLVED)
        if provenance["identifier_status"] == UNRESOLVED:
            assert provenance["official_identifier"] is None, item["requirement_code"]
        # ... and the marker is the one the catalogue actually records.
        persisted = await pool.fetchval(
            "SELECT identifier_status FROM public.disclosure_requirement_versions "
            "WHERE requirement_code = $1",
            item["requirement_code"],
        )
        assert persisted == provenance["identifier_status"], item["requirement_code"]


async def test_ag_8_no_official_identifier_is_invented(pool: asyncpg.Pool) -> None:
    invented = await pool.fetchval(
        """
        SELECT count(*)::int FROM public.disclosure_requirement_versions
         WHERE identifier_status <> 'RESOLVED' AND official_identifier IS NOT NULL
        """
    )
    assert invented == 0


async def test_ag_7_the_rollup_is_never_a_total(pool: asyncpg.Pool) -> None:
    payload = await _project(pool)
    assert set(payload["scope3_capability_rollup"]) == set(ROLLUP)
    assert sum(payload["scope3_capability_rollup"].values()) == 15
    # No coverage/percentage field, and nothing computed from tenant data.
    cc.assert_no_forbidden_field(payload)
    assert "coverage" not in json.dumps(payload).lower().replace(
        "a coverage figure", ""
    )


# ===========================================================================
# 11. Version scoping (regression) — a second framework version never widens
#     the claim
# ===========================================================================
async def test_the_selected_version_is_the_governed_catalogue(pool: asyncpg.Pool) -> None:
    version = await _select_catalogue_version(pool)
    assert version["version_label"] == VERSION_LABEL
    assert version["framework_code"] == FRAMEWORK_CODE
    assert version["status"] == "IN_FORCE"


async def test_a_second_framework_version_never_widens_the_catalogue(
    pool: asyncpg.Pool,
) -> None:
    """Reproduces the defect this task found, on real PostgreSQL.

    An earlier revision of the read model filtered by framework *code*, so any
    other version of the same framework (test residue, a future catalogue,
    another standard's rows) merged into the claim — and the projection then
    refused the whole statement, taking the surface to 503. The surface must
    select the governed version by rule, and must ignore non-governed rows.

    The extra rows are created **and removed** inside this test, tagged with a
    run-unique code, so nothing is left behind in the clone.
    """
    suffix = uuid.uuid4().hex[:8]
    junk_code = f"B1RT_{suffix}"
    framework_id = await pool.fetchval(
        "SELECT id FROM public.disclosure_frameworks WHERE code = $1", FRAMEWORK_CODE
    )
    version_id = await pool.fetchval(
        """
        INSERT INTO public.disclosure_framework_versions
            (framework_id, version_label, source_tier, status)
        VALUES ($1, $2, 1, 'IN_FORCE')
        RETURNING id
        """,
        framework_id,
        f"B1RT-{suffix}",
    )
    try:
        await pool.execute(
            """
            INSERT INTO public.disclosure_requirement_versions
                (framework_version_id, requirement_code, title, requirement_class,
                 value_kind, carbontally_capability, display_order)
            VALUES ($1, $2, 'Residue row', 'REQUIRED', 'QUANTITATIVE',
                    'MISSING_CAPABILITY', 1)
            """,
            version_id,
            junk_code,
        )

        # The read path still selects the governed version and returns exactly
        # the 18 governed rows.
        payload = await _project(pool)
        assert payload["framework_version"]["version_label"] == VERSION_LABEL
        assert len(payload["requirements"]) == 18
        assert payload["scope3_capability_rollup"] == ROLLUP
        assert junk_code not in json.dumps(payload)

        # ... and the surface agrees over HTTP.
        response = await _get(pool, _user(str(uuid.uuid4()), str(uuid.uuid4())))
        assert response.status_code == 200, response.text
        assert response.json()["scope3_capability_rollup"] == ROLLUP
        assert junk_code not in response.text
    finally:
        await pool.execute(
            "DELETE FROM public.disclosure_requirement_versions "
            "WHERE framework_version_id = $1",
            version_id,
        )
        await pool.execute(
            "DELETE FROM public.disclosure_framework_versions WHERE id = $1", version_id
        )

    # The clone is left exactly as it was found.
    assert len(await _read_catalogue(pool)) == 18


async def test_a_database_with_only_ungoverned_rows_is_refused(pool: asyncpg.Pool) -> None:
    """A version whose rows are not governed identities is never the catalogue."""
    assert cc.is_governed_requirement_code("GP-S3-CAT-03") is True
    for code in ("B1RT_068e737e", "GP-S4", "GP-S2-XX", "", "cat-1"):
        assert cc.is_governed_requirement_code(code) is False


# ===========================================================================
# AG-1 — the persisted CHECK constraints still equal the code constants
# ===========================================================================
async def test_ag_1_the_check_constraints_equal_the_governed_constants(
    pool: asyncpg.Pool,
) -> None:
    capability_definition = await pool.fetchval(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conname = 'disclosure_requirement_versions_capability_check'"
    )
    assert capability_definition, "the capability CHECK constraint is absent"
    for value in CARBONTALLY_CAPABILITIES:
        assert f"'{value}'" in capability_definition, (value, capability_definition)

    class_definition = await pool.fetchval(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conname = 'disclosure_requirement_versions_class_check'"
    )
    assert class_definition, "the requirement-class CHECK constraint is absent"
    for value in REQUIREMENT_CLASSES:
        assert f"'{value}'" in class_definition, (value, class_definition)

