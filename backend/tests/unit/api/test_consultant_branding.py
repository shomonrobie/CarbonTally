"""D21 — White-Label Foundation: consultant branding authorization + presentation.

Covers the required test matrix:

    A  consultant branding isolation / self-service
    B  customer cannot administer consultant branding
    C  Processing Entity staff cannot administer consultant branding
    D  internal staff retain operational access, no branding admin
    E  branding disabled → CarbonTally fallback
    F  white-label enabled → consultant brand
    G  co-branding enabled → consultant + CarbonTally
    H  Direct Customer never inherits consultant branding
    I  cross-consultant report-branding isolation
    J  client-supplied consultant id can never target another firm
    K  report branding uses the authorized context
    L  email branding uses only authorized consultant configuration
    M  Processing Entity staff cannot gain branding admin via role names

Every check runs in memory (no database access).
"""
from __future__ import annotations

from domain.staff import StaffProfile, StaffRole
from tests.unit.api.fakes import (
    consultant_user,
    entity_operator_user,
    member_user,
    staff_user,
)

BRANDING_URL = "/api/v3/consultants/me/branding"
BRANDING_CONTEXT_URL = "/api/v3/consultants/me/branding/context"


def _seed_firm(
    world,
    user_id: str = "u-cons",
    firm: str = "firm-1",
    role: str = "manager",
    can_manage_team: bool = True,
    company_name: str = "Acme Consultants",
):
    world.consultants.seed_profile(firm, user_id, company_name)
    world.consultants.seed_firm_member(
        firm,
        user_id,
        role=role,
        can_manage_clients=True,
        can_upload_documents=True,
        can_generate_reports=True,
        can_manage_team=can_manage_team,
    )
    return consultant_user(user_id, f"{user_id}@example.test")


# ---------------------------------------------------------------------------
# A — branding isolation / self-service
# ---------------------------------------------------------------------------


