"""Runtime integration coverage for the Phase 8 B1 disclosure repositories.

Gate **V1** (``CT-P8-B1-V1-INDEPENDENT-VERIFICATION-20260912-014``) found that the
B1 implementation tests were static/pure — they inspected SQL *text* — so they
could not detect PostgreSQL-level defects: two repository write methods raised
``asyncpg.AmbiguousParameterError``, a NULL-snapshot evidence link was not
idempotent, and no B1 write emitted an audit entry.

This module **executes the B1 repositories against a real PostgreSQL database**
so that class of defect fails here instead of in review. It runs against the
dedicated integration database (``INTEGRATION_DATABASE_URL``, see
``tests/integration/conftest.py``) and **SKIPS** when the B1 schema is not
provisioned there — B1 has not been applied to every environment, and absence is
not a failure (the same fail-safe convention as the rest of this suite).

Coverage:
* **F1** ``create_applicability_assessment`` — ``determined_by=None`` (system) and
  a real actor UUID.
* **F2** ``upsert_disclosure_value`` — materialisation, repeat upsert (single row),
  ``computed_at`` on RESOLVED.
* **F3** ``link_value_evidence`` — NULL-snapshot re-link is idempotent, distinct
  references remain representable, the non-NULL uniqueness path is unchanged.
* **F4** corrected privilege posture (anon / authenticated / service_role,
  TRUNCATE / TRIGGER / REFERENCES / MAINTAIN) and RLS actor behaviour.
* **F5** B1 audit emission through the existing ``audit_trail``.
* Cross-tenant rejection and APPROVED/FINAL immutability.

Correction under test: ``CT-P8-B1-CORRECTION-20260912-015``
(``supabase/migrations/20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql``).
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
from domain.disclosure import DisclosureViolation
from tests.integration.conftest import make_org, make_user, new_id

pytestmark = pytest.mark.asyncio

#: The 11 B1 tables (contract §8 / PQ-1).
B1_TABLES: tuple[str, ...] = (
    "disclosure_frameworks",
    "disclosure_framework_versions",
    "disclosure_requirement_versions",
    "disclosure_requirement_mappings",
    "disclosure_report_purposes",
    "disclosure_report_purpose_versions",
    "disclosure_purpose_requirements",
    "disclosure_applicability_assessments",
    "disclosure_report_instance_binding",
    "disclosure_values",
    "disclosure_value_evidence",
)

#: B1 tables where ``authenticated`` must hold SELECT only (no DML).
READONLY_FOR_AUTHENTICATED: tuple[str, ...] = (
    "disclosure_frameworks",
    "disclosure_framework_versions",
    "disclosure_requirement_versions",
    "disclosure_requirement_mappings",
    "disclosure_report_purposes",
    "disclosure_report_purpose_versions",
    "disclosure_purpose_requirements",
    "disclosure_values",
    "disclosure_value_evidence",
)

#: B1 tables where B1 grants ``authenticated`` DML (behind an RLS policy).
WRITABLE_FOR_AUTHENTICATED: tuple[str, ...] = (
    "disclosure_applicability_assessments",
    "disclosure_report_instance_binding",
)


async def _require_b1_schema(pool: asyncpg.Pool) -> None:
    """Skip (never fail) when the B1 schema is not provisioned in this database."""
    present = await pool.fetchval(
        "SELECT to_regclass('public.disclosure_values') IS NOT NULL"
    )
    if not present:
        pytest.skip(
            "B1 disclosure schema is not provisioned in this integration database; apply "
            "supabase/migrations/20260914000000_p8_b1_disclosure_model_foundation.sql"
        )


@asynccontextmanager
async def _session(
    pool: asyncpg.Pool, role: str, user_id: Optional[str] = None
) -> AsyncIterator[asyncpg.Connection]:
    """Yield a connection acting as ``role`` (optionally with a JWT ``sub``).

    Mirrors the established ``test_v3_rls_behavior`` emulation of a Supabase
    PostgREST session (``SET ROLE`` + ``request.jwt.claims`` → ``auth.uid()``).
    Session state is reset on exit so a pooled connection never leaks the role.
    """
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


async def _add_member(
    pool: asyncpg.Pool, org_id: str, user_id: str, role: str
) -> None:
    """Add an active organisation member with ``role`` (owner/admin/member/viewer)."""
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.organization_members "
            "(id, organization_id, user_id, role, is_active, created_at) "
            "VALUES ($1, $2, $3, $4, TRUE, NOW())",
            new_id(),
            org_id,
            user_id,
            role,
        )


@pytest.fixture
async def catalogue(pool: asyncpg.Pool) -> dict[str, Any]:
    """Seeded catalogue identities + a fresh framework/requirement/purpose version."""
    await _require_b1_schema(pool)
    cat = DisclosureCatalogRepository(pool)
    await cat.seed_reference_identities()  # idempotent; exercises the seed audit path
    fw = await cat.get_framework_by_code("GHG_PROTOCOL")
    assert fw is not None
    async with pool.acquire() as conn:
        fwv = await conn.fetchval(
            "INSERT INTO public.disclosure_framework_versions "
            "(framework_id, version_label, source_tier, status) "
            "VALUES ($1, $2, 1, 'IN_FORCE') RETURNING id",
            fw["id"],
            f"B1RT-{new_id()[:8]}",
        )
        req = await conn.fetchval(
            "INSERT INTO public.disclosure_requirement_versions "
            "(framework_version_id, requirement_code, title, requirement_class, "
            " value_kind, carbontally_capability) "
            "VALUES ($1, $2, 'B1 runtime requirement', 'REQUIRED', 'QUANTITATIVE', "
            "'SUPPORTED') RETURNING id",
            fwv,
            f"B1RT_{new_id()[:8]}",
        )
        pv = await conn.fetchval(
            "INSERT INTO public.disclosure_report_purpose_versions (purpose_id, version) "
            "SELECT p.id, (SELECT coalesce(max(v.version), 0) + 1 "
            "              FROM public.disclosure_report_purpose_versions v "
            "              WHERE v.purpose_id = p.id) "
            "FROM public.disclosure_report_purposes p WHERE p.code = 'ANNUAL_CARBON' "
            "RETURNING id"
        )
    return {
        "framework_id": fw["id"],
        "framework_version_id": str(fwv),
        "requirement_version_id": str(req),
        "purpose_version_id": str(pv),
    }


@pytest.fixture
async def case(pool: asyncpg.Pool, catalogue: dict[str, Any]) -> dict[str, Any]:
    """An organisation with DRAFT / APPROVED / FINAL report versions."""
    org = await make_org(pool, "B1 Runtime Org")
    out: dict[str, Any] = {"org": org, "catalogue": catalogue}
    for key, status in (
        ("rv_draft", "DRAFT"),
        ("rv_approved", "APPROVED"),
        ("rv_final", "FINAL"),
    ):
        async with pool.acquire() as conn:
            rep = await conn.fetchval(
                "INSERT INTO public.report_generation_queue "
                "(organization_id, report_type, reporting_year) "
                "VALUES ($1, 'ANNUAL_CARBON', 2025) RETURNING id",
                org,
            )
            rv = await conn.fetchval(
                "INSERT INTO public.report_versions (report_id, version_number, status) "
                "VALUES ($1, 1, $2) RETURNING id",
                rep,
                status,
            )
        out[key] = str(rv)
        out[f"rep_{key[3:]}"] = str(rep)
    return out


def _repo(pool: asyncpg.Pool) -> DisclosureRepository:
    return DisclosureRepository(pool)


async def _materialise(
    pool: asyncpg.Pool,
    case: dict[str, Any],
    *,
    rv: Optional[str] = None,
    value_status: str = "PENDING",
    effective_class: str = "CUSTOMER_INPUT_REQUIRED",
) -> dict[str, Any]:
    """Materialise one value for ``case`` (defaults to its DRAFT report version)."""
    return await _repo(pool).upsert_disclosure_value(
        organization_id=case["org"],
        report_version_id=rv or case["rv_draft"],
        requirement_version_id=case["catalogue"]["requirement_version_id"],
        effective_class=effective_class,
        value_status=value_status,
        value_kind="QUANTITATIVE",
        reporting_year=2025,
    )


async def _audit_rows(pool: asyncpg.Pool, table_name: str) -> list[asyncpg.Record]:
    return list(
        await pool.fetch(
            "SELECT id, action_type, record_id, table_name, performed_by, metadata "
            "FROM public.audit_trail WHERE table_name = $1 ORDER BY performed_at",
            table_name,
        )
    )


async def _org_file(pool: asyncpg.Pool, org_id: str) -> str:
    """Create a minimal ``organization_files`` row for an evidence reference."""
    async with pool.acquire() as conn:
        return str(
            await conn.fetchval(
                "INSERT INTO public.organization_files "
                "(organization_id, name, path, size_bytes, file_type, mime_type) "
                "VALUES ($1, $2, $3, 1024, 'application/pdf', 'application/pdf') "
                "RETURNING id",
                org_id,
                f"b1-runtime-{new_id()[:8]}.pdf",
                f"b1-runtime/{new_id()}.pdf",
            )
        )


async def _snapshot(pool: asyncpg.Pool, org_id: str) -> str:
    """Create a minimal calculation snapshot (``factor_kind='emission_factor'``)."""
    async with pool.acquire() as conn:
        factor = await conn.fetchval(
            "INSERT INTO public.emission_factors "
            "(reporting_year, activity_type, co2e_multiplier) "
            "VALUES (2025, $1, 0.2) RETURNING id",
            f"B1 runtime factor {new_id()[:8]}",
        )
        return str(
            await conn.fetchval(
                "INSERT INTO public.calculation_snapshots "
                "(organization_id, activity, activity_type, quantity, quantity_unit, "
                " co2e_multiplier, co2e_kg, date, factor_id, factor_kind, reporting_year, "
                " methodology, algorithm_version, content_hash) "
                "VALUES ($1, 'Electricity', 'Electricity', 100, 'kWh', 0.2, 20.0, "
                "DATE '2025-06-01', $2, 'emission_factor', 2025, 'activity_based', "
                "'v1.0', $3) RETURNING id",
                org_id,
                factor,
                "0" * 64,
            )
        )


# ---------------------------------------------------------------------------
# F1 — create_applicability_assessment (V1 defect: AmbiguousParameterError $9)
# ---------------------------------------------------------------------------
async def test_f1_assessment_system_determined_executes(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """``determined_by=None`` (the contract §9.8 "system" case) must execute."""
    row = await _repo(pool).create_applicability_assessment(
        organization_id=case["org"],
        framework_version_id=catalogue["framework_version_id"],
        reporting_year=2025,
        reporting_period_start=date(2025, 1, 1),
        reporting_period_end=date(2025, 12, 31),
        characteristic_snapshot={"country": "GB", "employees": 42},
        assessed_status="UNDETERMINED",
        basis="runtime test: facts and basis only",
    )
    assert row["id"]
    assert row["assessed_status"] == "UNDETERMINED"
    stored = await pool.fetchrow(
        "SELECT determined_by, determined_at, created_by, characteristic_snapshot "
        "FROM public.disclosure_applicability_assessments WHERE id = $1",
        row["id"],
    )
    assert stored is not None
    assert stored["determined_by"] is None
    assert stored["determined_at"] is None  # system write carries no actor timestamp
    assert stored["created_by"] is None
    assert json.loads(stored["characteristic_snapshot"]) == {
        "country": "GB",
        "employees": 42,
    }


async def test_f1_assessment_actor_determined_executes(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """The same INSERT must execute for a real actor UUID."""
    actor = await make_user(pool)
    row = await _repo(pool).create_applicability_assessment(
        organization_id=case["org"],
        framework_version_id=catalogue["framework_version_id"],
        reporting_year=2024,
        reporting_period_start=date(2024, 1, 1),
        reporting_period_end=date(2024, 12, 31),
        characteristic_snapshot={"country": "GB"},
        assessed_status="APPLIES",
        basis="runtime test: actor-determined",
        determined_by=actor,
    )
    stored = await pool.fetchrow(
        "SELECT determined_by, determined_at, created_by "
        "FROM public.disclosure_applicability_assessments WHERE id = $1",
        row["id"],
    )
    assert stored is not None
    assert str(stored["determined_by"]) == actor
    assert str(stored["created_by"]) == actor
    assert stored["determined_at"] is not None


# ---------------------------------------------------------------------------
# F2 — upsert_disclosure_value (V1 defect: AmbiguousParameterError $6)
# ---------------------------------------------------------------------------
async def test_f2_value_materialisation_executes(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """A value must materialise through the repository (PQ-3 dimensions kept apart)."""
    value = await _materialise(pool, case)
    assert value["id"]
    assert value["effective_class"] == "CUSTOMER_INPUT_REQUIRED"
    assert value["value_status"] == "PENDING"
    computed_at = await pool.fetchval(
        "SELECT computed_at FROM public.disclosure_values WHERE id = $1", value["id"]
    )
    assert computed_at is None  # not RESOLVED yet


async def test_f2_repeat_upsert_updates_one_row(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """A repeat materialisation updates in place (contract §25 uniqueness)."""
    first = await _materialise(pool, case)
    second = await _repo(pool).upsert_disclosure_value(
        organization_id=case["org"],
        report_version_id=case["rv_draft"],
        requirement_version_id=catalogue["requirement_version_id"],
        effective_class="REQUIRED",
        value_status="RESOLVED",
        value_kind="QUANTITATIVE",
        reporting_year=2025,
        numeric_value=Decimal("12.5"),
        value_unit="kg CO2e",
        source_kind="CALCULATION_AGGREGATE",
    )
    assert second["id"] == first["id"]
    assert second["value_status"] == "RESOLVED"
    rows = await pool.fetchval(
        "SELECT count(*)::int FROM public.disclosure_values "
        "WHERE report_version_id = $1 AND requirement_version_id = $2",
        case["rv_draft"],
        catalogue["requirement_version_id"],
    )
    assert rows == 1
    stored = await pool.fetchrow(
        "SELECT numeric_value, value_unit, computed_at FROM public.disclosure_values "
        "WHERE id = $1",
        first["id"],
    )
    assert stored is not None
    assert stored["numeric_value"] == Decimal("12.5")
    assert stored["value_unit"] == "kg CO2e"
    assert stored["computed_at"] is not None  # set only for RESOLVED


# ---------------------------------------------------------------------------
# F3 — link_value_evidence (V1 defect: NULL-snapshot duplicate links)
# ---------------------------------------------------------------------------
async def test_f3_null_snapshot_relink_is_idempotent(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """Re-linking the SAME evidence reference must not add a row (contract §25)."""
    value = await _materialise(pool, case)
    repo = _repo(pool)
    first = await repo.link_value_evidence(
        organization_id=case["org"],
        disclosure_value_id=value["id"],
        evidence_completeness="COMPLETE",
        source_page=3,
    )
    second = await repo.link_value_evidence(
        organization_id=case["org"],
        disclosure_value_id=value["id"],
        evidence_completeness="COMPLETE",
        source_page=7,
    )
    assert second["id"] == first["id"]  # updated in place, not duplicated
    assert second["source_page"] == 7
    rows = await pool.fetchval(
        "SELECT count(*)::int FROM public.disclosure_value_evidence "
        "WHERE disclosure_value_id = $1",
        value["id"],
    )
    assert rows == 1


async def test_f3_null_snapshot_db_backstop_rejects_raw_duplicate(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """The correction migration's NULL-safe unique index is the DB-level guarantee.

    A raw/concurrent writer that bypasses the repository must still be unable to
    create the duplicate the pre-correction schema allowed.
    """
    value = await _materialise(pool, case)
    await _repo(pool).link_value_evidence(
        organization_id=case["org"], disclosure_value_id=value["id"]
    )
    with pytest.raises(asyncpg.UniqueViolationError):
        await pool.execute(
            "INSERT INTO public.disclosure_value_evidence "
            "(organization_id, disclosure_value_id, calculation_snapshot_id, "
            " emissions_log_id, source_item_id, source_file_id) "
            "VALUES ($1, $2, NULL, NULL, NULL, NULL)",
            case["org"],
            value["id"],
        )


async def test_f3_distinct_references_stay_representable(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """Different evidence references remain independent rows (no over-restriction)."""
    value = await _materialise(pool, case)
    file_a = await _org_file(pool, case["org"])
    file_b = await _org_file(pool, case["org"])
    repo = _repo(pool)
    a = await repo.link_value_evidence(
        organization_id=case["org"], disclosure_value_id=value["id"], source_file_id=file_a
    )
    b = await repo.link_value_evidence(
        organization_id=case["org"], disclosure_value_id=value["id"], source_file_id=file_b
    )
    assert a["id"] != b["id"]

    async def _count() -> int:
        count = await pool.fetchval(
            "SELECT count(*)::int FROM public.disclosure_value_evidence "
            "WHERE disclosure_value_id = $1",
            value["id"],
        )
        return int(count)

    assert await _count() == 2
    again = await repo.link_value_evidence(
        organization_id=case["org"],
        disclosure_value_id=value["id"],
        source_file_id=file_a,
        source_page=11,
    )
    assert again["id"] == a["id"]  # the first reference updates in place
    assert await _count() == 2


async def test_f3_non_null_snapshot_uniqueness_unchanged(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """The calculated-snapshot link keeps its B1 upsert semantics (unchanged)."""
    value = await _materialise(pool, case)
    snapshot = await _snapshot(pool, case["org"])
    repo = _repo(pool)
    first = await repo.link_value_evidence(
        organization_id=case["org"],
        disclosure_value_id=value["id"],
        calculation_snapshot_id=snapshot,
    )
    second = await repo.link_value_evidence(
        organization_id=case["org"],
        disclosure_value_id=value["id"],
        calculation_snapshot_id=snapshot,
        source_page=5,
    )
    assert second["id"] == first["id"]
    assert (
        await pool.fetchval(
            "SELECT count(*)::int FROM public.disclosure_value_evidence "
            "WHERE disclosure_value_id = $1",
            value["id"],
        )
        == 1
    )
    definition = await pool.fetchval(
        "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE conname = 'disclosure_value_evidence_unique'"
    )
    assert "UNIQUE (disclosure_value_id, calculation_snapshot_id)" in definition


# ---------------------------------------------------------------------------
# Tenant isolation + lifecycle immutability (must be unchanged by the correction)
# ---------------------------------------------------------------------------
async def test_tenant_isolation_and_pq2_agreement_still_enforced(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """Cross-tenant writes stay rejected and the PQ-2 period agreement still holds."""
    other = await make_org(pool, "B1 Other Org")
    repo = _repo(pool)
    with pytest.raises(DisclosureViolation):
        await repo.upsert_disclosure_value(
            organization_id=other,
            report_version_id=case["rv_draft"],
            requirement_version_id=catalogue["requirement_version_id"],
            effective_class="REQUIRED",
            value_status="PENDING",
            value_kind="QUANTITATIVE",
            reporting_year=2025,
        )
    with pytest.raises(DisclosureViolation):
        await repo.create_instance_binding(
            organization_id=other,
            report_id=case["rep_draft"],
            purpose_version_id=catalogue["purpose_version_id"],
            reporting_period_start=date(2025, 1, 1),
            reporting_period_end=date(2025, 12, 31),
        )
    value = await _materialise(pool, case)
    with pytest.raises(DisclosureViolation):
        await repo.link_value_evidence(
            organization_id=other, disclosure_value_id=value["id"]
        )

    assessment = await repo.create_applicability_assessment(
        organization_id=case["org"],
        framework_version_id=catalogue["framework_version_id"],
        reporting_year=2025,
        reporting_period_start=date(2025, 1, 1),
        reporting_period_end=date(2025, 12, 31),
        characteristic_snapshot={"country": "GB"},
        assessed_status="APPLIES",
        basis="runtime test: agreement",
    )
    binding = await repo.create_instance_binding(
        organization_id=case["org"],
        report_id=case["rep_draft"],
        purpose_version_id=catalogue["purpose_version_id"],
        reporting_period_start=date(2025, 1, 1),
        reporting_period_end=date(2025, 12, 31),
        applicability_assessment_id=str(assessment["id"]),
    )
    assert binding["id"]
    with pytest.raises(DisclosureViolation):
        await repo.create_instance_binding(
            organization_id=case["org"],
            report_id=case["rep_approved"],
            purpose_version_id=catalogue["purpose_version_id"],
            reporting_period_start=date(2025, 1, 1),
            reporting_period_end=date(2025, 6, 30),
            applicability_assessment_id=str(assessment["id"]),
        )


async def test_approved_and_final_versions_are_immutable(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """PQ-4: APPROVED/FINAL reject value writes; DRAFT is mutable."""
    repo = _repo(pool)
    for rv in (case["rv_approved"], case["rv_final"]):
        with pytest.raises(DisclosureViolation):
            await _materialise(pool, case, rv=rv, effective_class="REQUIRED")
    draft = await _materialise(pool, case)
    await repo.delete_disclosure_value(draft["id"])
    assert (
        await pool.fetchval(
            "SELECT count(*)::int FROM public.disclosure_values WHERE id = $1",
            draft["id"],
        )
        == 0
    )
    # A FINAL-attached row (created outside the repository) can never be deleted.
    async with pool.acquire() as conn:
        frozen = await conn.fetchval(
            "INSERT INTO public.disclosure_values "
            "(organization_id, report_version_id, requirement_version_id, effective_class, "
            " value_status, value_kind, reporting_year) "
            "VALUES ($1, $2, $3, 'REQUIRED', 'RESOLVED', 'QUANTITATIVE', 2025) RETURNING id",
            case["org"],
            case["rv_final"],
            catalogue["requirement_version_id"],
        )
    with pytest.raises(DisclosureViolation):
        await repo.delete_disclosure_value(str(frozen))
    assert (
        await pool.fetchval(
            "SELECT count(*)::int FROM public.disclosure_values WHERE id = $1", frozen
        )
        == 1
    )


# ---------------------------------------------------------------------------
# F5 — B1 audit emission through the existing audit_trail
# ---------------------------------------------------------------------------
_SENSITIVE_MARKERS = ("signed", "token", "secret", "password", "jwt", "http", "bearer")


async def test_b1_writes_emit_audit_entries(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """Every B1 write path appends one existing-taxonomy audit entry (contract §26)."""
    repo = _repo(pool)
    assessment = await repo.create_applicability_assessment(
        organization_id=case["org"],
        framework_version_id=catalogue["framework_version_id"],
        reporting_year=2025,
        reporting_period_start=date(2025, 1, 1),
        reporting_period_end=date(2025, 12, 31),
        characteristic_snapshot={"country": "GB"},
        assessed_status="APPLIES",
        basis="runtime test: audit",
    )
    binding = await repo.create_instance_binding(
        organization_id=case["org"],
        report_id=case["rep_draft"],
        purpose_version_id=catalogue["purpose_version_id"],
        reporting_period_start=date(2025, 1, 1),
        reporting_period_end=date(2025, 12, 31),
    )
    value = await _materialise(pool, case)
    link = await repo.link_value_evidence(
        organization_id=case["org"], disclosure_value_id=value["id"]
    )

    expected = {
        "disclosure_applicability_assessments": (
            "report:disclosure_applicability_assessed",
            str(assessment["id"]),
        ),
        "disclosure_report_instance_binding": (
            "report:disclosure_report_bound",
            str(binding["id"]),
        ),
        "disclosure_values": (
            "report:disclosure_value_materialised",
            str(value["id"]),
        ),
        "disclosure_value_evidence": (
            "report:disclosure_evidence_linked",
            str(link["id"]),
        ),
    }
    for table, (action, entity_id) in expected.items():
        rows = await _audit_rows(pool, table)
        assert rows, f"expected an audit entry for {table}"
        row = rows[-1]
        assert row["action_type"] == action
        assert str(row["record_id"]) == entity_id
        metadata = json.loads(row["metadata"])
        assert metadata["category"] == "report"  # existing taxonomy classification
        assert metadata["actor"] == "system"
        assert metadata["origin"] == "system"
        assert metadata.get("organization_id") == case["org"]
        assert metadata.get("reason") is None
        # The audit record must never carry secrets / signed URLs / payload dumps.
        blob = await pool.fetchval(
            "SELECT (coalesce(old_data,'null'::jsonb)::text || "
            " coalesce(new_data,'null'::jsonb)::text || "
            " coalesce(changes,'null'::jsonb)::text || "
            " coalesce(metadata,'null'::jsonb)::text) "
            "FROM public.audit_trail WHERE id = $1",
            row["id"],
        )
        lowered = (blob or "").lower()
        for marker in _SENSITIVE_MARKERS:
            assert marker not in lowered, f"{marker!r} leaked into audit for {table}"


async def test_catalogue_seed_audits_only_actual_writes(pool: asyncpg.Pool) -> None:
    """An idempotent re-seed performs no write, so it adds no audit entry."""
    await _require_b1_schema(pool)
    cat = DisclosureCatalogRepository(pool)
    first = await cat.seed_reference_identities()
    before = len(await _audit_rows(pool, "disclosure_frameworks"))
    second = await cat.seed_reference_identities()
    after = len(await _audit_rows(pool, "disclosure_frameworks"))
    assert second == {"frameworks_inserted": 0, "purposes_inserted": 0}
    assert after == before
    assert first["frameworks_inserted"] in (0, 3)


# ---------------------------------------------------------------------------
# F4 — corrected privilege posture + RLS actor boundary
# ---------------------------------------------------------------------------
async def test_f4_corrected_privilege_posture(pool: asyncpg.Pool) -> None:
    """The correction migration's privilege posture (requires B1 + the correction).

    Fails loudly if a database carries the B1 schema without
    ``20260915000000_p8_b1_correction_privileges_and_evidence_idempotency.sql``.
    """
    await _require_b1_schema(pool)
    for table in B1_TABLES:
        qualified = f"public.{table}"
        assert not await pool.fetchval(
            "SELECT has_table_privilege('anon', $1::text, 'SELECT')", qualified
        ), f"anon must hold no privilege on {table}"
        for priv in ("TRUNCATE", "TRIGGER", "REFERENCES", "MAINTAIN"):
            granted = await pool.fetchval(
                f"SELECT has_table_privilege('authenticated', $1::text, '{priv}')",
                qualified,
            )
            assert not granted, f"authenticated must not hold {priv} on {table}"
        for priv in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            granted = await pool.fetchval(
                f"SELECT has_table_privilege('service_role', $1::text, '{priv}')",
                qualified,
            )
            assert granted, f"service_role must hold {priv} on {table}"
    for table in READONLY_FOR_AUTHENTICATED:
        for priv in ("INSERT", "UPDATE", "DELETE"):
            granted = await pool.fetchval(
                f"SELECT has_table_privilege('authenticated', $1::text, '{priv}')",
                f"public.{table}",
            )
            assert not granted, f"authenticated must not hold {priv} on {table}"
    for table in WRITABLE_FOR_AUTHENTICATED:
        for priv in ("SELECT", "INSERT", "UPDATE", "DELETE"):
            granted = await pool.fetchval(
                f"SELECT has_table_privilege('authenticated', $1::text, '{priv}')",
                f"public.{table}",
            )
            assert granted, f"authenticated must hold {priv} on {table}"
    # F3 (database half): the NULL-safe evidence-reference index exists.
    assert await pool.fetchval(
        "SELECT to_regclass('public.uq_dve_reference_nullsafe') IS NOT NULL"
    )


async def test_rls_actor_boundary_still_enforced(
    pool: asyncpg.Pool, catalogue: dict[str, Any], case: dict[str, Any]
) -> None:
    """RLS is unchanged by the grants correction: anon/owner/member boundaries hold."""
    owner = await make_user(pool)
    member = await make_user(pool)
    await _add_member(pool, case["org"], owner, "owner")
    await _add_member(pool, case["org"], member, "member")
    other_org = await make_org(pool, "B1 Other Org")
    value = await _materialise(pool, case)

    assessment_insert = (
        "INSERT INTO public.disclosure_applicability_assessments "
        "(organization_id, framework_version_id, reporting_year, reporting_period_start, "
        " reporting_period_end, characteristic_snapshot, assessed_status, basis) "
        "VALUES ($1, $2, 2025, DATE '2025-01-01', DATE '2025-12-31', '{}'::jsonb, "
        "'APPLIES', 'rls probe')"
    )
    value_insert = (
        "INSERT INTO public.disclosure_values "
        "(organization_id, report_version_id, requirement_version_id, effective_class, "
        " value_status, value_kind, reporting_year) "
        "VALUES ($1, $2, $3, 'REQUIRED', 'PENDING', 'QUANTITATIVE', 2025)"
    )

    # anon holds no grant at all.
    async with _session(pool, "anon") as conn:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetchval("SELECT count(*) FROM public.disclosure_frameworks")

    # owner: reads own organisation, never another organisation's rows.
    async with _session(pool, "authenticated", owner) as conn:
        own = await conn.fetchval(
            "SELECT count(*)::int FROM public.disclosure_values WHERE organization_id = $1",
            case["org"],
        )
        foreign = await conn.fetchval(
            "SELECT count(*)::int FROM public.disclosure_values WHERE organization_id = $1",
            other_org,
        )
    assert own == 1
    assert foreign == 0

    # owner: no write path to disclosure_values (no grant, no policy).
    async with _session(pool, "authenticated", owner) as conn:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.execute(
                value_insert,
                case["org"],
                case["rv_draft"],
                catalogue["requirement_version_id"],
            )

    # owner may assess its own organisation; a member may not; nobody crosses tenants.
    async with _session(pool, "authenticated", owner) as conn:
        await conn.execute(
            assessment_insert, case["org"], catalogue["framework_version_id"]
        )
    async with _session(pool, "authenticated", member) as conn:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.execute(
                assessment_insert, case["org"], catalogue["framework_version_id"]
            )
    async with _session(pool, "authenticated", owner) as conn:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.execute(
                assessment_insert, other_org, catalogue["framework_version_id"]
            )

    # service_role (BYPASSRLS) now has usable read/write access (the F4 correction).
    async with _session(pool, "service_role") as conn:
        visible = await conn.fetchval(
            "SELECT count(*)::int FROM public.disclosure_values WHERE organization_id = $1",
            case["org"],
        )
        assert visible >= 1
        await conn.execute(
            "UPDATE public.disclosure_values SET reason = 'service-role probe' WHERE id = $1",
            value["id"],
        )
    assert (
        await pool.fetchval(
            "SELECT reason FROM public.disclosure_values WHERE id = $1", value["id"]
        )
        == "service-role probe"
    )


async def test_b2_b3_b4_boundary_untouched(pool: asyncpg.Pool) -> None:
    """B1's own namespace: the 11 B1 tables plus the ratified B3/B4 tables.

    **AMENDED for Phase 8 B2** (contract §20.6 / F-B2-13 — *amended, never
    deleted*). The two former “B2 is absent” assertions are gone because B2 is
    now authorised and implemented; they are replaced by a check scoped to
    **B1's own namespace** (no B2 capability is smuggled into a ``disclosure_*``
    table), and the B2 *presence* checks now live in
    ``test_evidence_line_items_b2_runtime.py``.

    **AMENDED for Phase 8 B3, then for Phase 8 B4** under the same precedent:
    the B3 intensity tables and the single ratified B4 narrative store are
    authorised objects, so the namespace guard permits EXACTLY those and the
    negative guards are re-scoped rather than deleted. Each batch's own
    presence tests live in that batch's runtime suite.
    """
    await _require_b1_schema(pool)
    tables = await pool.fetchval(
        "SELECT string_agg(table_name, ',' ORDER BY table_name) "
        "FROM information_schema.tables WHERE table_schema = 'public' "
        "AND table_name LIKE 'disclosure%'"
    )
    # **AMENDED for Phase 8 B3** (the B2 20.6 precedent: amended, never deleted).
    # The B3 batch legitimately adds its three ratified intensity tables; the
    # assertion now permits exactly those.
    b3_intensity_tables = (
        "disclosure_intensity_denominator_types",
        "disclosure_intensity_denominator_framework_links",
        "disclosure_intensity_ratios",
    )
    # **AMENDED for Phase 8 B4**: the single ratified narrative store, authorised
    # by PO decision B4-D1 and the narrative decisions A1/A3 (requirement-bound,
    # plain text, no calculation reach). Nothing else is permitted.
    b4_narrative_tables = ("disclosure_narrative_entries",)
    assert tables == ",".join(
        sorted((*B1_TABLES, *b3_intensity_tables, *b4_narrative_tables))
    )
    # B1's namespace carries no B2 capability: the union of columns across the 11
    # B1 tables is exactly the disclosure model (no B2 line-addressability column
    # outside the one ratified additive link, which is B2-2's, not B1's).
    b2_columns = await pool.fetchval(
        "SELECT count(*)::int FROM information_schema.columns "
        "WHERE table_name LIKE 'disclosure%' AND column_name = 'line_number'"
    )
    assert b2_columns == 0
    # **AMENDED for Phase 8 B3**: intensity tables are now ratified B3 objects, so
    # the guard permits EXACTLY those three and nothing else.
    intensity_tables = await pool.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name LIKE '%intensity%' "
        "ORDER BY table_name"
    )
    assert [r["table_name"] for r in intensity_tables] == sorted(b3_intensity_tables)
    # **AMENDED for Phase 8 B4** (same precedent — re-scoped, never deleted).
    # The former blanket "no narrative/commentary table may exist" guard cannot
    # survive B4's authorised narrative store, so it is re-scoped into the two
    # properties that actually matter:
    #   1. narrative storage exists in EXACTLY the one ratified B4 table (no
    #      second narrative/commentary object may appear anywhere); and
    #   2. B1's own 11 tables still carry no narrative/commentary capability —
    #      B1's namespace is not the place B4 stores prose.
    narrative_tables = await pool.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND (table_name LIKE '%narrative%' "
        "OR table_name LIKE '%commentary%') ORDER BY table_name"
    )
    assert [r["table_name"] for r in narrative_tables] == sorted(b4_narrative_tables)
    b1_narrative_columns = await pool.fetchval(
        "SELECT count(*)::int FROM information_schema.columns "
        "WHERE table_name = ANY($1::text[]) AND (column_name LIKE '%narrative%' "
        "OR column_name LIKE '%commentary%')",
        list(B1_TABLES),
    )
    assert b1_narrative_columns == 0
