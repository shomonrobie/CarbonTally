"""G1 / G2 — emissions + document-activity organisation scope and staff access.

Both gaps live on handlers that read and write through the SERVICE-ROLE client,
so RLS is not the boundary: the guard and the handler's own checks are.

* **G1 — ``?organization_id=`` was the whole scope decision.**
  ``GET /api/emissions/stats`` and ``GET /api/emissions/export`` took an
  ``organization_id`` QUERY parameter and applied it as the only filter on an
  unfiltered service-role read. The existing enforcers are deliberately no-ops
  for a query parameter (``enforce_org_path_scope`` reads ``path_params``,
  ``enforce_org_body_scope`` reads the body), so with only
  ``require_org_member()`` attached a member of org A received org B's totals
  and org B's exported rows. Both handlers now authorise the named organisation
  (``auth.enforce_org_query_scope``) BEFORE applying it, and a caller whose
  memberships do not resolve is refused instead of degrading into an unscoped,
  all-tenant read.

* **G2 — the F1/F3 migration had removed internal staff access.** The eight
  operational handlers below were moved off ``require_auth()`` onto
  ``require_org_member()`` to close the suspended-tenant hole; that guard's
  membership test also refuses CarbonTally INTERNAL staff (``is_org_member`` is
  False for them, they hold no membership row) even though every other
  organisation guard exempts them. They now use
  ``require_org_member_or_internal_staff()``: organisation principals get
  exactly the decisions they had before (membership, D-7 lifecycle, F-05-R1
  path rule), internal staff keep the operational cross-organisation access,
  and Processing Entity staff are still refused (D20 scope-first).

The eight routes: ``PUT /api/emissions/{record_id}``,
``POST /api/emissions/bulk``, ``POST /api/emissions/verify``,
``GET /api/emissions/stats``, ``GET /api/emissions/export``,
``GET /api/documents/{file_id}/activity``,
``GET /api/documents/{file_id}/reviews`` and
``POST /api/documents/{file_id}/review/response``.

Evidence style mirrors ``test_d7_f1_f2_f3_enforcement.py``: real routers over an
in-memory service-role store, the REAL guards, denial asserted as HTTP 403 with
the canonical detail, and "the handler never ran" asserted through the recorded
store access (``FakeWorld.queried_tables`` / ``FakeWorld.writes``).

Two properties are pinned alongside the behaviour:

1. ORDERING — a caller with no authority over the named organisation never
   triggers a lifecycle (``organizations``) read for it: the F2 property,
   extended to the query parameter.
2. NO WIDENING — the staff exemption is SCOPE-based
   (``AuthUser.is_internal_staff``), never ``is_admin``, and the handlers' own
   record-level checks (the ``is_admin`` short-circuit) still apply to every
   other principal.
"""
from __future__ import annotations

from typing import Optional

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from auth import (
    ORGANIZATION_SUSPENDED_DETAIL,
    AuthUser,
    enforce_org_query_scope,
    require_org_member_or_internal_staff,
)
from tests.unit.api.fakes import (
    entity_operator_user,
    member_user,
    staff_user,
)
from tests.unit.api.test_d7_org_lifecycle_decisions import (
    ORG_A,
    ORG_B,
    FakeWorld,
    _install_store,
    _membership,
    _module_app,
    _org_row,
    _request,
    _suspended,
)

#: The guard's own denial when the caller holds no membership for the path
#: organisation — the decision F-05-R1 froze.
_CROSS_TENANT_DETAIL = "You don't have access to this organization"

#: What the two G1 handlers answer once the query scope was refused.
_QUERY_SCOPE_DETAIL = "You don't have access to this organization"

#: What ``require_org_member()`` answers a principal with no membership and no
#: staff scope (the guard the G2 routes moved off).
_NOT_A_MEMBER_DETAIL = "Organization member access required"


