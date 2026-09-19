"""F-039-1 remediation (CT-STEP2-F039-1-REMEDIATION-065) — REAL-schema lifecycle.

The 055 schema enforces "exactly one current version per adjudication lineage" with a
PARTIAL UNIQUE INDEX (``activity_clarifications_current_unique`` on
``(adjudication_id) WHERE is_current``). A partial index cannot be deferred, so a
modification must retire the previous version BEFORE inserting the new current row, in
ONE transaction. The pre-remediation implementation inserted first and retired second,
so version 2 could NEVER be created (``UniqueViolationError``); every pre-existing
F-039-1 persistence test used a scripted fake connection and therefore never touched
the real constraint.

These tests run against the DEDICATED disposable database (``ct_f0391_065`` by default,
or whatever ``INTEGRATION_DATABASE_URL`` names) through the repository's real pool, the
real router and the real authorization gate. The session fixture truncates the target,
which is why the target must be disposable (F-046-1).

    INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_f0391_065 \
        python -m pytest tests/integration/test_f039_1_adjudication_lifecycle_runtime.py
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import httpx
import pytest
from fastapi import FastAPI, HTTPException

from api.dependencies import get_matching_engine, get_repositories
from api.v3_activity_clarifications import router
from auth import AuthUser, get_current_user
from data.activity_clarifications import ActivityClarificationsRepository
from domain.factor import EmissionFactor
from domain.matching import MatchingPipelineConfig
from engines.activity_clarification import decline_clarification, resolve_clarification
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from infra.search_index import FactorSearchIndex

EFFECTIVE = "/api/v3/activity-clarifications/effective"
HISTORY = "/api/v3/activity-clarifications/history"
CLARIFY = "/api/v3/activity-clarifications/clarifications"

#: The 041/039 treatment-vs-combustion collision window (bare "Waste").
_WASTE_WINDOW = (
    ("Waste disposal > Construction > Aggregates - Landfill (kg CO2e)", "tonnes", "Scope 3",
     "1.26338", "lf"),
    ("Waste disposal > Construction > Aggregates - Open-loop (kg CO2e)", "tonnes", "Scope 3",
     "1.00835", "ol"),
    ("Waste disposal > Construction - Incineration with Energy Recovery (kg CO2e)", "tonnes",
     "Scope 3", "0.02106", "inc"),
    ("Fuels > Liquid fuels > Waste oils (kg CO2e)", "tonnes", "Scope 1", "3219.37916",
     "oils"),
)

#: Stable UUID identities for the seeded factors: ``selected_factor_id`` is a uuid FK in
#: the shipped schema, so the row the engine selects must exist in ``emission_factors``
#: under exactly that id.
_FACTOR_UUID = {
    key: str(uuid.uuid5(uuid.NAMESPACE_DNS, f"f0391-065:{key}"))
    for _name, _unit, _scope, _value, key in _WASTE_WINDOW
}


async def _new_org(pool) -> str:
    """An isolated organisation for one test (the fixture truncated the tables)."""
    async with pool.acquire() as conn:
        return str(await conn.fetchval(
            "INSERT INTO public.organizations (name) VALUES ($1) RETURNING id",
            f"F0391-065 {uuid.uuid4()}"))


async def _new_item(pool, org: str, *, activity: str = "Waste", unit: str = "tonnes",
                    scope: str = "Scope 3") -> str:
    """A persisted extraction item: the server-derived evidence context (item → batch)."""
    async with pool.acquire() as conn:
        batch = await conn.fetchval(
            "INSERT INTO public.manual_extraction_batches "
            "(organization_id, batch_name, total_documents, total_pages, total_cost) "
            "VALUES ($1,$2,1,1,0) RETURNING id", org, "f0391-065 batch")
        return str(await conn.fetchval(
            "INSERT INTO public.manual_extraction_items "
            "(batch_id, file_name, file_url, page_count, extracted_data) "
            "VALUES ($1,$2,$3,1,$4::jsonb) RETURNING id",
            batch, "waste.csv", f"uploads/{org}/waste.csv",
            '{"supplier":"F0391 Supplier","date":"05/01/2025","line_items":'
            f'[{{"activity":"{activity}","source_line":"{activity}",'
            f'"unit":"{unit}","scope":"{scope}","quantity":12.5}}]}}'))


async def _seed_factors(pool) -> None:
    """The QA factor window (idempotent: the session fixture truncates only once)."""
    async with pool.acquire() as conn:
        for name, unit, scope, value, key in _WASTE_WINDOW:
            await conn.execute(
                "INSERT INTO public.emission_factors "
                "(id, reporting_year, activity_type, co2e_multiplier, unit, scope, "
                " factor_set, factor_source, country) "
                "VALUES ($1,2025,$2,$3,$4,$5,'DEFRA-2025','DEFRA-DESNZ','GB') "
                "ON CONFLICT DO NOTHING",
                _FACTOR_UUID[key], name, Decimal(value), unit, scope)


def _real_engine() -> FactorMatchingEngine:
    """The REAL matching engine over the seeded factor window."""
    factors = [
        EmissionFactor(
            id=_FACTOR_UUID[key], reporting_year=2025, activity_type=f"{name} [{unit}]",
            co2e_multiplier=Decimal(value), unit=unit, scope=scope,
            factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025", country="GB",
            provider_key="DEFRA-DESNZ",
            natural_key=("2025", f"{name} [{unit}]", "GB", unit, scope),
        )
        for name, unit, scope, value, key in _WASTE_WINDOW
    ]
    index = FactorSearchIndex()
    index.load(factors)
    config = MatchingPipelineConfig()
    return FactorMatchingEngine(index, build_matching_pipeline(config), config=config)


def _member(org: str, user_id: str) -> AuthUser:
    return AuthUser(user_id=user_id, email="member@f0391.local", role="member",
                    organization_id=org, is_org_member=True)


def _api_app(pool, *, user, engine=None) -> FastAPI:
    """The REAL router over the REAL repository pool and the REAL authorization gate.

    Returned as an ASGI app so the test can drive it through ``httpx.ASGITransport``
    inside the SAME event loop as the asyncpg pool — ``TestClient`` runs the app in a
    separate loop, which an asyncpg pool cannot be shared across.
    """
    from data.consultants import ConsultantsRepository

    bundle = type(
        "Bundle", (),
        {
            "clarifications": ActivityClarificationsRepository(pool),
            # the real consultant chain (memberships → firm profile → client grant), so
            # consultant/you-vs-client isolation is exercised against the real tables
            "consultants": ConsultantsRepository(pool),
        },
    )()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_repositories] = lambda: bundle
    app.dependency_overrides[get_matching_engine] = lambda: engine or _real_engine()

    if user is None:
        def _anon():
            raise HTTPException(status_code=401, detail="Not authenticated")
        app.dependency_overrides[get_current_user] = _anon
    else:
        app.dependency_overrides[get_current_user] = lambda: user
    return app


def _client(app: FastAPI):
    """An in-loop async client for the real ASGI app."""
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                             base_url="http://f0391.test")


# ---------------------------------------------------------------------------
# Repository lifecycle against the REAL constraint (the blocking defect)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_v1_then_v2_lifecycle_against_the_real_schema(pool) -> None:
    """v1 → v2 must succeed, retire v1 atomically and keep the history immutable."""
    from engines.activity_clarification import resolve_clarification

    org = await _new_org(pool)
    repo = ActivityClarificationsRepository(pool)
    key = f"f0391-065:{uuid.uuid4()}"
    actor = str(uuid.uuid4())
    signature = repo.evidence_signature("Waste", "tonnes", "Scope 3")

    # ---- version 1 --------------------------------------------------------
    v1 = await repo.apply_versioned(
        decline_clarification("Waste", activity_key=key, actor_id=actor),
        organization_id=org, actor_id=actor, context_key=key,
        evidence_signature=signature)
    assert v1["version"] == 1
    assert v1["is_current"] is True
    assert v1["supersedes_id"] is None
    assert v1["adjudication_id"] is not None

    # ---- version 2 — raised UniqueViolationError before the fix -----------
    record2, _factor = resolve_clarification("Waste", "Landfill", [], activity_key=key)
    v2 = await repo.apply_versioned(
        record2, organization_id=org, actor_id=actor, context_key=key,
        evidence_signature=signature)
    assert v2["version"] == 2
    assert v2["is_current"] is True
    assert str(v2["supersedes_id"]) == str(v1["id"])
    assert str(v2["adjudication_id"]) == str(v1["adjudication_id"])  # one lineage

    # ---- the real rows: exactly one current, v1 retired, v1 unrewritten ---
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, version, is_current, clarification, supersedes_id "
            "FROM public.activity_clarifications WHERE organization_id=$1 ORDER BY version",
            org)
    assert [(r["version"], r["is_current"]) for r in rows] == [(1, False), (2, True)]
    assert rows[0]["clarification"] == v1["clarification"]      # history preserved
    assert rows[0]["supersedes_id"] is None                     # v1 still supersedes none
    assert str(rows[1]["supersedes_id"]) == str(v1["id"])

    # ---- effective() == v2 ; history() == [v1, v2] ordered ---------------
    eff = await repo.effective(organization_id=org, activity_key=key,
                               original_activity="Waste", context_key=key)
    assert eff is not None and eff["version"] == 2 and eff["is_current"] is True

    hist = await repo.history(str(v1["adjudication_id"]), organization_id=org)
    assert [r["version"] for r in hist] == [1, 2]
    assert [r["id"] for r in hist] == [v1["id"], v2["id"]]
    assert hist[0]["clarification"] == v1["clarification"]     # immutable



@pytest.mark.asyncio
async def test_replay_is_idempotent_and_changed_evidence_signature_is_enforced(pool) -> None:
    """Replaying the same write adds no version; the D-F039-1-I gate still applies."""
    org = await _new_org(pool)
    repo = ActivityClarificationsRepository(pool)
    key = f"f0391-065:{uuid.uuid4()}"
    actor = str(uuid.uuid4())
    tonnes = repo.evidence_signature("Waste", "tonnes", "Scope 3")
    litres = repo.evidence_signature("Waste", "litres", "Scope 3")

    record, _factor = resolve_clarification("Waste", "Landfill", [], activity_key=key)
    first = await repo.apply_versioned(
        record, organization_id=org, actor_id=actor, context_key=key,
        evidence_signature=tonnes)
    again = await repo.apply_versioned(
        record, organization_id=org, actor_id=actor, context_key=key,
        evidence_signature=tonnes)
    assert again["id"] == first["id"] and again["version"] == 1   # no new version

    # A MODIFICATION is a change of the stored clarification (the semantic answer is
    # what versions); identical-clarification writes stay replays by design.
    changed_record, _f = resolve_clarification("Waste", "Incineration", [],
                                              activity_key=key)
    changed = await repo.apply_versioned(
        changed_record, organization_id=org, actor_id=actor, context_key=key,
        evidence_signature=litres)
    assert changed["version"] == 2
    assert str(changed["supersedes_id"]) == str(first["id"])

    hist = await repo.history(str(first["adjudication_id"]), organization_id=org)
    assert [r["version"] for r in hist] == [1, 2]

    # the CURRENT row's stored signature is the litres one, so tonnes evidence is
    # incompatible and litres evidence is compatible (nothing silently reused)
    row, ok = await repo.effective_compatible(
        organization_id=org, activity_key=key, original_activity="Waste",
        unit="tonnes", scope="Scope 3", context_key=key)
    assert row is not None and ok is False
    row2, ok2 = await repo.effective_compatible(
        organization_id=org, activity_key=key, original_activity="Waste",
        unit="litres", scope="Scope 3", context_key=key)
    assert row2 is not None and ok2 is True


@pytest.mark.asyncio
async def test_concurrent_modifications_serialise_on_the_lineage(pool) -> None:
    """Two parallel modifiers must not collide; the lineage stays single-current."""
    import asyncio

    from engines.activity_clarification import resolve_clarification

    org = await _new_org(pool)
    repo = ActivityClarificationsRepository(pool)
    key = f"f0391-065:{uuid.uuid4()}"
    actor = str(uuid.uuid4())

    base, _factor = resolve_clarification("Waste", "Landfill", [], activity_key=key)
    await repo.apply_versioned(base, organization_id=org, actor_id=actor, context_key=key)

    left, _f1 = resolve_clarification("Waste", "Incineration", [], activity_key=key)
    right, _f2 = resolve_clarification("Waste", "Waste oils", [], activity_key=key)
    results = await asyncio.gather(
        repo.apply_versioned(left, organization_id=org, actor_id=actor, context_key=key),
        repo.apply_versioned(right, organization_id=org, actor_id=actor, context_key=key),
        return_exceptions=True,
    )
    assert not [r for r in results if isinstance(r, BaseException)], results
    assert sorted(int(r["version"]) for r in results) == [2, 3]

    async with pool.acquire() as conn:
        current = await conn.fetchval(
            "SELECT count(*) FROM public.activity_clarifications "
            "WHERE organization_id=$1 AND is_current", org)
        total = await conn.fetchval(
            "SELECT count(*) FROM public.activity_clarifications "
            "WHERE organization_id=$1", org)
    assert current == 1     # never two current, never zero current
    assert total == 3



# ---------------------------------------------------------------------------
# API lifecycle over the REAL router, gate, engine, repository and database
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_create_change_effective_history(pool) -> None:
    """POST #1 → 201, POST changed #2 → 201, GET effective → v2, GET history → [1, 2]."""
    await _seed_factors(pool)
    org = await _new_org(pool)
    item = await _new_item(pool, org)
    user = _member(org, str(uuid.uuid4()))
    base = {"organization_id": org, "activity": "Waste", "item_id": item}

    async with _client(_api_app(pool, user=user)) as client:
        first = await client.post(CLARIFY, json={**base, "clarification": "Landfill"})
        assert first.status_code == 201, first.text
        body1 = first.json()
        # server-derived provenance: the authenticated user and the server's scope
        assert body1["actor_id"] == user.user_id
        assert body1["actor_scope"] == "organization_member"
        # the policy's own text for the clarified meaning (never a factor id)
        assert body1["policy_input"] == "Waste Landfill"

        # the SECOND write is the one that used to fail with UniqueViolationError
        second = await client.post(CLARIFY, json={**base, "clarification": "Incineration"})
        assert second.status_code == 201, second.text

        effective = await client.get(EFFECTIVE, params=base)
        assert effective.status_code == 200
        assert effective.json()["found"] is True
        current = effective.json()["adjudication"]
        assert current["version"] == 2 and current["is_current"] is True
        assert current["clarification"] == "Incineration"

        history = await client.get(
            HISTORY, params={**base, "adjudication_id": str(current["id"])})
        assert history.status_code == 200
        assert [v["version"] for v in history.json()["versions"]] == [1, 2]
        assert history.json()["current_version"] == 2
        assert history.json()["versions"][0]["clarification"] == "Landfill"  # immutable
        assert history.json()["versions"][0]["is_current"] is False
        assert str(history.json()["versions"][1]["supersedes_id"]) == \
            str(history.json()["versions"][0]["id"])

    # the lineage itself: exactly one current version, both versions retained
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT version, is_current FROM public.activity_clarifications "
            "WHERE organization_id=$1 ORDER BY version", org)
    assert [(r["version"], r["is_current"]) for r in rows] == [(1, False), (2, True)]


