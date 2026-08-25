"""V3 consultant / multi-client surface (Phase 7) — authorization + access.

The P0 requirement: a consultant authorized for clients A+B can access A and B
but CANNOT access C, and the backend enforces this on every endpoint (client
id / org id manipulation and cross-client data access are denied server-side).
"""
from __future__ import annotations

from tests.unit.api.fakes import consultant_user
from tests.unit.api.route_paths import flatten_router_paths

EXPECTED_PATH_FRAGMENTS = (
    "/api/v3/consultants/me",
    "/api/v3/consultants/me/branding",
    "/api/v3/consultants/me/branding/context",
    "/api/v3/consultants/me/clients",
    "/api/v3/consultants/me/dashboard",
    "/api/v3/consultants/me/team",
    "/api/v3/consultants/me/tasks",
    "/api/v3/consultants/clients/{client_id}",
    "/api/v3/consultants/clients/{client_id}/context",
    "/api/v3/consultants/clients/{client_id}/dashboard",
    "/api/v3/consultants/clients/{client_id}/reports",
    "/api/v3/consultants/clients/{client_id}/documents",
    "/api/v3/consultants/clients/{client_id}/processing/status",
    "/api/v3/consultants/clients/{client_id}/issues",
)


def test_v3_consultant_routes_registered() -> None:
    from api.router import router as v3_router

    paths = flatten_router_paths(v3_router)
    missing = [
        fragment
        for fragment in EXPECTED_PATH_FRAGMENTS
        if not any(fragment in path for path in paths)
    ]
    assert not missing, f"missing V3 consultant routes: {missing}"


def _seed_consultant(world, user_id="u-cons", *, can_manage_clients=True):
    """Seed a consultant firm with clients A (org-a) and B (org-b)."""
    world.consultants.seed_profile("firm-1", user_id, "Acme Consultants")
    world.consultants.seed_firm_member(
        "firm-1",
        user_id,
        role="manager",
        can_manage_clients=can_manage_clients,
        can_upload_documents=True,
        can_generate_reports=True,
        can_manage_team=True,
    )
    world.consultants.seed_client("client-a", "firm-1", "org-a", "ACME LTD")
    world.consultants.seed_client("client-b", "firm-1", "org-b", "Example Manufacturing")
    # A client owned by another firm (org-c) — must be denied.
    world.consultants.seed_client("client-c", "firm-2", "org-c", "Example Retail")
    return consultant_user(user_id, "cons@example.test")


# ---------------------------------------------------------------------------
# Consultant identity / firm membership
# ---------------------------------------------------------------------------


def test_consultant_requires_authentication(client, user_provider) -> None:
    user_provider.set_unauthenticated()
    assert client.get("/api/v3/consultants/me").status_code == 401


def test_consultant_requires_firm_membership(client, world, user_provider) -> None:
    user_provider.set_user(consultant_user("u-nobody", "nobody@example.test"))
    assert client.get("/api/v3/consultants/me").status_code == 403