# ===========================================================================
# Principals — internal staff exactly as ``get_current_user`` builds them
# ===========================================================================
def _internal_staff(*, admin: bool = True) -> AuthUser:
    """A CarbonTally INTERNAL staff principal (``staff_profiles.entity_id`` NULL).

    ``auth.py`` (D20) grants ``is_admin`` to internal staff ONLY, and only when
    the staff role is ``admin``; ``is_org_member`` stays False because internal
    staff hold no ``organization_members`` row — which is precisely why the
    plain ``require_org_member()`` guard used to refuse them (G2). The
    handlers' record-level checks key off ``is_admin``, so the operational
    principal is the admin one.
    """
    role = "admin" if admin else "staff"
    return AuthUser(
        user_id="u-ops",
        email="ops@carbontally.test",
        role=role,
        role_name=role,
        is_active=True,
        is_staff=True,
        is_org_member=False,
        is_admin=admin,
    )


def _customer_no_membership() -> AuthUser:
    """An authenticated principal the guard must still refuse.

    ``is_org_member`` is False and there is no staff scope at all: the caller
    resolves to neither an organisation principal nor internal staff.
    """
    return AuthUser(
        user_id="u-nobody",
        email="nobody@carbontally.test",
        role="user",
        role_name="user",
        is_org_member=False,
    )


def _module(url: str):
    """The REAL router module a URL belongs to (emissions vs documents)."""
    if url.startswith("/api/emissions"):
        from routes import emissions as module
    else:
        from routes import document_activity as module
    return module


def _emission(record_id: str, org_id: str, amount: float = 10.0) -> dict:
    """An ``emissions_logs`` row as the stats/export handlers read it."""
    return {
        "id": record_id,
        "organization_id": org_id,
        "calculated_kg_co2e": amount,
    }


#: The eight operational routes G2 restored, addressed with a FOREIGN
#: organisation's record/file (org B) so the call can only succeed through the
#: internal-staff exemption.
_OPERATIONAL_ROUTES = [
    pytest.param("PUT", "/api/emissions/rec-b", {"json": {"raw_quantity": 1.0}}, id="put-record"),
    pytest.param(
        "POST",
        "/api/emissions/bulk",
        {"json": {"emissions": [{"organization_id": ORG_B}]}},
        id="bulk-create",
    ),
    pytest.param("POST", "/api/emissions/verify", {"json": ["rec-b"]}, id="verify"),
    pytest.param("GET", "/api/emissions/stats", {}, id="stats"),
    pytest.param("GET", "/api/emissions/export", {}, id="export"),
    pytest.param("GET", "/api/documents/file-b/activity", {}, id="document-activity"),
    pytest.param("GET", "/api/documents/file-b/reviews", {}, id="document-reviews"),
    pytest.param(
        "POST",
        "/api/documents/file-b/review/response",
        {"json": {"status": "approved"}},
        id="review-response",
    ),
]

#: The two G1 handlers, addressed through their query parameter.
_QUERY_SCOPE_ROUTES = [
    pytest.param("stats", id="stats"),
    pytest.param("export", id="export"),
]


# ===========================================================================
# G1 — the query parameter authorises the organisation it names
# ===========================================================================
@pytest.mark.parametrize("route", _QUERY_SCOPE_ROUTES)
def test_g1_query_scope_refuses_a_foreign_organisation(monkeypatch, route):
    """A member of org A cannot read org B through ``?organization_id=``.

    Two proofs in one: the refusal is the frozen cross-tenant denial (and a 403
    rather than a 500, i.e. the request-level ``HTTPException`` was re-raised),
    and the handler never ran — no ``emissions_logs`` read happened.
    """
    world = _foreign_store()
    url = _scoped_url(route, ORG_B)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, _module(url), world, user)

    with TestClient(app) as client:
        response = client.get(url)

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == _QUERY_SCOPE_DETAIL
    assert "emissions_logs" not in world.queried_tables
    # Property 1 — an unauthorised caller never triggers a lifecycle read for
    # the tenant it named: authority is proven first.
    assert "organizations" not in world.queried_tables