@pytest.mark.asyncio
async def test_api_rejects_foreign_tenant_anonymous_and_forged_factor(pool) -> None:
    """Authorization, provenance and anti-bypass hold over the real database."""
    await _seed_factors(pool)
    org = await _new_org(pool)
    other = await _new_org(pool)
    item = await _new_item(pool, org)
    user = _member(org, str(uuid.uuid4()))
    base = {"organization_id": org, "activity": "Waste", "item_id": item}

    async with _client(_api_app(pool, user=user)) as client:
        # another tenant's organisation: denied, nothing persisted
        denied = await client.post(
            CLARIFY, json={**base, "organization_id": other, "clarification": "Landfill"})
        assert denied.status_code == 403
        async with pool.acquire() as conn:
            assert await conn.fetchval(
                "SELECT count(*) FROM public.activity_clarifications "
                "WHERE organization_id=$1", other) == 0

        # an item belonging to another organisation is refused
        foreign_item = await _new_item(pool, other)
        cross = await client.post(
            CLARIFY, json={**base, "item_id": foreign_item, "clarification": "Landfill"})
        assert cross.status_code == 403

        # a factor id in the body is rejected outright (never a selection)
        forged = await client.post(
            CLARIFY, json={**base, "clarification": "Landfill",
                           "selected_factor_id": _FACTOR_UUID["oils"]})
        assert forged.status_code == 422

    # anonymous is denied
    async with _client(_api_app(pool, user=None)) as anon:
        assert (await anon.post(
            CLARIFY, json={**base, "clarification": "Landfill"})).status_code == 401


