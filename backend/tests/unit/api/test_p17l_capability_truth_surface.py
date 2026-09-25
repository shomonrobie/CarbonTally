"""P17-L — the governed capability truth surface, exercised through the real route.

`P17-DECISION-03 §18.3` defines the gates `AG-1`…`AG-8` for **any** capability
surface. `P17-K` met them at the catalogue/projection layer and reported the
*rendering* branches as **PENDING** because no surface existed. This suite closes
the branches a route + payload can close:

* `AG-3` — no Axis-A token is renderable (`IV-1`, `F-3`);
* `AG-4` — no placeholder and no fabricated figure (`F-6`);
* `AG-5` — no tenant identifier and no tenant query path (`SEC-1`, `SEC-3`);
* `AG-6` — the same requirement shows the same value to every caller (`CS-2`);
* `AG-7` — the four-way rollup, never a total (`S3-1`);
* `AG-8` — every claim resolves to persisted provenance or an explicit
  unresolved marker.

`AG-1` and `AG-2` are preserved (value-set membership and distinctness), and the
security gates are tested as **both** ALLOW and DENY (`AGENTS.md §72`).

Only the database is faked: the route, the canonical projection module and the
governed vocabulary constants are production code. The mounted application is
also asserted to expose exactly one capability route — the duplicate-endpoint
risk `§16` warns about.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.v3_disclosure as disclosure_api
from api.v3_disclosure import router as disclosure_router
from auth import AuthUser, get_current_user
from domain.disclosure import CARBONTALLY_CAPABILITIES, REQUIREMENT_CLASSES
from domain.disclosure_projection import UNSUPPORTED_CAPABILITIES

ROUTE = "/api/v3/capabilities"

#: The frozen `M-1` image of the category matrix (P17-DECISION-03 §11.1/§11.2),
#: byte-for-byte the P17-K runtime expectation.
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

_VERSION_LABEL = "Corporate Accounting and Reporting Standard (2004 revised edition)"

_UNRESOLVED = "UNRESOLVED_AUTHORITATIVE_SOURCE_LIMITATION"


def _requirement_row(code: str, capability: str, title: str, description: str) -> dict[str, Any]:
    """One catalogue row as the repository returns it (real column names)."""
    return {
        "id": f"00000000-0000-4000-8000-0000000000{code[-2:]}",
        "requirement_code": code,
        "title": title,
        "description": description,
        "requirement_class": "REQUIRED" if code.startswith("GP-S1") or code.startswith("GP-S2") else "CONDITIONAL",
        "carbontally_capability": capability,
        "is_quantitative": True,
        "value_kind": "QUANTITATIVE",
        "unit_hint": "kgCO2e",
        "scope_hint": "Scope 1",
        "scope2_method_hint": None,
        "display_order": 1,
        "source_locator": "GHG Protocol Corporate Value Chain (Scope 3) Standard",
        "authoritative_text_ref": (
            "GHG Protocol Corporate Standard (2004 revised edition) — Chapter 9 "
            "required-information lists not readable (binary PDF)"
        ),
        "source_tier": 1,
        "official_identifier": None,
        "identifier_status": _UNRESOLVED,
        "framework_code": "GHG_PROTOCOL",
        "framework_version_label": _VERSION_LABEL,
        "framework_version_status": "IN_FORCE",
    }


def catalogue_rows_codes() -> list[str]:
    """The requirement codes the fixture catalogue carries."""
    return [row["requirement_code"] for row in catalogue_rows()]


def catalogue_rows() -> list[dict[str, Any]]:
    """The 18 governed requirement rows, in the persisted shape."""
    scope1 = _requirement_row(
        "GP-S1", "SUPPORTED", "Scope 1 emissions",
        "Direct GHG emissions from sources owned or controlled by the reporting organisation.",
    )
    scope2_lb = _requirement_row(
        "GP-S2-LB", "SUPPORTED", "Scope 2 emissions — location-based",
        "Indirect GHG emissions, accounted on the location-based method.",
    )
    scope2_lb.update({"scope_hint": "Scope 2", "scope2_method_hint": "LOCATION_BASED"})
    scope2_mb = _requirement_row(
        "GP-S2-MB", "MISSING_CAPABILITY", "Scope 2 emissions — market-based",
        "No market-based engine is available, so this requirement is expected but not producible.",
    )
    scope2_mb.update({"scope_hint": "Scope 2", "scope2_method_hint": "MARKET_BASED"})
    rows = [scope1, scope2_lb, scope2_mb]
    for index, (code, capability) in enumerate(M1_IMAGE.items(), start=1):
        category = int(code[-2:])
        row = _requirement_row(
            code, capability, f"Scope 3 category {category} — Category {category}",
            f"Bounded scope. Prerequisite: the category {category} prerequisite.",
        )
        row.update(
            {
                "scope_hint": "Scope 3",
                "requirement_class": "CONDITIONAL",
                "display_order": 100 + index,
            }
        )
        rows.append(row)
    return rows


class _FakeCatalogRepository:
    """Stands in for ``DisclosureCatalogRepository`` (the only faked collaborator)."""

    def __init__(self, pool: Any = None) -> None:
        self.pool = pool
        self.framework_present = True
        self.versions_present = True
        #: Extra candidate versions the fake will offer **before** the governed
        #: one — used to prove the surface selects the governed catalogue by rule
        #: rather than by ordering.
        self.extra_candidates: list[dict[str, Any]] = []
        #: The framework version the surface asked for (proves version scoping).
        self.requested_version_id: Optional[str] = None
        #: Every query text this fake issued, so the tenant-query audit
        #: (`SEC-3`, `AG-5`) checks the *path*, not only the rendered output.
        self.queries: list[str] = []

    async def get_framework_by_code(self, code: str) -> Optional[dict[str, Any]]:
        self.queries.append("SELECT ... FROM public.disclosure_frameworks WHERE code = $1")
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
        self.queries.append(
            "SELECT ... FROM public.disclosure_framework_versions fv "
            "JOIN public.disclosure_frameworks f ... "
            "JOIN public.disclosure_requirement_versions rv ... GROUP BY ..."
        )
        if not self.versions_present:
            return []
        return [
            *self.extra_candidates,
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "framework_id": "11111111-1111-4111-8111-111111111111",
                "version_label": _VERSION_LABEL,
                "legal_reference": None,
                "source_tier": 1,
                "source_url": "https://ghgprotocol.org/corporate-standard",
                "authoritative_source_date": None,
                "status": "IN_FORCE",
                "applicable_from": None,
                "applicable_to": None,
                "verified_at": None,
                "framework_code": "GHG_PROTOCOL",
                "requirement_codes": sorted(catalogue_rows_codes()),
            },
        ]

    async def list_framework_versions(self, framework_id: str) -> list[dict[str, Any]]:
        self.queries.append(
            "SELECT ... FROM public.disclosure_framework_versions WHERE framework_id = $1"
        )
        if not self.versions_present:
            return []
        return [
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "framework_id": framework_id,
                "version_label": _VERSION_LABEL,
                "legal_reference": None,
                "source_tier": 1,
                "source_url": "https://ghgprotocol.org/corporate-standard",
                "authoritative_source_date": None,
                "status": "IN_FORCE",
                "applicable_from": None,
                "applicable_to": None,
                "verified_at": None,
            }
        ]

    async def list_capability_catalogue_requirements(
        self, framework_version_id: str
    ) -> list[dict[str, Any]]:
        self.queries.append(
            "SELECT ... FROM public.disclosure_requirement_versions rv "
            "JOIN public.disclosure_framework_versions fv ON fv.id = rv.framework_version_id "
            "JOIN public.disclosure_frameworks f ON f.id = fv.framework_id "
            "WHERE rv.framework_version_id = $1"
        )
        self.requested_version_id = framework_version_id
        return catalogue_rows()



def _user(
    user_id: str = "66666666-6666-4666-8666-666666666666",
    organization_id: Optional[str] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
) -> AuthUser:
    """An authenticated actor; the tenant dimension of the payload must not see it."""
    return AuthUser(
        user_id=user_id,
        email="owner@example.test",
        role="owner",
        organization_id=organization_id,
        is_org_member=True,
    )


@pytest.fixture
def repository(monkeypatch: pytest.MonkeyPatch) -> _FakeCatalogRepository:
    """Replace the *only* collaborator the route constructs itself."""
    repo = _FakeCatalogRepository()
    monkeypatch.setattr(
        disclosure_api, "DisclosureCatalogRepository", lambda pool=None: repo
    )
    return repo


def _app(monkeypatch: pytest.MonkeyPatch, repository: _FakeCatalogRepository, **kw: Any) -> FastAPI:
    monkeypatch.setattr(
        disclosure_api, "DisclosureCatalogRepository", lambda pool=None: repository
    )
    app = FastAPI()
    app.include_router(disclosure_router)
    app.dependency_overrides[disclosure_api.get_pool] = lambda: object()
    app.dependency_overrides[get_current_user] = kw.pop("user", lambda: _user())
    return app


def _app_without_auth_override() -> FastAPI:
    """The route mounted with **no** auth override — the real DENY path."""
    app = FastAPI()
    app.include_router(disclosure_router)
    return app


def _client(
    monkeypatch: pytest.MonkeyPatch, repository: Optional[_FakeCatalogRepository] = None, **kw: Any
) -> TestClient:
    return TestClient(_app(monkeypatch, repository or _FakeCatalogRepository(), **kw))


def _payload(client: TestClient) -> dict[str, Any]:
    response = client.get(ROUTE)
    assert response.status_code == 200, response.text
    return response.json()


def _serialised(payload: dict[str, Any]) -> str:
    return json.dumps(payload, default=str)


# ===========================================================================
# Registration — one route, no duplicate endpoint family (§16)
# ===========================================================================
def test_the_capability_route_is_registered_and_is_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The surface is a read model: exactly one GET, and no write verb."""
    app = _app(monkeypatch, _FakeCatalogRepository())
    paths = app.openapi()["paths"]
    assert ROUTE in paths, sorted(paths)
    assert list(paths[ROUTE]) == ["get"], list(paths[ROUTE])


