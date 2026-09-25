"""P17-IMPLEMENT-02 — API, acting-for persistence and audit attribution tests.

Exercises the real router through FastAPI's TestClient with the existing
dependency-injection points overridden, so the HTTP contract (status codes,
payloads, refusal behaviour) is tested rather than only the service functions.

Also covers:
* the closed acting-for carrier allowlist (no arbitrary table names);
* that the persisted attribution comes from the server-resolved context and not
  from the request payload (case 9);
* that a write on another tenant's record is refused (case 10);
* that the existing audit ledger records actor + acting-for + owner.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from api.dependencies import RepositoryBundle, get_repositories
from api.v3_accounting_context import router as accounting_router
from auth import AuthUser, get_current_user
from core.exceptions import CarbonTallyError
from data.accounting_context import ACTING_FOR_CARRIERS

OWN_ORG = "11111111-1111-4111-8111-111111111111"
CLIENT_A = "22222222-2222-4222-8222-222222222222"
UNRELATED = "33333333-3333-4333-8333-333333333333"
FIRM_ORG = "44444444-4444-4444-8444-444444444444"
RECORD_ID = "55555555-5555-4555-8555-555555555555"
USER_ID = "66666666-6666-4666-8666-666666666666"


class _OrgRepo:
    def __init__(self, orgs: dict[str, dict], member_roles: dict[str, str]) -> None:
        self._orgs = orgs
        self._member_roles = member_roles
        self.records: dict[tuple[str, str], dict] = {}
        self.writes: list[dict] = []

    async def get_organization_summary(self, organization_id: str):
        return self._orgs.get(organization_id)

    async def list_active_member_roles(self, user_id: str) -> dict[str, str]:
        return dict(self._member_roles)

    async def list_scope3_categories(self) -> list[dict]:
        return [
            {"category": n, "slug": f"c{n}", "name": f"Cat {n}",
             "is_downstream": n >= 9, "description": None}
            for n in range(1, 16)
        ]

    async def get_snapshot_dimensions(self, snapshot_id: str):
        return self.records.get(("snapshot", snapshot_id))

    async def persist_acting_for(
        self, *, carrier, record_id, actor_organization_id,
        acting_for_organization_id,
    ):
        self.writes.append(
            {
                "carrier": carrier,
                "record_id": record_id,
                "actor_organization_id": actor_organization_id,
                "acting_for_organization_id": acting_for_organization_id,
            }
        )
        record = self.records.get((carrier, record_id))
        if record is None:
            return None
        record["acting_for_organization_id"] = acting_for_organization_id
        record["actor_organization_id"] = actor_organization_id
        return {
            "carrier": carrier,
            "record_id": record_id,
            "actor_organization_id": actor_organization_id,
            "acting_for_organization_id": acting_for_organization_id,
        }

    async def get_acting_for_attribution(self, *, carrier: str, record_id: str):
        return self.records.get((carrier, record_id))


class _ConsultantRepo:
    def __init__(self, grants=None) -> None:
        self._grants = grants or []

    async def get_active_memberships_by_user(self, user_id: str):
        return []

    async def get_profile_by_id(self, firm_id: str):
        return None

    async def list_clients(self, consultant_id: str):
        return list(self._grants)

    async def get_client_by_org(self, consultant_id: str, organization_id: str):
        for grant in self._grants:
            if grant.organization_id == organization_id:
                return grant
        return None


class _AuditRepo:
    def __init__(self) -> None:
        self.entries: list = []

    async def record(self, entry):
        self.entries.append(entry)
        return entry


def _orgs(*ids: str) -> dict[str, dict]:
    return {
        oid: {
            "id": oid,
            "name": oid.upper(),
            "organization_type": "CUSTOMER",
            "consolidation_approach": None,
            "is_active": True,
        }
        for oid in ids
    }


def _build_app(user: AuthUser, repos) -> FastAPI:
    app = FastAPI()
    app.include_router(accounting_router)

    @app.exception_handler(CarbonTallyError)
    async def _p17_error_handler(request, exc: CarbonTallyError):  # noqa: ANN001
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_repositories] = lambda: repos
    return app


def _member_user() -> AuthUser:
    return AuthUser(
        user_id=USER_ID,
        email="m@example.com",
        role="owner",
        organization_id=OWN_ORG,
        is_org_member=True,
    )


def _repos(*, orgs: dict[str, dict], member_roles: dict[str, str]):
    class _Bundle:
        def __init__(self) -> None:
            self.accounting_context = _OrgRepo(orgs, member_roles)
            self.consultants = _ConsultantRepo()
            self.audit = _AuditRepo()

    return _Bundle()


# ---------------------------------------------------------------------------
# A / B — context and authorized organizations
# ---------------------------------------------------------------------------
def test_context_returns_the_actors_own_organization() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.get("/api/v3/accounting/context")
    assert response.status_code == 200
    payload = response.json()["context"]
    assert payload["data_owning_organization_id"] == OWN_ORG
    assert payload["acting_for_organization_id"] == OWN_ORG
    assert payload["is_delegated"] is False
    assert payload["acting_for_label"] is None


def test_context_for_an_unauthorized_organization_is_403() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG, UNRELATED), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.get(
        "/api/v3/accounting/context",
        params={"acting_for_organization_id": UNRELATED},
    )
    assert response.status_code == 403


def test_organizations_lists_only_the_actors_own_organization() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG, UNRELATED), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.get("/api/v3/accounting/organizations")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["organizations"][0]["organization_id"] == OWN_ORG
    assert body["organizations"][0]["is_own"] is True


# ---------------------------------------------------------------------------
# C — selecting / switching acting-for
# ---------------------------------------------------------------------------
def test_selecting_the_own_organization_succeeds_and_persists_nothing() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/acting-for",
        json={"acting_for_organization_id": OWN_ORG},
    )
    assert response.status_code == 200
    assert response.json()["persisted"] is False
    assert repos.accounting_context.writes == []


def test_selecting_an_unauthorized_organization_is_403() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG, UNRELATED), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/acting-for",
        json={"acting_for_organization_id": UNRELATED},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# D — CAMS dimension resolution / validation
# ---------------------------------------------------------------------------
def test_scope2_without_a_method_is_rejected() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/dimensions/resolve",
        json={"scope": "Scope 2", "energy_type": "electricity"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SCOPE2_METHOD_REQUIRED"


def test_scope2_with_fuel_is_rejected_with_its_reason() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/dimensions/resolve",
        json={
            "scope": "Scope 2",
            "scope2_method": "LOCATION_BASED",
            "energy_type": "fuel",
        },
    )
    assert response.status_code == 422
    assert "Scope 1" in response.json()["error"]["message"]


def test_category_4_without_a_transport_boundary_is_rejected() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/dimensions/resolve",
        json={"scope": "Scope 3", "scope3_category": 4},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BOUNDARY_AMBIGUITY"


def test_not_implemented_category_is_refused_by_the_api() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/dimensions/resolve",
        json={"scope": "Scope 3", "scope3_category": 10},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SCOPE3_CATEGORY_NOT_SUPPORTED"


def test_valid_dimensions_resolve_and_do_not_calculate() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/dimensions/resolve",
        json={
            "scope": "Scope 3",
            "scope3_category": 5,
            "waste_origin": "operations",
            "data_quality": "primary_supplier",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["dimensions"]["scope3_category"] == 5
    assert body["dimensions"]["waste_origin"] == "operations"
    assert body["would_persist"] is False
    assert "Waste generated in operations" in body["description"]["label"]


def test_dimension_resolution_for_an_unauthorized_organization_is_403() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG, UNRELATED), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/dimensions/resolve",
        json={"scope": "Scope 1", "acting_for_organization_id": UNRELATED},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# E / F — acting-for persistence, forgery resistance, attribution read
# ---------------------------------------------------------------------------
def _seed_record(repos, carrier: str, owner: str) -> None:
    repos.accounting_context.records[(carrier, RECORD_ID)] = {
        "carrier": carrier,
        "record_id": RECORD_ID,
        "owner_organization_id": owner,
        "actor_organization_id": None,
        "acting_for_organization_id": None,
    }


def test_attribution_is_persisted_from_the_server_resolved_context() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    _seed_record(repos, "customer_document", OWN_ORG)
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/acting-for/attribute",
        json={"carrier": "customer_document", "record_id": RECORD_ID},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["attribution"]["acting_for_organization_id"] == OWN_ORG
    assert body["owner_organization_id"] == OWN_ORG
    assert body["audited"] is True
    # The existing audit ledger carries the attribution.
    assert len(repos.audit.entries) == 1
    entry = repos.audit.entries[0]
    assert entry.acting_for_organization_id == OWN_ORG
    assert entry.organization_id == OWN_ORG
    assert entry.action == "acting_for_attributed"
    assert entry.entity_type == "customer_document"


def test_forged_attribution_in_the_request_payload_is_ignored() -> None:
    """Case 9: the payload cannot set the attribution."""
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    _seed_record(repos, "customer_document", OWN_ORG)
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/acting-for/attribute",
        json={
            "carrier": "customer_document",
            "record_id": RECORD_ID,
            "acting_for_organization_id": UNRELATED,
            "actor_organization_id": UNRELATED,
        },
    )
    assert response.status_code == 200
    assert repos.accounting_context.writes[-1]["acting_for_organization_id"] == OWN_ORG
    assert repos.accounting_context.writes[-1]["actor_organization_id"] == OWN_ORG


def test_attributing_another_tenants_record_is_403_and_writes_nothing() -> None:
    """Case 10: the record's owner is the authority."""
    repos = _repos(orgs=_orgs(OWN_ORG, UNRELATED), member_roles={OWN_ORG: "owner"})
    _seed_record(repos, "supplier", UNRELATED)
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/acting-for/attribute",
        json={"carrier": "supplier", "record_id": RECORD_ID},
    )
    assert response.status_code == 403
    assert repos.accounting_context.writes == []
    assert repos.audit.entries == []


