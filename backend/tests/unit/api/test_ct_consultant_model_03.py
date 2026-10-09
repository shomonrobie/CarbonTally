"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — remaining consultant-model scope.

Binding source: ``docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md`` and
the four now-binding OQ decisions + five CT02 PO decisions (P1..P5).

Covered here:

* **F-3** client ACCESS PROFILE (off/read_only/collaborative/managed) is
  persisted and enforced server-side — the Plane C CEILING (§8).
* **F-4** TERMINATED = RETAINED READ-ONLY, not total denial (PO-10, §15).
* **F-5** the three PRODUCT MODES are a real mode, not two booleans (PO-3B/PO-4).
* **F-6** a mode change is a REQUEST decided by CarbonTally (PO-1).
* **F-7** Plane C is served on ``/api/v3/portal/{clientId}`` with server-side
  isolation (PO-8 A).
* **F-8** client-side relationship CHANGE/END is a confirmed, audited REQUEST.
* **PO-9** a client NEVER maps factors or recalculates, in any profile.
* **P1/P5** firm capability administration negatives.
* **OQ-2** the 7-year retention policy is one authoritative, configurable source.

Everything is asserted server-side against real routers/guards over the
in-memory world (AGENTS.md §45: an ALLOW is only evidence when it returns the
authorised tenant's own data and a DENY never leaks it).
"""
from __future__ import annotations

import asyncio

import pytest

import auth
from api.client_portal_auth import PORTAL_DENIED_DETAIL
from domain.consultant_entitlement import (
    MODE_CO_BRANDED,
    MODE_STANDARD,
    MODE_WHITE_LABEL,
    client_plane_available,
    custom_domain_available,
    managed_profile_available,
    resolve_mode,
)
from domain.consultant_retention import (
    DEFAULT_RETENTION_YEARS,
    resolve_retention_policy,
)
from domain.relationship_access import (
    PROFILE_COLLABORATIVE,
    PROFILE_MANAGED,
    PROFILE_OFF,
    PROFILE_READ_ONLY,
    STATE_ACTIVE,
    STATE_OFF,
    STATE_RETAINED_READ_ONLY,
    profile_allows,
    resolve_relationship_state,
)
from tests.unit.api.fakes import consultant_user, member_user

ORG_A = "org-a"
ORG_B = "org-b"
FIRM_ID = "firm-1"
CONSULTANT_ID = "u-cons"
COLLEAGUE_ID = "u-second"
CLIENT_A = "client-a"

PORTAL_CONTEXT = "/api/v3/portal/{client_id}/context"
PORTAL_ORG = "/api/v3/portal/{client_id}/organization"
PORTAL_ANNOTATE = "/api/v3/portal/{client_id}/annotations"
PORTAL_REQUESTS = "/api/v3/portal/{client_id}/relationship-requests"
CAPABILITIES_PATH = "/api/v3/consultants/me/team/{member_id}/capabilities"
ACCESS_PROFILE_PATH = "/api/v3/consultants/clients/{client_id}/access-profile"
RETENTION_PATH = "/api/v3/consultants/clients/{client_id}/retention"
MODE_REQUEST_PATH = "/api/v3/consultants/me/mode-change-requests"


@pytest.fixture
def live_tenants(monkeypatch):
    monkeypatch.setattr(auth, "is_organization_active", lambda organization_id: True)
    monkeypatch.setattr(
        "api.dependencies.is_organization_active", lambda organization_id: True
    )


def _seed_firm(
    world,
    *,
    mode: str = MODE_CO_BRANDED,
    white_label_enabled: bool = False,
    co_branding_enabled: bool = False,
):
    """Seed an entitled firm + one owner member (firm administration capable)."""
    world.consultants.seed_profile(FIRM_ID, CONSULTANT_ID, "Acme Consultants")
    world.consultants.seed_branding(
        FIRM_ID,
        brand_name="Acme Green",
        commercial_mode=mode,
        white_label_enabled=white_label_enabled,
        co_branding_enabled=co_branding_enabled,
    )
    world.consultants.seed_firm_member(
        FIRM_ID,
        CONSULTANT_ID,
        role="owner",
        can_view_client=True,
        can_manage_clients=True,
        can_manage_team=True,
    )
    return consultant_user(CONSULTANT_ID, "cons@example.test")


def _seed_relationship(
    world,
    *,
    profile: str = PROFILE_READ_ONLY,
    status: str = "active",
    retained_read_only: bool = False,
    org: str = ORG_A,
):
    return world.consultants.seed_client(
        CLIENT_A,
        FIRM_ID,
        org,
        "ACME LTD",
        status=status,
        client_access_profile=profile,
        retained_read_only=retained_read_only,
    )


def _client_user(org: str = ORG_A, uid: str = "client-user"):
    return member_user(org, uid, f"{uid}@client.test")


# ---------------------------------------------------------------------------
# F-3 / F-4 / PO-9 — the access-profile matrix (pure semantics)
# ---------------------------------------------------------------------------
class TestClientAccessProfileMatrix:
    @pytest.mark.parametrize(
        "status,retained,expected",
        [
            ("active", False, STATE_ACTIVE),
            ("active", True, STATE_ACTIVE),
            ("ended", True, STATE_RETAINED_READ_ONLY),
            ("terminated", True, STATE_RETAINED_READ_ONLY),
            # The retained flag can NEVER lift a non-ended relationship.
            ("suspended", True, STATE_OFF),
            ("pending", True, STATE_OFF),
            ("ended", False, STATE_OFF),
            ("", True, STATE_OFF),
        ],
    )
    def test_relationship_state_derivation(self, status, retained, expected):
        assert resolve_relationship_state(status, retained) == expected

    @pytest.mark.parametrize(
        "profile",
        [PROFILE_OFF, PROFILE_READ_ONLY, PROFILE_COLLABORATIVE, PROFILE_MANAGED],
    )
    @pytest.mark.parametrize(
        "state", [STATE_ACTIVE, STATE_RETAINED_READ_ONLY, STATE_OFF]
    )
    def test_po9_is_forbidden_in_every_profile_and_state(self, profile, state):
        """PO-9 — mapping / mapping edits / recalculation are ALWAYS denied."""
        for op in ("map_factors", "edit_mappings", "recalculate"):
            assert profile_allows(op, profile, state) is False

    def test_off_profile_permits_nothing(self):
        for op in (
            "read_data",
            "read_reports",
            "read_evidence",
            "comment",
            "upload_document",
            "edit_master_data",
        ):
            assert profile_allows(op, PROFILE_OFF, STATE_ACTIVE) is False

    def test_read_only_profile_reads_and_comments_only(self):
        assert profile_allows("read_data", PROFILE_READ_ONLY, STATE_ACTIVE)
        assert profile_allows("comment", PROFILE_READ_ONLY, STATE_ACTIVE)
        assert not profile_allows("upload_document", PROFILE_READ_ONLY, STATE_ACTIVE)
        assert not profile_allows("edit_master_data", PROFILE_READ_ONLY, STATE_ACTIVE)
        assert not profile_allows("approve_final", PROFILE_READ_ONLY, STATE_ACTIVE)

    def test_collaborative_profile_may_contribute(self):
        for op in ("read_data", "comment", "upload_document", "edit_master_data"):
            assert profile_allows(op, PROFILE_COLLABORATIVE, STATE_ACTIVE)

    def test_managed_profile_is_curated(self):
        assert profile_allows("read_data", PROFILE_MANAGED, STATE_ACTIVE)
        assert profile_allows("comment", PROFILE_MANAGED, STATE_ACTIVE)
        assert not profile_allows("upload_document", PROFILE_MANAGED, STATE_ACTIVE)
        assert not profile_allows("edit_master_data", PROFILE_MANAGED, STATE_ACTIVE)

    def test_managed_denies_approve_final_fail_closed(self):
        """§8.2 marks MANAGED approve-final ``✓*``; the ``*`` is CONDITIONAL on a
        client-role + firm-configuration gate (§13.1) that does not exist yet.

        The ceiling therefore DENIES (fail closed): granting it from the profile
        alone would confer approval authority that no ratified component confers
        (PO-9/NB-3 spirit; AGENTS §7 and §62 — never broaden authority to make a
        workflow convenient). Divergence from the matrix text is recorded as an
        open item in the CT03 report (known gaps / PO DECISION REQUIRED).
        """
        assert not profile_allows("approve_final", PROFILE_MANAGED, STATE_ACTIVE)
        # COLLABORATIVE is the only profile whose ceiling admits it (§8.2 ✓*).
        assert profile_allows("approve_final", PROFILE_COLLABORATIVE, STATE_ACTIVE)

    def test_retained_state_is_read_only_and_no_send(self):
        """PO-10 / PA-2 / PA-3 — history readable, no write, no messaging-send."""
        for profile in (PROFILE_READ_ONLY, PROFILE_COLLABORATIVE, PROFILE_MANAGED):
            assert profile_allows("read_data", profile, STATE_RETAINED_READ_ONLY)
            assert not profile_allows("comment", profile, STATE_RETAINED_READ_ONLY)
            assert not profile_allows(
                "upload_document", profile, STATE_RETAINED_READ_ONLY
            )

    def test_unknown_operation_fails_closed(self):
        assert (
            profile_allows("delete_everything", PROFILE_COLLABORATIVE, STATE_ACTIVE)
            is False
        )


# ---------------------------------------------------------------------------
# F-5 / F-9 — product mode + entitlement, and the mode-capped brand (BR-5)
# ---------------------------------------------------------------------------
class TestProductModeEntitlement:
    def test_unknown_mode_fails_closed_to_standard(self):
        assert resolve_mode("enterprise", False, False) == MODE_STANDARD
        assert resolve_mode(None, False, False) == MODE_STANDARD

    def test_mode_wins_over_a_contradicting_legacy_flag(self):
        """IMPL-3 / FM-2 / BR-5 — the stored mode caps the stored flags."""
        assert resolve_mode(MODE_STANDARD, white_label_enabled=True) == MODE_STANDARD
        assert resolve_mode(MODE_WHITE_LABEL, co_branding_enabled=True) == (
            MODE_WHITE_LABEL
        )

    def test_backward_compatible_flag_derivation_when_no_mode_stored(self):
        assert resolve_mode(None, white_label_enabled=True) == MODE_WHITE_LABEL
        assert resolve_mode(None, co_branding_enabled=True) == MODE_CO_BRANDED

    def test_standard_mode_has_no_client_plane(self):
        assert client_plane_available(MODE_STANDARD) is False
        assert managed_profile_available(MODE_STANDARD) is False
        assert custom_domain_available(MODE_STANDARD) is False

    def test_co_branded_has_a_plane_but_no_custom_domain(self):
        assert client_plane_available(MODE_CO_BRANDED) is True
        assert managed_profile_available(MODE_CO_BRANDED) is True
        assert custom_domain_available(MODE_CO_BRANDED) is False

    def test_only_white_label_permits_a_custom_domain(self):
        assert client_plane_available(MODE_WHITE_LABEL) is True
        assert managed_profile_available(MODE_WHITE_LABEL) is True
        assert custom_domain_available(MODE_WHITE_LABEL) is True

    def test_brand_is_capped_by_the_mode(self):
        from domain.branding import ConsultantBranding, resolve_brand_context

        capped = ConsultantBranding(
            profile_id="f",
            brand_name="Acme",
            white_label_enabled=True,
            commercial_mode=MODE_STANDARD,
        )
        # A white-label flag on a STANDARD firm does NOT produce a white-label
        # experience — the mode caps it (BR-5) and the flag is not destroyed.
        assert resolve_brand_context(capped, "Acme").kind == "carbon_tally"
        assert capped.white_label_enabled is True

        legacy = ConsultantBranding(
            profile_id="f", brand_name="Acme", white_label_enabled=True
        )
        # No mode stored -> ratified D21 derivations preserved (backward compat).
        assert resolve_brand_context(legacy, "Acme").kind == "consultant"

    def test_emission_rederivation_order(self):
        """A mode that contradicts BOTH flags still decides the presentation."""
        from domain.branding import ConsultantBranding, resolve_brand_context

        branding = ConsultantBranding(
            profile_id="f",
            brand_name="Acme",
            white_label_enabled=False,
            co_branding_enabled=True,
            commercial_mode=MODE_WHITE_LABEL,
        )
        assert resolve_brand_context(branding, "Acme").kind == "consultant"


# ---------------------------------------------------------------------------
# OQ-2 — the retention policy is central, configurable and fail-safe
# ---------------------------------------------------------------------------
class TestRetentionPolicy:
    def test_default_is_seven_years(self):
        policy = resolve_retention_policy(None)
        assert policy.years == DEFAULT_RETENTION_YEARS == 7
        assert policy.retained_read_only is True
        assert policy.auto_delete_enabled is False

    def test_configurable_and_validated(self):
        assert resolve_retention_policy({"years": 10}).years == 10
        # Malformed / non-positive values fall back to the ratified default.
        assert resolve_retention_policy({"years": 0}).years == 7
        assert resolve_retention_policy({"years": "nonsense"}).years == 7

    def test_retained_expiry_is_derived_not_hardcoded(self):
        from datetime import datetime, timedelta, timezone

        ended = datetime(2020, 1, 1, tzinfo=timezone.utc)
        policy = resolve_retention_policy({"years": 7})
        assert policy.is_retained(ended, now=ended + timedelta(days=365 * 6)) is True
        assert policy.is_retained(ended, now=ended + timedelta(days=365 * 8)) is False


# ---------------------------------------------------------------------------
# F-7 / F-3 / F-4 — the Plane C gate (server-side, generic, isolating)
# ---------------------------------------------------------------------------
class TestPlaneCGate:
    def test_active_read_only_client_reaches_its_own_workspace(
        self, world, client, user_provider, live_tenants
    ):
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY)
        user_provider.set_user(_client_user())
        resp = client.get(PORTAL_CONTEXT.format(client_id=ORG_A))
        assert resp.status_code == 200
        body = resp.json()
        assert body["organization"]["id"] == ORG_A
        assert body["profile"] == PROFILE_READ_ONLY
        assert body["state"] == STATE_ACTIVE
        assert body["capabilities"]["read_data"] is True
        assert body["capabilities"]["map_factors"] is False
        assert body["capabilities"]["recalculate"] is False

    def test_foreign_client_id_is_denied_generically(
        self, world, client, user_provider, live_tenants
    ):
        """INV-B / INV-C / NT-04/05/06 — no existence oracle."""
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY)
        user_provider.set_user(_client_user(org=ORG_A))
        resp = client.get(PORTAL_CONTEXT.format(client_id=ORG_B))
        assert resp.status_code == 403
        # The platform's error envelope is {"error": {"code","message",...}}.
        assert resp.json()["error"]["message"] == PORTAL_DENIED_DETAIL
        assert "Org B" not in resp.text and "ACME" not in resp.text

    def test_direct_customer_has_no_plane(
        self, world, client, user_provider, live_tenants
    ):
        """An organisation with no consultant relationship is not on Plane C."""
        _seed_firm(world)
        user_provider.set_user(_client_user(org=ORG_B))
        resp = client.get(PORTAL_CONTEXT.format(client_id=ORG_B))
        assert resp.status_code == 403

    @pytest.mark.parametrize("profile", [PROFILE_OFF])
    def test_off_profile_has_no_plane(
        self, world, client, user_provider, live_tenants, profile
    ):
        _seed_firm(world)
        _seed_relationship(world, profile=profile)
        user_provider.set_user(_client_user())
        assert client.get(PORTAL_CONTEXT.format(client_id=ORG_A)).status_code == 403

    @pytest.mark.parametrize("status", ["suspended", "pending", "ended", "inactive"])
    def test_non_active_links_are_denied(
        self, world, client, user_provider, live_tenants, status
    ):
        """INV-E / NT-07 — only ACTIVE or RETAINED may use the plane."""
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY, status=status)
        user_provider.set_user(_client_user())
        assert client.get(PORTAL_CONTEXT.format(client_id=ORG_A)).status_code == 403

    def test_standard_mode_firm_has_no_plane_at_all(
        self, world, client, user_provider, live_tenants
    ):
        """AC-F-16 / MUSTNOT-5 — a STANDARD firm exposes no client plane."""
        _seed_firm(world, mode=MODE_STANDARD)
        _seed_relationship(world, profile=PROFILE_READ_ONLY)
        user_provider.set_user(_client_user())
        assert client.get(PORTAL_CONTEXT.format(client_id=ORG_A)).status_code == 403

    def test_retained_read_only_resolves_and_is_read_only(
        self, world, client, user_provider, live_tenants
    ):
        """F-4 / PO-10 / AC-F-5 — a retained client sees history, cannot write."""
        _seed_firm(world)
        _seed_relationship(
            world,
            profile=PROFILE_COLLABORATIVE,
            status="ended",
            retained_read_only=True,
        )
        user_provider.set_user(_client_user())
        resp = client.get(PORTAL_CONTEXT.format(client_id=ORG_A))
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == STATE_RETAINED_READ_ONLY
        assert body["capabilities"]["read_data"] is True
        assert body["capabilities"]["comment"] is False

    def test_unauthenticated_is_rejected(self, world, client, user_provider):
        _seed_firm(world)
        _seed_relationship(world)
        user_provider.set_unauthenticated()
        assert client.get(PORTAL_CONTEXT.format(client_id=ORG_A)).status_code == 401

    def test_consultant_identity_is_not_admitted_to_plane_c(
        self, world, client, user_provider, live_tenants
    ):
        """§7.1 — a consultant uses their own plane, never a client's."""
        user = _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY)
        user_provider.set_user(user)
        assert client.get(PORTAL_CONTEXT.format(client_id=ORG_A)).status_code == 403


