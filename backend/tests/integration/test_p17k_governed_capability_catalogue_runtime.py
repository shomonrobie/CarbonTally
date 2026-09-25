"""P17-K — governed capability catalogue: real-PostgreSQL runtime verification.

Why this file exists
--------------------
``P17-DECISION-03 §20.3`` defines P17-K as two things: the governed catalogue
rows, and "the §18.3 gates ``AG-1`` … ``AG-8`` as automated tests". Its §20.2
also records, as an explicit non-claim, that *"the governed requirement catalogue
populated"* was **NOT DONE — 0 rows (PR-2)**. Every claim in this file is
therefore a claim about a **stored row in a real database**, not about an
in-memory double or a migration text:

* the real P17 schema (the five authorised migrations, applied);
* the real governed vocabulary, read from the database and compared with
  ``domain.disclosure``;
* the real projection engine, ``domain.disclosure_projection``.

What it proves (gate → test)
----------------------------
1. ``AG-1`` — every persisted capability/class value is a member of the governed
   vocabulary, and the CHECK constraints are *identical* to the source constants.
2. ``AG-1``/``S3-2`` — the catalogue is the **exact** ``M-1`` image; nothing was
   upgraded.
3. ``AG-2`` — every category derives a governed outcome, and ``NOT_SUPPORTED``
   and ``CUSTOMER_INPUT_REQUIRED`` remain distinct.
4. ``AG-3`` — no Axis-A token (``PARTIAL``/``DEFERRED``/``NOT_IMPLEMENTED``) is
   persisted anywhere, and no ``architecture_status`` column exists at all.
5. ``AG-4`` — absence is carried by a governed value; no placeholder and no
   fabricated figure exists.
6. ``AG-5`` — the catalogue is tenant-free *by structure*: no tenant column, no
   tenant foreign key, and an identical result under two distinct tenant
   contexts.
7. ``AG-6`` — one governed value per requirement; no per-surface variant.
8. ``AG-7`` — the frozen four-way rollup (4 / 6 / 3 / 2), never a total.
9. ``AG-8`` — every row carries provenance or an explicit unresolved marker.
10. ``§19.4`` rows 8 and 9 — the two isolation boundaries this decision creates.
11. Idempotency and the absence of an applicability model, against the database.

Safety (F-046-1 restated)
-------------------------
This module uses the shared ``pool`` fixture, which performs **destructive**
setup (``TRUNCATE … RESTART IDENTITY CASCADE``). It therefore inherits that
fixture's guard: a target whose name matches ``qa`` / ``demo`` / ``investor`` /
``prod`` / ``live`` is refused before any statement runs, and the main
application databases are refused outright. Point ``INTEGRATION_DATABASE_URL``
at a disposable ``ct_*`` clone or at ``carbontally_test``::

    INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_p17k_20260926 \\
      .venv/bin/python -m pytest \\
      tests/integration/test_p17k_governed_capability_catalogue_runtime.py

The disclosure catalogue is **not** in the fixture's ``_TRUNCATE_TABLES`` list
(it is global, tenant-free reference data with no ``organization_id``), so the
rows seeded by the P17-K migration survive the reset and can be asserted. No
production, demo, investor or QA environment is contacted, and no migration is
applied to one.
"""
from __future__ import annotations

import pathlib
import re

import asyncpg
import pytest

from domain.disclosure import CARBONTALLY_CAPABILITIES, REQUIREMENT_CLASSES
from domain.disclosure_projection import derive_effective_class

pytestmark = pytest.mark.asyncio


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_CATALOGUE_SQL = (
    _REPO_ROOT
    / "supabase"
    / "migrations"
    / "20261020000000_p17k_governed_capability_catalogue.sql"
)

#: The frozen `M-1` image of the category matrix (P17-DECISION-03 §11.1/§11.2).
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

#: The four-way rollup (`S3-1`, `AG-7`) — never "15 categories".
ROLLUP: dict[str, int] = {
    "SUPPORTED": 4,
    "PARTIALLY_SUPPORTED": 6,
    "FUTURE": 3,
    "MISSING_CAPABILITY": 2,
}

#: Axis-A (internal architecture) tokens — forbidden outside internal surfaces.
AXIS_A_TOKENS: tuple[str, ...] = ("PARTIAL", "DEFERRED", "NOT_IMPLEMENTED")