@pytest.mark.parametrize("route", _QUERY_SCOPE_ROUTES)
def test_g1_query_scope_keeps_the_callers_own_organisation(monkeypatch, route):
    """No over-blocking: the caller's own organisation still scopes the read."""
    world = _foreign_store()
    url = _scoped_url(route, ORG_A)
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, _module(url), world, user)

    with TestClient(app) as client:
        response = client.get(url)

    assert response.status_code == 200, response.text
    # Exactly one store round trip — the scoped read itself. The own-tenant
    # scope decision is answered from the principal (F-05-R1's zero-query rule).
    assert world.queries == [("emissions_logs", (("organization_id", ORG_A),))]
    if route == "stats":
        data = response.json()["data"]
        assert data["total_records"] == 1
        assert data["total_emissions_kg_co2e"] == 5.0
    else:
        assert "text/csv" in response.headers["content-type"]
        assert "rec-a" in response.text
        assert "rec-b" not in response.text


def test_g1_query_scope_accepts_an_active_membership_in_another_organisation(monkeypatch):
    """A genuine multi-org member keeps the organisation they name."""
    world = FakeWorld(
        [
            _membership("u-multi", ORG_A, "member"),
            _membership("u-multi", ORG_B, "member"),
        ],
        organizations=[_org_row(ORG_A), _org_row(ORG_B)],
        emissions_logs=[_emission("rec-a", ORG_A, 5.0), _emission("rec-b", ORG_B, 7.0)],
    )
    user = member_user(ORG_A, "u-multi", "m@carbontally.test")
    app = _module_app(monkeypatch, _module("/api/emissions/stats"), world, user)

    with TestClient(app) as client:
        response = client.get(_scoped_url("stats", ORG_B))

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total_records"] == 1
    assert data["total_emissions_kg_co2e"] == 7.0


def test_g1_query_scope_refuses_an_inactive_organisation(monkeypatch):
    """Membership is not enough — the named organisation's lifecycle decides.

    D-7 Decision B reaches the query parameter too, so a suspended client of a
    consultant (or a suspended tenant's own member) cannot pull its emissions
    through the parameter instead of the path.
    """
    world = FakeWorld(
        [
            _membership("u-multi", ORG_A, "member"),
            _membership("u-multi", ORG_B, "member"),
        ],
        organizations=[_org_row(ORG_A), _org_row(ORG_B, active=False)],
        emissions_logs=[_emission("rec-b", ORG_B, 7.0)],
    )
    user = member_user(ORG_A, "u-multi", "m@carbontally.test")
    app = _module_app(monkeypatch, _module("/api/emissions/stats"), world, user)

    with TestClient(app) as client:
        response = client.get(_scoped_url("stats", ORG_B))

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == ORGANIZATION_SUSPENDED_DETAIL
    assert "emissions_logs" not in world.queried_tables


def _scoped_url(route: str, org_id: str) -> str:
    """``/api/emissions/{route}?organization_id=...`` — the G1 attack surface."""
    return f"/api/emissions/{route}?organization_id={org_id}"


def _foreign_store(**tables) -> FakeWorld:
    """A store holding org A's and org B's operational data.

    Org B's rows are what a member of org A must never reach, and what internal
    staff must still be able to operate on.
    """
    return FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A), _org_row(ORG_B)],
        emissions_logs=[_emission("rec-a", ORG_A, 5.0), _emission("rec-b", ORG_B, 7.0)],
        organization_files=[
            {"id": "file-a", "organization_id": ORG_A},
            {"id": "file-b", "organization_id": ORG_B},
        ],
        document_activity_log=[
            {"id": "act-b", "file_id": "file-b", "organization_id": ORG_B}
        ],
        customer_review_log=[
            {"id": "rev-b", "file_id": "file-b", "status": "pending"}
        ],
        **tables,
    )


@pytest.mark.parametrize("route", _QUERY_SCOPE_ROUTES)
def test_g1_unresolvable_memberships_never_degrade_to_an_all_tenant_read(
    monkeypatch, route
):
    """Fail closed: an empty membership set is an empty read, never all rows.

    The principal says ``is_org_member`` (so the guard admits it) while the
    store resolves no membership at all. Before G1 the handler skipped its
    ``.in_('organization_id', ...)`` filter in exactly this case, turning a
    scoped read into an unscoped, all-tenant one.
    """
    world = FakeWorld(
        organizations=[_org_row(ORG_A)],
        emissions_logs=[_emission("rec-a", ORG_A, 5.0), _emission("rec-b", ORG_B, 7.0)],
    )
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, _module("/api/emissions/stats"), world, user)

    with TestClient(app) as client:
        response = client.get(f"/api/emissions/{route}")

    assert response.status_code == 200, response.text
    assert "emissions_logs" not in world.queried_tables
    if route == "stats":
        assert response.json()["data"]["total_records"] == 0
    else:
        assert response.json() == {"success": True, "message": "No data to export"}