def test_attributing_an_unknown_record_is_404() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/acting-for/attribute",
        json={"carrier": "supplier", "record_id": RECORD_ID},
    )
    assert response.status_code == 404


def test_unknown_carrier_is_rejected() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/acting-for/attribute",
        json={"carrier": "users", "record_id": RECORD_ID},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# F — attribution read-back
# ---------------------------------------------------------------------------
def test_attribution_can_be_read_back() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    _seed_record(repos, "customer_document", OWN_ORG)
    client = TestClient(_build_app(_member_user(), repos))
    response = client.post(
        "/api/v3/accounting/acting-for/attribute",
        json={"carrier": "customer_document", "record_id": RECORD_ID},
    )
    assert response.status_code == 200
    read = client.get(
        "/api/v3/accounting/acting-for/attribution",
        params={"carrier": "customer_document", "record_id": RECORD_ID},
    )
    assert read.status_code == 200
    assert read.json()["attribution"]["acting_for_organization_id"] == OWN_ORG


def test_reading_another_tenants_attribution_is_403() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG, UNRELATED), member_roles={OWN_ORG: "owner"})
    _seed_record(repos, "supplier", UNRELATED)
    client = TestClient(_build_app(_member_user(), repos))
    response = client.get(
        "/api/v3/accounting/acting-for/attribution",
        params={"carrier": "supplier", "record_id": RECORD_ID},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Scope 3 reference vocabulary
# ---------------------------------------------------------------------------
def test_scope3_categories_expose_the_architecture_status() -> None:
    repos = _repos(orgs=_orgs(OWN_ORG), member_roles={OWN_ORG: "owner"})
    client = TestClient(_build_app(_member_user(), repos))
    response = client.get("/api/v3/accounting/scope3/categories")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 15
    by_number = {c["category"]: c for c in body["categories"]}
    assert by_number[10]["architecture_status"] == "NOT_IMPLEMENTED"
    assert by_number[10]["calculable"] is False
    assert by_number[2]["calculable"] is False
    assert by_number[11]["architecture_status"] == "DEFERRED"
    assert by_number[4]["calculable"] is True
    assert by_number[4]["requires_transport_boundary"] is True
    assert by_number[12]["requires_waste_origin"] is True
    assert by_number[8]["requires_consolidation_approach"] is True


# ---------------------------------------------------------------------------
# Carrier allowlist
# ---------------------------------------------------------------------------
def test_carrier_allowlist_covers_the_nine_architecture_paths() -> None:
    assert set(ACTING_FOR_CARRIERS) == {
        "calculation_snapshot",
        "emissions_log",
        "evidence_line_item",
        "customer_document",
        "supplier",
        "review_audit_trail",
        "review_assignment_history",
        "report_version",
        "audit_entry",
    }


def test_carrier_allowlist_never_uses_the_owner_column_as_acting_for() -> None:
    for spec in ACTING_FOR_CARRIERS.values():
        assert spec["table"]
        assert spec["actor"]
        assert spec["acting_for"] == "acting_for_organization_id"
        assert spec["owner"] != spec["acting_for"]


@pytest.mark.asyncio
async def test_repository_refuses_to_delete_provenance() -> None:
    """Acting-for attribution is provenance and must not be deletable."""
    from data.accounting_context import AccountingContextRepository

    class _Pool:
        def acquire(self):  # pragma: no cover - must never be reached
            raise AssertionError("the database must not be touched")

    repo = AccountingContextRepository(_Pool())  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        await repo.delete("x")