#: The P17 runtime dimensions (P17-A + P17-IMPLEMENT-10).
_P17_COLUMNS: tuple[str, ...] = (
    "scope2_method", "scope3_category", "energy_type", "data_quality",
    "facility_id", "transport_boundary", "waste_origin", "source_snapshot_id",
    "performed_by_organization_id", "acting_for_organization_id",
    "scope3_method", "transaction_provider",
)

#: The tables the five authorised P17 migrations create.
_P17_TABLES: tuple[str, ...] = (
    "contractual_instruments", "instrument_allocations", "estimation_records",
    "scope3_categories",
)

_CATALOGUE_QUERY = """
SELECT rv.requirement_code, rv.title, rv.description,
       rv.requirement_class, rv.carbontally_capability,
       rv.value_kind, rv.scope_hint, rv.scope2_method_hint, rv.display_order,
       rv.is_quantitative, rv.unit_hint, rv.identifier_status,
       rv.official_identifier, rv.source_locator, rv.source_tier,
       fv.version_label, fv.status AS framework_version_status,
       f.code AS framework_code
  FROM public.disclosure_requirement_versions rv
  JOIN public.disclosure_framework_versions fv ON fv.id = rv.framework_version_id
  JOIN public.disclosure_frameworks f ON f.id = fv.framework_id
 WHERE f.code = 'GHG_PROTOCOL'
   AND fv.version_label = $1
 ORDER BY rv.display_order NULLS LAST, rv.requirement_code
"""

#: The single framework version this catalogue governs. Every gate is scoped to
#: it, so the suite is exact on a clean deployment AND does not produce false
#: failures in a test/QA database that holds unrelated requirement rows under
#: other version labels (observed: 89 such rows in a verification clone).
VERSION_LABEL = "Corporate Accounting and Reporting Standard (2004 revised edition)"


async def _catalogue(pool: asyncpg.Pool) -> list[asyncpg.Record]:
    async with pool.acquire() as conn:
        return list(await conn.fetch(_CATALOGUE_QUERY, VERSION_LABEL))


def _digest(rows: list[asyncpg.Record]) -> str:
    """A stable, tenant-independent projection of the catalogue payload."""
    return "\n".join(
        "|".join(str(r[c]) for c in sorted(r.keys())) for r in rows
    )


# ---------------------------------------------------------------------------
# Target safety (PO operational control F-046-1)
# ---------------------------------------------------------------------------
async def test_the_target_is_a_disposable_clone(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        name = str(await conn.fetchval("SELECT current_database()"))
    assert name not in ("postgres", "supabase_db_carbon_ledger"), name
    for marker in ("qa", "demo", "investor", "prod", "live"):
        assert marker not in name.lower(), (name, marker)


async def test_the_f046_1_probe_refuses_persistent_environments() -> None:
    """The guard that makes the destructive fixture safe must cover the demo DB."""
    from tests.integration.conftest import (
        FORBIDDEN_MAIN_DB_NAMES,
        PROTECTED_PERSISTENT_MARKERS,
    )

    for name in (
        "carbontally_demo_local",
        "carbontally_qa_phase8",
        "ct_investor_demo",
        "carbontally_prod",
        "carbontally_live",
        "postgres",
        "supabase_db_carbon_ledger",
    ):
        refused = name in FORBIDDEN_MAIN_DB_NAMES or any(
            m in name.lower() for m in PROTECTED_PERSISTENT_MARKERS
        )
        assert refused, f"{name} would NOT be refused by the F-046-1 probe"


# ---------------------------------------------------------------------------
# The P17 runtime dimensions (PR-1)
# ---------------------------------------------------------------------------
async def test_the_p17_runtime_dimensions_exist(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        for table in ("calculation_snapshots", "emissions_logs"):
            rows = await conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=$1",
                table,
            )
            present = {str(r["column_name"]) for r in rows}
            missing = set(_P17_COLUMNS) - present
            assert not missing, (table, sorted(missing))

        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name = ANY($1::text[])",
            list(_P17_TABLES),
        )
        assert {str(r["table_name"]) for r in tables} == set(_P17_TABLES)

        # RLS is enabled on the governed catalogue and the new entity tables.
        rls = await conn.fetch(
            "SELECT relname, relrowsecurity FROM pg_class WHERE relname = ANY($1::text[])",
            ["disclosure_requirement_versions", "disclosure_framework_versions",
             *_P17_TABLES],
        )
        assert {str(r["relname"]) for r in rls} == {
            "disclosure_requirement_versions", "disclosure_framework_versions",
            *_P17_TABLES,
        }
        assert all(r["relrowsecurity"] for r in rls), [
            str(r["relname"]) for r in rls if not r["relrowsecurity"]
        ]