# ---------------------------------------------------------------------------
# F-3 / F-7 — the profile ceiling is enforced on WRITES too (§8.2)
# ---------------------------------------------------------------------------
class TestPlaneCWriteCeiling:
    @pytest.mark.parametrize(
        "profile", [PROFILE_READ_ONLY, PROFILE_COLLABORATIVE, PROFILE_MANAGED]
    )
    def test_active_profiles_may_comment(
        self, world, client, user_provider, live_tenants, profile
    ):
        _seed_firm(world)
        _seed_relationship(world, profile=profile)
        user_provider.set_user(_client_user())
        resp = client.post(
            PORTAL_ANNOTATE.format(client_id=ORG_A), json={"message": "question"}
        )
        assert resp.status_code == 201

    def test_retained_client_may_not_comment(
        self, world, client, user_provider, live_tenants
    ):
        """PA-3 — no messaging-send after termination, but reads still work."""
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_MANAGED, status="ended", retained_read_only=True)
        user_provider.set_user(_client_user())
        assert (
            client.post(PORTAL_ANNOTATE.format(client_id=ORG_A), json={"message": "x"})
            .status_code
            == 403
        )
        assert (
            client.get(PORTAL_ORG.format(client_id=ORG_A)).status_code == 200
        )

    def test_organization_read_is_organisation_scoped(
        self, world, client, user_provider, live_tenants
    ):
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY)
        user_provider.set_user(_client_user())
        resp = client.get(PORTAL_ORG.format(client_id=ORG_A))
        assert resp.status_code == 200
        assert resp.json()["organization"]["name"] == "Org A"

    def test_no_mapping_or_recalculation_route_exists_on_plane_c(self, app):
        """PO-9 / AC-F-10 / NB-3 — the capability is absent from the API."""
        paths = list(app.openapi()["paths"])
        portal = [p for p in paths if "/api/v3/portal" in p]
        assert portal, "the Plane C family must be mounted"
        for p in portal:
            assert "map" not in p
            assert "factor" not in p
            assert "recalc" not in p
            assert "invite" not in p
            assert "billing" not in p
            assert "subscription" not in p
            assert "brand" not in p
            assert "access-profile" not in p


