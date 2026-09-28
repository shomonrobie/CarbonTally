"""CT-IMPLEMENT-03 — canonical schedule/share E2E against a DISPOSABLE database.

This module drives the **real HTTP routes** (canonical ``/api/v3/reports`` and the
legacy ``/api/reports`` compat surface), the **real services**, the **real
repositories** and the **real runner/producer/report engine** against a real
PostgreSQL built from the canonical migration chain. Nothing here is mocked: the
only substitutions are the authenticated actor and the pool (both injected the way
production injects them).

TARGET SAFETY (PO operational control F-046-1)
---------------------------------------------
* The target is supplied by ``INTEGRATION_DATABASE_URL`` and must be a
  **disposable clone** — the shared ``pool`` fixture refuses the known main
  databases and any name matching ``qa``/``demo``/``investor``/``prod``/``live``,
  because it performs DESTRUCTIVE setup (``TRUNCATE … RESTART IDENTITY CASCADE``).
* This module therefore creates its own organisation/user rows and deletes only
  those at the end (an organisation delete cascades to everything it created).
* Run it ON ITS OWN in a fresh process, because the service pool is process-wide
  and its ``DATABASE_URL`` is fixed at first use::

      INTEGRATION_DATABASE_URL=postgresql://…@127.0.0.1:55481/ct_impl03_e2e \\
        python -m pytest tests/integration/test_ct03_report_schedule_share_canonical.py
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import urlparse

import asyncpg
import httpx
import pytest
from fastapi import FastAPI

from api.dependencies import (
    build_report_engine,
    get_audit_logger,
    get_current_user,
    get_event_bus,
    get_pool,
    get_repositories,
)
from auth import AuthUser
from data.report_schedules import ReportSchedulesRepository
from services.report_schedule_producer import CanonicalReportProducer
from services.report_schedule_runner import ReportScheduleRunner
from services.report_schedules import build_audit_sink
from tests.integration.conftest import make_org, make_user

pytestmark = pytest.mark.asyncio

CANONICAL = "/api/v3/reports"
LEGACY = "/api/reports"

#: Database names that are OFF-LIMITS to this suite (the F-046-1 discipline).
_FORBIDDEN_DATABASE_NAMES = ("postgres", "supabase_db_carbon_ledger")
_PROTECTED_MARKERS = ("qa", "demo", "investor", "prod", "live")

#: Rows this module created, deleted in teardown (nothing else is touched).
_CREATED_ORGS: list[str] = []
_CREATED_USERS: list[str] = []


@pytest.fixture(scope="module")
async def pool():
    """A NON-destructive pool to the disposable clone.

    This deliberately **overrides** the shared ``tests/integration/conftest.py``
    ``pool`` fixture: that fixture performs destructive setup
    (``TRUNCATE … RESTART IDENTITY CASCADE``) which the canonical schema's
    append-only audit guard now refuses — evidence recorded in the CT-IMPLEMENT-03
    report §18.4. This module therefore creates only the rows it needs (one
    organisation and two users per test) and deletes exactly those afterwards, so
    it is safe *and* it needs no guard exception anywhere.

    The target must be a disposable clone: ``INTEGRATION_DATABASE_URL`` must name a
    ``ct_*`` database, never a known main database and never a name matching the
    protected persistent markers.
    """
    url = os.getenv("INTEGRATION_DATABASE_URL")
    if not url:
        pytest.skip(
            "INTEGRATION_DATABASE_URL is not set; this suite requires a disposable "
            "canonical-schema clone"
        )
    name = urlparse(url).path.lstrip("/")
    if name in _FORBIDDEN_DATABASE_NAMES:
        raise RuntimeError(
            f"refusing to run the CT-IMPLEMENT-03 E2E suite against {name!r}: it is a "
            "main application database. Point INTEGRATION_DATABASE_URL at a "
            "disposable clone (ct_*)."
        )
    marker = next((m for m in _PROTECTED_MARKERS if m in name.lower()), None)
    if marker is not None:
        raise RuntimeError(
            f"refusing to run the CT-IMPLEMENT-03 E2E suite against {name!r}: the name "
            f"matches the protected persistent marker {marker!r} (PO control F-046-1)."
        )
    if not name.startswith("ct_"):
        raise RuntimeError(
            f"refusing to run the CT-IMPLEMENT-03 E2E suite against {name!r}: only a "
            "disposable clone (ct_*) is acceptable."
        )

    created = await asyncpg.create_pool(dsn=url, min_size=1, max_size=4)
    try:
        async with created.acquire() as conn:
            database = await conn.fetchval("SELECT current_database()")
            assert database == name
            has_schema = await conn.fetchval(
                "SELECT to_regclass('public.organizations') IS NOT NULL"
            )
        if not has_schema:
            pytest.skip(
                f"{name!r} has no canonical schema; build it with "
                "e2e/environment/scripts/canonical_schema_rebuild.sh first"
            )
        yield created
    finally:
        await created.close()


@pytest.fixture
async def actor_org(pool):
    """A fresh organisation plus an owner and a plain member in it."""
    org = await make_org(pool, name="CT-IMPLEMENT-03 E2E")
    owner_id = await make_user(pool)
    member_id = await make_user(pool)
    _CREATED_ORGS.append(org)
    _CREATED_USERS.extend([owner_id, member_id])
    yield SimpleNamespace(org=org, owner_id=owner_id, member_id=member_id)
    await _purge(pool)


async def _purge(pool) -> None:
    """Delete only the rows this module created; refusals are expected and noted.

    The canonical schema deliberately refuses two of these deletions:

    * ``report_share_access_events`` is append-only, so deleting its parent share
      (``ON DELETE CASCADE``) is refused;
    * ``report_schedule_runs`` is append-only, so deleting a schedule that has
      executed (``ON DELETE CASCADE``) is refused — and therefore so is deleting
      the organisation that owns it.

    Both refusals are the schema working as designed (CT-IMPLEMENT-02 hardening).
    Rather than disguising them, this teardown records what it could not remove:
    the target is a disposable clone that is discarded after the run, and nothing
    outside this module was touched.
    """
    leftover: list[str] = []
    statements = (
        (
            "report_shares",
            "DELETE FROM public.report_shares WHERE organization_id = $1",
        ),
        (
            "report_schedule_definitions",
            "DELETE FROM public.report_schedule_definitions"
            " WHERE organization_id = $1",
        ),
        (
            "report_versions",
            "DELETE FROM public.report_versions WHERE report_id IN"
            " (SELECT id FROM public.report_generation_queue"
            "  WHERE organization_id = $1)",
        ),
        (
            "report_generation_queue",
            "DELETE FROM public.report_generation_queue WHERE organization_id = $1",
        ),
        ("organizations", "DELETE FROM public.organizations WHERE id = $1"),
    )
    async with pool.acquire() as conn:
        for org in _CREATED_ORGS:
            for label, statement in statements:
                try:
                    await conn.execute(statement, org)
                except Exception as exc:  # noqa: BLE001 - by-design guard refusal
                    leftover.append(f"{label} ({type(exc).__name__})")
        for user in _CREATED_USERS:
            try:
                await conn.execute("DELETE FROM public.users WHERE id = $1", user)
            except Exception as exc:  # noqa: BLE001
                leftover.append(f"users ({type(exc).__name__})")
    if leftover:
        print(
            "CT-IMPLEMENT-03 E2E teardown — rows retained by the canonical guards "
            f"(disposable clone): {sorted(set(leftover))}"
        )
    _CREATED_ORGS.clear()
    _CREATED_USERS.clear()


def user_for(org: str, user_id: str, *, role: str = "owner") -> AuthUser:
    """An authenticated actor with the given organisation role."""
    return AuthUser(
        user_id=user_id,
        email=f"{role}-{user_id[:8]}@ct03.test",
        role=f"org_{role}",
        role_name=role,
        organization_id=org,
        is_org_member=True,
    )


def app_for(pool, user: AuthUser, *, legacy: bool = False) -> FastAPI:
    """The real routers over the real pool, with a fixed authenticated actor."""
    from api.v3_reports import router as v3_reports_router
    from routes.reports import router as legacy_reports_router

    app = FastAPI()
    app.include_router(v3_reports_router)
    if legacy:
        # The legacy compat surface is mounted in main.py, not in api.router; it is
        # included here so its delegation is exercised over real HTTP too.
        app.include_router(legacy_reports_router)

    async def _pool():
        return pool

    app.dependency_overrides[get_pool] = _pool
    app.dependency_overrides[get_current_user] = lambda: user
    return app


def client_for(pool, user: AuthUser, *, legacy: bool = False) -> httpx.AsyncClient:
    """An in-loop client for the real ASGI app (same loop as the asyncpg pool)."""
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_for(pool, user, legacy=legacy)),
        base_url="http://ct03.test",
    )


def schedule_payload(org: str, **overrides) -> dict:
    payload = {
        "organization_id": org,
        "name": "Quarterly pack",
        "report_type": "annual",
        "reporting_year": 2025,
        "frequency": "quarterly",
        "run_time": "07:00",
        "timezone": "Europe/London",
        "recipients": ["owner@example.com"],
    }
    payload.update(overrides)
    return payload


async def seed_immutable_report(pool, org: str, *, status: str = "APPROVED") -> dict:
    """A real report (``report_generation_queue``) with one version in ``status``."""
    repos = await get_repositories()
    report = await repos.reports.create_generation_request(
        org, "annual", 2025, None, created_by=None, report_name="CT03 seeded report"
    )
    version = await repos.report_versions.create(
        report_id=report.id,
        version_number=1,
        content={"page_count": 1},
        file_url="storage://seeded.json",
        created_by=None,
        change_summary="CT-IMPLEMENT-03 E2E fixture",
        is_current=True,
        status=status,
    )
    return {"report_id": report.id, "version": version}


# ---------------------------------------------------------------------------
# Target preconditions (the canonical schema, and the retired tables absent)
# ---------------------------------------------------------------------------
async def test_the_target_is_a_disposable_clone_with_the_canonical_schema(pool):
    async with pool.acquire() as conn:
        database = await conn.fetchval("SELECT current_database()")
        assert database.startswith("ct_"), (
            f"{database!r} is not a disposable clone; this suite must never run "
            "against a persistent environment (F-046-1)"
        )
        for table in (
            "report_schedule_definitions",
            "report_schedule_runs",
            "report_shares",
            "report_share_access_events",
            "report_generation_queue",
            "report_versions",
            "audit_trail",
        ):
            exists = await conn.fetchval(
                "SELECT to_regclass($1) IS NOT NULL", f"public.{table}"
            )
            assert exists, f"{table} is missing from the canonical schema"
        for retired in ("report_schedules", "report_history"):
            exists = await conn.fetchval(
                "SELECT to_regclass($1) IS NOT NULL", f"public.{retired}"
            )
            assert not exists, (
                f"{retired} exists in this target — the canonical schema must not "
                "contain it (PD-1/PD-2)"
            )


# ---------------------------------------------------------------------------
# Canonical schedule surface over real HTTP
# ---------------------------------------------------------------------------
async def test_frequency_api_matches_the_canonical_vocabulary(pool, actor_org):
    async with client_for(pool, user_for(actor_org.org, actor_org.owner_id)) as client:
        response = await client.get(f"{CANONICAL}/schedules/frequencies")

    assert response.status_code == 200
    assert [item["value"] for item in response.json()["frequencies"]] == [
        "weekly",
        "monthly",
        "quarterly",
        "annual",
    ]


async def test_schedule_create_read_pause_resume_delete_persist_canonically(
    pool, actor_org
):
    user = user_for(actor_org.org, actor_org.owner_id)
    async with client_for(pool, user) as client:
        created = await client.post(
            f"{CANONICAL}/schedules", json=schedule_payload(actor_org.org)
        )
        assert created.status_code == 201, created.text
        schedule_id = created.json()["schedule"]["id"]
        assert created.json()["schedule"]["frequency"] == "quarterly"

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT frequency, timezone, report_type, reporting_year, recipients,"
                " next_run_at, is_active, created_by, run_time"
                " FROM public.report_schedule_definitions WHERE id = $1",
                schedule_id,
            )
            audit = await conn.fetchrow(
                "SELECT record_id, table_name, action_type FROM public.audit_trail"
                " WHERE record_id = $1",
                schedule_id,
            )
        assert row is not None, "the schedule was not persisted to the canonical table"
        assert row["frequency"] == "quarterly"
        assert row["timezone"] == "Europe/London"
        assert row["report_type"] == "annual"
        assert row["reporting_year"] == 2025
        assert row["is_active"] is True
        assert str(row["run_time"]) == "07:00:00"
        assert row["next_run_at"] is not None
        assert str(row["created_by"]) == actor_org.owner_id
        assert json.loads(row["recipients"]) == [
            {"user_id": None, "email": "owner@example.com"}
        ]
        assert audit is not None and str(audit["record_id"]) == schedule_id

        listed = await client.get(
            f"{CANONICAL}/schedules", params={"organization_id": actor_org.org}
        )
        assert listed.status_code == 200
        listed_ids = [item["id"] for item in listed.json()["schedules"]]
        assert schedule_id in listed_ids
        assert listed.json()["total"] >= 1

        detail = await client.get(
            f"{CANONICAL}/schedules/{schedule_id}",
            params={"organization_id": actor_org.org},
        )
        assert detail.status_code == 200
        assert detail.json()["schedule"]["id"] == schedule_id
        assert detail.json()["runs"] == []

        paused = await client.post(
            f"{CANONICAL}/schedules/{schedule_id}/pause",
            params={"organization_id": actor_org.org},
        )
        assert paused.status_code == 200
        assert paused.json()["schedule"]["is_active"] is False
        assert paused.json()["schedule"]["paused_at"] is not None

        resumed = await client.post(
            f"{CANONICAL}/schedules/{schedule_id}/resume",
            params={"organization_id": actor_org.org},
        )
        assert resumed.status_code == 200
        assert resumed.json()["schedule"]["is_active"] is True
        assert resumed.json()["schedule"]["paused_at"] is None

        deleted = await client.delete(
            f"{CANONICAL}/schedules/{schedule_id}",
            params={"organization_id": actor_org.org},
        )
        assert deleted.status_code == 200
        assert deleted.json() == {"schedule_id": schedule_id, "deleted": True}

        again = await client.delete(
            f"{CANONICAL}/schedules/{schedule_id}",
            params={"organization_id": actor_org.org},
        )
        assert again.status_code == 404

    async with pool.acquire() as conn:
        gone = await conn.fetchval(
            "SELECT id FROM public.report_schedule_definitions WHERE id = $1",
            schedule_id,
        )
    assert gone is None


async def test_schedule_validation_and_authority_are_enforced_over_http(
    pool, actor_org
):
    owner = user_for(actor_org.org, actor_org.owner_id)
    member = user_for(actor_org.org, actor_org.member_id, role="member")

    async with client_for(pool, owner) as client:
        daily = await client.post(
            f"{CANONICAL}/schedules",
            json=schedule_payload(actor_org.org, frequency="daily"),
        )
        assert daily.status_code == 422, daily.text
        assert "not a canonical frequency" in str(daily.json()["detail"])

        wrong_type = await client.post(
            f"{CANONICAL}/schedules",
            json=schedule_payload(actor_org.org, report_type="summary"),
        )
        assert wrong_type.status_code == 422

        no_recipients = await client.post(
            f"{CANONICAL}/schedules",
            json=schedule_payload(actor_org.org, recipients=[]),
        )
        assert no_recipients.status_code == 422

        unknown_timezone = await client.post(
            f"{CANONICAL}/schedules",
            json=schedule_payload(actor_org.org, timezone="Europe/Nowhere"),
        )
        assert unknown_timezone.status_code == 422

    async with pool.acquire() as conn:
        rows = await conn.fetchval(
            "SELECT count(*) FROM public.report_schedule_definitions"
            " WHERE organization_id = $1",
            actor_org.org,
        )
    assert rows == 0, "no invalid request may be persisted"

    async with client_for(pool, member) as client:
        forbidden = await client.post(
            f"{CANONICAL}/schedules", json=schedule_payload(actor_org.org)
        )
        assert forbidden.status_code == 403
        allowed = await client.get(
            f"{CANONICAL}/schedules", params={"organization_id": actor_org.org}
        )
        assert allowed.status_code == 200

    outsider = user_for("00000000-0000-0000-0000-000000000000", actor_org.owner_id)
    async with client_for(pool, outsider) as client:
        denied = await client.get(
            f"{CANONICAL}/schedules", params={"organization_id": actor_org.org}
        )
        assert denied.status_code == 403


# ---------------------------------------------------------------------------
# The runner: due selection, real execution, idempotency, linkage, audit
# ---------------------------------------------------------------------------
async def _runner(pool) -> ReportScheduleRunner:
    repos = await get_repositories()
    engine = build_report_engine(
        repos, event_bus=await get_event_bus(), audit_logger=await get_audit_logger()
    )
    return ReportScheduleRunner(
        ReportSchedulesRepository(pool),
        produce=CanonicalReportProducer(repos, engine),
        audit_sink=build_audit_sink(repos),
    )


async def test_the_runner_executes_a_due_schedule_and_records_real_artefacts(
    pool, actor_org
):
    async with client_for(pool, user_for(actor_org.org, actor_org.owner_id)) as client:
        created = await client.post(
            f"{CANONICAL}/schedules",
            json=schedule_payload(actor_org.org, frequency="monthly"),
        )
    assert created.status_code == 201, created.text
    schedule_id = created.json()["schedule"]["id"]

    # Due-ness is PERSISTED, never inferred: move the slot into the past in the
    # table and let the runner select it from there.
    due = datetime.now(timezone.utc) - timedelta(minutes=5)
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.report_schedule_definitions SET next_run_at = $2"
            " WHERE id = $1",
            schedule_id,
            due,
        )

    tick = await (await _runner(pool)).run_due(now=datetime.now(timezone.utc))

    assert tick.due >= 1
    assert tick.succeeded == 1, [o.detail for o in tick.outcomes]
    assert tick.failed == 0

    async with pool.acquire() as conn:
        run = await conn.fetchrow(
            "SELECT status, attempt, report_id, report_version_id, scheduled_for,"
            " finished_at FROM public.report_schedule_runs"
            " WHERE schedule_id = $1 ORDER BY scheduled_for DESC LIMIT 1",
            schedule_id,
        )
        assert run is not None, "the runner recorded no run"
        assert run["status"] == "succeeded"
        assert run["attempt"] == 1
        assert run["finished_at"] is not None
        assert run["scheduled_for"] == due
        assert run["report_id"] is not None
        assert run["report_version_id"] is not None

        queue = await conn.fetchrow(
            "SELECT generated_content FROM public.report_generation_queue"
            " WHERE id = $1",
            run["report_id"],
        )
        assert queue is not None and queue["generated_content"] is not None

        version = await conn.fetchrow(
            "SELECT report_id, version_number, is_current"
            " FROM public.report_versions WHERE id = $1",
            run["report_version_id"],
        )
        assert version is not None
        assert version["report_id"] == run["report_id"]
        assert version["is_current"] is True

        schedule = await conn.fetchrow(
            "SELECT next_run_at, last_result, failure_count, is_active"
            " FROM public.report_schedule_definitions WHERE id = $1",
            schedule_id,
        )
        assert schedule["last_result"] == "succeeded"
        assert schedule["failure_count"] == 0
        assert schedule["is_active"] is True
        assert schedule["next_run_at"] > due

        audited = await conn.fetchval(
            "SELECT count(*) FROM public.audit_trail WHERE record_id = $1"
            " AND action_type = 'report_schedule_run_succeeded'",
            schedule_id,
        )
    assert audited == 1, (
        "every run outcome must be audited with correlation_id = schedule id"
    )


async def test_a_repeated_tick_cannot_create_a_second_run_or_report(pool, actor_org):
    async with client_for(pool, user_for(actor_org.org, actor_org.owner_id)) as client:
        created = await client.post(
            f"{CANONICAL}/schedules",
            json=schedule_payload(actor_org.org, name="Idempotency probe"),
        )
    schedule_id = created.json()["schedule"]["id"]

    due = datetime.now(timezone.utc) - timedelta(minutes=5)
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.report_schedule_definitions SET next_run_at = $2"
            " WHERE id = $1",
            schedule_id,
            due,
        )

    runner = await _runner(pool)
    now = datetime.now(timezone.utc)
    first = await runner.run_due(now=now)
    assert first.succeeded == 1

    # Rewind to the SAME due slot: the UNIQUE (schedule_id, scheduled_for) key must
    # refuse the second claim instead of producing a second report.
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE public.report_schedule_definitions"
            " SET next_run_at = $2, is_active = TRUE, paused_at = NULL WHERE id = $1",
            schedule_id,
            due,
        )
    second = await runner.run_due(now=now)

    assert second.duplicate_slots == 1
    assert second.executed == 0

    async with pool.acquire() as conn:
        runs = await conn.fetchval(
            "SELECT count(*) FROM public.report_schedule_runs WHERE schedule_id = $1",
            schedule_id,
        )
        reports = await conn.fetchval(
            "SELECT count(*) FROM public.report_generation_queue"
            " WHERE organization_id = $1 AND report_name LIKE 'Idempotency probe%'",
            actor_org.org,
        )
    assert runs == 1, "one due slot has exactly one run row"
    assert reports == 1, "a repeated tick must not produce a second report"

    # A schedule that has EXECUTED cannot be deleted: its run history is immutable
    # (the schema refuses DELETE on runs, so the definition's cascade would breach
    # it). The refusal is a described 409, never a raw database error.
    async with client_for(pool, user_for(actor_org.org, actor_org.owner_id)) as client:
        refused = await client.delete(
            f"{CANONICAL}/schedules/{schedule_id}",
            params={"organization_id": actor_org.org},
        )
    assert refused.status_code == 409, refused.text
    assert "pause it" in str(refused.json()["detail"])
    async with pool.acquire() as conn:
        survivor = await conn.fetchval(
            "SELECT id FROM public.report_schedule_definitions WHERE id = $1",
            schedule_id,
        )
    assert survivor is not None, "the schedule must survive the refusal"


# ---------------------------------------------------------------------------
# Canonical report sharing over real HTTP
# ---------------------------------------------------------------------------
async def test_sharing_and_revoking_persist_the_canonical_share_register(
    pool, actor_org
):
    seeded = await seed_immutable_report(pool, actor_org.org)
    report_id = seeded["report_id"]
    version_id = seeded["version"]["id"]
    owner = user_for(actor_org.org, actor_org.owner_id)

    async with client_for(pool, owner) as client:
        created = await client.post(
            f"{CANONICAL}/{report_id}/shares",
            json={
                "organization_id": actor_org.org,
                "recipients": ["Reader@Example.com"],
                "permission": "download",
            },
        )
        assert created.status_code == 201, created.text
        share = created.json()["shared"][0]
        share_id = share["id"]
        assert share["report_version_id"] == version_id
        assert share["recipient_email"] == "reader@example.com"
        assert share["permission"] == "download"

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT organization_id, report_id, report_version_id, permission,"
                " recipient_email, revoked_at FROM public.report_shares WHERE id = $1",
                share_id,
            )
            events = await conn.fetch(
                "SELECT event_type FROM public.report_share_access_events"
                " WHERE share_id = $1 ORDER BY occurred_at",
                share_id,
            )
            audit = await conn.fetchval(
                "SELECT count(*) FROM public.audit_trail"
                " WHERE action_type = 'report_share_created' AND record_id = $1",
                share_id,
            )
        assert row is not None, "the share was not persisted to the canonical table"
        assert str(row["report_version_id"]) == version_id
        assert str(row["report_id"]) == report_id
        assert row["permission"] == "download"
        assert row["recipient_email"] == "reader@example.com"
        assert row["revoked_at"] is None
        assert [e["event_type"] for e in events] == ["created"]
        assert audit == 1

        listed = await client.get(
            f"{CANONICAL}/{report_id}/shares",
            params={"organization_id": actor_org.org},
        )
        assert listed.status_code == 200
        assert [s["id"] for s in listed.json()["shares"]] == [share_id]

        history = await client.get(
            f"{CANONICAL}/shares/{share_id}/access-history",
            params={"organization_id": actor_org.org},
        )
        assert history.status_code == 200
        assert [e["event_type"] for e in history.json()["events"]] == ["created"]

        revoked = await client.post(
            f"{CANONICAL}/shares/{share_id}/revoke",
            json={"organization_id": actor_org.org, "reason": "role changed"},
        )
        assert revoked.status_code == 200, revoked.text
        assert revoked.json()["share"]["is_active"] is False
        assert revoked.json()["share"]["revocation_reason"] == "role changed"

        history = await client.get(
            f"{CANONICAL}/shares/{share_id}/access-history",
            params={"organization_id": actor_org.org},
        )
        assert [e["event_type"] for e in history.json()["events"]] == [
            "revoked",
            "created",
        ]

        # Revocation is one-way: a second attempt preserves the first reason.
        again = await client.post(
            f"{CANONICAL}/shares/{share_id}/revoke",
            json={"organization_id": actor_org.org, "reason": "second reason"},
        )
        assert again.json()["share"]["revocation_reason"] == "role changed"


async def test_sharing_a_mutable_version_is_refused_and_persists_nothing(
    pool, actor_org
):
    seeded = await seed_immutable_report(pool, actor_org.org, status="DRAFT")
    owner = user_for(actor_org.org, actor_org.owner_id)

    async with client_for(pool, owner) as client:
        refused = await client.post(
            f"{CANONICAL}/{seeded['report_id']}/shares",
            json={
                "organization_id": actor_org.org,
                "recipients": ["reader@example.com"],
            },
        )

    assert refused.status_code == 409, refused.text
    assert "immutable" in str(refused.json()["detail"])
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM public.report_shares WHERE organization_id = $1",
            actor_org.org,
        )
    assert count == 0


# ---------------------------------------------------------------------------
# Legacy compat surface: the same implementation, canonical persistence
# ---------------------------------------------------------------------------
async def test_legacy_schedule_surface_delegates_and_persists_canonically(
    pool, actor_org
):
    owner = user_for(actor_org.org, actor_org.owner_id)
    async with client_for(pool, owner, legacy=True) as client:
        frequencies = await client.get(f"{LEGACY}/schedule/frequencies")
        assert frequencies.status_code == 200
        assert [item["value"] for item in frequencies.json()["frequencies"]] == [
            "weekly",
            "monthly",
            "quarterly",
            "annual",
        ]
        assert frequencies.headers.get("deprecation") == "true"

        created = await client.post(
            f"{LEGACY}/schedule",
            json={
                "name": "Legacy compat pack",
                "report_type": "annual",
                "reporting_year": 2025,
                "frequency": "annual",
                "run_time": "06:30",
                "recipients": ["owner@example.com"],
            },
        )
        assert created.status_code == 200, created.text
        schedule_id = created.json()["schedule"]["id"]

        listed = await client.get(f"{LEGACY}/schedule")
        assert listed.status_code == 200
        assert schedule_id in [item["id"] for item in listed.json()["schedules"]]

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT organization_id, created_by, frequency, next_run_at"
            " FROM public.report_schedule_definitions WHERE id = $1",
            schedule_id,
        )
    assert row is not None, "the legacy path must persist to the canonical table"
    assert str(row["organization_id"]) == actor_org.org
    assert str(row["created_by"]) == actor_org.owner_id
    assert row["frequency"] == "annual"
    assert row["next_run_at"] is not None

    async with client_for(pool, owner, legacy=True) as client:
        deleted = await client.delete(f"{LEGACY}/schedule/{schedule_id}")
        assert deleted.status_code == 200
        assert deleted.json()["success"] is True
    async with pool.acquire() as conn:
        assert (
            await conn.fetchval(
                "SELECT id FROM public.report_schedule_definitions WHERE id = $1",
                schedule_id,
            )
            is None
        )


async def test_legacy_share_surface_is_version_bound_and_canonical(pool, actor_org):
    seeded = await seed_immutable_report(pool, actor_org.org)
    owner = user_for(actor_org.org, actor_org.owner_id)

    async with client_for(pool, owner, legacy=True) as client:
        shared = await client.post(
            f"{LEGACY}/{seeded['report_id']}/share",
            json={"shared_with": [owner.email], "permission": "view"},
        )
        assert shared.status_code == 200, shared.text
        share_id = shared.json()["shared_with"][0]

        received = await client.get(f"{LEGACY}/shared")
        assert received.status_code == 200
        assert share_id in [item["id"] for item in received.json()["shares"]]

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT report_version_id, recipient_email FROM public.report_shares"
            " WHERE id = $1",
            share_id,
        )
    assert row is not None, "the legacy share must persist to the canonical table"
    assert str(row["report_version_id"]) == seeded["version"]["id"]
    assert row["recipient_email"] == owner.email

    member = user_for(actor_org.org, actor_org.member_id, role="member")
    async with client_for(pool, member, legacy=True) as client:
        denied = await client.post(
            f"{LEGACY}/{seeded['report_id']}/share",
            json={"shared_with": ["x@example.com"]},
        )
        assert denied.status_code == 403
