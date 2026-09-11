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
    # P6-1C: engaging an ALREADY-EXISTING organisation creates a PENDING
    # request — never an instant active grant. Customer acceptance is required.
    world.organizations.seed_org("org-d", name="Org D")
    user = _seed_consultant(world, can_manage_clients=True)
    user_provider.set_user(user)
    response = client.post(
        "/api/v3/consultants/me/clients",
        json={"organization_id": "org-d", "client_name": "Org D"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["organization_id"] == "org-d"
    assert body["status"] == "pending"
    assert body["relationship_origin"] == "engagement_request"
    assert body["engagement_requested_at"] is not None


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


def test_team_roster_returns_human_readable_members(client, world, user_provider) -> None:
    """CL-61 — the team roster is enriched with display names/emails (no raw
    UUID-only rows) and only exposes the calling firm's members."""
    _seed_consultant(world)
    world.consultants.seed_firm_member("firm-1", "u-team-a", role="consultant", can_upload_documents=True)
    world.consultants.seed_firm_member("firm-2", "u-other-firm", role="consultant")
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))

    response = client.get("/api/v3/consultants/me/team")
    assert response.status_code == 200
    members = response.json()["members"]
    ids = {m["user_id"] for m in members}
    # Firm-1 members only; the other firm's member is never exposed.
    assert ids == {"u-cons", "u-team-a"}
    first = next(m for m in members if m["user_id"] == "u-team-a")
    assert first["email"] == "u-team-a@example.test"
    assert first["first_name"] == "u-team-a"
    assert first["can_upload_documents"] is True


# ---------------------------------------------------------------------------
# CON-2/3 — consultant client document upload + processing items
# ---------------------------------------------------------------------------


def test_consultant_upload_cross_firm_denied(client, world, user_provider) -> None:
    """A consultant cannot upload a document into another firm's client."""
    _seed_consultant(world)  # firm-1 owns client-a/b; client-c belongs to firm-2
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    response = client.post(
        "/api/v3/consultants/clients/client-c/documents",
        files={"file": ("bill.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"data_type": "utility"},
    )
    assert response.status_code == 403


def test_consultant_upload_requires_upload_permission(client, world, user_provider) -> None:
    """CON-2 — the upload action needs the real can_upload_documents permission
    (server-side), not merely an active client grant."""
    _seed_consultant(world)
    # Strip the upload capability from the firm member (re-seed as limited).
    world.consultants._members = [
        m for m in world.consultants._members
        if getattr(m, "firm_id", None) != "firm-1" or getattr(m, "user_id", None) != "u-cons"
    ]
    world.consultants.seed_firm_member(
        "firm-1", "u-cons", role="manager",
        can_manage_clients=True, can_upload_documents=False,
        can_generate_reports=True, can_manage_team=True,
    )
    world.consultants.seed_client("client-a", "firm-1", "org-a", "ACME LTD")
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    response = client.post(
        "/api/v3/consultants/clients/client-a/documents",
        files={"file": ("bill.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"data_type": "utility"},
    )
    assert response.status_code == 403


def test_consultant_client_processing_items(client, world, user_provider) -> None:
    """CON-3 — the consultant can list their client's processing items with
    org context (grant-authorized)."""
    user = _seed_consultant(world)
    user_provider.set_user(user)
    world.manual_extraction.seed_item("item-a1", "org-a", "electricity.csv", status="pending")
    response = client.get("/api/v3/consultants/clients/client-a/processing/items")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["file_name"] == "electricity.csv"
    assert data["items"][0]["organization"]["name"] is not None


def test_consultant_client_processing_items_cross_firm_denied(client, world, user_provider) -> None:
    """The items list never crosses firm boundaries."""
    _seed_consultant(world)
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    assert client.get("/api/v3/consultants/clients/client-c/processing/items").status_code == 403


def test_consultant_client_evidence_grant_scoped(client, world, user_provider) -> None:
    """E7 — the consultant's evidence view is grant-scoped: an authorized client
    returns the org evidence contract; a foreign client is denied."""
    user = _seed_consultant(world)
    user_provider.set_user(user)
    ok = client.get("/api/v3/consultants/clients/client-a/evidence")
    assert ok.status_code == 200
    body = ok.json()
    assert body["organization"]["id"] == "org-a"
    assert isinstance(body["calculations"], list)

    denied = client.get("/api/v3/consultants/clients/client-c/evidence")
    assert denied.status_code == 403


# ---------------------------------------------------------------------------
# CL-61 close-out — team member revoke (deactivate) / reactivate
# ---------------------------------------------------------------------------


def test_team_member_deactivate_revokes_access(client, world, user_provider) -> None:
    """Deactivating a team member flips their firm-membership to inactive and
    removes them from the active roster (server-side, not a UI affordance).
    ``require_consultant`` rejects inactive members on every request."""
    user = _seed_consultant(world)
    world.consultants.seed_firm_member("firm-1", "u-team-b", role="consultant", can_upload_documents=True)
    user_provider.set_user(user)  # the manager deactivates u-team-b
    team = client.get("/api/v3/consultants/me/team")
    member = next(m for m in team.json()["members"] if m["user_id"] == "u-team-b")

    deact = client.post(f"/api/v3/consultants/me/team/{member['id']}/deactivate")
    assert deact.status_code == 200
    assert deact.json()["is_active"] is False

    # The roster now shows the member as inactive.
    team = client.get("/api/v3/consultants/me/team")
    updated = next(m for m in team.json()["members"] if m["user_id"] == "u-team-b")
    assert updated["is_active"] is False

    # Reactivate restores the roster row.
    react = client.post(f"/api/v3/consultants/me/team/{member['id']}/reactivate")
    assert react.status_code == 200
    assert react.json()["is_active"] is True


def test_team_member_actions_require_manage_team(client, world, user_provider) -> None:
    """A firm member without can_manage_team cannot revoke/reactivate."""
    _seed_consultant(world)
    world.consultants.seed_profile("firm-limited", "u-limited", "Small Consultancy")
    world.consultants.seed_firm_member("firm-limited", "u-limited", role="consultant")
    world.consultants.seed_firm_member("firm-limited", "u-other", role="consultant")
    user_provider.set_user(consultant_user("u-limited", "limited@example.test"))
    member = world.consultants._members[-1]
    response = client.post(f"/api/v3/consultants/me/team/{member.id}/deactivate")
    assert response.status_code == 403


def test_team_member_cannot_deactivate_self(client, world, user_provider) -> None:
    _seed_consultant(world)
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    team = client.get("/api/v3/consultants/me/team")
    own = next(m for m in team.json()["members"] if m["user_id"] == "u-cons")
    response = client.post(f"/api/v3/consultants/me/team/{own['id']}/deactivate")
    assert response.status_code == 422


def test_team_member_deactivate_cross_firm_denied(client, world, user_provider) -> None:
    """A firm cannot revoke a member of another firm."""
    _seed_consultant(world)
    world.consultants.seed_firm_member("firm-2", "u-other", role="consultant")
    user_provider.set_user(consultant_user("u-cons", "cons@example.test"))
    other = world.consultants._members[-1]
    response = client.post(f"/api/v3/consultants/me/team/{other.id}/deactivate")
    assert response.status_code == 404


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


