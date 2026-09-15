"""Runtime integration tests for the Phase 8 B4 approval/finalisation path.

Executes against ``INTEGRATION_DATABASE_URL`` (the dedicated non-production QA
database) and **skips — never fails —** when the B4 schema is absent there.

Proves, against real rows and the real repositories:

* the **`B4-D1`** boundary (Owner/Admin act; member/consultant/staff roles are refused);
* the **`DM-5`** gate (unresolved ``REQUIRED`` blocks; ``NOT_SUPPORTED`` is surfaced);
* the ratified S3 transition + terminal-version behaviour.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import asyncpg
import pytest

from data.disclosure import DisclosureCatalogRepository
from domain.disclosure import DisclosureViolation
from services.disclosure_finalisation import (
    DisclosureFinalisationService,
    FinalisationBlocked,
)
from tests.integration.conftest import make_org, new_id

YEAR = 2025
PERIOD_START = date(2025, 1, 1)
PERIOD_END = date(2025, 12, 31)


async def _require_b4_schema(pool: asyncpg.Pool) -> None:
    if not await pool.fetchval("SELECT to_regclass('public.disclosure_narrative_entries') IS NOT NULL"):
        pytest.skip(
            "B4 narrative schema is not provisioned here; apply "
            "supabase/migrations/20260918000000_p8_b4_narrative_overlay.sql"
        )
    for table in ("disclosure_values", "report_versions", "report_generation_queue"):
        if not await pool.fetchval(f"SELECT to_regclass('public.{table}') IS NOT NULL"):
            pytest.skip(f"{table} is not provisioned in this integration database")


@pytest.fixture
async def case(pool: asyncpg.Pool) -> dict[str, Any]:
    """An org with a REVIEWED report version and three disclosure values."""
    await _require_b4_schema(pool)
    cat = DisclosureCatalogRepository(pool)
    await cat.seed_reference_identities()
    fw = await cat.get_framework_by_code("GHG_PROTOCOL")
    assert fw is not None

    org = await make_org(pool, "B4 Finalisation Org")
    out: dict[str, Any] = {"org": org}

    async with pool.acquire() as conn:
        fwv = await conn.fetchval(
            "INSERT INTO public.disclosure_framework_versions "
            "(framework_id, version_label, source_tier, status) "
            "VALUES ($1, $2, 1, 'IN_FORCE') RETURNING id",
            fw["id"],
            f"B4RT-{new_id()[:8]}",
        )

        async def _req(code: str, klass: str, capability: str) -> str:
            return str(
                await conn.fetchval(
                    "INSERT INTO public.disclosure_requirement_versions "
                    "(framework_version_id, requirement_code, title, requirement_class, "
                    " value_kind, carbontally_capability) "
                    "VALUES ($1, $2, $3, $4, 'QUANTITATIVE', $5) RETURNING id",
                    fwv,
                    code,
                    f"B4 runtime requirement {code}",
                    klass,
                    capability,
                )
            )

        out["req_required"] = await _req(f"B4RT_R_{new_id()[:8]}", "REQUIRED", "SUPPORTED")
        out["req_input"] = await _req(
            f"B4RT_I_{new_id()[:8]}", "CUSTOMER_INPUT_REQUIRED", "STRUCTURED_INPUT_REQUIRED"
        )
        out["req_unsupported"] = await _req(
            f"B4RT_U_{new_id()[:8]}", "REQUIRED", "MISSING_CAPABILITY"
        )

        purpose_version_id = await conn.fetchval(
            "INSERT INTO public.disclosure_report_purpose_versions (purpose_id, version) "
            "SELECT p.id, (SELECT coalesce(max(v.version), 0) + 1 "
            "              FROM public.disclosure_report_purpose_versions v "
            "              WHERE v.purpose_id = p.id) "
            "FROM public.disclosure_report_purposes p WHERE p.code = 'ANNUAL_CARBON' "
            "RETURNING id"
        )
        report_id = await conn.fetchval(
            "INSERT INTO public.report_generation_queue "
            "(organization_id, report_type, reporting_year) "
            "VALUES ($1, 'ANNUAL_CARBON', $2) RETURNING id",
            org,
            YEAR,
        )
        out["report_id"] = str(report_id)
        version_id = await conn.fetchval(
            "INSERT INTO public.report_versions (report_id, version_number, status) "
            "VALUES ($1, 1, 'REVIEWED') RETURNING id",
            report_id,
        )
        out["version_id"] = str(version_id)
        await conn.execute(
            "INSERT INTO public.disclosure_report_instance_binding "
            "(organization_id, report_id, purpose_version_id, "
            " reporting_period_start, reporting_period_end, consolidation_approach) "
            "VALUES ($1, $2, $3, $4, $5, 'OPERATIONAL_CONTROL')",
            org,
            report_id,
            purpose_version_id,
            PERIOD_START,
            PERIOD_END,
        )
        for key, klass in (
            ("req_required", "REQUIRED"),
            ("req_input", "CUSTOMER_INPUT_REQUIRED"),
            ("req_unsupported", "NOT_SUPPORTED"),
        ):
            await conn.execute(
                "INSERT INTO public.disclosure_values "
                "(organization_id, report_version_id, requirement_version_id, "
                " effective_class, value_status, value_kind, reporting_year, reason) "
                "VALUES ($1, $2, $3, $4, 'UNRESOLVED', 'QUANTITATIVE', $5, $6)",
                org,
                version_id,
                out[key],
                klass,
                YEAR,
                f"B4 runtime fixture ({klass})",
            )
    return out


async def _set_role(pool: asyncpg.Pool, requirement_version_id: str, role: str) -> None:
    await pool.execute(
        "UPDATE public.disclosure_values SET value_status = $3, updated_at = now() "
        "WHERE requirement_version_id = $1 AND value_status <> $3",
        requirement_version_id,
        role,
    )


def _service(pool: asyncpg.Pool) -> DisclosureFinalisationService:
    return DisclosureFinalisationService(pool)


async def test_assess_reports_blocking_and_surfaced_limitations(pool: asyncpg.Pool, case: dict) -> None:
    result = await _service(pool).assess(report_version_id=case["version_id"])
    assert result["version_status"] == "REVIEWED"
    assert result["can_finalise"] is False
    blocking = {item["requirement_version_id"] for item in result["blocking"]}
    assert case["req_required"] in blocking
    assert case["req_input"] in blocking
    surfaced = {item["requirement_version_id"] for item in result["surfaced_limitations"]}
    assert case["req_unsupported"] in surfaced
    assert case["req_unsupported"] not in blocking


async def test_finalisation_is_blocked_while_required_is_unresolved(pool: asyncpg.Pool, case: dict) -> None:
    service = _service(pool)
    await service.approve(report_version_id=case["version_id"], actor_role="owner")
    with pytest.raises(FinalisationBlocked):
        await service.finalise(report_version_id=case["version_id"], actor_role="owner")
    status = await pool.fetchval(
        "SELECT status FROM public.report_versions WHERE id = $1", case["version_id"]
    )
    assert status == "APPROVED"  # gate refused before any transition


async def test_owner_can_finalise_once_required_is_resolved(pool: asyncpg.Pool, case: dict) -> None:
    """AMENDED for PO `B4-D5` (the B2 §20.6 precedent: amended, never deleted).

    Finalisation now requires the mandatory frozen artefact, so the call supplies
    a producer and an in-memory storage double. The mandate itself — that
    finalisation is *refused* without them — is proven separately by
    ``test_finalisation_is_refused_without_the_frozen_artefact``.
    """
    from services.report_artefact_storage import InMemoryReportArtefactStorage

    service = _service(pool)
    storage = InMemoryReportArtefactStorage()
    await service.approve(report_version_id=case["version_id"], actor_role="owner")

    async with pool.acquire() as conn:
        for key in ("req_required", "req_input"):
            await conn.execute(
                "UPDATE public.disclosure_values SET value_status = 'RESOLVED', updated_at = now() "
                "WHERE report_version_id = $1 AND requirement_version_id = $2",
                case["version_id"],
                case[key],
            )

    result = await service.finalise(
        report_version_id=case["version_id"],
        actor_role="admin",
        pdf_producer=lambda: b"%PDF-1.7\nfrozen for the lifecycle test\n",
        storage=storage,
    )
    assert result["previous_status"] == "APPROVED"
    assert result["version_status"] == "FINAL"
    assert result["frozen_artefact"]["storage_bucket"] == "report-artifacts"
    # DM-5: the unsupported limitation is still reported, never silently satisfied.
    assert [i["requirement_version_id"] for i in result["surfaced_limitations"]] == [
        case["req_unsupported"]
    ]
    status = await pool.fetchval(
        "SELECT status FROM public.report_versions WHERE id = $1", case["version_id"]
    )
    assert status == "FINAL"

    # A finalised version is never re-transitioned (D15 / terminal state).
    with pytest.raises(DisclosureViolation):
        await service.finalise(
            report_version_id=case["version_id"],
            actor_role="owner",
            pdf_producer=lambda: b"%PDF-1.7\nsecond attempt\n",
            storage=storage,
        )


@pytest.mark.parametrize("role", ["member", "viewer", "consultant", "pe_staff", "staff", None])
async def test_non_owner_admin_roles_are_refused(pool: asyncpg.Pool, case: dict, role: str | None) -> None:
    """B4-D1 defence in depth: the service re-checks the acting role."""
    with pytest.raises(DisclosureViolation):
        await _service(pool).approve(report_version_id=case["version_id"], actor_role=role)
    status = await pool.fetchval(
        "SELECT status FROM public.report_versions WHERE id = $1", case["version_id"]
    )
    assert status == "REVIEWED"


async def test_narrative_table_is_not_readable_by_anon(pool: asyncpg.Pool) -> None:
    await _require_b4_schema(pool)
    allowed = await pool.fetchval(
        "SELECT has_table_privilege('anon', 'public.disclosure_narrative_entries', 'SELECT')"
    )
    assert allowed is False
    rls = await pool.fetchval(
        "SELECT relrowsecurity FROM pg_class WHERE oid = "
        "'public.disclosure_narrative_entries'::regclass"
    )
    assert rls is True


# ---------------------------------------------------------------------------
# S4 narrative — A1/A3/D15 against the real table
# ---------------------------------------------------------------------------
async def test_narrative_authoring_binding_and_immutability(pool: asyncpg.Pool, case: dict) -> None:
    """The narrative store is requirement-bound (A1) and refuses post-approval edits (D15)."""
    import uuid

    from services.disclosure_narrative import DisclosureNarrativeService

    svc = DisclosureNarrativeService(pool)
    body = "Operational control boundary note (B4 runtime)."
    written = await svc.write_narrative(
        report_version_id=case["version_id"],
        requirement_version_id=case["req_required"],
        narrative_kind="CUSTOMER_COMMENTARY",
        body=body,
        actor_role="owner",
    )
    assert written["state"] == "DRAFT"
    assert written["actor_role"] == "owner"

    listed = await svc.list_narrative(report_version_id=case["version_id"])
    assert listed["count"] == 1
    assert listed["entries"][0]["body"] == body
    assert listed["authoring_allowed"] is True

    # Idempotent re-authoring replaces the single entry (A1 unique binding).
    await svc.write_narrative(
        report_version_id=case["version_id"],
        requirement_version_id=case["req_required"],
        narrative_kind="CUSTOMER_COMMENTARY",
        body=body + " (revised)",
        actor_role="admin",
    )
    again = await svc.list_narrative(report_version_id=case["version_id"])
    assert again["count"] == 1
    assert again["entries"][0]["body"].endswith("(revised)")

    # A1: a requirement that is not part of this report version is refused.
    with pytest.raises(DisclosureViolation):
        await svc.write_narrative(
            report_version_id=case["version_id"],
            requirement_version_id=str(uuid.uuid4()),
            narrative_kind="CUSTOMER_COMMENTARY",
            body="not bound to this report",
            actor_role="owner",
        )

    # A1/P3: a non-Owner/Admin role cannot author even with a valid binding.
    with pytest.raises(DisclosureViolation):
        await svc.write_narrative(
            report_version_id=case["version_id"],
            requirement_version_id=case["req_required"],
            narrative_kind="CUSTOMER_COMMENTARY",
            body="member attempt",
            actor_role="member",
        )

    # D15: an APPROVED version refuses authoring.
    await DisclosureFinalisationService(pool).approve(
        report_version_id=case["version_id"], actor_role="owner"
    )
    with pytest.raises(DisclosureViolation):
        await svc.write_narrative(
            report_version_id=case["version_id"],
            requirement_version_id=case["req_required"],
            narrative_kind="CUSTOMER_COMMENTARY",
            body="late edit",
            actor_role="owner",
        )




# ---------------------------------------------------------------------------
# S5 frozen artefact — mandate, integrity and append-only proof (B4-D5/D6/D7)
# ---------------------------------------------------------------------------
async def _resolve_required(pool: asyncpg.Pool, case: dict) -> None:
    """Resolve every blocking value so the DM-5 gate passes."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.disclosure_values SET value_status = 'RESOLVED', updated_at = now() "
            "WHERE report_version_id = $1 AND effective_class IN "
            "('REQUIRED', 'CUSTOMER_INPUT_REQUIRED')",
            case["version_id"],
        )


