"""P17-M2 — `DEF-1` regression exercised through the real capability route.

`P17-M` showed that `GET /api/v3/capabilities` could be hijacked by a second
`GHG_PROTOCOL` framework version that was `IN_FORCE`, `source_tier` 1, sorted
lexically before the governed version and carried **one** governed requirement
code (`GP-S3-CAT-01` → `SUPPORTED`). The endpoint then answered **200** with 1
requirement, category 1 `SUPPORTED` and rollup `1/0/0/0` — a narrower and
*upgraded* product claim.

This suite pins the fix at the HTTP surface. Only the database is faked: the
route, the governed identity module and the canonical projection are production
code. The fake offers the competing version **first**, so a regression to
positional selection fails here even if it changes nothing else.

Required outcomes under the adversarial state (`P17-M2` §5 case C, §6):

* the canonical 18-row `4/6/3/2` payload is served unchanged, or
* the surface fails closed (`503`) with no claim at all.

Anything else — a 200 carrying the competing catalogue, a changed `M-1` value, a
changed rollup, or a silent upgrade — is a failure of this suite.
"""
from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.v3_disclosure as disclosure_api
from api.v3_disclosure import router as disclosure_router
from auth import AuthUser, get_current_user
from domain import capability_catalogue as cc

ROUTE = "/api/v3/capabilities"

#: Persisted identities used by the fake read model.
GOVERNED_VERSION_ID = "22222222-2222-4222-8222-222222222222"
HIJACK_VERSION_ID = "33333333-3333-4333-8333-333333333333"
DUPLICATE_VERSION_ID = "66666666-6666-4666-8666-666666666666"
GOVERNED_LABEL = "Corporate Accounting and Reporting Standard (2004 revised edition)"
UNRESOLVED = "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION"

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

GOVERNED_CODES: tuple[str, ...] = ("GP-S1", "GP-S2-LB", "GP-S2-MB", *tuple(M1_IMAGE))

CAPABILITY_BY_CODE: dict[str, str] = {
    "GP-S1": "SUPPORTED",
    "GP-S2-LB": "SUPPORTED",
    "GP-S2-MB": "MISSING_CAPABILITY",
    **M1_IMAGE,
}


def _row(code: str, capability: str | None = None) -> dict[str, Any]:
    """One catalogue row as the repository returns it (real column names)."""
    category = int(code[-2:]) if "-CAT-" in code else None
    return {
        "id": f"00000000-0000-4000-8000-0000000000{code[-2:]}",
        "requirement_code": code,
        "title": f"Governed requirement {code}",
        "description": f"Governed description of {code}.",
        "requirement_class": "CONDITIONAL" if category else "REQUIRED",
        "carbontally_capability": capability or CAPABILITY_BY_CODE[code],
        "is_quantitative": True,
        "value_kind": "QUANTITATIVE",
        "unit_hint": "kgCO2e",
        "scope_hint": "Scope 3" if category else "Scope 1",
        "scope2_method_hint": {
            "GP-S2-LB": "LOCATION_BASED",
            "GP-S2-MB": "MARKET_BASED",
        }.get(code),
        "display_order": category or 1,
        "source_locator": "GHG Protocol Corporate Standard (2004 revised edition)",
        "authoritative_text_ref": "Persisted governed reference text.",
        "source_tier": 1,
        "official_identifier": None,
        "identifier_status": UNRESOLVED,
        "framework_code": "GHG_PROTOCOL",
        "framework_version_label": GOVERNED_LABEL,
        "framework_version_status": "IN_FORCE",
    }


def _catalogue_rows() -> list[dict[str, Any]]:
    return [_row(code) for code in GOVERNED_CODES]


def _candidate(
    *,
    version_id: str,
    label: str,
    codes: list[str],
    status: str = "IN_FORCE",
    source_tier: int = 1,
) -> dict[str, Any]:
    return {
        "id": version_id,
        "framework_id": "11111111-1111-4111-8111-111111111111",
        "version_label": label,
        "legal_reference": None,
        "source_tier": source_tier,
        "source_url": "https://ghgprotocol.org/corporate-standard",
        "authoritative_source_date": None,
        "status": status,
        "applicable_from": None,
        "applicable_to": None,
        "verified_at": None,
        "framework_code": "GHG_PROTOCOL",
        "requirement_codes": list(codes),
    }