def test_consultant_reads_own_branding(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_branding(
        "firm-a", brand_name="A Green", white_label_enabled=True
    )
    user_provider.set_user(user)
    response = client.get(BRANDING_URL)
    assert response.status_code == 200
    body = response.json()
    assert body["branding"]["profile_id"] == "firm-a"
    assert body["branding"]["brand_name"] == "A Green"
    assert body["branding"]["white_label_enabled"] is True
    assert body["brand_context"]["kind"] == "consultant"
    assert body["can_manage_branding"] is True


def test_consultant_updates_own_branding(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    user_provider.set_user(user)
    response = client.put(
        BRANDING_URL,
        json={
            "brand_name": "A Green Ltd",
            "primary_color": "#0f766e",
            "white_label_enabled": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["branding"]["brand_name"] == "A Green Ltd"
    assert body["branding"]["primary_color"] == "#0f766e"
    assert body["branding"]["white_label_enabled"] is True
    assert body["brand_context"]["kind"] == "consultant"
    assert body["brand_context"]["display_name"] == "A Green Ltd"


def test_cross_consultant_isolation_and_arbitrary_id(client, world, user_provider) -> None:
    """A client-supplied ``consultant_id`` can never redirect an update.

    The endpoint has no consultant-id parameter: the profile id is always the
    authenticated caller's own. Firm B's branding stays untouched even when A
    sends B's id in the body.
    """
    user_a = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_branding("firm-a", brand_name="Firm A Brand")
    world.consultants.seed_profile("firm-b", "u-b", "Firm B Ltd")
    world.consultants.seed_firm_member(
        "firm-b", "u-b", role="owner", can_manage_team=True
    )
    world.consultants.seed_branding("firm-b", brand_name="Firm B Brand")

    user_provider.set_user(user_a)
    response = client.put(
        BRANDING_URL,
        json={"consultant_id": "firm-b", "brand_name": "Hijacked"},
    )
    assert response.status_code == 200
    assert response.json()["branding"]["profile_id"] == "firm-a"
    assert response.json()["branding"]["brand_name"] == "Hijacked"

    # Firm B is unchanged, verified through B's own authorized view.
    user_provider.set_user(consultant_user("u-b", "u-b@example.test"))
    b_view = client.get(BRANDING_URL)
    assert b_view.status_code == 200
    assert b_view.json()["branding"]["profile_id"] == "firm-b"
    assert b_view.json()["branding"]["brand_name"] == "Firm B Brand"


def test_non_admin_consultant_can_read_but_not_write(client, world, user_provider) -> None:
    user = _seed_firm(
        world,
        user_id="u-a",
        firm="firm-a",
        role="consultant",
        can_manage_team=False,
    )
    user_provider.set_user(user)
    assert client.get(BRANDING_URL).status_code == 200
    assert client.get(BRANDING_URL).json()["can_manage_branding"] is False
    assert (
        client.put(BRANDING_URL, json={"brand_name": "Nope"}).status_code == 403
    )


def test_firm_owner_can_administer_branding(client, world, user_provider) -> None:
    user = _seed_firm(
        world,
        user_id="u-a",
        firm="firm-a",
        role="owner",
        can_manage_team=False,
    )
    user_provider.set_user(user)
    response = client.put(BRANDING_URL, json={"brand_name": "Owner Brand"})
    assert response.status_code == 200
    assert response.json()["branding"]["brand_name"] == "Owner Brand"


def test_branding_update_is_audited(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_branding("firm-a", brand_name="Before")
    user_provider.set_user(user)
    response = client.put(BRANDING_URL, json={"brand_name": "After"})
    assert response.status_code == 200
    entries = [
        e
        for e in world.audit._entries
        if e.action == "consultant.branding.update"
    ]
    assert len(entries) == 1
    assert entries[0].entity_id == "firm-a"
    assert entries[0].actor == "u-a"
    assert entries[0].before.get("brand_name") == "Before"
    assert entries[0].after.get("brand_name") == "After"


# ---------------------------------------------------------------------------
# B — customers cannot administer consultant branding
# ---------------------------------------------------------------------------


def test_customer_denied_branding_admin(client, world, user_provider) -> None:
    _seed_firm(world, user_id="u-a", firm="firm-a")
    user_provider.set_user(member_user("org-a", "u-cust", "cust@example.test"))
    assert client.get(BRANDING_URL).status_code == 403
    assert client.get(BRANDING_CONTEXT_URL).status_code == 403
    assert (
        client.put(BRANDING_URL, json={"brand_name": "x"}).status_code == 403
    )


# ---------------------------------------------------------------------------
# C / M — Processing Entity staff can never administer consultant branding
# ---------------------------------------------------------------------------


def test_processing_entity_staff_denied_branding_admin(
    client, world, user_provider
) -> None:
    _seed_firm(world, user_id="u-a", firm="firm-a")
    user_provider.set_user(entity_operator_user("entity-1", "u-entity"))
    assert client.get(BRANDING_URL).status_code == 403
    assert (
        client.put(BRANDING_URL, json={"brand_name": "x"}).status_code == 403
    )


def test_entity_staff_cannot_gain_admin_via_role_names(
    client, world, user_provider
) -> None:
    """Role strings never grant branding administration on their own."""
    _seed_firm(world, user_id="u-a", firm="firm-a")
    # An identity named like a consultant is still not a consultant firm member.
    user_provider.set_user(
        consultant_user("u-ent", "ent@entity.test", role="consultant")
    )
    assert client.get(BRANDING_URL).status_code == 403
    # A consultant-like identity with no ACTIVE firm membership is also denied.
    user_provider.set_user(consultant_user("u-nomember", "nobody@example.test"))
    assert (
        client.put(BRANDING_URL, json={"brand_name": "x"}).status_code == 403
    )


# ---------------------------------------------------------------------------
# D — internal staff: operational access retained, no branding admin
# ---------------------------------------------------------------------------


def test_internal_staff_ops_access_retained_no_branding_admin(
    client, world, user_provider
) -> None:
    # Seed the ops world exactly like the operations suite (real staff model).
    world.staff.seed_role(
        StaffRole(id="role-manager", name="manager", permissions={"can_view_all": True})
    )
    world.staff.seed_profile(
        StaffProfile(
            id="sp-mgr",
            user_id="u-mgr",
            first_name="Mgr",
            last_name="One",
            email="mgr@carbontally.test",
            role_id="role-manager",
            entity_id=None,
        )
    )
    user_provider.set_user(staff_user("u-mgr", email="mgr@carbontally.test"))

    # Internal staff operational surface still works (D20 model intact).
    assert client.get("/api/v3/ops/me").status_code == 200

    # But there is no global consultant-branding administration: internal staff
    # without a consultant firm membership are denied.
    assert client.get(BRANDING_URL).status_code == 403
    assert (
        client.put(BRANDING_URL, json={"brand_name": "x"}).status_code == 403
    )


# ---------------------------------------------------------------------------
# E / F / G — presentation-mode resolution
# ---------------------------------------------------------------------------


def test_branding_disabled_uses_carbontally_fallback(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_branding(
        "firm-a",
        brand_name="Acme",
        white_label_enabled=False,
        co_branding_enabled=False,
    )
    user_provider.set_user(user)
    response = client.get(BRANDING_CONTEXT_URL)
    assert response.status_code == 200
    context = response.json()["brand_context"]
    assert context["kind"] == "carbon_tally"
    assert context["display_name"] == "CarbonTally"
    assert context["co_branded_with_carbontally"] is False


def test_white_label_enabled_uses_consultant_brand(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_branding(
        "firm-a",
        brand_name="Acme",
        logo_url="https://acme.example/logo.png",
        white_label_enabled=True,
        co_branding_enabled=False,
    )
    user_provider.set_user(user)
    context = client.get(BRANDING_CONTEXT_URL).json()["brand_context"]
    assert context["kind"] == "consultant"
    assert context["display_name"] == "Acme"
    assert context["logo_url"] == "https://acme.example/logo.png"
    assert context["co_branded_with_carbontally"] is False


def test_co_branding_enabled_uses_both_brands(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_branding(
        "firm-a",
        brand_name="Acme",
        white_label_enabled=False,
        co_branding_enabled=True,
    )
    user_provider.set_user(user)
    context = client.get(BRANDING_CONTEXT_URL).json()["brand_context"]
    assert context["kind"] == "co_branded"
    assert context["display_name"] == "Acme"
    assert context["co_branded_with_carbontally"] is True


def test_white_label_wins_over_co_branding(client, world, user_provider) -> None:
    """Mutually exclusive modes: white-label takes precedence (never both)."""
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_branding(
        "firm-a",
        brand_name="Acme",
        white_label_enabled=True,
        co_branding_enabled=True,
    )
    user_provider.set_user(user)
    context = client.get(BRANDING_CONTEXT_URL).json()["brand_context"]
    assert context["kind"] == "consultant"
    assert context["co_branded_with_carbontally"] is False


# ---------------------------------------------------------------------------
# H / K / I — report branding comes from authorized context only
# ---------------------------------------------------------------------------


def test_direct_customer_reports_use_carbontally_branding(
    client, world, user_provider
) -> None:
    user_provider.set_user(member_user("org-a", "u-cust", "cust@example.test"))
    response = client.get("/api/v3/reports?organization_id=org-a")
    assert response.status_code == 200
    assert response.json()["branding"]["kind"] == "carbon_tally"
    assert response.json()["branding"]["display_name"] == "CarbonTally"


def test_consultant_client_reports_use_own_branding(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_client("client-a", "firm-a", "org-a", "ACME LTD", status="active")
    world.consultants.seed_branding(
        "firm-a", brand_name="Acme Green", white_label_enabled=True
    )
    user_provider.set_user(user)
    response = client.get("/api/v3/consultants/clients/client-a/reports")
    assert response.status_code == 200
    branding = response.json()["branding"]
    assert branding["kind"] == "consultant"
    assert branding["display_name"] == "Acme Green"


def test_cross_consultant_report_branding_isolation(
    client, world, user_provider
) -> None:
    user_a = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_client("client-a", "firm-a", "org-a", "ACME LTD", status="active")
    world.consultants.seed_branding(
        "firm-a", brand_name="Firm A", white_label_enabled=True
    )
    world.consultants.seed_profile("firm-b", "u-b", "Firm B Ltd")
    world.consultants.seed_firm_member(
        "firm-b", "u-b", role="owner", can_manage_team=True
    )
    world.consultants.seed_branding(
        "firm-b", brand_name="Firm B", white_label_enabled=True
    )
    world.consultants.seed_client("client-b", "firm-b", "org-b", "B LTD", status="active")

    # A's client reports carry A's branding, never B's.
    user_provider.set_user(user_a)
    a_reports = client.get("/api/v3/consultants/clients/client-a/reports")
    assert a_reports.status_code == 200
    assert a_reports.json()["branding"]["display_name"] == "Firm A"

    # B's client reports carry B's branding.
    user_provider.set_user(consultant_user("u-b", "u-b@example.test"))
    b_reports = client.get("/api/v3/consultants/clients/client-b/reports")
    assert b_reports.status_code == 200
    assert b_reports.json()["branding"]["display_name"] == "Firm B"


def test_inactive_grant_denies_report_access_and_branding(
    client, world, user_provider
) -> None:
    """D15 stays intact: an inactive grant is no data access (and therefore no
    consultant-branded report surface either)."""
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    world.consultants.seed_client(
        "client-old", "firm-a", "org-a", "Ended Client", status="inactive"
    )
    world.consultants.seed_branding(
        "firm-a", brand_name="Firm A", white_label_enabled=True
    )
    user_provider.set_user(user)
    response = client.get("/api/v3/consultants/clients/client-old/reports")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# L — email branding uses only authorized consultant configuration
# ---------------------------------------------------------------------------


def test_email_from_validation_and_isolation(client, world, user_provider) -> None:
    user_a = _seed_firm(world, user_id="u-a", firm="firm-a")
    user_provider.set_user(user_a)

    # Invalid sender address is rejected — no arbitrary sender strings.
    assert (
        client.put(BRANDING_URL, json={"email_from": "not-an-email"}).status_code == 422
    )
    # A valid address for the firm's own branding is accepted.
    response = client.put(
        BRANDING_URL, json={"email_from": "hello@acme.example"}
    )
    assert response.status_code == 200
    assert response.json()["branding"]["email_from"] == "hello@acme.example"

    # Firm B never sees A's sender configuration through its own endpoint.
    world.consultants.seed_profile("firm-b", "u-b", "Firm B Ltd")
    world.consultants.seed_firm_member(
        "firm-b", "u-b", role="owner", can_manage_team=True
    )
    user_provider.set_user(consultant_user("u-b", "u-b@example.test"))
    b_view = client.get(BRANDING_URL)
    assert b_view.status_code == 200
    assert b_view.json()["branding"]["email_from"] is None
    # B cannot re-point A's sender: the update writes B's own row only.
    client.put(BRANDING_URL, json={"email_from": "hello@firm-b.example"})
    user_provider.set_user(user_a)
    assert (
        client.get(BRANDING_URL).json()["branding"]["email_from"]
        == "hello@acme.example"
    )


# ---------------------------------------------------------------------------
# Validation hygiene
# ---------------------------------------------------------------------------


def test_branding_payload_validation(client, world, user_provider) -> None:
    user = _seed_firm(world, user_id="u-a", firm="firm-a")
    user_provider.set_user(user)
    assert (
        client.put(BRANDING_URL, json={"logo_url": "javascript:alert(1)"}).status_code
        == 422
    )
    assert (
        client.put(BRANDING_URL, json={"primary_color": "blue"}).status_code == 422
    )
    assert (
        client.put(
            BRANDING_URL, json={"logo_url": "https://cdn.example/a.png"}
        ).status_code
        == 200
    )