@pytest.mark.parametrize("route", _QUERY_SCOPE_ROUTES)
def test_g1_entity_staff_are_still_refused(monkeypatch, route):
    """D20 scope-first is untouched by G2.

    A Processing Entity operator (``staff_profiles.entity_id`` NOT NULL) is
    staff, but NOT CarbonTally internal staff, so neither the guard nor the
    handler's scope dimension admits it.
    """
    world = _foreign_store()
    url = _scoped_url(route, ORG_B)
    app = _module_app(monkeypatch, _module(url), world, entity_operator_user("entity-1"))

    with TestClient(app) as client:
        response = client.get(url)

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == _NOT_A_MEMBER_DETAIL
    assert "emissions_logs" not in world.queried_tables


# ===========================================================================
# G2 — internal staff keep the operational routes (scope-based exemption)
# ===========================================================================
def test_g2_internal_staff_can_update_a_foreign_organisations_record(monkeypatch):
    """``PUT /emissions/{record_id}`` — the F1 migration had made this a 403."""
    world = FakeWorld(emissions_logs=[_emission("rec-b", ORG_B)])
    app = _module_app(monkeypatch, _module("/api/emissions/rec-b"), world, _internal_staff())

    with TestClient(app) as client:
        response = client.put("/api/emissions/rec-b", json={"raw_quantity": 1.0})

    assert response.status_code == 200, response.text
    # The record-level check (the ``is_admin`` short-circuit) admitted the
    # caller without any membership row — and the update was written.
    assert [write[0] for write in world.writes] == ["emissions_logs"]