def test_the_route_cannot_be_mounted_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    """A second capability endpoint is the duplicate `§16` forbids."""
    app = _app(monkeypatch, _FakeCatalogRepository())
    paths = app.openapi()["paths"]
    assert len([p for p in paths if p == ROUTE]) == 1, sorted(paths)


def test_no_second_capability_named_route_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _app(monkeypatch, _FakeCatalogRepository())
    capability_like = [
        path for path in app.openapi()["paths"] if re.search(r"capabilit", path, re.IGNORECASE)
    ]
    assert capability_like == [ROUTE], capability_like


# ===========================================================================
# Authentication (AGENTS.md §72 — DENY branch)
# ===========================================================================
def test_an_unauthenticated_request_is_refused() -> None:
    client = TestClient(_app_without_auth_override())
    response = client.get(ROUTE)  # no Authorization header, no override
    assert response.status_code == 401, response.text


def test_the_route_declares_an_authentication_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Authentication is a route dependency, never a client-side convention.

    The route's own behaviour proves it independently: with no override and no
    ``Authorization`` header the surface answers **401**, which is only possible
    because the route resolved and refused — a missing route would be **404**.
    """
    unauthenticated = TestClient(_app_without_auth_override())
    response = unauthenticated.get(ROUTE)
    assert response.status_code == 401, response.text

    app = _app(monkeypatch, _FakeCatalogRepository())
    operation = app.openapi()["paths"][ROUTE]["get"]
    declared = {
        parameter
        for parameter in [p.get("name") for p in operation.get("parameters", [])]
        if parameter
    }
    # The capability surface accepts no tenant context at all (AG-5/SEC-1).
    assert declared == set(), declared



# ===========================================================================
# AG-1 / §7 — the governed minimum is present for every requirement
# ===========================================================================
REQUIRED_FIELDS = (
    "requirement_code",
    "requirement_name",
    "framework_code",
    "framework_version_label",
    "scope",
    "scope2_method",
    "scope3_category",
    "carbontally_capability",
    "capability_explanation",
    "requirement_class",
    "requirement_class_expression",
    "supported",
    "provenance",
    "capability_detail",
    "result_presence",
)


def test_every_requirement_carries_the_governed_minimum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    assert payload["surface"] == "CAPABILITY_TRUTH"
    assert len(payload["requirements"]) == 18
    for item in payload["requirements"]:
        for field in REQUIRED_FIELDS:
            assert field in item, (item.get("requirement_code"), field)
        assert item["carbontally_capability"] in CARBONTALLY_CAPABILITIES
        assert item["requirement_class_expression"] in REQUIREMENT_CLASSES
        assert item["scope"] in ("Scope 1", "Scope 2", "Scope 3")


def test_ag_1_the_vocabulary_is_quoted_from_the_governed_constant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    assert payload["capability_vocabulary"] == list(CARBONTALLY_CAPABILITIES)
    assert [g["value"] for g in payload["capability_glossary"]] == list(
        CARBONTALLY_CAPABILITIES
    )
    assert all(g["explanation"].strip() for g in payload["capability_glossary"])


def test_the_m1_image_is_exact_and_never_upgraded(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(_client(monkeypatch))
    by_code = {item["requirement_code"]: item for item in payload["requirements"]}
    for code, capability in M1_IMAGE.items():
        assert by_code[code]["carbontally_capability"] == capability, code


# ===========================================================================
# AG-2 — distinct governed outcomes for non-produced items
# ===========================================================================
def test_ag_2_not_supported_and_input_required_stay_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    by_code = {item["requirement_code"]: item for item in payload["requirements"]}
    # M-1 column 3, on the real payload.
    assert by_code["GP-S3-CAT-02"]["requirement_class_expression"] == "NOT_SUPPORTED"
    assert by_code["GP-S3-CAT-10"]["requirement_class_expression"] == "NOT_SUPPORTED"
    assert by_code["GP-S3-CAT-11"]["requirement_class_expression"] == "FUTURE"
    assert by_code["GP-S3-CAT-03"]["requirement_class_expression"] == "CONDITIONAL"
    assert by_code["GP-S2-MB"]["requirement_class_expression"] == "NOT_SUPPORTED"
    # A capability value can never become an applicability outcome (PO-3 / C-5).
    assert "NOT_APPLICABLE" not in {
        item["requirement_class_expression"] for item in payload["requirements"]
    }


def test_ag_2_supported_distinction_uses_the_governed_unsupported_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    for item in payload["requirements"]:
        expected = item["carbontally_capability"] not in UNSUPPORTED_CAPABILITIES
        assert item["supported"] is expected, item["requirement_code"]
    # Bounded support is support (it is not an upgrade, and not a downgrade).
    by_code = {item["requirement_code"]: item for item in payload["requirements"]}
    assert by_code["GP-S3-CAT-01"]["supported"] is True
    assert by_code["GP-S3-CAT-02"]["supported"] is False
    assert by_code["GP-S3-CAT-11"]["supported"] is False



# ===========================================================================
# AG-3 — no Axis-A token is renderable (IV-1, F-3, §19.4 row 9)
# ===========================================================================
def test_ag_3_no_axis_a_token_is_renderable(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(_client(monkeypatch))
    text = _serialised(payload)
    # Word-boundary scan: `PARTIALLY_SUPPORTED` is a governed value, not the
    # internal token `PARTIAL` (IV-2 / IV-5).
    match = re.search(r"\b(PARTIAL|DEFERRED|NOT_IMPLEMENTED)\b", text, re.IGNORECASE)
    assert match is None, f"Axis-A token {match.group(0)!r} is renderable"


def test_ag_3_no_architecture_status_field_is_projected(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(_client(monkeypatch))
    text = _serialised(payload)
    assert "architecture_status" not in text
    assert "architecture" not in text.lower()


def test_ag_3_the_governed_value_is_still_quoted_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    """AG-3 must not be satisfied by censoring a legitimate governed value."""
    payload = _payload(_client(monkeypatch))
    values = {item["carbontally_capability"] for item in payload["requirements"]}
    assert "PARTIALLY_SUPPORTED" in values
    assert "PARTIALLY_SUPPORTED" in _serialised(payload)


# ===========================================================================
# AG-4 — no placeholder, no fabricated figure (F-6, §9.4 item 7)
# ===========================================================================
FORBIDDEN_PLACEHOLDERS = (
    "N/A",
    "not applicable",
    "excluded",
    "coming soon",
    "TBC",
    "TBD",
)


@pytest.mark.parametrize("placeholder", FORBIDDEN_PLACEHOLDERS)
def test_ag_4_no_placeholder_is_renderable(
    monkeypatch: pytest.MonkeyPatch, placeholder: str
) -> None:
    payload = _payload(_client(monkeypatch))
    assert placeholder.lower() not in _serialised(payload).lower()


def test_ag_4_no_emissions_figure_is_renderable(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(_client(monkeypatch))
    match = re.search(
        r"\d[\d,]*(?:\.\d+)?\s*(?:kg|t|tonnes?|tco2e|kgco2e)\b",
        _serialised(payload),
        re.IGNORECASE,
    )
    assert match is None, f"fabricated figure {match.group(0)!r} is renderable"


def test_ag_4_a_requirement_with_no_result_is_never_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    for item in payload["requirements"]:
        assert item["result_presence"] is None, item["requirement_code"]
        assert item["result_presence"] != 0
    assert payload["result_presence_note"]



# ===========================================================================
# AG-5 / SEC-1 / SEC-3 — no tenant identifier and no tenant query path
# ===========================================================================
TENANT_TOKENS = (
    "organization_id",
    "organisation_id",
    "tenant_id",
    "org_id",
    "facility_id",
    "supplier_id",
    "customer_id",
    "user_id",
    "report_id",
    "report_version_id",
    "current_setting",
    "auth.uid",
)


@pytest.mark.parametrize("token", TENANT_TOKENS)
def test_ag_5_no_tenant_token_is_renderable(
    monkeypatch: pytest.MonkeyPatch, token: str
) -> None:
    payload = _payload(_client(monkeypatch))
    assert token not in _serialised(payload), token


def test_ag_5_the_read_model_queries_no_tenant_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`SEC-3` checks the query *path*, not only the rendered output."""
    repository = _FakeCatalogRepository()
    _payload(_client(monkeypatch, repository))
    assert repository.queries, "the route must read the catalogue"
    tenant_tables = (
        "organizations",
        "organization_members",
        "organization_metadata",
        "facilities",
        "suppliers",
        "customer_documents",
        "calculation_snapshots",
        "emissions_logs",
        "disclosure_values",
        "disclosure_applicability_assessments",
        "report_versions",
        "reports",
    )
    for query in repository.queries:
        lowered = query.lower()
        for table in tenant_tables:
            assert table not in lowered, (query, table)
        assert "current_setting" not in lowered, query
        assert "auth.uid" not in lowered, query
        assert "organization_id" not in lowered, query