def _def1_hijack() -> dict[str, Any]:
    """The exact adversarial candidate from `P17-M`: in-force, tier 1, early label."""
    return _candidate(
        version_id=HIJACK_VERSION_ID,
        label="AAA-P17M2-hijack",
        codes=["GP-S3-CAT-01"],
    )


class _FakeCatalogRepository:
    """The only faked collaborator: the catalogue read model."""

    def __init__(self, pool: Any = None) -> None:
        self.pool = pool
        self.framework_present = True
        self.candidates_present = True
        self.rows: list[dict[str, Any]] = _catalogue_rows()
        #: Candidate versions offered **before** the governed one.
        self.extra_candidates: list[dict[str, Any]] = []
        #: Every framework version id the surface asked for — proves the surface
        #: never read a competing version's rows.
        self.requested_version_ids: list[str] = []

    @property
    def candidates(self) -> list[dict[str, Any]]:
        return [
            *self.extra_candidates,
            _candidate(
                version_id=GOVERNED_VERSION_ID,
                label=GOVERNED_LABEL,
                codes=sorted(CAPABILITY_BY_CODE),
            ),
        ]

    async def get_framework_by_code(self, code: str) -> dict[str, Any] | None:
        if not self.framework_present:
            return None
        return {
            "id": "11111111-1111-4111-8111-111111111111",
            "code": code,
            "name": "GHG Protocol Corporate Standard",
            "publisher": "GHG Protocol / WRI & WBCSD",
            "kind": "accounting_foundation",
            "is_primary_foundation": True,
            "description": None,
        }

    async def capability_catalogue_candidates(self) -> list[dict[str, Any]]:
        return self.candidates if self.candidates_present else []

    async def list_capability_catalogue_requirements(
        self, framework_version_id: str
    ) -> list[dict[str, Any]]:
        self.requested_version_ids.append(framework_version_id)
        if framework_version_id == GOVERNED_VERSION_ID:
            return self.rows
        # The competing version's own single row: `GP-S3-CAT-01` as `SUPPORTED`.
        # If the surface ever selected it, the payload would claim 1 requirement
        # and rollup `1/0/0/0` — the `DEF-1` failure this suite forbids.
        return [_row("GP-S3-CAT-01", capability="SUPPORTED")]


def _user(
    user_id: str = "66666666-6666-4666-8666-666666666666",
    organization_id: str | None = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
) -> AuthUser:
    """An authenticated actor; the payload must not depend on who is asking."""
    return AuthUser(
        user_id=user_id,
        email="owner@example.test",
        role="owner",
        organization_id=organization_id,
        is_org_member=True,
    )


@pytest.fixture
def repository(monkeypatch: pytest.MonkeyPatch) -> _FakeCatalogRepository:
    repo = _FakeCatalogRepository()
    monkeypatch.setattr(
        disclosure_api, "DisclosureCatalogRepository", lambda pool=None: repo
    )
    return repo


def _client(
    monkeypatch: pytest.MonkeyPatch,
    repository: _FakeCatalogRepository | None = None,
    **kw: Any,
) -> TestClient:
    repo = repository or _FakeCatalogRepository()
    monkeypatch.setattr(
        disclosure_api, "DisclosureCatalogRepository", lambda pool=None: repo
    )
    app = FastAPI()
    app.include_router(disclosure_router)
    app.dependency_overrides[disclosure_api.get_pool] = lambda: object()
    app.dependency_overrides[get_current_user] = kw.pop("user", lambda: _user())
    return TestClient(app)


def _serialised(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=str)


def _claim(client: TestClient) -> dict[str, Any]:
    response = client.get(ROUTE)
    assert response.status_code == 200, response.text
    return response.json()


