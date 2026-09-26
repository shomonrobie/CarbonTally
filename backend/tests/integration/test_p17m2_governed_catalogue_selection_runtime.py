"""P17-M2 — the governed catalogue version is chosen by *identity*, on real PostgreSQL.

Why this file exists
--------------------
`P17-M` found `DEF-1`: the capability truth surface picked a framework version by
**ordering luck** — ``next(candidate for candidate in candidates if any(
is_governed_requirement_code(code) for code in candidate["requirement_codes"]))``.
The read model ordered candidates ``IN_FORCE`` first, then ``source_tier``, then
``version_label``, so a *competing* ``GHG_PROTOCOL`` version that happened to
carry **one** governed-looking requirement code and sorted early became the
product capability catalogue. Because the projection is happy to state a
partial claim, the surface then answered **200** with a narrower and *upgraded*
claim — a silent product-claim change with no governance event behind it.

`P17-M2` fixes it by anchoring selection to the catalogue's **identity**: a
candidate is the governed capability catalogue only if every one of its
requirement rows is a governed requirement identity *and* those rows include the
complete governed identity set
(:data:`domain.capability_catalogue.GOVERNED_CATALOGUE_IDENTITIES`). Position is
never consulted, and **two** complete candidates are an ambiguous governed state
— the surface then fails closed with **503** rather than choosing.

`tests/unit/domain/test_p17m2_governed_catalogue_identity.py` verifies the rule
and `tests/unit/api/test_p17m2_governed_catalogue_version_selection.py` verifies
it over the real route with a faked read model. *This* suite verifies it against
a real, migrated PostgreSQL database, with a real competing framework version
**persisted, offered first by the real ORDER BY, and servable** — i.e. under the
pre-fix rule the competitor would genuinely have been published. The suite also
proves the fix is present in the **shipped** code (the route and the repository
SQL are read from disk) and that the read path writes nothing.

Required outcomes under the adversarial state (`P17-M2` case C):

* the canonical 18-row `4/6/3/2` payload is served unchanged, or
* the surface fails closed (`503`) with no claim at all.

Anything else — a 200 carrying the competing catalogue, a changed `M-1` value, a
changed rollup, or a silent upgrade — fails this suite.

Mutation safety (F-046-1 restated, and stronger here)
-----------------------------------------------------
The shared ``pool`` fixture performs **destructive** setup (``TRUNCATE …
RESTART IDENTITY CASCADE``), so this module inherits its guard: a target whose
name matches ``qa`` / ``demo`` / ``investor`` / ``prod`` / ``live`` (or a main
application database) is refused *before* any statement executes, and
``test_the_target_is_a_disposable_clone`` re-asserts the target's identity here.
Point ``INTEGRATION_DATABASE_URL`` at a disposable ``ct_*`` clone::

    INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_iv_p17m2_20260926 \\
      .venv/bin/python -m pytest \\
      tests/integration/test_p17m2_governed_catalogue_selection_runtime.py

Every competing row this module creates is inserted on one dedicated connection
inside an explicit transaction that is **rolled back in a ``finally`` block**, so
the clone cannot be left polluted even if a test fails mid-way. Each mutation
test then asserts the rollback (row count back to zero and a byte-for-byte
catalogue digest identical to the pre-mutation digest). No migration is applied,
and no production, demo, investor or QA environment is contacted.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Mapping, Sequence
from urllib.parse import urlparse

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
from domain.disclosure import DisclosureViolation
from domain.organization import Organization

pytestmark = pytest.mark.asyncio

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

#: The four-way rollup (`S3-1`, `AG-7`) — never a total or a percentage.
ROLLUP: dict[str, int] = {
    "SUPPORTED": 4,
    "PARTIALLY_SUPPORTED": 6,
    "FUTURE": 3,
    "MISSING_CAPABILITY": 2,
}

#: The rollup the *competitor* would have published, with one `M-1` value raised
#: from `MISSING_CAPABILITY` to `SUPPORTED` — the concrete `DEF-1` harm.
UPGRADED_ROLLUP: dict[str, int] = {
    "SUPPORTED": 5,
    "PARTIALLY_SUPPORTED": 6,
    "FUTURE": 3,
    "MISSING_CAPABILITY": 1,
}

GOVERNED_CODES: tuple[str, ...] = ("GP-S1", "GP-S2-LB", "GP-S2-MB", *tuple(M1_IMAGE))

CAPABILITY_BY_CODE: dict[str, str] = {
    "GP-S1": "SUPPORTED",
    "GP-S2-LB": "SUPPORTED",
    "GP-S2-MB": "MISSING_CAPABILITY",
    **M1_IMAGE,
}

#: The three governed catalogue tables the read model may touch.
CATALOGUE_TABLES: tuple[str, ...] = (
    "disclosure_requirement_versions",
    "disclosure_framework_versions",
    "disclosure_frameworks",
)

#: Mirrors ``tests/integration/conftest.py`` — PO operational control `F-046-1`.
#: Duplicated deliberately: this module also opens *its own* second pool (for the
#: un-provisioned target) and must apply the same refusal to it.
PROTECTED_DB_MARKERS: tuple[str, ...] = ("qa", "demo", "investor", "prod", "live")
FORBIDDEN_MAIN_DB_NAMES: tuple[str, ...] = ("postgres", "supabase_db_carbon_ledger")

#: A clone that has **never** been provisioned with a catalogue (optional; the
#: un-provisioned test skips with an explicit reason when it is not configured).
NO_CATALOGUE_ENV = "INTEGRATION_NOCAT_DATABASE_URL"


def _refuse_persistent_target(name: str) -> None:
    """`F-046-1` — never mutate a persistent, data-bearing target."""
    lowered = name.lower()
    assert name not in FORBIDDEN_MAIN_DB_NAMES, f"F-046-1: refused main database {name!r}"
    marker = next((m for m in PROTECTED_DB_MARKERS if m in lowered), None)
    assert marker is None, f"F-046-1: refused persistent target {name!r} (marker {marker!r})"



# ===========================================================================
# Helpers — the real read path (repository → shipped selector → projection)
# ===========================================================================
async def _database_name(pool: Any) -> str:
    return str(await pool.fetchval("SELECT current_database()"))


async def _catalogue_digest(pool: Any) -> str:
    """A byte-for-byte digest of the three catalogue tables.

    Any accidental write by the read path — or any row this module forgot to
    remove — changes the digest, so "the clone is exactly as it was found" is a
    single comparable value (`SEC-3`, `AG-5`).
    """
    rows: list[tuple[Any, ...]] = []
    for table in CATALOGUE_TABLES:
        rows.append((table, await pool.fetchval(f"SELECT count(*)::int FROM public.{table}")))
        rows.append(
            (
                table,
                await pool.fetchval(
                    f"SELECT md5(coalesce(string_agg(t::text, '|' ORDER BY t::text), '')) "
                    f"FROM public.{table} t"
                ),
            )
        )
    return hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()


async def _requirement_row_count(pool: Any, framework_version_id: str) -> int:
    return int(
        await pool.fetchval(
            "SELECT count(*)::int FROM public.disclosure_requirement_versions "
            "WHERE framework_version_id = $1",
            framework_version_id,
        )
    )


async def _framework_id(pool: Any) -> str:
    framework_id = await pool.fetchval(
        "SELECT id FROM public.disclosure_frameworks WHERE code = $1", FRAMEWORK_CODE
    )
    assert framework_id is not None, f"framework {FRAMEWORK_CODE} is absent"
    return str(framework_id)


async def _candidates(pool: Any) -> list[dict[str, Any]]:
    """The real repository read: candidates in the order the SQL actually returns."""
    return await DisclosureCatalogRepository(pool).capability_catalogue_candidates()


async def _select(pool: Any) -> dict[str, Any]:
    """The **shipped** selector over the real candidates (never re-implemented)."""
    selected = cc.select_governed_catalogue_version(await _candidates(pool))
    assert selected is not None, "the governed catalogue is not selectable"
    return selected


async def _project(pool: Any) -> dict[str, Any]:
    """The shipped read path end to end: candidates → selector → rows → projection."""
    repository = DisclosureCatalogRepository(pool)
    selected = await _select(pool)
    framework = await repository.get_framework_by_code(str(selected.get("framework_code") or ""))
    assert framework is not None, "the framework of the governed catalogue must exist"
    return cc.project_capability_catalogue(
        framework=framework,
        framework_version=selected,
        requirement_rows=await repository.list_capability_catalogue_requirements(
            str(selected["id"])
        ),
    )


def _app(pool: Any, user: AuthUser) -> FastAPI:
    """The real ASGI app with the real pool and a fixed authenticated actor."""
    app = FastAPI()
    app.include_router(disclosure_router)

    async def _pool() -> Any:
        return pool

    app.dependency_overrides[get_pool] = _pool
    app.dependency_overrides[get_current_user] = lambda: user
    return app


async def _get(pool: Any, user: AuthUser | None = None) -> httpx.Response:
    """Drive the real HTTP route in-process, against the real database."""
    actor = user or _user(str(uuid.uuid4()), str(uuid.uuid4()))
    transport = httpx.ASGITransport(app=_app(pool, actor))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(ROUTE)


def _user(organization_id: str, user_id: str, email: str = "owner@example.test") -> AuthUser:
    return AuthUser(
        user_id=user_id,
        email=email,
        role="owner",
        organization_id=organization_id,
        is_org_member=True,
    )


# ---------------------------------------------------------------------------
# Helpers — a real competing framework version, inside a rolled-back transaction
# ---------------------------------------------------------------------------
class _TxPool:
    """A pool-like shim handing out ONE real connection inside a transaction.

    `AbstractRepository` only needs ``acquire()`` → async context manager, so the
    route and the read model run their **real SQL** against a real connection
    while every statement stays inside a transaction this test controls
    (rollback only — no committed residue, `F-046-1`).
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