def test_ag_5_the_committed_read_model_sql_is_tenant_free() -> None:
    """The shipped read model must carry no tenant predicate (`SEC-1`, `SEC-3`).

    Both P17-L read methods are audited, against their **executable SQL
    literals** — the docstrings, which explain the property, are dropped first —
    plus the exact column list the query selects.
    """
    import ast
    import inspect
    import textwrap

    from data import disclosure as disclosure_data
    from data.disclosure import DisclosureCatalogRepository

    def executed_sql(function: Any) -> str:
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        body = list(getattr(tree.body[0], "body", []))
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            body = body[1:]  # drop the docstring: only executable SQL is audited
        return " ".join(
            node.value
            for node in ast.walk(ast.Module(body=body, type_ignores=[]))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        )

    candidates_sql = executed_sql(DisclosureCatalogRepository.capability_catalogue_candidates)
    requirements_sql = executed_sql(
        DisclosureCatalogRepository.list_capability_catalogue_requirements
    )
    columns = disclosure_data._CAPABILITY_REQUIREMENT_COLUMNS

    for sql in (candidates_sql, requirements_sql, columns):
        for forbidden in (
            "organization_id",
            "current_setting",
            "auth.uid",
            "organizations",
            "organization_members",
            "facility_id",
            "supplier_id",
            "calculation_snapshots",
            "report_versions",
        ):
            assert forbidden not in sql, (forbidden, sql)

    # ... and they read only the governed catalogue tables.
    for sql in (candidates_sql, requirements_sql):
        assert "public.disclosure_requirement_versions" in sql
        tables = set(re.findall(r"public\.\w+", sql))
        assert tables == {
            "public.disclosure_requirement_versions",
            "public.disclosure_framework_versions",
            "public.disclosure_frameworks",
        }, tables