@pytest.mark.asyncio
async def test_api_rejects_malformed_identifiers_with_422_not_500(pool) -> None:
    """A non-uuid identifier is an input error (422) — never a database 500.

    Before the boundary check, a malformed ``item_id``/``organization_id`` reached asyncpg
    and raised ``DataError``, which the endpoints do not translate: the caller saw a 500.
    """
    await _seed_factors(pool)
    org = await _new_org(pool)
    item = await _new_item(pool, org)
    user = _member(org, str(uuid.uuid4()))
    base = {"organization_id": org, "activity": "Waste", "item_id": item}

    async with _client(_api_app(pool, user=user)) as client:
        for body in ({**base, "organization_id": "not-a-uuid"},
                     {**base, "item_id": "not-a-uuid"}):
            response = await client.post(CLARIFY, json={**body, "clarification": "Landfill"})
            assert response.status_code == 422, response.text

        effective = await client.get(
            EFFECTIVE, params={**base, "organization_id": "not-a-uuid"})
        assert effective.status_code == 422, effective.text

        history = await client.get(
            HISTORY, params={**base, "adjudication_id": "not-a-uuid"})
        assert history.status_code == 422, history.text

    async with pool.acquire() as conn:
        assert await conn.fetchval(
            "SELECT count(*) FROM public.activity_clarifications "
            "WHERE organization_id=$1", org) == 0