# ---------------------------------------------------------------------------
# AG-1 — the vocabulary is the governed vocabulary, on both sides
# ---------------------------------------------------------------------------
async def test_ag_1_check_constraints_are_identical_to_the_source(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        defs: dict[str, set[str]] = {}
        for constraint in (
            "disclosure_requirement_versions_capability_check",
            "disclosure_requirement_versions_class_check",
        ):
            definition = await conn.fetchval(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname=$1",
                constraint,
            )
            assert definition is not None, f"{constraint} is missing"
            defs[constraint] = set(re.findall(r"'([A-Z_]+)'", str(definition)))

    assert defs["disclosure_requirement_versions_capability_check"] == set(
        CARBONTALLY_CAPABILITIES
    )
    assert defs["disclosure_requirement_versions_class_check"] == set(
        REQUIREMENT_CLASSES
    )


async def test_ag_1_every_persisted_value_is_a_governed_member(pool: asyncpg.Pool) -> None:
    rows = await _catalogue(pool)
    assert rows, "the governed catalogue is empty (PR-2 not satisfied)"
    for row in rows:
        assert row["carbontally_capability"] in CARBONTALLY_CAPABILITIES, row
        assert row["requirement_class"] in REQUIREMENT_CLASSES, row
    # No unexpected value can exist: every distinct value is a member.
    assert {r["carbontally_capability"] for r in rows} <= set(CARBONTALLY_CAPABILITIES)
    assert {r["requirement_class"] for r in rows} <= set(REQUIREMENT_CLASSES)


async def test_ag_1_the_catalogue_is_the_exact_non_upgrading_m1_image(
    pool: asyncpg.Pool,
) -> None:
    rows = await _catalogue(pool)
    by_code = {str(r["requirement_code"]): str(r["carbontally_capability"]) for r in rows}
    assert len(by_code) == len(rows) == 18, len(rows)
    for code, capability in M1_IMAGE.items():
        assert by_code.get(code) == capability, (code, by_code.get(code), capability)
    # Scope 1/2 are present and Scope 2 is split per method.
    assert by_code["GP-S1"] == "SUPPORTED"
    assert by_code["GP-S2-LB"] == "SUPPORTED"
    assert by_code["GP-S2-MB"] == "MISSING_CAPABILITY"
    # Non-upgrade: no bounded/absent category was recorded as full support.
    for code in ("GP-S3-CAT-01", "GP-S3-CAT-07", "GP-S3-CAT-08",
                 "GP-S3-CAT-09", "GP-S3-CAT-12", "GP-S3-CAT-13"):
        assert by_code[code] != "SUPPORTED", code
    for code in ("GP-S3-CAT-02", "GP-S3-CAT-10", "GP-S3-CAT-11",
                 "GP-S3-CAT-14", "GP-S3-CAT-15"):
        assert by_code[code] not in ("SUPPORTED", "PARTIALLY_SUPPORTED"), code


async def test_the_framework_version_row_is_evidenced_and_not_invented(
    pool: asyncpg.Pool,
) -> None:
    rows = await _catalogue(pool)
    versions = {str(r["version_label"]) for r in rows}
    assert versions == {
        "Corporate Accounting and Reporting Standard (2004 revised edition)"
    }, versions
    assert {str(r["framework_code"]) for r in rows} == {"GHG_PROTOCOL"}
    assert {str(r["framework_version_status"]) for r in rows} == {"IN_FORCE"}
    assert {r["source_tier"] for r in rows} == {1}


# ---------------------------------------------------------------------------
# AG-2 — governed, distinct outcomes for every non-produced item
# ---------------------------------------------------------------------------
async def test_ag_2_every_category_derives_a_governed_outcome(pool: asyncpg.Pool) -> None:
    rows = await _catalogue(pool)
    outcomes: dict[str, str] = {}
    for row in rows:
        outcomes[str(row["requirement_code"])] = derive_effective_class(
            requirement_class=str(row["requirement_class"]),
            applicability_status="APPLIES",
            carbontally_capability=str(row["carbontally_capability"]),
        )
    for outcome in outcomes.values():
        assert outcome in REQUIREMENT_CLASSES, outcome

    # M-1's third column, realised by the engine on the PERSISTED values.
    assert outcomes["GP-S3-CAT-02"] == "NOT_SUPPORTED"
    assert outcomes["GP-S3-CAT-10"] == "NOT_SUPPORTED"
    assert outcomes["GP-S3-CAT-11"] == "FUTURE"
    assert outcomes["GP-S3-CAT-14"] == "FUTURE"
    assert outcomes["GP-S3-CAT-15"] == "FUTURE"
    assert outcomes["GP-S3-CAT-03"] == "CONDITIONAL"
    assert outcomes["GP-S2-MB"] == "NOT_SUPPORTED"

    # NOT_SUPPORTED and CUSTOMER_INPUT_REQUIRED are structurally distinct.
    assert "NOT_APPLICABLE" not in set(outcomes.values()), (
        "a product-capability value must never become a tenant applicability "
        "outcome (PO-3 / C-5)"
    )
    assert outcomes["GP-S3-CAT-02"] != derive_effective_class(
        requirement_class="CONDITIONAL",
        applicability_status="CUSTOMER_INPUT_REQUIRED",
        carbontally_capability="SUPPORTED",
    )


# ---------------------------------------------------------------------------
# AG-3 — Axis-A vocabulary is unusable outside internal surfaces
# ---------------------------------------------------------------------------
async def test_ag_3_no_architecture_status_column_exists_anywhere(
    pool: asyncpg.Pool,
) -> None:
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE column_name = 'architecture_status'"
        )
    assert count == 0, "the internal status axis must not be persisted"