def test_ag_5_two_tenant_contexts_see_an_identical_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§13 — the same capability response under two authorised tenant contexts."""
    first = _payload(
        _client(
            monkeypatch,
            user=lambda: _user(
                user_id="66666666-6666-4666-8666-666666666666",
                organization_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            ),
        )
    )
    monkeypatch.setattr(
        disclosure_api, "DisclosureCatalogRepository", lambda pool=None: _FakeCatalogRepository()
    )
    second = _payload(
        _client(
            monkeypatch,
            user=lambda: _user(
                user_id="77777777-7777-4777-8777-777777777777",
                organization_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            ),
        )
    )
    assert _serialised(first) == _serialised(second)


def test_the_payload_is_independent_of_who_is_asking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A customer, a consultant and internal staff get the same product truth."""
    internal = _payload(
        _client(
            monkeypatch,
            user=lambda: AuthUser(
                user_id="88888888-8888-4888-8888-888888888888",
                email="staff@carbontally.local",
                role="reviewer",
                is_staff=True,
                is_org_member=False,
            ),
        )
    )
    monkeypatch.setattr(
        disclosure_api, "DisclosureCatalogRepository", lambda pool=None: _FakeCatalogRepository()
    )
    customer = _payload(_client(monkeypatch))
    assert _serialised(internal) == _serialised(customer)
    # ... and an authenticated non-org-member is still admitted (product truth,
    # not tenant data) — the ALLOW branch of the gate.
    assert internal["requirements"]