# ---------------------------------------------------------------------------
# F-064-1 — the /history identifier contract against the real schema
# ---------------------------------------------------------------------------
# The parameter is named ``adjudication_id`` and /effective publishes that LINEAGE identity
# (``adjudication.adjudication_id``) alongside the version ROW identity
# (``adjudication.id``). The shipped 055 schema makes them different values, which is why
# resolving only the row column 404'd the documented form.

OPTIONS = "/api/v3/activity-clarifications/options"


async def _semantic_options(client, base: dict, limit: int = 5) -> list:
    """The engine's OWN eligible semantic options (the API refuses anything else)."""
    offered = await client.get(OPTIONS, params=base)
    assert offered.status_code == 200, offered.text
    return [o["semantic_term"] for o in offered.json()["options"]][:limit]


async def _consultant_identity(pool, org: str, *, status: str = "active") -> AuthUser:
    """A REAL consultant: users + firm profile + active membership + client grant."""
    consult, firm = str(uuid.uuid4()), str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO public.users (id,email) VALUES ($1,$2)",
            consult, f"f0391-070-cons-{consult[:8]}@qa.local")
        await conn.execute(
            "INSERT INTO public.consultant_profiles (id,user_id,company_name,"
            " white_label_enabled) VALUES ($1,$2,'F0391-070 Firm',false)", firm, consult)
        await conn.execute(
            "INSERT INTO public.consultant_firm_members (firm_id,user_id,role,is_active)"
            " VALUES ($1,$2,'owner',true)", firm, consult)
        await conn.execute(
            "INSERT INTO public.consultant_clients (consultant_id,organization_id,"
            " client_name,status) VALUES ($1,$2,'F0391-070 Client',$3)", firm, org, status)
    return AuthUser(user_id=consult, email="f0391-070-cons@qa.local", role="consultant")



