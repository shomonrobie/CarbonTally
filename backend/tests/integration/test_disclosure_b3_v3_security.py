"""Phase 8 B3 — V3 independent verification: security matrix, lineage and audit.

Executed against a fresh production-shaped clone (``ct_b3_v3_20260913``) carrying
the complete Phase 8 migration chain. Skips — never fails — when the B3 schema is
absent. The main application database is never used.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from typing import Any, AsyncIterator, Optional

import asyncpg
import pytest

from data.disclosure import DisclosureCatalogRepository, DisclosureRepository
from data.disclosure_projection import DisclosureProjectionRepository
from services.disclosure_projection import DisclosureProjectionService
from tests.integration.conftest import make_org, make_user, new_id

YEAR = 2025
PERIOD_START = date(2025, 1, 1)
PERIOD_END = date(2025, 12, 31)


async def _require_b3_schema(pool: asyncpg.Pool) -> None:
    if not await pool.fetchval("SELECT to_regclass('public.disclosure_intensity_denominator_types') IS NOT NULL"):
        pytest.skip("B3 intensity schema is not provisioned in this database")
    if not await pool.fetchval("SELECT to_regclass('public.evidence_line_items') IS NOT NULL"):
        pytest.skip("B2 evidence_line_items is not provisioned")


@asynccontextmanager
async def _session(pool: asyncpg.Pool, role: str, user_id: Optional[str] = None) -> AsyncIterator[asyncpg.Connection]:
    """Yield a connection acting as ``role`` with an optional JWT ``sub`` (B1 pattern)."""
    conn = await pool.acquire()
    try:
        if user_id is not None:
            await conn.execute(
                "SELECT set_config('request.jwt.claims', $1, false)",
                json.dumps({"sub": user_id, "role": role}),
            )
        await conn.execute(f"SET ROLE {role}")
        yield conn
    finally:
        await conn.execute("RESET ROLE")
        await conn.execute("SELECT set_config('request.jwt.claims', '{}', false)")
        await pool.release(conn)


async def _member(pool: asyncpg.Pool, org_id: str, user_id: str, role: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.organization_members "
            "(id, organization_id, user_id, role, is_active, created_at) "
            "VALUES ($1, $2, $3, $4, TRUE, NOW())",
            new_id(), org_id, user_id, role,
        )


@pytest.fixture
async def world(pool: asyncpg.Pool) -> dict[str, Any]:
    """Two tenant organisations, four roles, a value, a real line link and a binding."""
    await _require_b3_schema(pool)
    cat = DisclosureCatalogRepository(pool)
    await cat.seed_reference_identities()
    fw = await cat.get_framework_by_code("GHG_PROTOCOL")
    assert fw is not None

    org_a = await make_org(pool, "B3 V3 Org A")
    org_b = await make_org(pool, "B3 V3 Org B")
    out: dict[str, Any] = {"org_a": org_a, "org_b": org_b}

    # organization_members.user_id FKs to public.users - create real user rows.
    users = {
        "owner": await make_user(pool),
        "admin": await make_user(pool),
        "member": await make_user(pool),
        "viewer": await make_user(pool),
        "other_org": await make_user(pool),
        "stranger": await make_user(pool),
    }
    out["users"] = users
    await _member(pool, org_a, users["owner"], "owner")
    await _member(pool, org_a, users["admin"], "admin")
    await _member(pool, org_a, users["member"], "member")
    await _member(pool, org_a, users["viewer"], "viewer")
    await _member(pool, org_b, users["other_org"], "owner")
    # ``stranger`` is deliberately NOT a member of any organisation (PE-like).

    async with pool.acquire() as conn:
        fwv = await conn.fetchval(
            "INSERT INTO public.disclosure_framework_versions "
            "(framework_id, version_label, source_tier, status) "
            "VALUES ($1, $2, 1, 'IN_FORCE') RETURNING id",
            fw["id"], f"B3V3-{new_id()[:8]}",
        )
        requirement = await conn.fetchval(
            "INSERT INTO public.disclosure_requirement_versions "
            "(framework_version_id, requirement_code, title, requirement_class, "
            " value_kind, carbontally_capability) "
            "VALUES ($1, $2, 'B3 V3 requirement', 'REQUIRED', 'QUANTITATIVE', "
            "'SUPPORTED') RETURNING id",
            fwv, f"B3V3_{new_id()[:8]}",
        )
        purpose_version = await conn.fetchval(
            "INSERT INTO public.disclosure_report_purpose_versions (purpose_id, version) "
            "SELECT p.id, (SELECT coalesce(max(v.version), 0) + 1 FROM public.disclosure_report_purpose_versions v "
            "              WHERE v.purpose_id = p.id) "
            "FROM public.disclosure_report_purposes p WHERE p.code = 'ANNUAL_CARBON' RETURNING id"
        )
        await conn.execute(
            "INSERT INTO public.disclosure_purpose_requirements "
            "(purpose_version_id, requirement_version_id, display_order, required_for_finalisation) "
            "VALUES ($1, $2, 1, TRUE)",
            purpose_version, requirement,
        )
        await conn.execute(
            "INSERT INTO public.disclosure_requirement_mappings "
            "(requirement_version_id, mapping_version, source_kind, aggregation, is_current) "
            "VALUES ($1, 1, 'CALCULATION_AGGREGATE', 'SUM_KG_CO2E', TRUE)",
            requirement,
        )
        assessment = await conn.fetchval(
            "INSERT INTO public.disclosure_applicability_assessments "
            "(organization_id, framework_version_id, reporting_year, reporting_period_start, "
            " reporting_period_end, characteristic_snapshot, assessed_status, basis, version) "
            "VALUES ($1, $2, $3, $4, $5, '{}'::jsonb, 'APPLIES', "
            "        'B3 V3 basis: turnover above threshold per filed accounts', 1) RETURNING id",
            org_a, fwv, YEAR, PERIOD_START, PERIOD_END,
        )
        report = await conn.fetchval(
            "INSERT INTO public.report_generation_queue (organization_id, report_type, reporting_year) "
            "VALUES ($1, 'ANNUAL_CARBON', $2) RETURNING id",
            org_a, YEAR,
        )
        report_version = await conn.fetchval(
            "INSERT INTO public.report_versions (report_id, version_number, status) "
            "VALUES ($1, 1, 'DRAFT') RETURNING id",
            report,
        )
        await conn.execute(
            "INSERT INTO public.disclosure_report_instance_binding "
            "(organization_id, report_id, purpose_version_id, applicability_assessment_id, "
            " reporting_period_start, reporting_period_end, consolidation_approach) "
            "VALUES ($1, $2, $3, $4, $5, $6, 'OPERATIONAL_CONTROL')",
            org_a, report, purpose_version, assessment, PERIOD_START, PERIOD_END,
        )
        factor = await conn.fetchval(
            "INSERT INTO public.emission_factors (reporting_year, activity_type, co2e_multiplier) "
            "VALUES ($1, $2, 1.0) RETURNING id",
            YEAR, f"B3 V3 factor {new_id()[:8]}",
        )
        snapshot = await conn.fetchval(
            "INSERT INTO public.calculation_snapshots "
            "(organization_id, activity, activity_type, quantity, quantity_unit, co2e_multiplier, "
            " co2e_kg, scope, date, reporting_year, methodology, algorithm_version, content_hash, "
            " factor_id, factor_kind) "
            "VALUES ($1, 'B3 V3 activity', 'Stationary combustion', 10, 'kWh', 1.0, 123.5, "
            "        'Scope 1', $2, $3, 'b3-v3', 'v1', $4, $5, 'emission_factor') RETURNING id",
            org_a, PERIOD_START, YEAR, "0" * 64, factor,
        )
        out.update(
            {
                "framework_version_id": str(fwv),
                "requirement": str(requirement),
                "purpose_version": str(purpose_version),
                "assessment": str(assessment),
                "report": str(report),
                "report_version": str(report_version),
                "snapshot": str(snapshot),
            }
        )

    # Real line-linked evidence chain: batch -> item -> line -> value evidence.
    async with pool.acquire() as conn:
        batch = await conn.fetchval(
            "INSERT INTO public.manual_extraction_batches "
            "(organization_id, batch_name, total_documents, total_pages, total_cost, currency, "
            " status, created_at, updated_at) "
            "VALUES ($1, $2, 1, 1, 0, 'GBP', 'open', NOW(), NOW()) RETURNING id",
            org_a, f"B3 V3 batch {new_id()[:8]}",
        )
        item = await conn.fetchval(
            "INSERT INTO public.manual_extraction_items "
            "(batch_id, file_name, file_url, page_count, document_type, status) "
            "VALUES ($1, $2, $3, 1, 'invoice', 'extracted') RETURNING id",
            batch, f"b3-v3-{new_id()[:8]}.csv", f"b3-v3/{new_id()}.csv",
        )
        line = await conn.fetchval(
            "INSERT INTO public.evidence_line_items "
            "(organization_id, source_item_id, line_number, source_page, raw_description, "
            " raw_quantity, raw_unit, payload_hash, extraction_method, materialisation_kind) "
            "VALUES ($1, $2, 1, 1, 'Water', 38.4, 'm3', $3, 'deterministic', 'FORWARD') RETURNING id",
            org_a, item, "x" * 64,
        )
        out["line_item"] = str(line)

    disclosure = DisclosureRepository(pool)
    value = await disclosure.upsert_disclosure_value(
        organization_id=org_a,
        report_version_id=out["report_version"],
        requirement_version_id=out["requirement"],
        effective_class="REQUIRED",
        value_kind="QUANTITATIVE",
        reporting_year=YEAR,
        value_status="RESOLVED",
        numeric_value=Decimal("123.5"),
        value_unit="kgCO2e",
        source_kind="CALCULATION_AGGREGATE",
    )
    out["value"] = str(value["id"])
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.disclosure_value_evidence "
            "(organization_id, disclosure_value_id, calculation_snapshot_id, source_line_item_id, "
            " evidence_completeness) VALUES ($1, $2, $3, $4, 'PARTIAL')",
            org_a, value["id"], out["snapshot"], out["line_item"],
        )
        catalogue = await conn.fetchrow(
            "SELECT id FROM public.disclosure_intensity_denominator_types WHERE code = 'NET_REVENUE'"
        )
    out["denominator"] = str(catalogue["id"])
    return out


# ---------------------------------------------------------------------------
# Security matrix
# ---------------------------------------------------------------------------
async def test_cross_tenant_isolation(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    async with _session(pool, "authenticated", world["users"]["member"]) as conn:
        visible = await conn.fetchval(
            "SELECT count(*) FROM public.disclosure_values WHERE organization_id = $1",
            world["org_a"],
        )
        assert visible >= 1, "org A member must see org A values"
        leaked = await conn.fetchval(
            "SELECT count(*) FROM public.disclosure_values WHERE organization_id = $1",
            world["org_b"],
        )
        assert leaked == 0
    async with _session(pool, "authenticated", world["users"]["other_org"]) as conn:
        cross = await conn.fetchval(
            "SELECT count(*) FROM public.disclosure_values WHERE organization_id = $1",
            world["org_a"],
        )
        assert cross == 0, "org B member must not see org A values"


async def test_non_member_and_pe_like_user_see_nothing(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    async with _session(pool, "authenticated", world["users"]["stranger"]) as conn:
        assert await conn.fetchval("SELECT count(*) FROM public.disclosure_values") == 0
        assert await conn.fetchval("SELECT count(*) FROM public.disclosure_intensity_ratios") == 0


async def test_member_and_viewer_cannot_write_intensity(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    for role in ("member", "viewer"):
        async with _session(pool, "authenticated", world["users"][role]) as conn:
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO public.disclosure_intensity_ratios "
                    "(organization_id, report_version_id, denominator_type_id, selection_basis) "
                    "VALUES ($1::uuid, $2::uuid, $3::uuid, 'attempted write')",
                    world["org_a"], world["report_version"], world["denominator"],
                )


async def test_owner_can_select_intensity_and_member_can_read_it(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    async with _session(pool, "authenticated", world["users"]["owner"]) as conn:
        await conn.execute(
            "INSERT INTO public.disclosure_intensity_ratios "
            "(organization_id, report_version_id, denominator_type_id, denominator_value, "
            " denominator_unit, ratio_value, selection_basis, selection_source) "
            "VALUES ($1::uuid, $2::uuid, $3::uuid, 100, 'GBP', 1.25, "
            "        'B3 V3 owner selection', 'CUSTOMER_SELECTED')",
            world["org_a"], world["report_version"], world["denominator"],
        )
    async with _session(pool, "authenticated", world["users"]["member"]) as conn:
        assert await conn.fetchval(
            "SELECT count(*) FROM public.disclosure_intensity_ratios WHERE organization_id = $1",
            world["org_a"],
        ) == 1


async def test_catalogue_read_allowed_write_denied(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    async with _session(pool, "authenticated", world["users"]["owner"]) as conn:
        assert await conn.fetchval("SELECT count(*) FROM public.disclosure_intensity_denominator_types") == 4
    async with _session(pool, "authenticated", world["users"]["owner"]) as conn:
        with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
            await conn.execute(
                "INSERT INTO public.disclosure_intensity_denominator_types (code, name, denominator_kind) "
                "VALUES ('ARBITRARY', 'Customer authored', 'PHYSICAL')"
            )


async def test_anonymous_has_no_catalogue_access(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    async with _session(pool, "anon") as conn:
        try:
            count = await conn.fetchval("SELECT count(*) FROM public.disclosure_intensity_denominator_types")
        except asyncpg.exceptions.InsufficientPrivilegeError:
            return
        assert count == 0


# ---------------------------------------------------------------------------
# Lineage (real line link, both COALESCE branches)
# ---------------------------------------------------------------------------
async def test_value_lines_returns_the_real_line_item(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    repo = DisclosureProjectionRepository(pool)
    rows = await repo.value_lines(report_version_id=world["report_version"])
    linked = [r for r in rows if str(r["disclosure_value_id"]) == world["value"]]
    assert linked, "the value must appear in the read model"
    assert any(str(r["evidence_line_item_id"]) == world["line_item"] for r in linked)
    line = next(r for r in linked if str(r["evidence_line_item_id"]) == world["line_item"])
    assert line["line_number"] == 1
    assert Decimal(str(line["raw_quantity"])) == Decimal("38.4")
    assert line["raw_unit"] == "m3"
    # Snapshot-fallback branch: with the dve link removed, the COALESCE uses the
    # snapshot's own source_line_item_id (B2-2).
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.calculation_snapshots SET source_line_item_id = $2 WHERE id = $1",
            world["snapshot"], world["line_item"],
        )
    rows2 = await repo.value_lines(report_version_id=world["report_version"])
    assert any(str(r["evidence_line_item_id"]) == world["line_item"] for r in rows2)


# ---------------------------------------------------------------------------
# Audit + honesty
# ---------------------------------------------------------------------------
async def test_audit_events_are_recorded_without_secrets(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    service = DisclosureProjectionService(pool)
    await service.project_report_version(report_version_id=world["report_version"])
    rows = await pool.fetch(
        "SELECT action_type, new_data FROM public.audit_trail "
        "WHERE record_id::text = $1 OR new_data::text LIKE $2 ORDER BY performed_at DESC LIMIT 50",
        world["value"], f"%{world['value']}%",
    )
    assert rows, "the value materialisation must be audited"
    blob = " ".join(str(r["new_data"]) for r in rows).lower()
    for forbidden in ("password", "jwt", "refresh_token", "signed_url", "api_key"):
        assert forbidden not in blob


async def test_undetermined_applicability_is_never_coerced(pool: asyncpg.Pool, world: dict[str, Any]) -> None:
    repo = DisclosureProjectionRepository(pool)
    binding = await DisclosureRepository(pool).get_instance_binding(world["report"])
    assert binding is not None
    # No assessment referenced ⇒ the service must treat applicability as UNDETERMINED.
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.disclosure_report_instance_binding SET applicability_assessment_id = NULL "
            "WHERE report_id = $1",
            world["report"],
        )
    assert await repo.report_context(world["report_version"]) is not None
    service = DisclosureProjectionService(pool)
    summary = await service.project_report_version(report_version_id=world["report_version"])
    assert summary["applicability_status"] == "UNDETERMINED"
    assert summary["resolved"] == 0