def _refusal(client: TestClient) -> str:
    """The surface refused to state anything: 503 and no capability claim."""
    response = client.get(ROUTE)
    assert response.status_code == 503, response.text
    body = response.text
    assert "requirements" not in body, body
    assert "scope3_capability_rollup" not in body, body
    assert "PARTIALLY_SUPPORTED" not in body, body
    return body


def _category_capabilities(payload: dict[str, Any]) -> dict[str, str]:
    return {
        item["requirement_code"]: item["carbontally_capability"]
        for item in payload["requirements"]
        if item["requirement_code"] in M1_IMAGE
    }


def _assert_the_canonical_claim(payload: dict[str, Any]) -> None:
    """The governed statement, asserted in full — no widening, no narrowing."""
    assert payload["surface"] == "CAPABILITY_TRUTH"
    assert len(payload["requirements"]) == 18
    assert payload["framework_version"]["version_label"] == GOVERNED_LABEL
    assert _category_capabilities(payload) == M1_IMAGE
    assert payload["scope3_capability_rollup"] == ROLLUP
    text = _serialised(payload)
    assert "AAA-P17M2-hijack" not in text
    assert HIJACK_VERSION_ID not in text


def _superset_of_the_catalogue() -> dict[str, Any]:
    """A version carrying the full governed set **plus** an extra identity.

    A wider requirement set is a different catalogue (a transition is a PO
    decision), so it is not the governed catalogue.
    """
    return _candidate(
        version_id="44444444-4444-4444-8444-444444444444",
        label="AAA-superset",
        codes=[*sorted(CAPABILITY_BY_CODE), "GP-S3-CAT-99"],
    )


def _residue_version() -> dict[str, Any]:
    """A version whose codes are not governed requirement identities at all."""
    return _candidate(
        version_id="55555555-5555-4555-8555-555555555555",
        label="AAA-B1RT",
        codes=["B1RT-00000001"],
        status="DRAFT",
        source_tier=9,
    )


def _duplicate_of_the_catalogue() -> dict[str, Any]:
    return _candidate(
        version_id=DUPLICATE_VERSION_ID,
        label="ZZZ-duplicate",
        codes=sorted(CAPABILITY_BY_CODE),
        status="SUPERSEDED",
        source_tier=3,
    )


# ===========================================================================
# 1. The baseline, and the two honest refusals
# ===========================================================================
def test_the_governed_catalogue_is_served_when_it_alone_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _FakeCatalogRepository()
    _assert_the_canonical_claim(_claim(_client(monkeypatch, repo)))
    # The surface read exactly the version it selected, and only that version.
    assert repo.requested_version_ids == [GOVERNED_VERSION_ID]