async def test_finalisation_is_refused_without_the_frozen_artefact(
    pool: asyncpg.Pool, case: dict
) -> None:
    """B4-D5: no producer → no FINAL. The version stays APPROVED."""
    from services.disclosure_finalisation import ArtefactRequired

    service = _service(pool)
    await service.approve(report_version_id=case["version_id"], actor_role="owner")
    await _resolve_required(pool, case)
    with pytest.raises(ArtefactRequired):
        await service.finalise(report_version_id=case["version_id"], actor_role="owner")
    status = await pool.fetchval(
        "SELECT status FROM public.report_versions WHERE id = $1", case["version_id"]
    )
    assert status == "APPROVED"
    assert (
        await pool.fetchval(
            "SELECT count(*)::int FROM public.report_version_artifacts WHERE report_version_id = $1",
            case["version_id"],
        )
        == 0
    )


async def test_finalisation_freezes_and_records_the_artefact(
    pool: asyncpg.Pool, case: dict
) -> None:
    """The frozen artefact is stored privately and recorded before FINAL (B4-D5/D6/D7)."""
    import hashlib

    from services.report_artefact_storage import InMemoryReportArtefactStorage

    payload = b"%PDF-1.7\nB4 runtime frozen artefact\n"
    storage = InMemoryReportArtefactStorage()
    service = _service(pool)
    await service.approve(report_version_id=case["version_id"], actor_role="owner")
    await _resolve_required(pool, case)

    result = await service.finalise(
        report_version_id=case["version_id"],
        actor_role="owner",
        pdf_producer=lambda: payload,
        storage=storage,
    )
    assert result["version_status"] == "FINAL"
    assert result["frozen_artefact"]["object_key"].endswith(f"{case['version_id']}.pdf")

    row = await pool.fetchrow(
        "SELECT organization_id, report_id, storage_bucket, object_key, content_sha256, "
        "byte_size, content_type FROM public.report_version_artifacts WHERE report_version_id = $1",
        case["version_id"],
    )
    assert row is not None, "the artefact record must exist for a finalised version"
    expected_key = f"{row['organization_id']}/{row['report_id']}/{case['version_id']}.pdf"
    assert row["object_key"] == expected_key, "the key must be the derived layout (B4-D6)"
    assert row["storage_bucket"] == "report-artifacts"
    assert row["content_type"] == "application/pdf"
    assert str(row["content_sha256"]).strip() == hashlib.sha256(payload).hexdigest()
    assert int(row["byte_size"]) == len(payload)
    assert list(storage.objects) == [expected_key]

    assert (
        await pool.fetchval(
            "SELECT count(*)::int FROM public.report_version_artifacts WHERE report_version_id = $1",
            case["version_id"],
        )
        == 1
    )

    # A frozen artefact is never rewritten: a changed render is refused.
    with pytest.raises(DisclosureViolation):
        await service.finalise(
            report_version_id=case["version_id"],
            actor_role="owner",
            pdf_producer=lambda: payload + b"tampered",
            storage=storage,
        )


