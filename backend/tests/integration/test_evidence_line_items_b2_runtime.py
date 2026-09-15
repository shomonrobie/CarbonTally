"""Phase 8 B2 — runtime acceptance tests (contract §20.2, tests 1–20).

Database-backed. **Skips** (never fails) when the B2 schema is unprovisioned,
mirroring B1's ``_require_b1_schema`` — a skipped suite is *not* a PASS, so the
implementation report states the environment explicitly. Provision a disposable
B1+B2 clone (contract §18.5) and point ``INTEGRATION_DATABASE_URL`` at it.

Test 18 (migration idempotency) is executed by the clone harness
(``tools/b2_clone_schema_harness.py``), which applies B1+B2 twice and asserts a
zero diff; it is deliberately **not** faked here.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from typing import AsyncIterator, Optional

import asyncpg
import pytest

from data.base import dumps_jsonb, loads_jsonb
from data.disclosure import DisclosureCatalogRepository, DisclosureRepository
from data.emission_factors import EmissionFactorsRepository
from data.emissions_logs import EmissionsLogsRepository
from data.evidence_line_items import EvidenceLineItemsRepository
from data.manual_extraction import ManualExtractionRepository
from domain.factor import EmissionFactor
from domain.line_items import (
    AUDIT_LINE_ITEMS_BACKFILLED,
    AUDIT_LINE_ITEMS_DIVERGENCE_DETECTED,
    AUDIT_LINE_ITEMS_MATERIALISED,
    MATERIALISATION_BACKFILL,
    MATERIALISATION_FORWARD,
)
from engines.calculation import CalculationEngine, CalculationRequest
from tests.integration.conftest import make_org, make_user, new_id

pytestmark = pytest.mark.asyncio

_ACTIVITY = "Fuels > Gas fuels > Natural gas P5 (kg CO2e) [kWh]"


async def _require_b2_schema(pool: asyncpg.Pool) -> None:
    """Skip (never fail) when the B2 schema is not provisioned in this database."""
    present = await pool.fetchval(
        "SELECT to_regclass('public.evidence_line_items') IS NOT NULL"
    )
    if not present:
        pytest.skip(
            "B2 evidence-line schema is not provisioned in this integration "
            "database; apply supabase/migrations/20260916000000_p8_b2_"
            "evidence_line_items.sql and …20260916010000_p8_b2_provenance_"
            "line_links.sql (see the §18.5 disposable-clone recipe)"
        )


@asynccontextmanager
async def _session(
    pool: asyncpg.Pool, role: str, user_id: Optional[str] = None
) -> AsyncIterator[asyncpg.Connection]:
    """Yield a connection acting as ``role`` (optionally with a JWT ``sub``)."""
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
    pool: asyncpg.Pool, org_id: str, user_id: str, role: str = "member"
) -> None:
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


async def _batch(pool: asyncpg.Pool, org_id: str) -> str:
    async with pool.acquire() as conn:
        return str(
            await conn.fetchval(
                "INSERT INTO public.manual_extraction_batches "
                "(organization_id, batch_name, total_documents, total_pages, "
                " total_cost, currency, status, created_at, updated_at) "
                "VALUES ($1, $2, 1, 1, 0, 'GBP', 'open', NOW(), NOW()) RETURNING id",
                org_id,
                f"B2 runtime batch {new_id()[:8]}",
            )
        )


async def _item(
    pool: asyncpg.Pool,
    batch_id: str,
    extracted_data: Optional[dict],
    *,
    file_id: Optional[str] = None,
    queue_id: Optional[str] = None,
    mapped_data: Optional[dict] = None,
) -> str:
    async with pool.acquire() as conn:
        return str(
            await conn.fetchval(
                "INSERT INTO public.manual_extraction_items "
                "(batch_id, document_processing_queue_id, file_name, file_url, "
                " page_count, document_type, status, extracted_data, mapped_data, "
                " file_id) "
                "VALUES ($1, $2, $3, $4, 1, 'invoice', 'extracted', $5, $6, $7) "
                "RETURNING id",
                batch_id,
                queue_id,
                f"b2-runtime-{new_id()[:8]}.csv",
                f"b2-runtime/{new_id()}.csv",
                dumps_jsonb(extracted_data) if extracted_data is not None else None,
                dumps_jsonb(mapped_data) if mapped_data is not None else None,
                file_id,
            )
        )



async def _org_file(pool: asyncpg.Pool, org_id: str) -> str:
    async with pool.acquire() as conn:
        return str(
            await conn.fetchval(
                "INSERT INTO public.organization_files "
                "(organization_id, name, path, size_bytes, file_type, mime_type) "
                "VALUES ($1, $2, $3, 1024, 'text/csv', 'text/csv') RETURNING id",
                org_id,
                f"b2-runtime-{new_id()[:8]}.csv",
                f"b2-runtime/{new_id()}.csv",
            )
        )


async def _queue(pool: asyncpg.Pool, org_id: str, method: str) -> str:
    async with pool.acquire() as conn:
        return str(
            await conn.fetchval(
                "INSERT INTO public.document_processing_queue "
                "(organization_id, processing_type, status, file_name, file_url, "
                " ai_extraction_method) "
                "VALUES ($1, 'ai_extraction', 'ai_extracted', $2, $3, $4) RETURNING id",
                org_id,
                f"b2-runtime-{new_id()[:8]}.xlsx",
                f"b2-runtime/{new_id()}.xlsx",
                method,
            )
        )


def _repo(pool: asyncpg.Pool) -> EvidenceLineItemsRepository:
    return EvidenceLineItemsRepository(pool)


async def _lines(pool: asyncpg.Pool, item_id: str) -> list[asyncpg.Record]:
    return list(
        await pool.fetch(
            "SELECT id, organization_id, source_item_id, source_file_id, line_number, "
            "       source_page, row_reference, raw_description, raw_quantity, raw_unit, "
            "       payload_hash, extraction_method, materialisation_kind "
            "FROM public.evidence_line_items WHERE source_item_id = $1 "
            "ORDER BY line_number",
            item_id,
        )
    )


async def _audit(pool: asyncpg.Pool, action: str) -> list[asyncpg.Record]:
    return list(
        await pool.fetch(
            "SELECT id, record_id, metadata FROM public.audit_trail "
            "WHERE action_type = $1 ORDER BY performed_at",
            action,
        )
    )


async def _seed_factor(pool: asyncpg.Pool) -> EmissionFactor:
    return await EmissionFactorsRepository(pool).save(
        EmissionFactor(
            id=new_id(),
            reporting_year=2025,
            activity_type=_ACTIVITY,
            co2e_multiplier=Decimal("0.18400"),
            unit="kWh",
            scope="Scope 1",
            factor_source="DEFRA-DESNZ",
            factor_set="DEFRA-2025",
            country="GB",
            provider_key="defra",
        )
    )


def _request(
    org_id: str, factor: EmissionFactor, *, source_item_id: str, source_line_item_id
) -> CalculationRequest:
    return CalculationRequest(
        match_request_id=new_id(),
        organization_id=org_id,
        factor=factor,
        quantity=Decimal("100"),
        quantity_unit="kWh",
        date=date(2025, 6, 1),
        reporting_year=2025,
        activity="Natural gas",
        activity_type=_ACTIVITY,
        scope="Scope 1",
        source_item_id=source_item_id,
        source_line_item_id=source_line_item_id,
    )



# --- 0. B2 presence (moved here from B1's boundary test, §20.6) -------------


async def test_00_b2_objects_are_present_and_wired(pool: asyncpg.Pool) -> None:
    """The B2 objects exist exactly as the contract enumerates them.

    These checks were **moved** out of
    ``test_disclosure_b1_runtime.py::test_b2_b3_b4_boundary_untouched`` by the
    contract §20.6 amendment (the B1 test asserted B2's *absence*; the presence
    assertions belong to the B2 suite).
    """
    await _require_b2_schema(pool)
    assert await pool.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'calculation_snapshots' "
        "AND column_name = 'source_line_item_id')"
    )
    assert await pool.fetchval(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'disclosure_value_evidence' "
        "AND column_name = 'source_line_item_id')"
    )
    assert await pool.fetchval(
        "SELECT count(*)::int FROM pg_indexes WHERE indexname IN "
        "('idx_eli_org', 'idx_eli_source_file', "
        " 'idx_calculation_snapshots_source_line_item', 'idx_dve_source_line_item')"
    ) == 4
    assert await pool.fetchval(
        "SELECT count(*)::int FROM pg_policies "
        "WHERE tablename = 'evidence_line_items' AND cmd = 'SELECT'"
    ) == 2


# --- 1. Materialisation count/order (via the forward hook, §12.1) -----------


async def test_01_forward_hook_materialises_count_and_order(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Forward Org")
    batch_id = await _batch(pool, org_id)
    file_id = await _org_file(pool, org_id)
    queue_id = await _queue(pool, org_id, "csv")
    item_id = await _item(
        pool, batch_id, FOUR_LINES, file_id=file_id, queue_id=queue_id
    )
    actor = await make_user(pool)

    updated = await ManualExtractionRepository(pool).save_extracted_data(
        item_id, FOUR_LINES, actor, "csv"
    )
    assert updated is not None

    rows = await _lines(pool, item_id)
    assert [r["line_number"] for r in rows] == [1, 2, 3, 4]
    assert {str(r["organization_id"]) for r in rows} == {org_id}  # server-resolved
    assert {r["materialisation_kind"] for r in rows} == {MATERIALISATION_FORWARD}
    assert {str(r["source_file_id"]) for r in rows} == {file_id}
    assert {r["extraction_method"] for r in rows} == {"csv"}
    assert rows[0]["raw_description"] == "Electricity"
    assert str(rows[0]["raw_quantity"]) == "100"
    assert rows[0]["raw_unit"] == "kWh"
    assert rows[0]["source_page"] is None  # never page_count (F-B2-7)


# --- 2. Idempotency ---------------------------------------------------------


async def test_02_backfill_is_idempotent(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Idempotency Org")
    batch_id = await _batch(pool, org_id)
    item_id = await _item(pool, batch_id, FOUR_LINES)
    repo = _repo(pool)

    first = await repo.materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    assert first.materialised == 4
    before = {r["line_number"]: r["payload_hash"] for r in await _lines(pool, item_id)}

    report = await repo.backfill(dry_run=False)
    after_rows = await _lines(pool, item_id)
    assert report.materialised_rows == 0  # nothing new anywhere
    assert report.divergences == 0
    assert {r["line_number"]: r["payload_hash"] for r in after_rows} == before
    assert len(after_rows) == 4
    assert {r["materialisation_kind"] for r in after_rows} == {
        MATERIALISATION_BACKFILL
    }


# --- 3. Identical duplicate lines stay distinct -----------------------------


async def test_03_identical_duplicate_lines_stay_distinct(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Duplicate Org")
    batch_id = await _batch(pool, org_id)
    line = {"activity": "Same", "quantity": 5, "unit": "kg"}
    item_id = await _item(pool, batch_id, {"line_items": [dict(line), dict(line)]})

    outcome = await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data={"line_items": [dict(line), dict(line)]},
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    rows = await _lines(pool, item_id)
    assert outcome.materialised == 2
    assert [r["line_number"] for r in rows] == [1, 2]
    assert rows[0]["payload_hash"] == rows[1]["payload_hash"]  # never merged
    assert rows[0]["id"] != rows[1]["id"]


# --- 4. Ordinal gaps --------------------------------------------------------


async def test_04_gaps_are_preserved_and_counted(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Gap Org")
    batch_id = await _batch(pool, org_id)
    payload = {
        "line_items": [
            {"activity": "one", "quantity": 1, "unit": "kg"},
            "not-an-object",
            {"activity": "three", "quantity": 3, "unit": "kg"},
        ]
    }
    item_id = await _item(pool, batch_id, payload)
    outcome = await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data=payload,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    rows = await _lines(pool, item_id)
    assert [r["line_number"] for r in rows] == [1, 3]  # ordinal never renumbered
    assert outcome.skipped_malformed == 1
    assert outcome.skipped_empty == 0


# --- 5/6. No line_items, and the empty array (no flat fallback) -------------


async def test_05_no_line_items_materialises_nothing(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Flat Org")
    batch_id = await _batch(pool, org_id)
    flat = {"activity": "Diesel", "quantity": 500, "unit": "litres", "page_count": 8}
    item_id = await _item(pool, batch_id, flat)

    outcome = await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data=flat,
        materialisation_kind=MATERIALISATION_FORWARD,
    )
    assert outcome.eligible is False
    assert outcome.materialised == 0
    assert await _lines(pool, item_id) == []
    assert await _repo(pool).count_for_item(item_id) == 0


async def test_06_empty_array_never_falls_back_to_the_flat_record(
    pool: asyncpg.Pool,
) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Empty Array Org")
    batch_id = await _batch(pool, org_id)
    empty = {"line_items": [], "activity": "Diesel", "quantity": 500, "unit": "litres"}
    item_id = await _item(pool, batch_id, empty)

    outcome = await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data=empty,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    assert outcome.skipped_no_lines == 1
    assert outcome.materialised == 0
    assert await _lines(pool, item_id) == []


#: Four CSV-shaped lines (contract §20.2 test 1).
FOUR_LINES = {
    "line_items": [
        {"activity": "Electricity", "quantity": 100, "unit": "kWh"},
        {"activity": "Natural gas", "quantity": 250, "unit": "kWh"},
        {"activity": "Diesel", "quantity": 40, "unit": "litres"},
        {"activity": "Water", "quantity": 12, "unit": "m3"},
    ]
}



# --- 7/8/9. Calculation → line linkage (§13) --------------------------------


async def test_07_each_snapshot_carries_its_own_line(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Linkage Org")
    batch_id = await _batch(pool, org_id)
    item_id = await _item(pool, batch_id, FOUR_LINES)
    repo = _repo(pool)
    await repo.materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    factor = await _seed_factor(pool)
    engine = CalculationEngine(EmissionsLogsRepository(pool))

    resolved = await repo.get_by_ordinals(item_id, [1, 2, 3, 4])
    assert set(resolved) == {1, 2, 3, 4}
    for ordinal in (1, 2, 3, 4):
        await engine.calculate(
            _request(
                org_id,
                factor,
                source_item_id=item_id,
                source_line_item_id=resolved[ordinal],
            )
        )

    rows = await pool.fetch(
        "SELECT id, source_item_id, source_line_item_id, content_hash "
        "FROM public.calculation_snapshots WHERE source_item_id = $1",
        item_id,
    )
    assert len(rows) == 4
    assert {str(r["source_line_item_id"]) for r in rows} == set(resolved.values())
    for row in rows:
        assert str(row["source_item_id"]) == item_id
        line = await repo.get(str(row["source_line_item_id"]))
        assert line is not None and line["source_item_id"] == item_id  # §8.3


async def test_08_flat_document_snapshot_link_stays_null(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Flat Link Org")
    batch_id = await _batch(pool, org_id)
    flat = {"activity": "Diesel", "quantity": 500, "unit": "litres"}
    item_id = await _item(pool, batch_id, flat)
    factor = await _seed_factor(pool)
    engine = CalculationEngine(EmissionsLogsRepository(pool))

    resolved = await _repo(pool).get_by_ordinals(item_id, [1])
    assert resolved == {}  # no synthetic line was created
    await engine.calculate(
        _request(
            org_id, factor, source_item_id=item_id, source_line_item_id=resolved.get(1)
        )
    )
    row = await pool.fetchrow(
        "SELECT source_item_id, source_line_item_id FROM public.calculation_snapshots "
        "WHERE source_item_id = $1",
        item_id,
    )
    assert row is not None
    assert str(row["source_item_id"]) == item_id  # document-level chain intact
    assert row["source_line_item_id"] is None  # NULL is the honest value (§8.2)
    assert await _lines(pool, item_id) == []


async def test_09_two_calculations_on_one_line(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Multi Calc Org")
    batch_id = await _batch(pool, org_id)
    item_id = await _item(pool, batch_id, FOUR_LINES)
    repo = _repo(pool)
    await repo.materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    line_id = (await repo.get_by_ordinals(item_id, [1]))[1]
    stored_before = await repo.get(line_id)
    factor = await _seed_factor(pool)
    engine = CalculationEngine(EmissionsLogsRepository(pool))

    for _ in range(2):
        await engine.calculate(
            _request(
                org_id, factor, source_item_id=item_id, source_line_item_id=line_id
            )
        )
    snapshots = await pool.fetchval(
        "SELECT count(*)::int FROM public.calculation_snapshots "
        "WHERE source_line_item_id = $1",
        line_id,
    )
    assert snapshots == 2  # no uniqueness violation, no mutation
    assert await repo.get(line_id) == stored_before



# --- 10/11. Divergence, and forward rows surviving a later backfill ---------


async def test_10_divergence_is_reported_and_never_rewritten(
    pool: asyncpg.Pool,
) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Divergence Org")
    batch_id = await _batch(pool, org_id)
    item_id = await _item(pool, batch_id, FOUR_LINES)
    repo = _repo(pool)
    await repo.materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    before = {r["line_number"]: r["payload_hash"] for r in await _lines(pool, item_id)}

    # Correct the persisted element for ordinal 2 only (G6-D style rewrite).
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.manual_extraction_items "
            "SET extracted_data = jsonb_set(extracted_data, "
            "  '{line_items,1,quantity}', '999'::jsonb) WHERE id = $1",
            item_id,
        )
        updated = loads_jsonb(
            await conn.fetchval(
                "SELECT extracted_data FROM public.manual_extraction_items "
                "WHERE id = $1",
                item_id,
            )
        )

    outcome = await repo.materialise_for_item(
        source_item_id=item_id,
        extracted_data=updated,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    assert outcome.divergent_ordinals == (2,)  # detected and reported
    assert outcome.materialised == 0  # never reconciled in place
    after = {r["line_number"]: r["payload_hash"] for r in await _lines(pool, item_id)}
    assert after == before  # stored rows untouched, other ordinals unaffected


async def test_11_forward_rows_survive_a_later_backfill(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Forward Then Backfill Org")
    batch_id = await _batch(pool, org_id)
    item_id = await _item(pool, batch_id, FOUR_LINES)
    actor = await make_user(pool)
    await ManualExtractionRepository(pool).save_extracted_data(
        item_id, FOUR_LINES, actor, "xlsx"
    )
    before = {
        r["line_number"]: (r["payload_hash"], r["materialisation_kind"])
        for r in await _lines(pool, item_id)
    }
    report = await _repo(pool).backfill(dry_run=False)
    after = {
        r["line_number"]: (r["payload_hash"], r["materialisation_kind"])
        for r in await _lines(pool, item_id)
    }
    assert after == before  # identical hashes, still FORWARD
    assert {kind for _, kind in after.values()} == {MATERIALISATION_FORWARD}
    assert report.materialised_rows == 0



# --- 12. RLS ALLOW / DENY ---------------------------------------------------


async def _pe_work(pool: asyncpg.Pool, item_id: str, name: str) -> tuple[str, str]:
    """Create an active entity + staff profile + OPEN assignment over ``item_id``."""
    entity_id = new_id()
    user_id = await make_user(pool)
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.processing_entities (id, name, status) "
            "VALUES ($1, $2, 'active')",
            entity_id,
            name,
        )
        await conn.execute(
            "INSERT INTO public.staff_profiles "
            "(user_id, first_name, last_name, email, entity_id, is_active) "
            "VALUES ($1, 'PE', 'User', $2, $3, TRUE)",
            user_id,
            f"pe-{user_id}@example.test",
            entity_id,
        )
        await conn.execute(
            "INSERT INTO public.work_item_assignments "
            "(manual_extraction_item_id, status, action, assignee_kind, "
            " processing_entity_id, assigned_by, actor_domain) "
            "VALUES ($1, 'open', 'assign', 'processing_entity', $2, $3, "
            "        'processing_entity')",
            item_id,
            entity_id,
            user_id,
        )
    return str(entity_id), user_id


async def test_12_rls_allows_members_and_denies_other_tenants(
    pool: asyncpg.Pool,
) -> None:
    await _require_b2_schema(pool)
    org_a = await make_org(pool, "B2 RLS Org A")
    org_b = await make_org(pool, "B2 RLS Org B")
    single = {"line_items": [{"activity": "B", "quantity": 1, "unit": "kg"}]}
    item_a = await _item(pool, await _batch(pool, org_a), FOUR_LINES)
    item_b = await _item(pool, await _batch(pool, org_b), single)
    repo = _repo(pool)
    for item_id, payload in ((item_a, FOUR_LINES), (item_b, single)):
        await repo.materialise_for_item(
            source_item_id=item_id,
            extracted_data=payload,
            materialisation_kind=MATERIALISATION_BACKFILL,
        )
    member_a = await make_user(pool)
    await _add_member(pool, org_a, member_a)
    member_b = await make_user(pool)
    await _add_member(pool, org_b, member_b)

    async with _session(pool, "authenticated", member_a) as conn:
        assert await conn.fetchval(
            "SELECT count(*)::int FROM public.evidence_line_items"
        ) == 4
        assert await conn.fetchval(
            "SELECT count(*)::int FROM public.evidence_line_items "
            "WHERE source_item_id = $1::uuid",
            item_a,
        ) == 4
    # cross-tenant denial is the primary negative test (§16.1)
    async with _session(pool, "authenticated", member_b) as conn:
        assert await conn.fetchval(
            "SELECT count(*)::int FROM public.evidence_line_items "
            "WHERE source_item_id = $1::uuid",
            item_a,
        ) == 0
        assert await conn.fetchval(
            "SELECT count(*)::int FROM public.evidence_line_items"
        ) == 1
    # authenticated but not a member of any organisation
    stranger = await make_user(pool)
    async with _session(pool, "authenticated", stranger) as conn:
        assert await conn.fetchval(
            "SELECT count(*)::int FROM public.evidence_line_items"
        ) == 0
    # anon: REVOKE ALL — denied at the privilege layer (stronger than 0 rows)
    async with _session(pool, "anon") as conn:
        try:
            visible = await conn.fetchval(
                "SELECT count(*)::int FROM public.evidence_line_items"
            )
        except asyncpg.exceptions.InsufficientPrivilegeError:
            visible = 0
        assert visible == 0


async def test_12b_pe_boundary_mirrors_the_item_policy(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 PE Org")
    single_y = {"line_items": [{"activity": "Y", "quantity": 2, "unit": "kg"}]}
    item_x = await _item(pool, await _batch(pool, org_id), FOUR_LINES)
    item_y = await _item(pool, await _batch(pool, org_id), single_y)
    repo = _repo(pool)
    await repo.materialise_for_item(
        source_item_id=item_x,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    await repo.materialise_for_item(
        source_item_id=item_y,
        extracted_data=single_y,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    entity_x, pe_x_user = await _pe_work(pool, item_x, f"B2 PE X {new_id()[:8]}")
    _, pe_y_user = await _pe_work(pool, item_y, f"B2 PE Y {new_id()[:8]}")

    async with _session(pool, "authenticated", pe_x_user) as conn:
        assert await conn.fetchval(
            "SELECT count(*)::int FROM public.evidence_line_items "
            "WHERE source_item_id = $1::uuid",
            item_x,
        ) == 4
        assert await conn.fetchval(
            "SELECT count(*)::int FROM public.evidence_line_items "
            "WHERE source_item_id = $1::uuid",
            item_y,
        ) == 0  # PE X → PE Y denied
    async with _session(pool, "authenticated", pe_y_user) as conn:
        assert await conn.fetchval(
            "SELECT count(*)::int FROM public.evidence_line_items "
            "WHERE source_item_id = $1::uuid",
            item_x,
        ) == 0
    assert entity_x  # the entity context existed and resolved


# --- 13. Privileges ---------------------------------------------------------


async def test_13_privilege_posture_is_enforced(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Privilege Org")
    item_id = await _item(pool, await _batch(pool, org_id), FOUR_LINES)
    await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_FORWARD,
    )  # service_role (the pool) CAN insert
    assert len(await _lines(pool, item_id)) == 4

    member = await make_user(pool)
    await _add_member(pool, org_id, member)
    insert_sql = (
        "INSERT INTO public.evidence_line_items (organization_id, source_item_id, "
        "line_number, payload_hash, materialisation_kind) "
        "VALUES ($1::uuid, $2::uuid, 99, 'x', 'FORWARD')"
    )
    async with _session(pool, "authenticated", member) as conn:
        with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
            await conn.execute(insert_sql, org_id, item_id)
        for sql in (
            "UPDATE public.evidence_line_items SET payload_hash = 'y'",
            "DELETE FROM public.evidence_line_items",
        ):
            with pytest.raises(asyncpg.exceptions.InsufficientPrivilegeError):
                await conn.execute(sql)




# --- 14. Historical immutability -------------------------------------------


async def test_14_pre_existing_rows_are_never_rewritten(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Immutability Org")
    item_id = await _item(pool, await _batch(pool, org_id), FOUR_LINES)
    factor = await _seed_factor(pool)
    snapshot_id = new_id()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.calculation_snapshots "
            "(id, organization_id, activity, activity_type, quantity, quantity_unit, "
            " co2e_multiplier, co2e_kg, date, factor_id, factor_kind, reporting_year, "
            " methodology, algorithm_version, content_hash, source_item_id) "
            "VALUES ($1, $2, 'Electricity', 'Electricity', 100, 'kWh', 0.2, 20.0, "
            "        DATE '2025-06-01', $3, 'emission_factor', 2025, 'activity_based', "
            "        'v1.0', $4, $5)",
            snapshot_id,
            org_id,
            factor.id,
            "0" * 64,
            item_id,
        )

    async def _hash(sid: str) -> Optional[str]:
        return await pool.fetchval(
            "SELECT md5(t::text) FROM public.calculation_snapshots t WHERE id = $1",
            sid,
        )

    before = await _hash(snapshot_id)
    await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    await _repo(pool).backfill(dry_run=False)
    assert await _hash(snapshot_id) == before  # byte-identical row
    assert await pool.fetchval(
        "SELECT source_line_item_id IS NULL FROM public.calculation_snapshots "
        "WHERE id = $1",
        snapshot_id,
    )  # no retro-linking (B2-D12)


# --- 15. Evidence linkage (§9) ---------------------------------------------


async def _disclosure_value(pool: asyncpg.Pool, org_id: str) -> str:
    """Minimal B1 catalogue + report version + materialised disclosure value."""
    await DisclosureCatalogRepository(pool).seed_reference_identities()
    async with pool.acquire() as conn:
        fwv = await conn.fetchval(
            "INSERT INTO public.disclosure_framework_versions "
            "(framework_id, version_label, source_tier, status) "
            "SELECT id, $1, 1, 'IN_FORCE' FROM public.disclosure_frameworks "
            "WHERE code = 'GHG_PROTOCOL' RETURNING id",
            f"B2RT-{new_id()[:8]}",
        )
        req = await conn.fetchval(
            "INSERT INTO public.disclosure_requirement_versions "
            "(framework_version_id, requirement_code, title, requirement_class, "
            " value_kind, carbontally_capability) "
            "VALUES ($1, $2, 'B2 runtime requirement', 'REQUIRED', 'QUANTITATIVE', "
            "'SUPPORTED') RETURNING id",
            fwv,
            f"B2RT_{new_id()[:8]}",
        )
        rep = await conn.fetchval(
            "INSERT INTO public.report_generation_queue "
            "(organization_id, report_type, reporting_year) "
            "VALUES ($1, 'ANNUAL_CARBON', 2025) RETURNING id",
            org_id,
        )
        rv = await conn.fetchval(
            "INSERT INTO public.report_versions (report_id, version_number, status) "
            "VALUES ($1, 1, 'DRAFT') RETURNING id",
            rep,
        )
    value = await DisclosureRepository(pool).upsert_disclosure_value(
        organization_id=org_id,
        report_version_id=str(rv),
        requirement_version_id=str(req),
        effective_class="CUSTOMER_INPUT_REQUIRED",
        value_status="PENDING",
        value_kind="QUANTITATIVE",
        reporting_year=2025,
    )
    return str(value["id"])


async def test_15_evidence_link_is_written_idempotent_and_consistent(
    pool: asyncpg.Pool,
) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Evidence Link Org")
    item_id = await _item(pool, await _batch(pool, org_id), FOUR_LINES)
    repo = _repo(pool)
    await repo.materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    lines = await _lines(pool, item_id)
    line_id = str(lines[0]["id"])
    factor = await _seed_factor(pool)
    engine = CalculationEngine(EmissionsLogsRepository(pool))
    snapshot_id = (
        await engine.calculate(
            _request(
                org_id, factor, source_item_id=item_id, source_line_item_id=line_id
            )
        )
    ).snapshot.id
    value_id = await _disclosure_value(pool, org_id)
    disclosure = DisclosureRepository(pool)

    first = await disclosure.link_value_evidence(
        organization_id=org_id,
        disclosure_value_id=value_id,
        calculation_snapshot_id=snapshot_id,
        source_item_id=item_id,
        source_line_item_id=line_id,
    )
    assert first["source_line_item_id"] == line_id
    again = await disclosure.link_value_evidence(
        organization_id=org_id,
        disclosure_value_id=value_id,
        calculation_snapshot_id=snapshot_id,
        source_item_id=item_id,
        source_line_item_id=line_id,
    )
    assert again["id"] == first["id"]  # re-linking is idempotent
    assert await pool.fetchval(
        "SELECT count(*)::int FROM public.disclosure_value_evidence "
        "WHERE disclosure_value_id = $1::uuid",
        value_id,
    ) == 1

    # §9.2 — omitting the kwarg still records the finer fact, taken from the snapshot
    derived = await disclosure.link_value_evidence(
        organization_id=org_id,
        disclosure_value_id=value_id,
        calculation_snapshot_id=snapshot_id,
        source_item_id=item_id,
    )
    assert derived["source_line_item_id"] == line_id

    # §9.2 consistency invariant: every linked row matches its snapshot
    inconsistent = await pool.fetchval(
        "SELECT count(*)::int FROM public.disclosure_value_evidence d "
        "JOIN public.calculation_snapshots s ON s.id = d.calculation_snapshot_id "
        "WHERE d.source_line_item_id IS NOT NULL "
        "  AND d.source_line_item_id IS DISTINCT FROM s.source_line_item_id"
    )
    assert inconsistent == 0

    # and a backfill run never rewrites the evidence row
    hash_before = await pool.fetchval(
        "SELECT md5(t::text) FROM public.disclosure_value_evidence t WHERE id = $1",
        first["id"],
    )
    await repo.backfill(dry_run=False)
    assert (
        await pool.fetchval(
            "SELECT md5(t::text) FROM public.disclosure_value_evidence t WHERE id = $1",
            first["id"],
        )
        == hash_before
    )


# --- 16. Audit --------------------------------------------------------------


async def test_16_audit_volume_granularity_and_payload_discipline(
    pool: asyncpg.Pool,
) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Audit Org")
    item_id = await _item(pool, await _batch(pool, org_id), FOUR_LINES)
    actor = await make_user(pool)

    # one forward event per source document (B2-D5)
    await ManualExtractionRepository(pool).save_extracted_data(
        item_id, FOUR_LINES, actor, "csv"
    )
    materialised = [
        r
        for r in await _audit(pool, AUDIT_LINE_ITEMS_MATERIALISED)
        if str(r["record_id"]) == item_id
    ]
    assert len(materialised) == 1
    # never a line value or a document in the payload (§17)
    payload = str(materialised[0]["metadata"])
    for leak in ("Electricity", "Natural gas", "Diesel", "Water"):
        assert leak not in payload

    # exactly one summary event per backfill RUN (not per item)
    before = len(await _audit(pool, AUDIT_LINE_ITEMS_BACKFILLED))
    await _repo(pool).backfill(dry_run=False)
    assert len(await _audit(pool, AUDIT_LINE_ITEMS_BACKFILLED)) == before + 1

    # divergence is audited per affected item
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.manual_extraction_items SET extracted_data = "
            "jsonb_set(extracted_data, '{line_items,0,quantity}', '777'::jsonb) "
            "WHERE id = $1",
            item_id,
        )
        updated = loads_jsonb(
            await conn.fetchval(
                "SELECT extracted_data FROM public.manual_extraction_items "
                "WHERE id = $1",
                item_id,
            )
        )
    await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data=updated,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    divergences = [
        r
        for r in await _audit(pool, AUDIT_LINE_ITEMS_DIVERGENCE_DETECTED)
        if str(r["record_id"]) == item_id
    ]
    assert len(divergences) == 1
    assert "777" not in str(divergences[0]["metadata"])


# --- 17. No re-extraction ---------------------------------------------------


async def test_17_materialisation_never_touches_extraction_payloads(
    pool: asyncpg.Pool,
) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 No Re-extraction Org")
    mapped = {"line_items": [{"factor_id": "irrelevant", "scope": "Scope 1"}]}
    item_id = await _item(
        pool, await _batch(pool, org_id), FOUR_LINES, mapped_data=mapped
    )

    async def _payload_hashes() -> dict:
        return dict(
            await pool.fetchrow(
                "SELECT md5(extracted_data::text) AS extracted, "
                "       md5(mapped_data::text) AS mapped "
                "FROM public.manual_extraction_items WHERE id = $1",
                item_id,
            )
        )

    before = await _payload_hashes()
    await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_FORWARD,
    )
    await _repo(pool).backfill(dry_run=False)
    assert await _payload_hashes() == before  # byte-identical payloads

    # static: the materialisation modules import no extractor/OCR/AI/parser
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    for path in (
        root / "domain" / "line_items.py",
        root / "data" / "evidence_line_items.py",
    ):
        source = path.read_text(encoding="utf-8")
        code = re.sub(r'"""(.*?)"""', "", source, flags=re.S)
        code = "\n".join(line.split("#", 1)[0] for line in code.splitlines())
        for forbidden in (
            "automatic_extraction",
            "ai_document_extraction",
            "extraction_suggestions",
            "tesseract",
            "openai",
            "pytesseract",
        ):
            assert forbidden not in code.lower(), f"{path.name}: {forbidden}"



# --- 19. RESTRICT behaviour (B2-D1) ----------------------------------------


async def test_19_parent_delete_is_restricted(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    org_id = await make_org(pool, "B2 Restrict Org")
    item_id = await _item(pool, await _batch(pool, org_id), FOUR_LINES)
    await _repo(pool).materialise_for_item(
        source_item_id=item_id,
        extracted_data=FOUR_LINES,
        materialisation_kind=MATERIALISATION_BACKFILL,
    )
    async with pool.acquire() as conn:
        with pytest.raises(asyncpg.exceptions.ForeignKeyViolationError):
            await conn.execute(
                "DELETE FROM public.manual_extraction_items WHERE id = $1", item_id
            )
    assert len(await _lines(pool, item_id)) == 4  # no cascade, lines intact


# --- 20. No retention / trigger artefacts (B2-D11) -------------------------


async def test_20_schema_carries_no_retention_artefact(pool: asyncpg.Pool) -> None:
    await _require_b2_schema(pool)
    assert (
        await pool.fetchval(
            "SELECT count(*)::int FROM information_schema.triggers "
            "WHERE event_object_table = 'evidence_line_items'"
        )
        == 0
    )
    columns = {
        r["column_name"]
        for r in await pool.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'evidence_line_items'"
        )
    }
    for forbidden in ("deleted_at", "is_active", "updated_at", "purged_at"):
        assert forbidden not in columns
    assert columns == {
        "id",
        "organization_id",
        "source_item_id",
        "source_file_id",
        "line_number",
        "source_page",
        "row_reference",
        "raw_description",
        "raw_quantity",
        "raw_unit",
        "payload_hash",
        "extraction_method",
        "materialisation_kind",
        "created_at",
    }
    assert await pool.fetchval(
        "SELECT relrowsecurity FROM pg_class WHERE oid = "
        "'public.evidence_line_items'::regclass"
    )
    # no delete path exists in the data layer (it raises rather than deleting)
    with pytest.raises(NotImplementedError):
        await _repo(pool).delete("00000000-0000-0000-0000-000000000000")