def test_a_malformed_capability_value_yields_no_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A value outside the governed vocabulary is never rendered (`AG-1`)."""
    repo = _FakeCatalogRepository()
    for row in repo.rows:
        if row["requirement_code"] == "GP-S3-CAT-01":
            row["carbontally_capability"] = "PARTIAL"  # an Axis-A token
    body = _refusal(_client(monkeypatch, repo))
    assert "PARTIAL" not in body


def test_an_unprovisioned_catalogue_yields_no_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _FakeCatalogRepository()
    repo.candidates_present = False
    body = _refusal(_client(monkeypatch, repo))
    assert "not provisioned" in body
    assert repo.requested_version_ids == []


# ===========================================================================
# 2. DEF-1 — a competing version, offered first, cannot replace the catalogue
# ===========================================================================
@pytest.mark.parametrize(
    "hostile",
    [
        pytest.param(_def1_hijack(), id="one-governed-code-upgraded-to-SUPPORTED"),
        pytest.param(_superset_of_the_catalogue(), id="complete-set-plus-extra-code"),
        pytest.param(_residue_version(), id="non-governed-codes-only"),
    ],
)
def test_def1_the_competing_version_never_replaces_the_catalogue(
    monkeypatch: pytest.MonkeyPatch, hostile: dict[str, Any]
) -> None:
    repo = _FakeCatalogRepository()
    repo.extra_candidates.append(hostile)
    # The hostile condition itself: the competing version leads the candidate
    # list. Under the pre-fix rule (`any(is_governed_requirement_code(...))`) the
    # first candidate won, so this ordering is what made `DEF-1` reachable.
    assert repo.candidates[0]["id"] == hostile["id"]
    assert repo.candidates[0]["status"] == hostile["status"]
    client = _client(monkeypatch, repo)

    _assert_the_canonical_claim(_claim(client))
    # The competing version's rows were never read, so its claims cannot appear.
    assert repo.requested_version_ids == [GOVERNED_VERSION_ID]
    assert hostile["id"] not in repo.requested_version_ids


def test_def1_the_rule_that_let_it_through_is_really_defeated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adversary is *viable* under the pre-fix predicate, defeated only by identity."""
    hostile = _def1_hijack()
    # Pre-fix viability: the candidate carries at least one governed code, and it
    # leads the ordered candidate list.
    assert cc.is_governed_requirement_code("GP-S3-CAT-01") is True
    assert hostile["status"] == "IN_FORCE" and hostile["source_tier"] == 1
    assert hostile["version_label"] < GOVERNED_LABEL
    # Post-fix: it is not the governed catalogue, because it is incomplete.
    assert cc.is_governed_catalogue_version(hostile) is False
    assert cc.is_governed_catalogue_version(
        _candidate(
            version_id=GOVERNED_VERSION_ID,
            label=GOVERNED_LABEL,
            codes=sorted(CAPABILITY_BY_CODE),
        )
    ) is True

    repo = _FakeCatalogRepository()
    repo.extra_candidates.append(hostile)
    _assert_the_canonical_claim(_claim(_client(monkeypatch, repo)))


def test_def1_no_value_is_silently_upgraded_over_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The upgrade `DEF-1` produced can no longer be stated.

    The competing version records `GP-S3-CAT-01` as `SUPPORTED`; the governed
    catalogue records `PARTIALLY_SUPPORTED`, bounded support (`supported = True`).
    """
    repo = _FakeCatalogRepository()
    repo.extra_candidates.append(_def1_hijack())
    payload = _claim(_client(monkeypatch, repo))
    by_code = {item["requirement_code"]: item for item in payload["requirements"]}

    assert by_code["GP-S3-CAT-01"]["carbontally_capability"] == "PARTIALLY_SUPPORTED"
    assert by_code["GP-S3-CAT-01"]["supported"] is True
    # The category-1 row is exactly the governed row: nothing else came with it.
    assert by_code["GP-S3-CAT-01"]["framework_version_label"] == GOVERNED_LABEL
    assert by_code["GP-S3-CAT-01"]["provenance"]["source_tier"] == 1
    assert by_code["GP-S3-CAT-01"]["provenance"]["identifier_status"] == UNRESOLVED
    # The upgraded 1/0/0/0 statement is not reachable in any form.
    assert payload["scope3_capability_rollup"] == ROLLUP
    assert len(payload["requirements"]) == 18


def test_a_second_complete_governed_catalogue_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two candidates claim the catalogue identity: no claim, never a chosen one."""
    repo = _FakeCatalogRepository()
    repo.extra_candidates.append(_duplicate_of_the_catalogue())
    body = _refusal(_client(monkeypatch, repo))
    assert "ambiguous" in body
    assert repo.requested_version_ids == []


def test_two_tenant_contexts_see_the_same_canonical_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`CS-2`/`AG-6` under the adversarial state: the claim does not vary."""
    customer = _client(monkeypatch, _FakeCatalogRepository(), user=lambda: _user())
    repo = _FakeCatalogRepository()
    repo.extra_candidates.append(_def1_hijack())
    other = _client(
        monkeypatch,
        repo,
        user=lambda: _user(
            user_id="77777777-7777-4777-8777-777777777777",
            organization_id=None,
        ),
    )
    first = _serialised(_claim(customer))
    second = _serialised(_claim(other))
    assert first == second