async def test_artefact_table_is_append_only(pool: asyncpg.Pool) -> None:
    """B4-D7: the frozen record is append-only for authenticated callers."""
    await _require_b4_schema(pool)
    for privilege in ("UPDATE", "DELETE"):
        allowed = await pool.fetchval(
            "SELECT has_table_privilege('authenticated', 'public.report_version_artifacts', $1)",
            privilege,
        )
        assert allowed is False, f"authenticated must not hold {privilege} on the frozen record"
    assert (
        await pool.fetchval(
            "SELECT has_table_privilege('authenticated', 'public.report_version_artifacts', 'INSERT')"
        )
        is True
    )
    assert (
        await pool.fetchval(
            "SELECT has_table_privilege('anon', 'public.report_version_artifacts', 'SELECT')"
        )
        is False
    )


async def test_signed_url_requires_a_frozen_artefact(pool: asyncpg.Pool, case: dict) -> None:
    """A draft version is never served from the frozen bucket (A15)."""
    from services.report_artefact_storage import InMemoryReportArtefactStorage

    with pytest.raises(DisclosureViolation):
        await _service(pool).artefact_download_url(
            report_version_id=case["version_id"], storage=InMemoryReportArtefactStorage()
        )



async def _freeze_case(pool: asyncpg.Pool, case: dict, payload: bytes):
    """Approve, resolve, finalise and return (service, storage) for follow-up checks."""
    from services.report_artefact_storage import InMemoryReportArtefactStorage

    service = _service(pool)
    storage = InMemoryReportArtefactStorage()
    await service.approve(report_version_id=case["version_id"], actor_role="owner")
    await _resolve_required(pool, case)
    await service.finalise(
        report_version_id=case["version_id"],
        actor_role="owner",
        pdf_producer=lambda: payload,
        storage=storage,
    )
    return service, storage