def test_consultant_me_returns_profile(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.get("/api/v3/consultants/me")
    assert response.status_code == 200
    assert response.json()["company_name"] == "Acme Consultants"


def test_consultant_list_clients(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.get("/api/v3/consultants/me/clients")
    assert response.status_code == 200
    names = [c["client_name"] for c in response.json()["clients"]]
    assert names == ["ACME LTD", "Example Manufacturing"]


def test_consultant_non_member_cannot_list_clients(client, world, user_provider) -> None:
    user_provider.set_user(consultant_user("u-nobody", "nobody@example.test"))
    assert client.get("/api/v3/consultants/me/clients").status_code == 403


# ---------------------------------------------------------------------------
# Authorized / unauthorized clients (A, B allowed; C denied)
# ---------------------------------------------------------------------------


def test_client_a_allowed(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.get("/api/v3/consultants/clients/client-a")
    assert response.status_code == 200
    assert response.json()["client"]["client_name"] == "ACME LTD"


def test_client_b_allowed(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.get("/api/v3/consultants/clients/client-b")
    assert response.status_code == 200
    assert response.json()["client"]["client_name"] == "Example Manufacturing"


def test_client_c_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    # Client C belongs to another firm → denied even though the id is known.
    assert client.get("/api/v3/consultants/clients/client-c").status_code == 403


def test_nonexistent_client_404(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert client.get("/api/v3/consultants/clients/does-not-exist").status_code == 404


def test_client_id_manipulation_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    # Manipulating the client id to another firm's client is denied (403).
    assert client.get("/api/v3/consultants/clients/client-c").status_code == 403


# ---------------------------------------------------------------------------
# Client workspace / client data access (cross-client isolation)
# ---------------------------------------------------------------------------


def test_client_context_a(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.get("/api/v3/consultants/clients/client-a/context")
    assert response.status_code == 200
    body = response.json()
    assert body["client"]["organization_id"] == "org-a"
    assert "organization" in body
    assert "processing" in body
    assert "issues" in body
    assert "reports" in body


def test_client_context_cross_client_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert client.get("/api/v3/consultants/clients/client-c/context").status_code == 403


def test_cross_client_document_access_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert client.get("/api/v3/consultants/clients/client-c/documents").status_code == 403


def test_cross_client_emissions_access_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert client.get(
        "/api/v3/consultants/clients/client-c/dashboard",
        params={"start_date": "2025-01-01", "end_date": "2025-12-31"},
    ).status_code == 403


def test_cross_client_report_access_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert client.get("/api/v3/consultants/clients/client-c/reports").status_code == 403


def test_cross_client_processing_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert client.get("/api/v3/consultants/clients/client-c/processing/status").status_code == 403


def test_cross_client_issues_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    assert client.get("/api/v3/consultants/clients/client-c/issues").status_code == 403


def test_client_a_dashboard_real_data(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.get(
        "/api/v3/consultants/clients/client-a/dashboard",
        params={"start_date": "2025-01-01", "end_date": "2025-12-31"},
    )
    assert response.status_code == 200
    body = response.json()
    # Real persisted org-a log: 1000 kWh × 0.183 = 183.000000.
    assert body["total_co2e_kg"] == "183.000000"
    assert body["total_rows"] == 1


def test_client_reports_real_data(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    world.reports.seed_report(report_id="rep-a", org_id="org-a", status="completed")
    response = client.get("/api/v3/consultants/clients/client-a/reports")
    assert response.status_code == 200
    assert [r["id"] for r in response.json()["reports"]] == ["rep-a"]


def test_client_dashboard_invalid_period(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    response = client.get(
        "/api/v3/consultants/clients/client-a/dashboard",
        params={"start_date": "not-a-date", "end_date": "2025-12-31"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Consultant dashboard (real aggregates)
# ---------------------------------------------------------------------------


def test_consultant_dashboard_real_aggregates(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    world.reports.seed_report(report_id="rep-a", org_id="org-a", status="completed")
    response = client.get("/api/v3/consultants/me/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["client_count"] == 2  # firm-1 owns client-a + client-b only
    assert body["active_client_count"] == 2
    assert body["ready_reports"] == 1
    assert body["clients_by_status"]["active"] == 2


# ---------------------------------------------------------------------------
# Consultant action permissions (role-based restrictions)
# ---------------------------------------------------------------------------


def test_add_client_requires_manage_clients(client, world, user_provider) -> None:
    user = _seed_consultant(world, can_manage_clients=False)
    user_provider.set_user(user)
    response = client.post(
        "/api/v3/consultants/me/clients",
        json={"organization_id": "org-d", "client_name": "Org D"},
    )
    assert response.status_code == 403


def test_add_client_succeeds_with_permission(client, world, user_provider) -> None:
    user = _seed_consultant(world, can_manage_clients=True)
    user_provider.set_user(user)
    response = client.post(
        "/api/v3/consultants/me/clients",
        json={"organization_id": "org-d", "client_name": "Org D"},
    )
    assert response.status_code == 201
    assert response.json()["organization_id"] == "org-d"


def test_add_client_duplicate_409(client, world, user_provider) -> None:
    user = _seed_consultant(world, can_manage_clients=True)
    user_provider.set_user(user)
    response = client.post(
        "/api/v3/consultants/me/clients",
        json={"organization_id": "org-a", "client_name": "ACME again"},
    )
    assert response.status_code == 409


def test_add_team_member_requires_manage_team(client, world, user_provider) -> None:
    _seed_consultant(world)
    # A consultant without can_manage_team (separate firm membership) is denied.
    world.consultants.seed_profile("firm-limited", "u-limited", "Small Consultancy")
    world.consultants.seed_firm_member("firm-limited", "u-limited", role="consultant")
    user_provider.set_user(consultant_user("u-limited", "limited@example.test"))
    response = client.post(
        "/api/v3/consultants/me/team",
        json={"user_id": "u-new", "role": "consultant"},
    )
    assert response.status_code == 403


def test_client_status_update(client, world, user_provider) -> None:
    user = _seed_consultant(world, can_manage_clients=True)
    user_provider.set_user(user)
    response = client.put(
        "/api/v3/consultants/clients/client-b",
        json={"status": "inactive"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


def test_client_status_update_invalid(client, world, user_provider) -> None:
    user = _seed_consultant(world, can_manage_clients=True)
    user_provider.set_user(user)
    response = client.put(
        "/api/v3/consultants/clients/client-b",
        json={"status": "archived"},
    )
    assert response.status_code == 422


def test_deactivate_client_cross_firm_denied(client, world, user_provider) -> None:
    user = _seed_consultant(world, can_manage_clients=True)
    user_provider.set_user(user)
    assert client.delete("/api/v3/consultants/clients/client-c").status_code == 403


def test_consultant_cannot_use_customer_member_surface(client, world, user_provider) -> None:
    user = _seed_consultant(world)
    user_provider.set_user(user)
    # A consultant is not an org member: the customer surface is denied.
    assert client.get("/api/v3/organizations/org-a/profile").status_code == 403