@contextlib.asynccontextmanager
async def _rolled_back(pool: asyncpg.Pool) -> AsyncIterator[_TxPool]:
    """A real connection in an explicit transaction that is always rolled back."""
    connection = await pool.acquire()
    transaction = connection.transaction()
    await transaction.start()
    try:
        yield _TxPool(connection)
    finally:
        with contextlib.suppress(Exception):
            await transaction.rollback()
        await pool.release(connection)


async def _insert_competing_version(
    connection: asyncpg.Connection,
    label: str,
    *,
    status: str = "IN_FORCE",
    source_tier: int = 1,
) -> str:
    """A real, persisted competing framework version of the same framework.

    ``IN_FORCE`` and ``source_tier`` 1 by default, so the competitor is exactly
    what the pre-fix ordering treated as the *most* authoritative candidate.
    """
    version_id = await connection.fetchval(
        """
        INSERT INTO public.disclosure_framework_versions
            (framework_id, version_label, source_tier, status)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        await _framework_id(connection),
        label,
        source_tier,
        status,
    )
    return str(version_id)


async def _insert_requirement(
    connection: asyncpg.Connection,
    framework_version_id: str,
    code: str,
    capability: str,
    *,
    display_order: int = 1,
) -> None:
    """One real requirement row on a competing version (satisfying the CHECKs)."""
    await connection.execute(
        """
        INSERT INTO public.disclosure_requirement_versions
            (framework_version_id, requirement_code, title, requirement_class,
             value_kind, carbontally_capability, display_order)
        VALUES ($1, $2, $3, 'REQUIRED', 'QUANTITATIVE', $4, $5)
        """,
        framework_version_id,
        code,
        f"Competing row {code}",
        capability,
        display_order,
    )


async def _clone_governed_rows(
    connection: asyncpg.Connection,
    framework_version_id: str,
    source_version_id: str,
) -> None:
    """Copy the complete governed identity set onto a competing version.

    The copy is verbatim, so the competitor carries **every** governed
    requirement identity — the case in which the pre-fix rule would have
    published a full-looking claim from another version. A caller may then
    change one value (see the silent-upgrade test) to show the claim would have
    *differed*, not merely been re-attributed.
    """
    await connection.execute(
        """
        INSERT INTO public.disclosure_requirement_versions
            (framework_version_id, requirement_code, official_identifier,
             identifier_status, title, description, requirement_class,
             is_quantitative, value_kind, unit_hint, scope_hint, gas_hint,
             scope2_method_hint, period_semantics, display_order, purpose_hint,
             carbontally_capability, source_locator, authoritative_text_ref,
             source_tier, verified_at)
        SELECT $1, requirement_code, official_identifier, identifier_status,
               title, description, requirement_class, is_quantitative, value_kind,
               unit_hint, scope_hint, gas_hint, scope2_method_hint,
               period_semantics, display_order, purpose_hint,
               carbontally_capability, source_locator, authoritative_text_ref,
               source_tier, verified_at
          FROM public.disclosure_requirement_versions
         WHERE framework_version_id = $2
        """,
        framework_version_id,
        source_version_id,
    )


def _legacy_rule_selection(
    candidates: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    """The **pre-fix** rule, re-implemented to demonstrate the defect it caused.

    This is not production code. It exists so the suite can assert that the
    competitor it creates really *was* selectable by the old expression
    (``next(... any(is_governed_requirement_code(...) ...))`` over the ordered
    candidates) — test-only evidence that the setup is still adversarial.
    """
    for candidate in candidates:
        if any(
            cc.is_governed_requirement_code(code)
            for code in (candidate.get("requirement_codes") or [])
        ):
            return candidate
    return None


async def _version_label(pool: Any, framework_version_id: str) -> str:
    return str(
        await pool.fetchval(
            "SELECT version_label FROM public.disclosure_framework_versions WHERE id = $1",
            framework_version_id,
        )
    )


def _claims_in(body: Mapping[str, Any]) -> bool:
    """Does this HTTP body carry a capability claim at all?"""
    return "requirements" in body or "scope3_capability_rollup" in body


def _requirement_payloads(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(item["requirement_code"]): item for item in payload["requirements"]}


async def _project_version(pool: Any, version: Mapping[str, Any]) -> dict[str, Any]:
    """Project one *given* candidate — "what would this version have claimed?".

    Used to state the harm `DEF-1` caused: a competing version that the pre-fix
    rule selected is projected exactly as the old endpoint would have projected
    it, on the real database.
    """
    repository = DisclosureCatalogRepository(pool)
    framework = await repository.get_framework_by_code(str(version.get("framework_code") or ""))
    assert framework is not None, "the framework of the candidate must exist"
    return cc.project_capability_catalogue(
        framework=framework,
        framework_version=version,
        requirement_rows=await repository.list_capability_catalogue_requirements(
            str(version["id"])
        ),
    )


async def _make_org(pool: Any, name: str) -> str:
    """A real organisation row (a genuine tenant), on the caller's connection.

    Uses the same repository the application uses, exactly as `P17-L` does, so a
    tenant context here is a real tenant context.
    """
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
# 1. The target, and the claim it currently serves
# ===========================================================================
async def test_the_target_is_a_disposable_clone(pool: asyncpg.Pool) -> None:
    """F-046-1 — destructive-setup suites never point at a data-bearing target.

    The shared ``pool`` fixture refuses protected names before any statement; this
    test re-asserts the identity of the target this module actually mutated, so a
    reader of the report can see which database produced the evidence.
    """
    name = await _database_name(pool)
    lowered = name.lower()
    assert not any(marker in lowered for marker in PROTECTED_DB_MARKERS), name
    if name != "carbontally_test":
        assert name.startswith("ct_"), name
    assert await pool.fetchval("SELECT version() LIKE 'PostgreSQL%'") is True


async def test_the_persisted_catalogue_is_the_complete_governed_identity_set(
    pool: asyncpg.Pool,
) -> None:
    """Exactly one candidate carries the governed identity set — and it is whole."""
    candidates = await _candidates(pool)
    assert candidates, "the catalogue is not provisioned in this clone"

    governed = [
        candidate for candidate in candidates if cc.is_governed_catalogue_version(candidate)
    ]
    assert len(governed) == 1, [c["version_label"] for c in governed]

    selected = await _select(pool)
    assert selected["id"] == governed[0]["id"]
    assert selected["framework_code"] == FRAMEWORK_CODE
    assert selected["version_label"] == VERSION_LABEL

    codes = set(selected["requirement_codes"])
    assert codes == set(GOVERNED_CODES), sorted(codes)
    assert len(codes) == 18
    # The identity set is derived, never re-typed: the module constant equals the
    # persisted identity set of the governed catalogue.
    assert set(cc.GOVERNED_CATALOGUE_IDENTITIES) == codes
    assert set(cc.governed_requirement_identities()) == codes


async def test_the_persisted_rows_match_the_frozen_m1_image(pool: asyncpg.Pool) -> None:
    """The canonical claim, from the persisted rows, is the frozen `M-1` image."""
    payload = await _project(pool)
    requirements = _requirement_payloads(payload)
    assert sorted(requirements) == sorted(GOVERNED_CODES)
    for code, capability in CAPABILITY_BY_CODE.items():
        assert requirements[code]["carbontally_capability"] == capability, code
    assert payload["framework_version"]["version_label"] == VERSION_LABEL
    assert payload["scope3_capability_rollup"] == ROLLUP


async def test_the_route_serves_the_canonical_claim_on_the_real_database(
    pool: asyncpg.Pool,
) -> None:
    """The real route, on the real database, states the canonical claim."""
    response = await _get(pool)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["framework_version"]["version_label"] == VERSION_LABEL
    assert len(body["requirements"]) == 18
    assert body["scope3_capability_rollup"] == ROLLUP
    assert _claims_in(body) is True


# ===========================================================================
# 2. Selection is identity-anchored and order-free (the P17-M2 rule)
# ===========================================================================
async def test_the_selector_ignores_position_on_real_candidates(pool: asyncpg.Pool) -> None:
    """Reordering the real candidate list cannot change which version is chosen.

    The clone carries many competing framework versions (residue from earlier
    suites), so this is a real ordering, not a synthetic one.
    """
    candidates = await _candidates(pool)
    selected = await _select(pool)

    for permutation in (list(reversed(candidates)), candidates[1:] + candidates[:1]):
        assert cc.select_governed_catalogue_version(permutation)["id"] == selected["id"]

    # ... and no candidate other than the governed one is the catalogue.
    others = [c for c in candidates if c["id"] != selected["id"]]
    assert others, "this clone was expected to carry competing framework versions"
    for candidate in others:
        assert cc.is_governed_catalogue_version(candidate) is False, candidate["version_label"]


async def test_the_governed_identity_set_is_closed_and_matches_the_grammar() -> None:
    """Every governed identity is accepted by the grammar; near-misses are not."""
    identities = cc.governed_requirement_identities()
    assert identities == cc.GOVERNED_CATALOGUE_IDENTITIES
    assert len(identities) == 18 == len(GOVERNED_CODES)
    for identity in identities:
        assert cc.is_governed_requirement_code(identity) is True, identity
    for impostor in ("B1RT_068e737e", "GP-S4", "GP-S2-XX", "GP-S3-CAT-16", "cat-1", ""):
        assert cc.is_governed_requirement_code(impostor) is False, impostor


# ===========================================================================
# 3. `DEF-1` on real PostgreSQL — the competing version is offered first and
#    the pre-fix rule genuinely selects it
# ===========================================================================
async def test_a_one_code_competitor_offered_first_cannot_hijack_the_catalogue(
    pool: asyncpg.Pool,
) -> None:
    """The exact `P17-M` attack, persisted, on a real database.

    The competitor is ``IN_FORCE``, ``source_tier`` 1, carries a single *governed*
    requirement code (``GP-S3-CAT-01`` → ``SUPPORTED``, where the governed
    catalogue states ``PARTIALLY_SUPPORTED``) and sorts lexically before the
    governed version, so the old rule selects **it**. The shipped rule must ignore
    it entirely and serve the canonical claim unchanged.

    Everything is inserted inside a transaction that is rolled back, so the clone
    is left exactly as it was found.
    """
    before = await _catalogue_digest(pool)
    governed_id = str((await _select(pool))["id"])

    async with _rolled_back(pool) as tx:
        competitor_id = await _insert_competing_version(
            tx._connection, f"AAA-P17M2-hijack-{uuid.uuid4().hex[:8]}"
        )
        await _insert_requirement(tx._connection, competitor_id, "GP-S3-CAT-01", "SUPPORTED")

        candidates = await _candidates(tx)
        index_competitor = next(
            i for i, c in enumerate(candidates) if str(c["id"]) == competitor_id
        )
        index_governed = next(i for i, c in enumerate(candidates) if str(c["id"]) == governed_id)
        # (a) the competitor is offered *before* the governed catalogue ...
        assert index_competitor < index_governed, (index_competitor, index_governed)
        # (b) ... it carries a governed requirement code ...
        assert list(candidates[index_competitor]["requirement_codes"]) == ["GP-S3-CAT-01"]
        assert cc.is_governed_requirement_code("GP-S3-CAT-01") is True
        # (c) ... so the PRE-FIX rule really did select it (DEF-1 reproduced) ...
        legacy = _legacy_rule_selection(candidates)
        assert legacy is not None and str(legacy["id"]) == competitor_id
        # (d) ... and its claim is narrower AND upgraded: genuinely harmful.
        competitor_claim = await _project_version(tx, candidates[index_competitor])
        assert str(competitor_claim["framework_version"]["version_label"]).startswith("AAA-")
        assert competitor_claim["scope3_capability_rollup"] == {
            "SUPPORTED": 1,
            "PARTIALLY_SUPPORTED": 0,
            "FUTURE": 0,
            "MISSING_CAPABILITY": 0,
        }
        assert _requirement_payloads(competitor_claim)["GP-S3-CAT-01"][
            "carbontally_capability"
        ] == "SUPPORTED"

        # The shipped rule selects the governed catalogue, whatever the order.
        selected = await _select(tx)
        assert str(selected["id"]) == governed_id
        assert selected["version_label"] == VERSION_LABEL

        # And the surface still states the canonical claim over HTTP.
        response = await _get(tx)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["framework_version"]["version_label"] == VERSION_LABEL
        assert len(body["requirements"]) == 18
        assert _requirement_payloads(body)["GP-S3-CAT-01"]["carbontally_capability"] == (
            "PARTIALLY_SUPPORTED"
        )
        assert body["scope3_capability_rollup"] == ROLLUP
        assert str(competitor_id) not in response.text
        assert "AAA-P17M2" not in response.text

    # Hygiene: the rollback happened and nothing was left behind.
    assert await _requirement_row_count(pool, competitor_id) == 0
    assert await pool.fetchval(
        "SELECT count(*)::int FROM public.disclosure_framework_versions WHERE id = $1",
        competitor_id,
    ) == 0
    assert await _catalogue_digest(pool) == before


async def test_a_complete_competitor_is_ambiguous_and_the_surface_fails_closed(
    pool: asyncpg.Pool,
) -> None:
    """Two complete governed versions ⇒ **no** claim, not a chosen one.

    This is the sharper half of `DEF-1`: a competing version that is a full copy of
    the governed catalogue (all 18 requirement identities) with **one capability
    value raised** — ``GP-S3-CAT-02`` from ``MISSING_CAPABILITY`` to
    ``SUPPORTED``, the concrete upgrade this revision was raised against. The old
    rule would have published it (it sorted first and carried governed codes); the
    shipped rule must refuse to choose at all and the surface must fail closed with
    **503** and no claim vocabulary.
    """
    before = await _catalogue_digest(pool)
    governed_id = str((await _select(pool))["id"])

    async with _rolled_back(pool) as tx:
        clone_id = await _insert_competing_version(
            tx._connection, f"AAA-P17M2-clone-{uuid.uuid4().hex[:8]}"
        )
        await _clone_governed_rows(tx._connection, clone_id, governed_id)
        await tx._connection.execute(
            """
            UPDATE public.disclosure_requirement_versions
               SET carbontally_capability = 'SUPPORTED'
             WHERE framework_version_id = $1 AND requirement_code = 'GP-S3-CAT-02'
            """,
            clone_id,
        )

        candidates = await _candidates(tx)
        index_clone = next(i for i, c in enumerate(candidates) if str(c["id"]) == clone_id)
        index_governed = next(i for i, c in enumerate(candidates) if str(c["id"]) == governed_id)
        assert index_clone < index_governed, (index_clone, index_governed)
        assert len(candidates[index_clone]["requirement_codes"]) == 18
        assert cc.is_governed_catalogue_version(candidates[index_clone]) is True

        # The pre-fix rule pressed straight past the governed catalogue ...
        legacy = _legacy_rule_selection(candidates)
        assert legacy is not None and str(legacy["id"]) == clone_id
        # ... and published an UPGRADED claim (5/6/3/1, not 4/6/3/2).
        published = await _project_version(tx, candidates[index_clone])
        assert str(published["framework_version"]["version_label"]).startswith("AAA-")
        assert published["scope3_capability_rollup"] == UPGRADED_ROLLUP
        assert _requirement_payloads(published)["GP-S3-CAT-02"]["carbontally_capability"] == (
            "SUPPORTED"
        )

        # The shipped rule refuses to choose between two complete candidates.
        with pytest.raises(DisclosureViolation) as raised:
            cc.select_governed_catalogue_version(candidates)
        assert "ambiguous" in str(raised.value).lower(), str(raised.value)

        # ... and the surface states nothing at all.
        response = await _get(tx)
        assert response.status_code == 503, response.text
        body = response.json()
        assert _claims_in(body) is False
        assert "ambiguous" in json.dumps(body).lower()
        assert "SUPPORTED" not in json.dumps(body)
        assert str(clone_id) not in response.text

    # Rollback: the ambiguity is gone, and the clone is byte-for-byte unchanged.
    assert await _requirement_row_count(pool, clone_id) == 0
    assert await _catalogue_digest(pool) == before


async def test_the_surface_serves_the_canonical_claim_once_the_ambiguity_is_gone(
    pool: asyncpg.Pool,
) -> None:
    """Recovery: the 503 above was caused by the inserted state, not by damage.

    The previous test removed its competing version by rollback; the same clone,
    same route and same connection path must now serve the canonical `M-1` claim
    again. Without this, a 503 could be dismissed as a broken environment.
    """
    candidates = await _candidates(pool)
    governed = [
        candidate for candidate in candidates if cc.is_governed_catalogue_version(candidate)
    ]
    assert len(governed) == 1, [c["version_label"] for c in governed]

    response = await _get(pool, _user(str(uuid.uuid4()), str(uuid.uuid4())))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["framework_version"]["version_label"] == VERSION_LABEL
    assert len(body["requirements"]) == 18
    assert body["scope3_capability_rollup"] == ROLLUP
    assert _requirement_payloads(body)["GP-S3-CAT-02"]["carbontally_capability"] == (
        "MISSING_CAPABILITY"
    )
    assert _claims_in(body) is True


@pytest.mark.parametrize(
    "impostor",
    [
        "gp-s3-cat-01",  # the right shape in the wrong case — the grammar is exact
        "GP-S3-CAT-1",  # one digit, not the governed two
        "GP-S3-CAT-01 ",  # a trailing space is a different identity
        "GP-S3-CAT-16",  # outside the governed 1..15 taxonomy
        "GP-S4-CAT-01",  # a scope that is not governed at all
        "B1RT_068e737e",  # real residue already present in this clone
    ],
)
async def test_a_near_miss_code_offered_first_neither_hijacks_nor_ambiguates(
    pool: asyncpg.Pool, impostor: str
) -> None:
    """The identity rule is exact — and *proportionate*.

    A near-miss is not a governed requirement identity (§2), so a version built
    from one is not the catalogue. Just as importantly it must not be counted as a
    *second* catalogue either: over-triggering would turn a healthy surface into a
    503 whenever unrelated residue exists. The pre-fix rule asked only whether a
    candidate carried *any* governed-looking code; the shipped rule asks whether
    the candidate carries the complete governed identity set and nothing else.
    """
    assert cc.is_governed_requirement_code(impostor) is False, impostor
    before = await _catalogue_digest(pool)
    governed_id = str((await _select(pool))["id"])

    async with _rolled_back(pool) as tx:
        competitor_id = await _insert_competing_version(
            tx._connection, f"AAA-P17M2-nearmiss-{uuid.uuid4().hex[:8]}"
        )
        await _insert_requirement(tx._connection, competitor_id, impostor, "SUPPORTED")

        candidates = await _candidates(tx)
        index_competitor = next(
            i for i, c in enumerate(candidates) if str(c["id"]) == competitor_id
        )
        index_governed = next(i for i, c in enumerate(candidates) if str(c["id"]) == governed_id)
        # (a) the impostor really is offered ahead of the governed catalogue ...
        assert index_competitor < index_governed, (index_competitor, index_governed)
        # (b) ... it is not the catalogue ...
        assert cc.is_governed_catalogue_version(candidates[index_competitor]) is False
        # (c) ... and it did not manufacture a second one (so: no ambiguity).
        governed = [c for c in candidates if cc.is_governed_catalogue_version(c)]
        assert [str(c["id"]) for c in governed] == [governed_id]
        assert str(cc.select_governed_catalogue_version(candidates)["id"]) == governed_id

        # The surface serves the canonical claim: no hijack, no spurious 503.
        response = await _get(tx)
        assert response.status_code == 200, response.text
        body = response.json()
        assert _claims_in(body) is True
        assert body["framework_version"]["version_label"] == VERSION_LABEL
        assert len(body["requirements"]) == 18
        assert body["scope3_capability_rollup"] == ROLLUP
        assert f"Competing row {impostor}" not in json.dumps(body)
        assert str(competitor_id) not in response.text

    assert await _requirement_row_count(pool, competitor_id) == 0
    assert await _catalogue_digest(pool) == before


async def test_a_version_with_the_complete_set_plus_residue_is_not_the_catalogue(
    pool: asyncpg.Pool,
) -> None:
    """The *second* pre-fix hole: "governed-looking" was decided by ``any``.

    A version is not the capability catalogue merely because it carries the
    governed identities — it must carry **nothing else**, because a claim built on
    a non-governed row is not the governed claim (`§5`, `§21`). This competitor is
    a verbatim clone of the governed set **plus** one non-governed residue code, so
    the old rule selected it on the strength of its first governed code.
    """
    before = await _catalogue_digest(pool)
    governed_id = str((await _select(pool))["id"])

    async with _rolled_back(pool) as tx:
        clone_id = await _insert_competing_version(
            tx._connection, f"AAA-P17M2-residue-{uuid.uuid4().hex[:8]}"
        )
        await _clone_governed_rows(tx._connection, clone_id, governed_id)
        await _insert_requirement(
            tx._connection, clone_id, "B1RT_068e737e", "SUPPORTED", display_order=99
        )

        candidates = await _candidates(tx)
        index_clone = next(i for i, c in enumerate(candidates) if str(c["id"]) == clone_id)
        index_governed = next(i for i, c in enumerate(candidates) if str(c["id"]) == governed_id)
        assert index_clone < index_governed, (index_clone, index_governed)
        codes = list(candidates[index_clone]["requirement_codes"])
        assert len(codes) == 19 and "B1RT_068e737e" in codes
        assert cc.is_governed_catalogue_version(candidates[index_clone]) is False

        # The pre-fix rule pressed past the governed catalogue: one governed code
        # was the entire test it applied.
        legacy = _legacy_rule_selection(candidates)
        assert legacy is not None and str(legacy["id"]) == clone_id

        # Projecting that version is impossible — a non-governed row has no governed
        # dimension, and the projection refuses to invent one. The pre-fix selection
        # was therefore a claim defect and an availability defect at once.
        with pytest.raises(DisclosureViolation):
            await _project_version(tx, candidates[index_clone])

        # The shipped rule: still exactly one catalogue, and a healthy surface.
        governed = [c for c in candidates if cc.is_governed_catalogue_version(c)]
        assert [str(c["id"]) for c in governed] == [governed_id]
        response = await _get(tx)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["framework_version"]["version_label"] == VERSION_LABEL
        assert len(body["requirements"]) == 18
        assert body["scope3_capability_rollup"] == ROLLUP
        assert "Competing row" not in json.dumps(body)

    assert await _requirement_row_count(pool, clone_id) == 0
    assert await _catalogue_digest(pool) == before


async def test_a_version_with_no_requirement_rows_is_not_a_candidate_at_all(
    pool: asyncpg.Pool,
) -> None:
    """A candidate is defined by its rows; an empty version cannot claim or confuse.

    The read model aggregates requirement rows, so a version carrying none is not
    offered at all. That is what stops an empty version becoming a phantom second
    catalogue (a spurious 503) and pins the join semantics the identity rule relies
    on: this test should fail loudly if that read ever becomes an outer join.
    """
    before = await _catalogue_digest(pool)
    governed_id = str((await _select(pool))["id"])

    async with _rolled_back(pool) as tx:
        empty_id = await _insert_competing_version(
            tx._connection, f"AAA-P17M2-empty-{uuid.uuid4().hex[:8]}"
        )
        assert await _requirement_row_count(tx._connection, empty_id) == 0

        candidates = await _candidates(tx)
        assert all(str(c["id"]) != empty_id for c in candidates)
        assert str(cc.select_governed_catalogue_version(candidates)["id"]) == governed_id

        response = await _get(tx)
        assert response.status_code == 200, response.text
        assert response.json()["framework_version"]["version_label"] == VERSION_LABEL
        assert str(empty_id) not in response.text

    assert await _catalogue_digest(pool) == before


# ---------------------------------------------------------------------------
# Helper — a real, separate database that has no catalogue at all
# ---------------------------------------------------------------------------
@contextlib.asynccontextmanager
async def _temporary_pool(dsn: str) -> AsyncIterator[asyncpg.Pool]:
    """A second real pool, guarded by the same `F-046-1` refusal.

    Used only for read-only verification against an un-provisioned clone: this
    module writes nothing there.
    """
    name = urlparse(dsn).path.lstrip("/")
    _refuse_persistent_target(name)
    created = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=2)
    try:
        actual = str(await created.fetchval("SELECT current_database()"))
        assert actual == name, f"expected to talk to {name!r}, connected to {actual!r}"
        yield created
    finally:
        await created.close()


async def test_a_database_without_the_catalogue_states_no_claim() -> None:
    """Un-provisioned catalogue ⇒ **503** with no claim (never a partial one).

    Verified against a real second database that holds no catalogue rows at all,
    so this is the SQL's own empty result, not a fake read model. Configure it
    with ``INTEGRATION_NOCAT_DATABASE_URL``; the test skips with an explicit
    reason (rather than quietly passing) when it is not configured.
    """
    dsn = os.environ.get(NO_CATALOGUE_ENV)
    if not dsn:
        pytest.skip(
            f"{NO_CATALOGUE_ENV} is not set — create a disposable `ct_*` clone with no "
            "catalogue rows and point the variable at it"
        )

    async with _temporary_pool(dsn) as absent:
        assert await _candidates(absent) == []
        assert cc.select_governed_catalogue_version([]) is None
        assert _legacy_rule_selection([]) is None

        response = await _get(absent, _user(str(uuid.uuid4()), str(uuid.uuid4())))
        assert response.status_code == 503, response.text
        body = response.json()
        assert _claims_in(body) is False
        assert "not provisioned" in json.dumps(body).lower()
        for token in ("SUPPORTED", "PARTIALLY_SUPPORTED", "MISSING_CAPABILITY", "rollup"):
            assert token not in response.text


# ===========================================================================
# 4. The claim is product-level truth: no tenant can move it, attacker included
# ===========================================================================
async def test_two_real_tenants_receive_the_same_claim_under_the_attack(
    pool: asyncpg.Pool,
) -> None:
    """`CS-1`/`CS-2`/`SEC-1` — with the adversary persisted, both tenants agree.

    Two **real** organisation rows are created on the same rolled-back
    connection, and the same request is made as an owner of each. Under `DEF-1`
    the danger was not a per-tenant difference but a *global* claim change; this
    asserts both halves: the claim is canonical for each caller, and the two
    callers' payloads are identical even while a competing governed-looking
    version is offered first.
    """
    before = await _catalogue_digest(pool)
    governed_id = str((await _select(pool))["id"])

    async with _rolled_back(pool) as tx:
        first = await _make_org(tx, f"P17M2 Tenant A {uuid.uuid4().hex[:8]}")
        second = await _make_org(tx, f"P17M2 Tenant B {uuid.uuid4().hex[:8]}")
        assert first != second

        competitor_id = await _insert_competing_version(
            tx._connection, f"AAA-P17M2-tenant-{uuid.uuid4().hex[:8]}"
        )
        await _insert_requirement(tx._connection, competitor_id, "GP-S3-CAT-15", "SUPPORTED")

        candidates = await _candidates(tx)
        legacy = _legacy_rule_selection(candidates)
        assert legacy is not None and str(legacy["id"]) == competitor_id
        assert str((await _select(tx))["id"]) == governed_id

        left = await _get(tx, _user(first, str(uuid.uuid4()), "owner-a@example.test"))
        right = await _get(tx, _user(second, str(uuid.uuid4()), "owner-b@example.test"))
        assert left.status_code == 200 and right.status_code == 200, (left.text, right.text)

        # Identical bodies: a product fact, not a tenant projection.
        assert left.json() == right.json()
        body = left.json()
        assert body["framework_version"]["version_label"] == VERSION_LABEL
        assert body["scope3_capability_rollup"] == ROLLUP
        assert _requirement_payloads(body)["GP-S3-CAT-15"]["carbontally_capability"] == "FUTURE"
        assert str(first) not in left.text and str(second) not in left.text
        assert str(competitor_id) not in left.text

    assert await _requirement_row_count(pool, competitor_id) == 0
    assert await _catalogue_digest(pool) == before


# ===========================================================================
# 5. The fix is in the **shipped** code, not only in this suite's expectations
# ===========================================================================
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (BACKEND_ROOT / relative).read_text(encoding="utf-8")


def _code_only(source: str, anchor: str, until: str | None = None) -> str:
    """The code after the docstring that precedes ``anchor`` (comments kept).

    Docstrings legitimately *describe* the removed ordering (`source_tier`,
    `IN_FORCE`), so the assertions below inspect only executable text. When
    ``until`` is given, the slice stops at its next occurrence after the anchor,
    which keeps the check inside one handler rather than the whole module.
    """
    start = source.index(anchor)
    doc_end = source.rindex('"""', 0, start)
    end = len(source)
    if until is not None and until in source[start:]:
        end = source.index(until, start)
    return source[doc_end + 3 : end]


def _method_sql(source: str, name: str) -> str:
    """The executable body of ``async def <name>`` (its docstring stripped)."""
    start = source.index(f"async def {name}")
    opening = source.index('"""', start)
    closing = source.index('"""', opening + 3)
    after = source.index("\n    async def ", closing)
    return source[closing + 3 : after]


async def test_the_shipped_route_selects_by_identity_not_by_position(
    pool: asyncpg.Pool,
) -> None:
    """Read from disk: the route calls the selector and refuses to guess."""
    source = _source("api/v3_disclosure.py")
    code = _code_only(source, "catalog = DisclosureCatalogRepository(pool)")

    assert "candidates = await catalog.capability_catalogue_candidates()" in code
    assert "select_governed_catalogue_version(candidates)" in code
    assert "if selected is None:" in code

    # The pre-fix expression is gone from the module entirely ...
    assert "is_governed_requirement_code" not in source
    assert re.search(r"next\(\s*candidate for candidate in candidates", source) is None

    # ... and no ordering input survives as a selection signal in the handler.
    assert "source_tier" not in code
    assert "IN_FORCE" not in code
    assert "version_label" not in code
    assert "ORDER BY" not in code.upper()

    # Fail-closed branches are present with their governed wording.
    assert code.count("status_code=503") >= 3
    assert "ambiguous governed catalogue" in code
    assert (
        "capability surface: no framework version carries a governed requirement catalogue"
        in code
    )
    assert "is not provisioned, so no " in code
    assert "Made rather than an unverified one" in code or "made rather than an unverified one" in code


async def test_the_shipped_order_by_is_not_a_precedence_rule(pool: asyncpg.Pool) -> None:
    """Read from disk: the repository order is deterministic, never a choice.

    ``DEF-1`` was only possible because the SQL ordered candidates by authority
    (``IN_FORCE``, ``source_tier``) and the caller took the first hit. The shipped
    SQL must order for reproducibility only, and must expose the requirement codes
    the identity rule needs.
    """
    source = _source("data/disclosure.py")
    sql = _method_sql(source, "capability_catalogue_candidates")

    assert "ORDER BY f.code, fv.version_label, fv.id" in sql
    assert "array_agg(rv.requirement_code" in sql
    assert "requirement_codes" in sql
    # Ordering authority words may appear in the *projection* (the payload carries
    # them for honest reporting, and ``array_agg`` needs an inner ORDER BY) but the
    # outer ORDER BY clause — the only one selection could have leaned on — must be
    # a pure reproducibility key.
    tail = sql[sql.rindex("ORDER BY") :]
    match = re.search(r"ORDER BY ([^\"']*)", tail)
    assert match is not None, tail
    clause = match.group(1).strip()
    assert clause == "f.code, fv.version_label, fv.id"
    for forbidden in ("IN_FORCE", "source_tier", "status", "verified_at", " NULLS "):
        assert forbidden not in clause, (forbidden, clause)
    assert " DRAFT" not in sql and "SUPERSEDED" not in sql


async def test_the_read_path_writes_nothing(pool: asyncpg.Pool) -> None:
    """`AG-5`/`SEC-3` — the surface is a reader; the clone is byte-identical after.

    Both halves are checked: the shipped statements contain no write verb, and the
    real tables are unchanged by a real request.
    """
    source = _source("data/disclosure.py")
    statements = _method_sql(source, "capability_catalogue_candidates") + _method_sql(
        source, "list_capability_catalogue_requirements"
    )
    route_code = _code_only(
        source=_source("api/v3_disclosure.py"),
        anchor="candidates = await",
        until="\n@router.",
    )
    for verb in ("INSERT ", "UPDATE ", "DELETE ", "TRUNCATE", "ALTER "):
        assert verb not in statements, verb
        assert verb not in route_code, verb

    before = await _catalogue_digest(pool)
    counts = [
        await pool.fetchval(f"SELECT count(*)::int FROM public.{table}")
        for table in CATALOGUE_TABLES
    ]
    response = await _get(pool)
    assert response.status_code == 200, response.text
    assert await _catalogue_digest(pool) == before
    after = [
        await pool.fetchval(f"SELECT count(*)::int FROM public.{table}")
        for table in CATALOGUE_TABLES
    ]
    assert after == counts