async def test_ag_3_no_axis_a_token_is_persisted(pool: asyncpg.Pool) -> None:
    rows = await _catalogue(pool)
    status_columns = ("requirement_class", "carbontally_capability", "value_kind",
                      "scope_hint", "scope2_method_hint")
    for row in rows:
        for column in status_columns:
            value = str(row[column] or "").upper()
            for token in AXIS_A_TOKENS:
                assert not re.search(rf"\b{token}\b", value), (row["requirement_code"], column, value)


async def test_ag_3_no_applicability_vocabulary_is_persisted(pool: asyncpg.Pool) -> None:
    rows = await _catalogue(pool)
    for row in rows:
        assert row["requirement_class"] != "NOT_APPLICABLE", row["requirement_code"]
    async with pool.acquire() as conn:
        text = await conn.fetchval(
            "SELECT string_agg(rv.title || ' ' || coalesce(rv.description,'') || ' ' "
            "|| rv.source_locator, ' ') FROM public.disclosure_requirement_versions rv"
        )
    for token in ("NOT_APPLICABLE", "DOES_NOT_APPLY", "NO_DATA_YET",
                  "EXCLUDED_WITH_REASON"):
        assert token not in str(text), token


# ---------------------------------------------------------------------------
# AG-4 — absence is never a number, a placeholder or a claim
# ---------------------------------------------------------------------------
async def test_ag_4_no_placeholder_or_figure_is_carried(pool: asyncpg.Pool) -> None:
    rows = await _catalogue(pool)
    for row in rows:
        for column in ("title", "description", "source_locator"):
            value = str(row.get(column) or "")
            for token in ("N/A", "n/a", "not applicable", "excluded", "coming soon"):
                assert token not in value, (row["requirement_code"], column, token)
            assert not re.search(r"\d+(?:\.\d+)?\s*(kg|t)\s*CO2e", value, re.I), value
    # Every row carries a governed capability value, never a placeholder.
    assert {r["carbontally_capability"] for r in rows} <= set(CARBONTALLY_CAPABILITIES)


# ---------------------------------------------------------------------------
# AG-5 — the catalogue cannot become a tenant-data path (`SEC-1`, `SEC-3`)
# ---------------------------------------------------------------------------
async def test_ag_5_the_catalogue_carries_no_tenant_column(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name IN "
            "('disclosure_requirement_versions','disclosure_framework_versions',"
            "'disclosure_frameworks','scope3_categories')"
        )
    tenant_keys = {
        "organization_id", "organisation_id", "org_id", "tenant_id",
        "owner_organization_id",
    }
    assert not {str(r["column_name"]) for r in rows} & tenant_keys