async def test_signed_url_is_audited_without_recording_the_url(
    pool: asyncpg.Pool, case: dict
) -> None:
    """B4-D11: download issuance is auditable; the signed URL itself is never stored."""
    service, storage = await _freeze_case(pool, case, b"%PDF-1.7\naudit probe\n")
    result = await service.artefact_download_url(
        report_version_id=case["version_id"], storage=storage
    )
    assert result["signed_url"]

    rows = await pool.fetch(
        "SELECT action_type, new_data FROM public.audit_trail "
        "WHERE table_name = 'report_version_artifacts' AND action_type = $1 "
        "ORDER BY performed_at DESC",
        "frozen_artefact.signed_url_issued",
    )
    assert rows, "the signed-URL issuance must be audited"
    payload = str(rows[0]["new_data"])
    assert result["object_key"] in payload, "the audit must record which object was served"
    assert result["signed_url"] not in payload, "a signed URL must never enter the audit trail"


async def test_staleness_is_reported_and_never_auto_invalidates(
    pool: asyncpg.Pool, case: dict
) -> None:
    """B4-D11: staleness is surfaced; the finalised version is never invalidated."""
    service, _ = await _freeze_case(pool, case, b"%PDF-1.7\nstaleness probe\n")

    fresh = await service.artefact_status(report_version_id=case["version_id"])
    assert fresh["frozen"] is True
    assert fresh["stale"] is False
    assert fresh["data_as_of"] is not None
    assert "never auto-invalidated" in fresh["staleness_action"]

    # Simulate later data movement inside this version's value set.
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.disclosure_values SET updated_at = now() + interval '1 hour' "
            "WHERE report_version_id = $1",
            case["version_id"],
        )

    stale = await service.artefact_status(report_version_id=case["version_id"])
    assert stale["stale"] is True, "a value changed after the artefact was produced"
    status = await pool.fetchval(
        "SELECT status FROM public.report_versions WHERE id = $1", case["version_id"]
    )
    assert status == "FINAL", "staleness must never auto-invalidate a finalised version"