@pytest.mark.asyncio
async def test_history_is_addressable_by_the_lineage_identity_effective_publishes(pool) -> None:
    """F-064-1: the id /effective publishes as ``adjudication_id`` addresses /history."""
    await _seed_factors(pool)
    org = await _new_org(pool)
    item = await _new_item(pool, org)
    user = _member(org, str(uuid.uuid4()))
    base = {"organization_id": org, "activity": "Waste", "item_id": item}

    async with _client(_api_app(pool, user=user)) as client:
        terms = await _semantic_options(client, base, limit=4)
        assert len(terms) == 4, terms
        for term in terms:
            written = await client.post(CLARIFY, json={**base, "clarification": term})
            assert written.status_code == 201, written.text

        current = (await client.get(EFFECTIVE, params=base)).json()["adjudication"]
        lineage, row_id = str(current["adjudication_id"]), str(current["id"])
        # the 055 shape that broke the old row-only resolution
        assert lineage != row_id

        by_lineage = await client.get(HISTORY, params={**base, "adjudication_id": lineage})
        assert by_lineage.status_code == 200, by_lineage.text
        body = by_lineage.json()
        assert body["adjudication_id"] == lineage
        assert [v["version"] for v in body["versions"]] == [1, 2, 3, 4]
        assert body["current_version"] == 4
        assert body["versions"][3]["is_current"] is True
        assert body["versions"][0]["clarification"] == terms[0]  # immutable history

        # the compatibility form (a version row identity) resolves to the same lineage
        by_row = await client.get(HISTORY, params={**base, "adjudication_id": row_id})
        assert by_row.status_code == 200, by_row.text
        assert by_row.json()["adjudication_id"] == lineage
        assert [v["version"] for v in by_row.json()["versions"]] == [1, 2, 3, 4]

        # the lineage identity is stable across versions: a further modification does not
        # invalidate the identifier a caller already holds
        again = await client.post(CLARIFY, json={**base, "clarification": terms[0]})
        assert again.status_code == 201, again.text
        after = await client.get(HISTORY, params={**base, "adjudication_id": lineage})
        assert after.status_code == 200
        assert [v["version"] for v in after.json()["versions"]] == [1, 2, 3, 4, 5]
        assert after.json()["adjudication_id"] == lineage

        # unknown and malformed identifiers stay explicit 4xx answers
        unknown = await client.get(
            HISTORY, params={**base, "adjudication_id": str(uuid.uuid4())})
        assert unknown.status_code == 404
        malformed = await client.get(
            HISTORY, params={**base, "adjudication_id": "not-a-uuid"})
        assert malformed.status_code == 422



