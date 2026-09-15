"""Runtime integration tests for the B3 disclosure projection (QA environment).

Skips — never fails — when the B3 schema is not provisioned, mirroring the B1
runtime suite. Executes against ``INTEGRATION_DATABASE_URL`` (the dedicated
non-production QA database), never the main application database.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Optional

import asyncpg
import pytest

from data.disclosure import DisclosureCatalogRepository
from data.disclosure_projection import DisclosureProjectionRepository
from services.disclosure_projection import DisclosureProjectionService
from tests.integration.conftest import make_org, new_id

YEAR = 2025
PERIOD_START = date(2025, 1, 1)
PERIOD_END = date(2025, 12, 31)


async def _require_b3_schema(pool: asyncpg.Pool) -> None:
    present = await pool.fetchval(
        "SELECT to_regclass('public.disclosure_intensity_denominator_types') IS NOT NULL"
    )
    if not present:
        pytest.skip(
            "B3 intensity schema is not provisioned in this integration database; apply "
            "supabase/migrations/20260917000000_p8_b3_intensity_catalogue.sql"
        )
    if not await pool.fetchval("SELECT to_regclass('public.evidence_line_items') IS NOT NULL"):
        pytest.skip("B2 evidence_line_items is not provisioned (B3 needs the B2 line links)")


@pytest.fixture
async def case(pool: asyncpg.Pool) -> dict[str, Any]:
    """An organisation, purpose, four requirements, snapshots and a DRAFT version."""
    await _require_b3_schema(pool)
    cat = DisclosureCatalogRepository(pool)
    await cat.seed_reference_identities()
    fw = await cat.get_framework_by_code("GHG_PROTOCOL")
    assert fw is not None

    org = await make_org(pool, "B3 Projection Org")
    out: dict[str, Any] = {"org": org, "framework_id": fw["id"]}

    async with pool.acquire() as conn:
        fwv = await conn.fetchval(
            "INSERT INTO public.disclosure_framework_versions "
            "(framework_id, version_label, source_tier, status) "
            "VALUES ($1, $2, 1, 'IN_FORCE') RETURNING id",
            fw["id"],
            f"B3RT-{new_id()[:8]}",
        )
        out["framework_version_id"] = str(fwv)

        async def _req(code: str, klass: str, capability: str) -> str:
            rid = await conn.fetchval(
                "INSERT INTO public.disclosure_requirement_versions "
                "(framework_version_id, requirement_code, title, requirement_class, "
                " value_kind, carbontally_capability) "
                "VALUES ($1, $2, $3, $4, 'QUANTITATIVE', $5) RETURNING id",
                fwv,
                code,
                f"B3 runtime requirement {code}",
                klass,
                capability,
            )
            return str(rid)

        out["req_mapped"] = await _req(f"B3RT_A_{new_id()[:8]}", "REQUIRED", "SUPPORTED")
        out["req_needs_input"] = await _req(
            f"B3RT_B_{new_id()[:8]}", "CUSTOMER_INPUT_REQUIRED", "STRUCTURED_INPUT_REQUIRED"
        )
        out["req_unsupported"] = await _req(
            f"B3RT_C_{new_id()[:8]}", "REQUIRED", "MISSING_CAPABILITY"
        )
        out["req_unmapped"] = await _req(f"B3RT_D_{new_id()[:8]}", "REQUIRED", "SUPPORTED")

        pv = await conn.fetchval(
            "INSERT INTO public.disclosure_report_purpose_versions (purpose_id, version) "
            "SELECT p.id, (SELECT coalesce(max(v.version), 0) + 1 "
            "              FROM public.disclosure_report_purpose_versions v "
            "              WHERE v.purpose_id = p.id) "
            "FROM public.disclosure_report_purposes p WHERE p.code = 'ANNUAL_CARBON' "
            "RETURNING id"
        )
        out["purpose_version_id"] = str(pv)
        for order, key in enumerate(
            ("req_mapped", "req_needs_input", "req_unsupported", "req_unmapped"), start=1
        ):
            await conn.execute(
                "INSERT INTO public.disclosure_purpose_requirements "
                "(purpose_version_id, requirement_version_id, display_order, required_for_finalisation) "
                "VALUES ($1, $2, $3, TRUE)",
                pv,
                out[key],
                order,
            )

        # Producer mapping for exactly one requirement (B3 authors no content).
        await conn.execute(
            "INSERT INTO public.disclosure_requirement_mappings "
            "(requirement_version_id, mapping_version, source_kind, aggregation, is_current) "
            "VALUES ($1, 1, 'CALCULATION_AGGREGATE', 'SUM_KG_CO2E', TRUE)",
            out["req_mapped"],
        )

        assessment = await conn.fetchval(
            "INSERT INTO public.disclosure_applicability_assessments "
            "(organization_id, framework_version_id, reporting_year, reporting_period_start, "
            " reporting_period_end, characteristic_snapshot, assessed_status, basis, version) "
            "VALUES ($1, $2, $3, $4, $5, '{}'::jsonb, 'APPLIES', "
            "        'B3 runtime basis: turnover above threshold per filed accounts', 1) "
            "RETURNING id",
            org,
            fwv,
            YEAR,
            PERIOD_START,
            PERIOD_END,
        )
        out["assessment_applies"] = str(assessment)

        for key, status, assessment_id in (
            ("rv_bound", "DRAFT", assessment),
            ("rv_unassessed", "DRAFT", None),
        ):
            rep = await conn.fetchval(
                "INSERT INTO public.report_generation_queue "
                "(organization_id, report_type, reporting_year) "
                "VALUES ($1, 'ANNUAL_CARBON', $2) RETURNING id",
                org,
                YEAR,
            )
            rv = await conn.fetchval(
                "INSERT INTO public.report_versions (report_id, version_number, status) "
                "VALUES ($1, 1, $2) RETURNING id",
                rep,
                status,
            )
            await conn.execute(
                "INSERT INTO public.disclosure_report_instance_binding "
                "(organization_id, report_id, purpose_version_id, applicability_assessment_id, "
                " reporting_period_start, reporting_period_end, consolidation_approach) "
                "VALUES ($1, $2, $3, $4, $5, $6, 'OPERATIONAL_CONTROL')",
                org,
                rep,
                pv,
                assessment_id,
                PERIOD_START,
                PERIOD_END,
            )
            out[key] = str(rv)

        # Two authoritative snapshots (the only numeric source the projection may read).
        # calculation_snapshots_exactly_one_source_check requires a real factor row.
        factor_id = await conn.fetchval(
            "INSERT INTO public.emission_factors "
            "(reporting_year, activity_type, co2e_multiplier) "
            "VALUES ($1, $2, 1.0) RETURNING id",
            YEAR,
            f"B3 runtime factor {new_id()[:8]}",
        )
        for co2e in ("100.0", "23.5"):
            await conn.execute(
                "INSERT INTO public.calculation_snapshots "
                "(organization_id, activity, activity_type, quantity, quantity_unit, "
                " co2e_multiplier, co2e_kg, scope, date, reporting_year, "
                " methodology, algorithm_version, content_hash, factor_id, factor_kind) "
                "VALUES ($1, 'B3 runtime activity', 'Stationary combustion', 10, 'kWh', "
                "        1.0, $2, 'Scope 1', $3, $4, 'b3-runtime', 'v1', $6, $5, "
                "        'emission_factor')",
                org,
                Decimal(co2e),
                PERIOD_START,
                YEAR,
                factor_id,
                f"b3-{co2e}",
            )
    return out


async def _values(pool: asyncpg.Pool, report_version_id: str) -> dict[str, dict]:
    rows = await pool.fetch(
        "SELECT requirement_version_id, value_status, effective_class, numeric_value, "
        "       value_unit, source_kind, reason "
        "FROM public.disclosure_values WHERE report_version_id = $1",
        report_version_id,
    )
    return {str(r["requirement_version_id"]): dict(r) for r in rows}


async def test_projection_materialises_and_is_idempotent(
    pool: asyncpg.Pool, case: dict[str, Any]
) -> None:
    service = DisclosureProjectionService(pool)
    summary = await service.project_report_version(report_version_id=case["rv_bound"])

    assert summary["applicability_status"] == "APPLIES"
    assert summary["requirement_count"] == 4

    values = await _values(pool, case["rv_bound"])
    assert len(values) == 4, "exactly one disclosure value per requirement"

    mapped = values[case["req_mapped"]]
    assert mapped["value_status"] == "RESOLVED"
    assert Decimal(str(mapped["numeric_value"])) == Decimal("123.5")
    assert mapped["value_unit"] == "kgCO2e"
    assert mapped["source_kind"] == "CALCULATION_AGGREGATE"

    needs_input = values[case["req_needs_input"]]
    assert needs_input["value_status"] == "UNRESOLVED"
    assert needs_input["reason"] == "customer input required"
    assert needs_input["effective_class"] == "CUSTOMER_INPUT_REQUIRED"

    unsupported = values[case["req_unsupported"]]
    assert unsupported["value_status"] == "UNRESOLVED"
    assert unsupported["reason"] == "not supported by CarbonTally"
    assert unsupported["reason"] != needs_input["reason"], "DM-5: never conflated"

    unmapped = values[case["req_unmapped"]]
    assert unmapped["value_status"] == "UNRESOLVED"
    assert unmapped["reason"] == "no producer mapping recorded for this requirement"
    assert unmapped["numeric_value"] is None, "no fabricated zero"

    # Idempotency: a second run updates the same rows, it does not duplicate them.
    first_ids = {
        rid: str(
            await pool.fetchval(
                "SELECT id FROM public.disclosure_values "
                "WHERE report_version_id = $1 AND requirement_version_id = $2",
                case["rv_bound"],
                rid,
            )
        )
        for rid in values
    }
    second = await service.project_report_version(report_version_id=case["rv_bound"])
    assert second["resolved"] == summary["resolved"]
    values2 = await _values(pool, case["rv_bound"])
    assert len(values2) == 4
    for rid, value_id in first_ids.items():
        assert values2[rid]["value_status"] == values[rid]["value_status"]
    count = await pool.fetchval(
        "SELECT count(*) FROM public.disclosure_values WHERE report_version_id = $1",
        case["rv_bound"],
    )
    assert count == 4


async def test_undetermined_applicability_is_preserved(
    pool: asyncpg.Pool, case: dict[str, Any]
) -> None:
    """No recorded assessment means UNDETERMINED — never a silent default (APPL)."""
    service = DisclosureProjectionService(pool)
    summary = await service.project_report_version(report_version_id=case["rv_unassessed"])
    assert summary["applicability_status"] == "UNDETERMINED"
    assert summary["resolved"] == 0
    values = await _values(pool, case["rv_unassessed"])
    assert len(values) == 4
    for row in values.values():
        assert row["value_status"] == "UNRESOLVED"
        assert row["effective_class"] == "UNDETERMINED"
        assert "undetermined" in str(row["reason"])


async def test_value_lines_read_model_executes(pool: asyncpg.Pool, case: dict[str, Any]) -> None:
    """The B2 value→line read model runs and is scoped to the report version."""
    service = DisclosureProjectionService(pool)
    await service.project_report_version(report_version_id=case["rv_bound"])
    repo = DisclosureProjectionRepository(pool)
    rows = await repo.value_lines(report_version_id=case["rv_bound"])
    assert rows, "the join must return the version's disclosure values"
    ids = {str(r["disclosure_value_id"]) for r in rows}
    assert len(ids) == 4
    for row in rows:
        assert set(row) >= {
            "disclosure_value_id",
            "calculation_snapshot_id",
            "evidence_line_item_id",
            "line_number",
            "raw_quantity",
            "materialisation_kind",
        }


async def test_intensity_catalogue_and_ratio_selection(pool: asyncpg.Pool, case: dict[str, Any]) -> None:
    """The generic catalogue is exposed; a ratio is org-scoped and idempotent."""
    repo = DisclosureProjectionRepository(pool)
    catalogue = await repo.list_intensity_catalogue()
    codes = {row["code"] for row in catalogue}
    assert {"NET_REVENUE", "FLOOR_AREA", "FTE_HEADCOUNT", "PHYSICAL_OUTPUT"} <= codes
    for row in catalogue:
        assert row["support_class"] == "CARBONTALLY_SUPPORTED"

    net_revenue = next(row for row in catalogue if row["code"] == "NET_REVENUE")
    assert await repo.list_framework_treatment(denominator_type_id=str(net_revenue["id"])) == []

    first = await repo.upsert_intensity_ratio(
        organization_id=case["org"],
        report_version_id=case["rv_bound"],
        denominator_type_id=str(net_revenue["id"]),
        selection_basis="Customer confirmed net revenue for the reporting period",
        denominator_value=Decimal("100"),
        denominator_unit="GBP",
        numerator_value=Decimal("250"),
        selection_source="CUSTOMER_CONFIRMED",
    )
    assert first is not None
    assert Decimal(str(first["ratio_value"])) == Decimal("2.5")

    second = await repo.upsert_intensity_ratio(
        organization_id=case["org"],
        report_version_id=case["rv_bound"],
        denominator_type_id=str(net_revenue["id"]),
        selection_basis="Customer corrected net revenue after review",
        denominator_value=Decimal("200"),
        denominator_unit="GBP",
        numerator_value=Decimal("250"),
        selection_source="CUSTOMER_CONFIRMED",
    )
    assert second is not None
    assert Decimal(str(second["ratio_value"])) == Decimal("1.25")
    count = await pool.fetchval(
        "SELECT count(*) FROM public.disclosure_intensity_ratios "
        "WHERE organization_id = $1 AND report_version_id = $2",
        case["org"],
        case["rv_bound"],
    )
    assert count == 1, "selection is upserted, never duplicated"