async def test_frozen_artefact_survives_a_new_version(pool: asyncpg.Pool, case: dict) -> None:
    """B4-D2/D15: corrections create a NEW version; the frozen artefact is untouched."""
    import hashlib

    payload = b"%PDF-1.7\ncorrection baseline\n"
    await _freeze_case(pool, case, payload)
    before = await pool.fetchrow(
        "SELECT id, object_key, content_sha256, produced_at FROM public.report_version_artifacts "
        "WHERE report_version_id = $1",
        case["version_id"],
    )
    assert before is not None

    async with pool.acquire() as conn:
        new_version = await conn.fetchval(
            "INSERT INTO public.report_versions (report_id, version_number, status) "
            "VALUES ($1, 2, 'DRAFT') RETURNING id",
            case["report_id"],
        )

    after = await pool.fetchrow(
        "SELECT id, object_key, content_sha256, produced_at FROM public.report_version_artifacts "
        "WHERE report_version_id = $1",
        case["version_id"],
    )
    assert dict(after) == dict(before), "the frozen artefact of the FINAL version is immutable"
    assert str(after["content_sha256"]).strip() == hashlib.sha256(payload).hexdigest()
    assert (
        await pool.fetchval(
            "SELECT count(*)::int FROM public.report_version_artifacts WHERE report_version_id = $1",
            new_version,
        )
        == 0
    ), "a new draft version starts with no artefact"