@pytest.mark.asyncio
async def test_history_contract_is_tenant_and_consultant_bounded(pool) -> None:
    """The corrected addressing changes no authorisation boundary."""
    await _seed_factors(pool)
    org_a, org_b = await _new_org(pool), await _new_org(pool)
    item_a = await _new_item(pool, org_a)
    item_b = await _new_item(pool, org_b)
    member_a = _member(org_a, str(uuid.uuid4()))
    base_a = {"organization_id": org_a, "activity": "Waste", "item_id": item_a}

    async with _client(_api_app(pool, user=member_a)) as client:
        terms = await _semantic_options(client, base_a, limit=2)
        for term in terms:
            assert (await client.post(
                CLARIFY, json={**base_a, "clarification": term})).status_code == 201
        lineage = (await client.get(EFFECTIVE, params=base_a)).json()[
            "adjudication"]["adjudication_id"]
        assert (await client.get(
            HISTORY, params={**base_a, "adjudication_id": lineage})).status_code == 200
        # the same member cannot address org A's lineage inside another organisation
        assert (await client.get(HISTORY, params={
            **base_a, "adjudication_id": lineage, "organization_id": org_b,
        })).status_code == 403

    # a legitimate member of org B, with org B's item, cannot read org A's lineage
    async with _client(_api_app(pool, user=_member(org_b, str(uuid.uuid4())))) as client:
        cross = await client.get(HISTORY, params={
            "organization_id": org_b, "activity": "Waste", "item_id": item_b,
            "adjudication_id": lineage})
        assert cross.status_code == 404, cross.text
        assert "versions" not in cross.json()

    # an ACTIVE consultant client reads it; an ended grant does not
    for status_value, expected in (("active", 200), ("ended", 403)):
        consultant = await _consultant_identity(pool, org_a, status=status_value)
        async with _client(_api_app(pool, user=consultant)) as client:
            response = await client.get(
                HISTORY, params={**base_a, "adjudication_id": lineage})
            assert response.status_code == expected, (status_value, response.text)
            if expected == 200:
                assert response.json()["adjudication_id"] == lineage
                assert [v["version"] for v in response.json()["versions"]] == [1, 2]

    # a consultant granted only org B has no access to org A
    ungranted = await _consultant_identity(pool, org_b)
    async with _client(_api_app(pool, user=ungranted)) as client:
        assert (await client.get(
            HISTORY, params={**base_a, "adjudication_id": lineage})).status_code == 403

    # and an unauthenticated caller is refused outright
    async with _client(_api_app(pool, user=None)) as client:
        assert (await client.get(
            HISTORY, params={**base_a, "adjudication_id": lineage})).status_code == 401