def test_g2_internal_staff_can_bulk_create_for_a_foreign_organisation(monkeypatch):
    """``POST /emissions/bulk`` — one successful row, no authorisation error."""
    world = FakeWorld()
    app = _module_app(monkeypatch, _module("/api/emissions/bulk"), world, _internal_staff())
    payload = {"emissions": [{"organization_id": ORG_B, "calculated_kg_co2e": 5}]}

    with TestClient(app) as client:
        response = client.post("/api/emissions/bulk", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["success_count"] == 1
    assert data["failed_count"] == 0
    assert [write[0] for write in world.writes] == ["emissions_logs"]


def test_g2_internal_staff_can_verify_a_foreign_organisations_record(monkeypatch):
    """``POST /emissions/verify`` — the exact-tenant rule admits internal staff."""
    world = FakeWorld(emissions_logs=[_emission("rec-b", ORG_B)])
    app = _module_app(monkeypatch, _module("/api/emissions/verify"), world, _internal_staff())

    with TestClient(app) as client:
        response = client.post("/api/emissions/verify", json=["rec-b"])

    assert response.status_code == 200, response.text
    assert response.json()["data"]["verified"] == 1
    assert [write[0] for write in world.writes] == ["emissions_logs"]


def test_g2_internal_staff_read_the_any_organisation_stats(monkeypatch):
    """The exemption is query-free: the scoped read is the only store round trip."""
    world = FakeWorld(emissions_logs=[_emission("rec-b", ORG_B, 7.0)])
    app = _module_app(monkeypatch, _module("/api/emissions/stats"), world, _internal_staff())

    with TestClient(app) as client:
        response = client.get(_scoped_url("stats", ORG_B))

    assert response.status_code == 200, response.text
    assert response.json()["data"]["total_records"] == 1
    assert world.queries == [("emissions_logs", (("organization_id", ORG_B),))]


def test_g2_internal_staff_export_every_organisation(monkeypatch):
    """Without a parameter, internal staff keep the documented all-tenant export."""
    world = FakeWorld(
        emissions_logs=[_emission("rec-a", ORG_A, 5.0), _emission("rec-b", ORG_B, 7.0)]
    )
    app = _module_app(monkeypatch, _module("/api/emissions/export"), world, _internal_staff())

    with TestClient(app) as client:
        response = client.get("/api/emissions/export")

    assert response.status_code == 200, response.text
    assert "text/csv" in response.headers["content-type"]
    assert len(response.text.strip().splitlines()) == 3  # header + both tenants
    assert "rec-a" in response.text and "rec-b" in response.text


def test_g2_internal_staff_read_a_foreign_documents_activity(monkeypatch):
    """``GET /documents/{file_id}/activity`` — F3's route, staff still admitted."""
    world = _foreign_store()
    app = _module_app(
        monkeypatch, _module("/api/documents/file-b/activity"), world, _internal_staff()
    )

    with TestClient(app) as client:
        response = client.get("/api/documents/file-b/activity")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["total"] == 1


def test_g2_internal_staff_read_a_foreign_documents_reviews(monkeypatch):
    """``GET /documents/{file_id}/reviews`` — F3's tenant boundary keeps staff."""
    world = _foreign_store()
    app = _module_app(
        monkeypatch, _module("/api/documents/file-b/reviews"), world, _internal_staff()
    )

    with TestClient(app) as client:
        response = client.get("/api/documents/file-b/reviews")

    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1


def test_g2_internal_staff_respond_to_a_foreign_documents_review(monkeypatch):
    """``POST /documents/{file_id}/review/response`` — the write path too."""
    world = _foreign_store()
    app = _module_app(
        monkeypatch,
        _module("/api/documents/file-b/review/response"),
        world,
        _internal_staff(),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/documents/file-b/review/response",
            json={"status": "approved", "notes": "checked"},
        )

    assert response.status_code == 200, response.text
    assert [write[0] for write in world.writes] == [
        "customer_review_log",
        "organization_files",
    ]


@pytest.mark.parametrize("route", _QUERY_SCOPE_ROUTES)
def test_g2_the_exemption_is_scope_based_not_is_admin_based(monkeypatch, route):
    """A NON-admin internal staff principal is still internal staff.

    ``staff_user()`` is ``is_staff`` with ``is_admin=False``. The guard exempts
    it on the D20 scope dimension (``is_internal_staff``), while the handlers
    that short-circuit on ``is_admin`` keep their own, stricter rule — so the
    exemption can never widen a read for a principal without staff scope.
    """
    world = FakeWorld(emissions_logs=[_emission("rec-b", ORG_B, 7.0)])
    url = _scoped_url(route, ORG_B)
    app = _module_app(monkeypatch, _module(url), world, staff_user())

    with TestClient(app) as client:
        response = client.get(url)

    assert response.status_code == 200, response.text


# ===========================================================================
# G2 — the exemption widened nothing: customer isolation is unchanged
# ===========================================================================
def test_g2_put_still_refuses_a_foreign_tenants_record(monkeypatch):
    """A member of org A keeps the record-level denial — and writes nothing."""
    world = _foreign_store()
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, _module("/api/emissions/rec-b"), world, user)

    with TestClient(app) as client:
        response = client.put("/api/emissions/rec-b", json={"raw_quantity": 1.0})

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not authorized to update this record"
    assert world.writes == []