async def test_all_b4_writes_are_audited(pool: asyncpg.Pool, case: dict) -> None:
    """A10: narrative write, approval and finalisation each leave an audit entry."""
    from services.disclosure_narrative import DisclosureNarrativeService

    narrative = DisclosureNarrativeService(pool)
    await narrative.write_narrative(
        report_version_id=case["version_id"],
        requirement_version_id=case["req_required"],
        narrative_kind="CUSTOMER_COMMENTARY",
        body="Audited narrative (runtime).",
        actor_role="owner",
    )
    await _freeze_case(pool, case, b"%PDF-1.7\naudited artefact\n")

    actions = {
        row["action_type"]
        for row in await pool.fetch(
            "SELECT action_type FROM public.audit_trail "
            "WHERE record_id = ANY($1::uuid[]) "
            "   OR (table_name = 'disclosure_narrative_entries' "
            "       AND new_data ->> 'report_version_id' = $2) "
            "   OR (table_name = 'report_version_artifacts' "
            "       AND new_data ->> 'object_key' LIKE $3)",
            [
                case["version_id"],
                case["req_required"],
            ],
            case["version_id"],
            f"%{case['version_id']}.pdf",
        )
    }
    for expected in (
        "disclosure_narrative.written",
        "report_version.approved",
        "report_version.finalised",
        "frozen_artefact.created",
    ):
        assert expected in actions, f"{expected} was not audited"

    # A10: no secret material in any B4 audit payload.
    payloads = await pool.fetch(
        "SELECT new_data::text AS payload FROM public.audit_trail "
        "WHERE table_name IN ('report_versions', 'report_version_artifacts', "
        "'disclosure_narrative_entries')"
    )
    for row in payloads:
        assert "http" not in (row["payload"] or ""), "no URL may enter the audit trail"