# ---------------------------------------------------------------------------
# Workstream C — effective-adjudication determinism against the REAL schema
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_effective_read_determinism_is_enforced_by_the_real_schema(pool) -> None:
    """No ORDER BY/LIMIT is needed: the predicates match a UNIQUE index (D-F039-1-J).

    Proven in three parts against the real database: the uniqueness basis exists, the read
    really is bounded by exactly that basis, and repeated reads of a multi-version lineage
    always return the same current row (there is no second current row to alternate with).
    """
    index_sql = """
        SELECT c.relname AS name,
               i.indisunique AS is_unique,
               pg_get_indexdef(i.indexrelid) AS definition
          FROM pg_index i
          JOIN pg_class c ON c.oid = i.indexrelid
         WHERE c.relname = ANY($1::text[])
    """
    async with pool.acquire() as conn:
        rows = {
            r["name"]: r for r in await conn.fetch(index_sql, [
                "activity_clarifications_context_unique",
                "activity_clarifications_current_unique",
                "activity_clarifications_replay_unique",
                "activity_clarifications_pkey",
            ])
        }

    # 1. every single-row read is backed by a UNIQUE index
    for name in ("activity_clarifications_context_unique",
                 "activity_clarifications_current_unique",
                 "activity_clarifications_replay_unique",
                 "activity_clarifications_pkey"):
        assert name in rows, f"{name} is missing: the determinism basis is absent"
        assert rows[name]["is_unique"] is True, f"{name} is not unique"
    assert ("(organization_id, effective_context_key, activity_key, original_activity) "
            "WHERE is_current") in rows["activity_clarifications_context_unique"]["definition"]
    assert "(adjudication_id) WHERE is_current" in \
        rows["activity_clarifications_current_unique"]["definition"]

    # 2. a real 3-version lineage in one bounded context
    org = await _new_org(pool)
    repo = ActivityClarificationsRepository(pool)
    key = f"f0391-070:{uuid.uuid4()}"
    actor = str(uuid.uuid4())
    signature = repo.evidence_signature("Waste", "tonnes", "Scope 3")
    versions = []
    for clarification in ("Landfill", "Incineration", "Waste oils"):
        record, _factor = resolve_clarification(
            "Waste", clarification, [], activity_key=key)
        versions.append(await repo.apply_versioned(
            record, organization_id=org, actor_id=actor, context_key=key,
            evidence_signature=signature))
    assert [v["version"] for v in versions] == [1, 2, 3]
    assert len({str(v["adjudication_id"]) for v in versions}) == 1   # one lineage

    # 3. the read is deterministic: 25 reads, always the SAME current row
    seen = set()
    for _ in range(25):
        row = await repo.effective(
            organization_id=org, activity_key=key, original_activity="Waste",
            context_key=key)
        seen.add((str(row["id"]), int(row["version"])))
    assert seen == {(str(versions[2]["id"]), 3)}

    # and the consumption read (which delegates to the effective read) agrees
    compatible_row, compatible = await repo.effective_compatible(
        organization_id=org, activity_key=key, original_activity="Waste",
        unit="tonnes", scope="Scope 3", context_key=key)
    assert compatible is True
    assert str(compatible_row["id"]) == str(versions[2]["id"])

    # the rejected alternative: supplying ORDER BY/LIMIT would not strengthen this —
    # the invariant, not the row order, is what makes the answer unambiguous
    async with pool.acquire() as conn:
        current = await conn.fetchval(
            "SELECT count(*) FROM public.activity_clarifications "
            "WHERE organization_id=$1 AND effective_context_key=$2 AND is_current", org, key)
    assert current == 1