# ---------------------------------------------------------------------------
# F-8 — client-initiated relationship CHANGE/END is a confirmed REQUEST
# ---------------------------------------------------------------------------
class TestClientRelationshipRequests:
    def test_client_can_request_an_end_of_relationship(
        self, world, client, user_provider, live_tenants
    ):
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY)
        user_provider.set_user(_client_user())
        resp = client.post(
            PORTAL_REQUESTS.format(client_id=ORG_A),
            json={"request_type": "end_relationship", "confirmed": True},
        )
        assert resp.status_code == 201
        body = resp.json()["request"]
        assert body["request_type"] == "end_relationship"
        assert body["initiated_capacity"] == "client"
        assert body["status"] == "requested"
        # Non-destructive: the relationship row is untouched.
        rel = asyncio.run(world.consultants.get_client_by_org(FIRM_ID, ORG_A))
        assert rel.status == "active"

    def test_request_requires_explicit_confirmation(
        self, world, client, user_provider, live_tenants
    ):
        """T-1 — no single-click termination."""
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY)
        user_provider.set_user(_client_user())
        resp = client.post(
            PORTAL_REQUESTS.format(client_id=ORG_A),
            json={"request_type": "end_relationship"},
        )
        assert resp.status_code == 428

    def test_invalid_request_type_is_rejected(
        self, world, client, user_provider, live_tenants
    ):
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY)
        user_provider.set_user(_client_user())
        resp = client.post(
            PORTAL_REQUESTS.format(client_id=ORG_A),
            json={"request_type": "delete_everything", "confirmed": True},
        )
        assert resp.status_code == 422

    def test_retained_client_cannot_re_request_on_the_plane(
        self, world, client, user_provider, live_tenants
    ):
        _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY, status="ended", retained_read_only=True)
        user_provider.set_user(_client_user())
        resp = client.post(
            PORTAL_REQUESTS.format(client_id=ORG_A),
            json={"request_type": "end_relationship", "confirmed": True},
        )
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# P1 / P5 — capability administration negatives
# ---------------------------------------------------------------------------
class TestCapabilityAdministration:
    def test_firm_admin_can_grant_the_full_operational_set(
        self, world, client, user_provider, live_tenants
    ):
        user = _seed_firm(world)
        world.consultants.seed_firm_member(
            FIRM_ID, COLLEAGUE_ID, role="consultant", can_map=True
        )
        user_provider.set_user(user)
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{COLLEAGUE_ID}"),
            json={"can_approve": True, "can_manage_team": True, "can_extract": True},
        )
        assert resp.status_code == 200
        member = asyncio.run(
            world.consultants.get_firm_member(FIRM_ID, f"fm-{COLLEAGUE_ID}")
        )
        assert member.can_approve is True
        assert member.can_manage_team is True
        assert member.can_extract is True
        # F-10 — a capability absent from the request keeps its stored value.
        assert member.can_map is True

    def test_a_consultant_cannot_elevate_itself(
        self, world, client, user_provider, live_tenants
    ):
        user = _seed_firm(world)
        user_provider.set_user(user)
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{CONSULTANT_ID}"),
            json={"can_approve": True},
        )
        assert resp.status_code == 422
        member = asyncio.run(
            world.consultants.get_firm_member(FIRM_ID, f"fm-{CONSULTANT_ID}")
        )
        assert member.can_approve is False

    def test_cross_firm_target_is_denied(
        self, world, client, user_provider, live_tenants
    ):
        """INV-A — a firm can only administer its OWN members."""
        user = _seed_firm(world)
        world.consultants.seed_profile("firm-2", "u-other", "Rival Consultants")
        world.consultants.seed_firm_member("firm-2", "u-other", role="owner")
        user_provider.set_user(user)
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id="fm-u-other"),
            json={"can_approve": True},
        )
        assert resp.status_code == 404

    def test_commercial_entitlement_is_not_addressable(
        self, world, client, user_provider, live_tenants
    ):
        """P5 / §6.3 / NB-7 — no field here can grant commercial entitlement."""
        user = _seed_firm(world)
        world.consultants.seed_firm_member(FIRM_ID, COLLEAGUE_ID, role="consultant")
        user_provider.set_user(user)
        for field in ("white_label_enabled", "seats", "plan", "commercial_mode"):
            resp = client.patch(
                CAPABILITIES_PATH.format(member_id=f"fm-{COLLEAGUE_ID}"),
                json={field: True},
            )
            assert resp.status_code == 422, field

    def test_without_cap_manage_team_administration_is_denied(
        self, world, client, user_provider, live_tenants
    ):
        _seed_firm(world)
        world.consultants.seed_firm_member(
            FIRM_ID, COLLEAGUE_ID, role="consultant", can_manage_team=False
        )
        user_provider.set_user(consultant_user(COLLEAGUE_ID, "second@example.test"))
        resp = client.patch(
            CAPABILITIES_PATH.format(member_id=f"fm-{CONSULTANT_ID}"),
            json={"can_approve": True},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# F-3 / F-4 / F-6 — firm-side relationship, retention and mode-request APIs
# ---------------------------------------------------------------------------
class TestFirmSideRelationshipAdministration:
    def test_access_profile_is_entitlement_checked(
        self, world, client, user_provider, live_tenants
    ):
        """A STANDARD firm cannot open a client plane (PO-4)."""
        user = _seed_firm(world, mode=MODE_STANDARD)
        _seed_relationship(world, profile=PROFILE_OFF)
        user_provider.set_user(user)
        resp = client.post(
            ACCESS_PROFILE_PATH.format(client_id=CLIENT_A),
            json={"profile": PROFILE_READ_ONLY},
        )
        assert resp.status_code == 403

    def test_access_profile_is_set_when_entitled(
        self, world, client, user_provider, live_tenants
    ):
        user = _seed_firm(world, mode=MODE_CO_BRANDED)
        _seed_relationship(world, profile=PROFILE_OFF)
        user_provider.set_user(user)
        resp = client.post(
            ACCESS_PROFILE_PATH.format(client_id=CLIENT_A),
            json={"profile": PROFILE_COLLABORATIVE},
        )
        assert resp.status_code == 200
        rel = asyncio.run(world.consultants.get_client(CLIENT_A))
        assert rel.client_access_profile == PROFILE_COLLABORATIVE

    def test_access_profile_unknown_value_is_rejected(
        self, world, client, user_provider, live_tenants
    ):
        user = _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_OFF)
        user_provider.set_user(user)
        resp = client.post(
            ACCESS_PROFILE_PATH.format(client_id=CLIENT_A),
            json={"profile": "readwrite-everything"},
        )
        assert resp.status_code == 422

    def test_foreign_client_target_is_denied(
        self, world, client, user_provider, live_tenants
    ):
        user = _seed_firm(world)
        world.consultants.seed_client(
            "client-other",
            "firm-2",
            ORG_B,
            "OTHER LTD",
            status="active",
            client_access_profile=PROFILE_READ_ONLY,
        )
        user_provider.set_user(user)
        resp = client.post(
            ACCESS_PROFILE_PATH.format(client_id="client-other"),
            json={"profile": PROFILE_COLLABORATIVE},
        )
        assert resp.status_code == 404

    def test_retention_only_applies_to_an_ended_relationship(
        self, world, client, user_provider, live_tenants
    ):
        user = _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY, status="active")
        user_provider.set_user(user)
        resp = client.post(
            RETENTION_PATH.format(client_id=CLIENT_A),
            json={"retained_read_only": True},
        )
        assert resp.status_code == 409

    def test_retention_can_be_applied_to_an_ended_relationship(
        self, world, client, user_provider, live_tenants
    ):
        """F-4 / PO-10 — non-destructive: the row is kept, only the flag changes."""
        user = _seed_firm(world)
        _seed_relationship(world, profile=PROFILE_READ_ONLY, status="ended")
        user_provider.set_user(user)
        resp = client.post(
            RETENTION_PATH.format(client_id=CLIENT_A),
            json={"retained_read_only": True},
        )
        assert resp.status_code == 200
        rel = asyncio.run(world.consultants.get_client(CLIENT_A))
        assert rel.status == "ended"  # structure/identity preserved
        assert rel.retained_read_only is True

    def test_mode_change_is_a_request_not_a_write(
        self, world, client, user_provider, live_tenants
    ):
        user = _seed_firm(world, mode=MODE_CO_BRANDED)
        user_provider.set_user(user)
        resp = client.post(
            MODE_REQUEST_PATH, json={"requested_mode": MODE_WHITE_LABEL}
        )
        assert resp.status_code == 201
        assert resp.json()["request"]["requested_mode"] == MODE_WHITE_LABEL
        # The firm's actual mode is unchanged — it is a REQUEST (PO-1).
        branding = asyncio.run(world.consultants.get_branding(FIRM_ID))
        assert branding.commercial_mode == MODE_CO_BRANDED

    def test_mode_change_rejects_unknown_and_no_op(
        self, world, client, user_provider, live_tenants
    ):
        user = _seed_firm(world, mode=MODE_CO_BRANDED)
        user_provider.set_user(user)
        assert (
            client.post(
                MODE_REQUEST_PATH, json={"requested_mode": "platinum"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                MODE_REQUEST_PATH, json={"requested_mode": MODE_CO_BRANDED}
            ).status_code
            == 422
        )