async def test_ag_5_no_foreign_key_leads_from_the_catalogue_to_a_tenant(
    pool: asyncpg.Pool,
) -> None:
    """`SEC-3`: absence of a tenant *query path*, not merely of a tenant id."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT c.conrelid::regclass::text AS source_table,
                   c.confrelid::regclass::text AS target_table
              FROM pg_constraint c
             WHERE c.contype = 'f'
               AND c.conrelid::regclass::text IN
                   ('disclosure_requirement_versions','disclosure_framework_versions',
                    'disclosure_frameworks','scope3_categories')
            """
        )
    targets = {str(r["target_table"]) for r in rows}
    assert targets <= {
        "disclosure_framework_versions", "disclosure_frameworks",
        "disclosure_requirement_versions",
    }, targets


# ---------------------------------------------------------------------------
# §19.4 row 8 — the investor surface cannot reach tenant data
# ---------------------------------------------------------------------------
async def test_isolation_row_8_tenant_context_cannot_change_the_catalogue(
    pool: asyncpg.Pool,
) -> None:
    """A capability statement is product-level: two tenants see the same bytes."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "SET LOCAL request.jwt.claims = "
                "'{\"sub\": \"00000000-0000-0000-0000-0000000000a1\", "
                "\"org_id\": \"00000000-0000-0000-0000-0000000000a1\"}'"
            )
            first = _digest(list(await conn.fetch(_CATALOGUE_QUERY, VERSION_LABEL)))
        async with conn.transaction():
            await conn.execute(
                "SET LOCAL request.jwt.claims = "
                "'{\"sub\": \"00000000-0000-0000-0000-0000000000b2\", "
                "\"org_id\": \"00000000-0000-0000-0000-0000000000b2\"}'"
            )
            second = _digest(list(await conn.fetch(_CATALOGUE_QUERY, VERSION_LABEL)))
    assert first and first == second, "a tenant context must not shape the catalogue"


async def test_isolation_row_8_the_catalogue_query_has_no_tenant_predicate() -> None:
    """`AG-5` checks the query path, so the shipped query is asserted directly."""
    lowered = _CATALOGUE_QUERY.lower()
    for token in ("organization_id", "organisation_id", "org_id", "tenant_id",
                  "current_setting", "auth.uid"):
        assert token not in lowered, token
    assert " where f.code = 'ghg_protocol'" in lowered


# ---------------------------------------------------------------------------
# §19.4 row 9 — no non-internal surface can obtain Axis-A vocabulary
# ---------------------------------------------------------------------------
async def test_isolation_row_9_axis_a_vocabulary_is_unreachable(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        columns = await conn.fetch(
            "SELECT count(*) AS n FROM information_schema.columns "
            "WHERE column_name = 'architecture_status'"
        )
        assert int(columns[0]["n"]) == 0

        # The ONLY place an Axis-A token exists in the schema is the internal
        # P17 category matrix, which is carried in code, not in the database.
        rows = await _catalogue(pool)
    for row in rows:
        assert str(row["requirement_class"]) not in AXIS_A_TOKENS
        assert str(row["carbontally_capability"]) not in AXIS_A_TOKENS


# ---------------------------------------------------------------------------
# AG-6 — one governed value per requirement (`CS-2`, `F-5`)
# ---------------------------------------------------------------------------
async def test_ag_6_one_value_per_requirement_and_no_surface_variant(
    pool: asyncpg.Pool,
) -> None:
    rows = await _catalogue(pool)
    assert len(rows) == 18
    assert len({str(r["requirement_code"]) for r in rows}) == 18
    async with pool.acquire() as conn:
        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='disclosure_requirement_versions'"
        )
    names = {str(r["column_name"]) for r in columns}
    for forbidden in ("investor_capability", "customer_capability", "coverage",
                      "completeness", "materiality", "assurance"):
        assert forbidden not in names, forbidden


# ---------------------------------------------------------------------------
# AG-7 — the four-way rollup, never a total (`S3-1`)
# ---------------------------------------------------------------------------
async def test_ag_7_the_persisted_catalogue_reproduces_the_frozen_rollup(
    pool: asyncpg.Pool,
) -> None:
    rows = await _catalogue(pool)
    categories = [
        r for r in rows if str(r["requirement_code"]).startswith("GP-S3-CAT-")
    ]
    assert len(categories) == 15
    counts: dict[str, int] = {}
    for row in categories:
        cap = str(row["carbontally_capability"])
        counts[cap] = counts.get(cap, 0) + 1
    assert counts == ROLLUP, counts


# ---------------------------------------------------------------------------
# AG-8 — provenance, or an explicit unresolved marker
# ---------------------------------------------------------------------------
async def test_ag_8_every_row_carries_provenance_or_an_unresolved_marker(
    pool: asyncpg.Pool,
) -> None:
    rows = await _catalogue(pool)
    for row in rows:
        assert str(row["identifier_status"]) == (
            "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION"
        ), row["requirement_code"]
        assert row["official_identifier"] is None, row["requirement_code"]
        assert str(row["source_locator"]).strip(), row["requirement_code"]
        assert row["source_tier"] == 1, row["requirement_code"]


# ---------------------------------------------------------------------------
# Idempotency, and the absence of an applicability model
# ---------------------------------------------------------------------------
async def test_rerunning_the_catalogue_migration_is_a_no_op(pool: asyncpg.Pool) -> None:
    sql = _CATALOGUE_SQL.read_text(encoding="utf-8")
    scoped = """
        SELECT count(*)
          FROM public.disclosure_requirement_versions rv
          JOIN public.disclosure_framework_versions fv
               ON fv.id = rv.framework_version_id
         WHERE fv.version_label = $1
    """
    async with pool.acquire() as conn:
        before = await conn.fetchval(scoped, VERSION_LABEL)
        await conn.execute(sql)
        after = await conn.fetchval(scoped, VERSION_LABEL)
        fv_count = await conn.fetchval(
            "SELECT count(*) FROM public.disclosure_framework_versions "
            "WHERE version_label = $1",
            VERSION_LABEL,
        )
    assert before == after == 18
    assert fv_count == 1


async def test_no_applicability_model_was_introduced(pool: asyncpg.Pool) -> None:
    """`F-1` — PO-3 refused a customer-facing applicability concept."""
    async with pool.acquire() as conn:
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND (table_name LIKE '%appl%' "
            "OR table_name LIKE '%applicab%')"
        )
        names = {str(r["table_name"]) for r in tables}
        assert names == {"disclosure_applicability_assessments"}, names

        # NOTE: the tenant-side lifecycle column is `assessed_status` (the
        # four-value APPL vocabulary). CT-PO-P17-DECISION-03 §12.1 cites it as
        # `applicability_status`; that citation is corrected in the P17-K
        # report — the vocabulary it names is right, the column name is not.
        columns = await conn.fetch(
            "SELECT table_name FROM information_schema.columns "
            "WHERE column_name IN ('assessed_status', 'applicability_status')"
        )
        assert {str(r["table_name"]) for r in columns} == {
            "disclosure_applicability_assessments"
        }

        # The tenant-side lifecycle exists, is untouched, and is empty here.
        rows = await conn.fetchval(
            "SELECT count(*) FROM public.disclosure_applicability_assessments"
        )
        assert rows == 0


# ---------------------------------------------------------------------------
# Scope 2 — the method is carried by the existing governed column
# ---------------------------------------------------------------------------
async def test_scope2_rows_carry_the_frozen_method_vocabulary(pool: asyncpg.Pool) -> None:
    rows = {str(r["requirement_code"]): r for r in await _catalogue(pool)}
    assert str(rows["GP-S2-LB"]["scope2_method_hint"]) == "LOCATION_BASED"
    assert str(rows["GP-S2-MB"]["scope2_method_hint"]) == "MARKET_BASED"
    assert rows["GP-S1"]["scope2_method_hint"] is None
    assert str(rows["GP-S2-LB"]["scope_hint"]) == "Scope 2"
    async with pool.acquire() as conn:
        definition = await conn.fetchval(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname='disclosure_requirement_versions_scope2_method_check'"
        )
    assert set(re.findall(r"'([A-Z_]+)'", str(definition))) == {
        "LOCATION_BASED", "MARKET_BASED"
    }


async def test_the_governed_scope3_taxonomy_supplies_the_category_names(
    pool: asyncpg.Pool,
) -> None:
    rows = await _catalogue(pool)
    async with pool.acquire() as conn:
        taxonomy = await conn.fetch(
            "SELECT category, name FROM public.scope3_categories ORDER BY category"
        )
        check = await conn.fetchval(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname='scope3_categories_range_check'"
        )
    assert len(taxonomy) == 15
    names = {int(r["category"]): str(r["name"]) for r in taxonomy}
    for row in rows:
        code = str(row["requirement_code"])
        if not code.startswith("GP-S3-CAT-"):
            continue
        number = int(code.rsplit("-", 1)[1])
        assert names[number] in str(row["title"]), (code, row["title"])
        assert str(row["display_order"]) == str(100 + number)
    upper = str(check).upper()
    assert "CATEGORY >= 1" in upper and "CATEGORY <= 15" in upper, upper