# ===========================================================================
# AG-6 / CS-2 — the same requirement shows the same value to both surfaces
# ===========================================================================
def test_ag_6_one_governed_value_per_requirement(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(_client(monkeypatch))
    codes = [item["requirement_code"] for item in payload["requirements"]]
    assert len(codes) == len(set(codes)), "a requirement must appear exactly once"
    for item in payload["requirements"]:
        assert item["carbontally_capability"] in payload["capability_vocabulary"]


def test_ag_6_no_per_surface_variant_field_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """`CS-2` cannot be violated by construction: there is no second value field."""
    payload = _payload(_client(monkeypatch))
    text = _serialised(payload)
    for variant in ("investor_capability", "customer_capability", "surface_capability"):
        assert variant not in text, variant


def test_ag_6_both_surfaces_render_from_this_single_payload() -> None:
    """Both surfaces fetch the same route — one read model, two presentations."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[4]
    for relative in (
        "frontend/src/v3/capabilities/CapabilitiesPage.jsx",
        "frontend/src/v3/capabilities/InvestorCapabilityPage.jsx",
    ):
        source = (root / relative).read_text()
        assert "getCapabilityCatalogue" in source, relative
    component = (root / "frontend/src/v3/components/CapabilityTruthSurface.jsx").read_text()
    assert "capability_vocabulary" in component
    # No category→status table may live in the frontend (`P17-L §5`): the only
    # capability fact the surface knows is the one the projection sent it.
    assert "GP-S3-CAT-" not in component
    assert "M1_IMAGE" not in component
    assert "carbontally_capability" in component


# ===========================================================================
# AG-7 — the four-way rollup, never a total
# ===========================================================================
def test_ag_7_the_rollup_is_exactly_the_frozen_four_way_split(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    assert payload["scope3_capability_rollup"] == ROLLUP


def test_ag_7_the_rollup_recomputes_from_the_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """The rollup is derived, not stored: changing a row changes the rollup."""
    payload = _payload(_client(monkeypatch))
    counts: dict[str, int] = {}
    for item in payload["requirements"]:
        if item["scope3_category"] is None:
            continue
        counts[item["carbontally_capability"]] = (
            counts.get(item["carbontally_capability"], 0) + 1
        )
    assert payload["scope3_capability_rollup"] == counts


def _all_keys(payload: Any) -> list[str]:
    """Every mapping key in a nested payload."""
    keys: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            keys.append(str(key))
            keys.extend(_all_keys(value))
    elif isinstance(payload, list):
        for item in payload:
            keys.extend(_all_keys(item))
    return keys


def test_ag_7_no_total_or_coverage_field_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """`AG-7` is about *fields*: prose may explain the prohibition, data may not
    contain a total, a coverage figure, a score or a materiality claim."""
    payload = _payload(_client(monkeypatch))
    keys = _all_keys(payload)
    for forbidden in ("coverage", "total", "percentage", "score", "materiality", "assurance"):
        offenders = [key for key in keys if forbidden in key.lower()]
        assert offenders == [], (forbidden, offenders)
    # The rollup is the only aggregate, and it is the four-way split.
    assert set(payload["scope3_capability_rollup"]) == {
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "FUTURE",
        "MISSING_CAPABILITY",
    }


def test_ag_7_no_unqualified_fifteen_category_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    text = _serialised(payload).lower()
    assert "all 15" not in text
    assert "15 categories supported" not in text


# ===========================================================================
# AG-8 — provenance, or an explicit unresolved-source marker
# ===========================================================================
def test_ag_8_every_claim_carries_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(_client(monkeypatch))
    for item in payload["requirements"]:
        provenance = item["provenance"]
        assert provenance["source_locator"], item["requirement_code"]
        assert provenance["authoritative_text_ref"], item["requirement_code"]
        assert provenance["source_tier"] in (1, 2, 3), item["requirement_code"]


def test_ag_8_an_unresolved_identifier_is_marked_not_invented(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    for item in payload["requirements"]:
        provenance = item["provenance"]
        status = provenance["identifier_status"]
        assert status in ("RESOLVED", _UNRESOLVED), item["requirement_code"]
        if status == _UNRESOLVED:
            assert provenance["official_identifier"] is None, item["requirement_code"]


def test_ag_8_the_framework_version_carries_its_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    version = payload["framework_version"]
    assert version["version_label"] == _VERSION_LABEL
    assert version["status"] in ("IN_FORCE", "ADOPTED_NOT_IN_FORCE", "SUPERSEDED", "WITHDRAWN")
    assert version["source_tier"] in (1, 2, 3)
    # Nothing invented: an unknown authority date is null, not a guessed date.
    assert version["authoritative_source_date"] in (None, "") or re.match(
        r"\d{4}-\d{2}-\d{2}", str(version["authoritative_source_date"])
    )



# ===========================================================================
# The applicability boundary (PO-3 / F-1) — asserted, not assumed
# ===========================================================================
def test_no_applicability_model_is_reachable_from_the_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    text = _serialised(payload).lower()
    for forbidden in (
        '"applicability',
        "applicability_status",
        "category_applicability",
        "customer_applicability",
        "not_applicable_tenant",
        "does_not_apply",
    ):
        assert forbidden not in text, forbidden


def test_the_projection_module_never_reads_the_applicability_tables() -> None:
    """`F-1` — the canonical projection has no tenant/applicability input at all."""
    import inspect

    from domain import capability_catalogue as module

    source = inspect.getsource(module)
    for forbidden in (
        "disclosure_applicability_assessments",
        "assessed_status",
        "disclosure_values",
        "organization_id",
        "current_setting",
        "auth.uid",
    ):
        assert forbidden not in source, forbidden


# ===========================================================================
# SC-4 — market-based Scope 2 is not a producible capability
# ===========================================================================
def test_sc_4_market_based_scope2_is_not_claimed_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _payload(_client(monkeypatch))
    by_method = {
        item["scope2_method"]: item
        for item in payload["requirements"]
        if item["scope2_method"] is not None
    }
    assert set(by_method) == {"LOCATION_BASED", "MARKET_BASED"}
    assert by_method["MARKET_BASED"]["carbontally_capability"] != "SUPPORTED"
    assert by_method["MARKET_BASED"]["carbontally_capability"] != "PARTIALLY_SUPPORTED"
    assert by_method["MARKET_BASED"]["supported"] is False
    assert by_method["LOCATION_BASED"]["carbontally_capability"] == "SUPPORTED"


# ===========================================================================
# Fail-closed behaviour (CS-3, IV-4) — no claim rather than a weaker one
# ===========================================================================
def test_an_unprovisioned_catalogue_yields_no_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _FakeCatalogRepository()
    repository.framework_present = False
    response = _client(monkeypatch, repository).get(ROUTE)
    assert response.status_code == 503, response.text
    body = response.json()
    assert "requirements" not in json.dumps(body)


def test_a_catalogue_with_no_candidate_version_yields_no_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _FakeCatalogRepository()
    repository.versions_present = False
    response = _client(monkeypatch, repository).get(ROUTE)
    assert response.status_code == 503, response.text


def test_a_database_with_only_ungoverned_requirement_rows_yields_no_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A candidate whose rows are not governed identities is never the catalogue."""
    repository = _FakeCatalogRepository()
    repository.extra_candidates = [
        {
            "id": "33333333-3333-4333-8333-333333333333",
            "version_label": "B1RT-00000001",
            "status": "IN_FORCE",
            "source_tier": 1,
            "framework_code": "GHG_PROTOCOL",
            "requirement_codes": ["B1RT_068e737e"],
        }
    ]
    repository.versions_present = False  # remove the governed candidate
    response = _client(monkeypatch, repository).get(ROUTE)
    assert response.status_code == 503, response.text


# ===========================================================================
# Version scoping — the surface reads ONE governed framework version
# ===========================================================================
def test_the_governed_catalogue_version_is_selected_not_the_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A version carrying non-governed requirement codes is never selected.

    Regression guard: an earlier revision of this read model filtered on the
    framework *code*, so a second version of the same framework (test residue, a
    future catalogue) merged into the claim. The surface must select by rule.
    """
    repository = _FakeCatalogRepository()
    repository.extra_candidates = [
        {
            "id": "33333333-3333-4333-8333-333333333333",
            "version_label": "B1RT-00000001",
            "status": "IN_FORCE",
            "source_tier": 1,
            "framework_code": "GHG_PROTOCOL",
            "requirement_codes": ["B1RT_068e737e", "B1RT_11111111"],
        }
    ]
    payload = _payload(_client(monkeypatch, repository))
    assert payload["framework_version"]["version_label"] == _VERSION_LABEL
    assert len(payload["requirements"]) == 18


def test_the_requirements_are_scoped_to_the_selected_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _FakeCatalogRepository()
    _payload(_client(monkeypatch, repository))
    assert repository.requested_version_id == "22222222-2222-4222-8222-222222222222"


def test_an_unusable_row_yields_no_claim_rather_than_a_guess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A catalogue row outside the governed vocabulary must not be rendered."""
    repository = _FakeCatalogRepository()

    async def poisoned(_framework_version_id: str) -> list[dict[str, Any]]:
        rows = catalogue_rows()
        rows[0] = dict(rows[0], carbontally_capability="PARTIAL")
        return rows

    repository.list_capability_catalogue_requirements = poisoned  # type: ignore[method-assign]
    response = _client(monkeypatch, repository).get(ROUTE)
    assert response.status_code == 503, response.text
    assert "PARTIAL" not in response.text


def test_an_unknown_requirement_identity_yields_no_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _FakeCatalogRepository()

    async def poisoned(_framework_version_id: str) -> list[dict[str, Any]]:
        return [dict(catalogue_rows()[0], requirement_code="GP-S4-99")]

    repository.list_capability_catalogue_requirements = poisoned  # type: ignore[method-assign]
    response = _client(monkeypatch, repository).get(ROUTE)
    assert response.status_code == 503, response.text


def test_failure_detail_is_not_a_technical_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """`AGENTS.md §46` — the user never receives a raw technical error."""
    repository = _FakeCatalogRepository()
    repository.framework_present = False
    detail = _client(monkeypatch, repository).get(ROUTE).json()["detail"]
    assert isinstance(detail, str) and detail
    for technical in ("Traceback", "asyncpg", "NoneType", "psycopg"):
        assert technical not in detail