def test_g2_bulk_still_refuses_a_foreign_tenants_organisation(monkeypatch):
    """The per-row check reports the refusal instead of writing the row."""
    world = _foreign_store()
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, _module("/api/emissions/bulk"), world, user)
    payload = {"emissions": [{"organization_id": ORG_B, "calculated_kg_co2e": 5}]}

    with TestClient(app) as client:
        response = client.post("/api/emissions/bulk", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["success_count"] == 0
    assert data["failed_count"] == 1
    assert data["errors"][0]["error"] == "Not authorized for this organization"
    assert world.writes == []


def test_g2_activity_still_refuses_a_foreign_tenants_document(monkeypatch):
    """F3's tenant boundary is unchanged by the guard swap."""
    world = _foreign_store()
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(monkeypatch, _module("/api/documents/file-b/activity"), world, user)

    with TestClient(app) as client:
        response = client.get("/api/documents/file-b/activity")

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not authorized to view this document"
    assert "document_activity_log" not in world.queried_tables


def test_g2_review_response_still_refuses_a_foreign_tenants_document(monkeypatch):
    """The review WRITE path keeps the same boundary (no review row written)."""
    world = _foreign_store()
    user = member_user(ORG_A, "u-member", "m@carbontally.test")
    app = _module_app(
        monkeypatch, _module("/api/documents/file-b/review/response"), world, user
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/documents/file-b/review/response", json={"status": "approved"}
        )

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Not authorized to review this document"
    assert world.writes == []


# ===========================================================================
# The guard swap kept D-7 Decision B on all eight routes
# ===========================================================================
@pytest.mark.parametrize("method,url,kwargs", _OPERATIONAL_ROUTES)
def test_suspended_tenant_is_refused_on_every_operational_route(
    monkeypatch, method, url, kwargs
):
    """A suspended tenant's member is refused — before any handler data access.

    ``require_org_member_or_internal_staff()`` retains the exact
    ``require_org_member()`` decision that the F1/F3 migrations introduced
    (D-7 Decision B), so the G2 fix cannot reopen the hole they closed. The
    data the requests name exists in the store, so a 200 here would be visible.
    """
    world = FakeWorld(
        [_membership("u-member", ORG_A, "member")],
        organizations=[_org_row(ORG_A, active=False), _org_row(ORG_B)],
        emissions_logs=[_emission("rec-b", ORG_B, 7.0)],
        organization_files=[{"id": "file-b", "organization_id": ORG_B}],
    )
    user = _suspended(member_user(ORG_A, "u-member", "m@carbontally.test"))
    app = _module_app(monkeypatch, _module(url), world, user)

    with TestClient(app) as client:
        response = client.request(method, url, **kwargs)

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == ORGANIZATION_SUSPENDED_DETAIL
    # Token-derived decision: not one store round trip, and no handler table.
    assert world.queries == []
    assert world.handler_tables == []


# ===========================================================================
# The guard — the contract both gaps share
# ===========================================================================
@pytest.mark.asyncio
async def test_guard_admits_internal_staff_without_a_store_round_trip(monkeypatch):
    """G2 in isolation: the exemption is scope-based and query-free."""
    world = FakeWorld()
    _install_store(monkeypatch, world)
    checker = require_org_member_or_internal_staff()

    for user in (_internal_staff(), _internal_staff(admin=False), staff_user()):
        assert await checker(current_user=user, request=_request()) is user
    assert world.queries == []


@pytest.mark.asyncio
async def test_guard_still_refuses_a_principal_without_membership(monkeypatch):
    """The pre-G2 denial is intact for a caller with no organisation and no scope."""
    world = FakeWorld()
    _install_store(monkeypatch, world)
    checker = require_org_member_or_internal_staff()

    with pytest.raises(HTTPException) as exc:
        await checker(current_user=_customer_no_membership(), request=_request())

    assert exc.value.status_code == 403
    assert exc.value.detail == _NOT_A_MEMBER_DETAIL
    assert world.queries == []


@pytest.mark.asyncio
async def test_guard_keeps_the_f05_r1_path_rule(monkeypatch):
    """The path rule the guard was migrated for is still enforced."""
    world = FakeWorld([_membership("u-member", ORG_A)], organizations=[_org_row(ORG_B)])
    _install_store(monkeypatch, world)
    checker = require_org_member_or_internal_staff()

    with pytest.raises(HTTPException) as exc:
        await checker(
            current_user=member_user(ORG_A, "u-member", "m@carbontally.test"),
            request=_request(org_id=ORG_B),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == _CROSS_TENANT_DETAIL


# ===========================================================================
# ``enforce_org_query_scope`` — the G1 decision, in isolation
# ===========================================================================
@pytest.mark.asyncio
async def test_query_scope_is_a_noop_without_an_organisation(monkeypatch):
    """No parameter, no decision — the handler's own scoping takes over."""
    world = FakeWorld()
    _install_store(monkeypatch, world)

    await enforce_org_query_scope(None, member_user(ORG_A, "u-member", "m@x.test"))

    assert world.queries == []


@pytest.mark.asyncio
async def test_query_scope_answers_the_callers_own_organisation_from_the_principal(
    monkeypatch,
):
    """F-05-R1's zero-query property survives in the query-parameter form."""
    world = FakeWorld([_membership("u-member", ORG_A)], organizations=[_org_row(ORG_A)])
    _install_store(monkeypatch, world)

    await enforce_org_query_scope(
        ORG_A, member_user(ORG_A, "u-member", "m@carbontally.test")
    )

    assert world.queries == []


@pytest.mark.asyncio
async def test_query_scope_refuses_the_callers_own_suspended_organisation(monkeypatch):
    """D-7 Decision B applies to the parameter exactly as it does to a path."""
    world = FakeWorld(
        [_membership("u-member", ORG_A)], organizations=[_org_row(ORG_A, active=False)]
    )
    _install_store(monkeypatch, world)
    user = _suspended(member_user(ORG_A, "u-member", "m@carbontally.test"))

    with pytest.raises(HTTPException) as exc:
        await enforce_org_query_scope(ORG_A, user)

    assert exc.value.status_code == 403
    assert exc.value.detail == ORGANIZATION_SUSPENDED_DETAIL
    assert world.queries == []


@pytest.mark.asyncio
async def test_query_scope_proves_authority_before_reading_a_foreign_lifecycle(
    monkeypatch,
):
    """Property 1 — an unauthorised caller never triggers the lifecycle read."""
    world = FakeWorld([_membership("u-member", ORG_A)], organizations=[_org_row(ORG_B)])
    _install_store(monkeypatch, world)

    with pytest.raises(HTTPException) as exc:
        await enforce_org_query_scope(
            ORG_B, member_user(ORG_A, "u-member", "m@carbontally.test")
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == _QUERY_SCOPE_DETAIL
    assert "organizations" not in world.queried_tables


@pytest.mark.asyncio
async def test_query_scope_accepts_an_active_membership_in_another_organisation(
    monkeypatch,
):
    world = FakeWorld(
        [_membership("u-multi", ORG_A), _membership("u-multi", ORG_B)],
        organizations=[_org_row(ORG_B)],
    )
    _install_store(monkeypatch, world)

    await enforce_org_query_scope(
        ORG_B, member_user(ORG_A, "u-multi", "m@carbontally.test")
    )

    assert "organization_members" in world.queried_tables


@pytest.mark.asyncio
async def test_query_scope_refuses_a_foreign_membership_in_a_suspended_organisation(
    monkeypatch,
):
    world = FakeWorld(
        [_membership("u-multi", ORG_A), _membership("u-multi", ORG_B)],
        organizations=[_org_row(ORG_B, active=False)],
    )
    _install_store(monkeypatch, world)

    with pytest.raises(HTTPException) as exc:
        await enforce_org_query_scope(
            ORG_B, member_user(ORG_A, "u-multi", "m@carbontally.test")
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == ORGANIZATION_SUSPENDED_DETAIL


@pytest.mark.asyncio
async def test_query_scope_is_a_noop_for_internal_staff(monkeypatch):
    """The guard already admitted them; the parameter is not a second decision."""
    world = FakeWorld()
    _install_store(monkeypatch, world)

    for user in (_internal_staff(), _internal_staff(admin=False), staff_user()):
        await enforce_org_query_scope(ORG_B, user)

    assert world.queries == []


@pytest.mark.asyncio
async def test_query_scope_never_admits_processing_entity_staff(monkeypatch):
    """D20 defense in depth: the exemption is internal staff ONLY.

    The guard refuses an entity operator before the handler runs; were the
    enforcer reached anyway, the membership test refuses it too.
    """
    world = FakeWorld()
    _install_store(monkeypatch, world)

    with pytest.raises(HTTPException) as exc:
        await enforce_org_query_scope(ORG_B, entity_operator_user("entity-1"))

    assert exc.value.status_code == 403
    assert exc.value.detail == _QUERY_SCOPE_DETAIL

