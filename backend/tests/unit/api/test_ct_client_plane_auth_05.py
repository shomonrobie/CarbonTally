"""CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05 — the client-access CEILING on
the ORGANISATION plane.

Binding source:
``docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md`` §8.1/§8.2/§8.3 and
§16 ("a consultant-managed client [must not] inherit direct-customer assumptions
inside the authorization layer"); ``Research/CT-CONSULTANT-MODEL-UIUX-DESIGN-01``
§8 ("Plane C … is Plane B rendered for the client's own users, with …
profile-driven capabilities"); ``CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02`` §1.

A consultant-managed client's own user reaches the SAME organisation surface a
direct customer uses; the client ACCESS PROFILE is the SERVER-SIDE ceiling
(§8.3 P-6). Asserted here over the real routers/guards:

* ALLOW  — a COLLABORATIVE client may create facilities/assets/vehicles + upload;
* DENY   — MANAGED / READ_ONLY / OFF / RETAINED may not (the observed defect);
* REGRESSION — a DIRECT customer (no consultant relationship) is unaffected;
* IDENTITY   — a consultant principal and internal staff are never treated as a
  client user; a foreign organisation is not touched by the ceiling.
"""
from __future__ import annotations

import asyncio

import pytest

import auth
from api.client_access_guard import (
    CLIENT_OPERATION_DENIED_DETAIL,
    enforce_client_operation,
    resolve_client_ceiling,
)
from domain.relationship_access import (
    PROFILE_COLLABORATIVE,
    PROFILE_MANAGED,
    PROFILE_OFF,
    PROFILE_READ_ONLY,
    STATE_ACTIVE,
    STATE_RETAINED_READ_ONLY,
)
from tests.unit.api.fakes import (
    consultant_user,
    org_owner_user,
    staff_user,
)

ORG_A = "org-a"
ORG_B = "org-b"
FIRM_ID = "firm-1"
CLIENT_A = "client-a"
CONSULTANT_ID = "u-cons"

FACILITIES_A = f"/api/v3/organizations/{ORG_A}/facilities"
ASSETS_A = f"/api/v3/organizations/{ORG_A}/assets"
VEHICLES = "/api/v3/vehicles"
UPLOAD_URL = "/api/v3/documents/upload-url"
ME_CONTEXT = "/api/v3/me/context"


@pytest.fixture
def live_tenants(monkeypatch):
    monkeypatch.setattr(auth, "is_organization_active", lambda organization_id: True)
    monkeypatch.setattr(
        "api.dependencies.is_organization_active", lambda organization_id: True
    )


def _seed_relationship(
    world, *, profile=PROFILE_MANAGED, status="active", retained=False, org=ORG_A
):
    world.consultants.seed_profile(FIRM_ID, CONSULTANT_ID)
    world.consultants.seed_firm_member(FIRM_ID, CONSULTANT_ID, role="owner")
    return world.consultants.seed_client(
        CLIENT_A,
        FIRM_ID,
        org,
        "ACME LTD",
        status=status,
        client_access_profile=profile,
        retained_read_only=retained,
    )


def _owner(org=ORG_A, uid="client-owner"):
    return org_owner_user(org, uid, f"{uid}@client.test")


def _ceiling(user, world, org=ORG_A):
    return asyncio.run(resolve_client_ceiling(user, world.bundle(), org))


def _deny_message(response):
    """The custom error envelope carries the detail at ``error.message``."""
    return response.json()["error"]["message"]


# ---------------------------------------------------------------------------
# Ceiling resolution — who is a "client user" at all
# ---------------------------------------------------------------------------
class TestCeilingResolution:
    def test_direct_customer_has_no_ceiling(self, world):
        """An org with no consultant relationship is a DIRECT customer."""
        assert _ceiling(_owner(), world) is None

    def test_managed_client_resolves_the_ceiling(self, world):
        _seed_relationship(world, profile=PROFILE_MANAGED)
        ceiling = _ceiling(_owner(), world)
        assert ceiling is not None
        assert ceiling.profile == PROFILE_MANAGED
        assert ceiling.state == STATE_ACTIVE

    def test_collaborative_client_resolves_the_ceiling(self, world):
        _seed_relationship(world, profile=PROFILE_COLLABORATIVE)
        ceiling = _ceiling(_owner(), world)
        assert ceiling is not None and ceiling.profile == PROFILE_COLLABORATIVE

    def test_retained_client_resolves_read_only_state(self, world):
        _seed_relationship(
            world, profile=PROFILE_MANAGED, status="ended", retained=True
        )
        ceiling = _ceiling(_owner(), world)
        assert ceiling is not None and ceiling.state == STATE_RETAINED_READ_ONLY

    def test_pending_relationship_is_not_a_ceiling(self, world):
        """A non-active, non-retained relationship is a direct customer."""
        _seed_relationship(world, profile=PROFILE_MANAGED, status="pending")
        assert _ceiling(_owner(), world) is None

    def test_internal_staff_has_no_ceiling(self, world):
        _seed_relationship(world, profile=PROFILE_MANAGED)
        assert _ceiling(staff_user(user_id="u-staff"), world) is None

    def test_consultant_has_no_ceiling(self, world):
        """A consultant principal is never a client user (identity separation)."""
        _seed_relationship(world, profile=PROFILE_MANAGED)
        assert _ceiling(consultant_user(CONSULTANT_ID, "cons@x.test"), world) is None

    def test_foreign_organisation_is_not_touched_by_the_ceiling(self, world):
        """The ceiling only applies to the caller's OWN organisation."""
        _seed_relationship(world, profile=PROFILE_MANAGED, org=ORG_B)
        # The caller belongs to ORG_A; the relationship is on ORG_B.
        assert _ceiling(_owner(), world, org=ORG_B) is None
        assert _ceiling(_owner(), world, org=ORG_A) is None


# ---------------------------------------------------------------------------
# Organisation-plane writes — facilities / assets / vehicles
# ---------------------------------------------------------------------------
class TestMasterDataCeiling:
    def _post_facility(self, client):
        return client.post(FACILITIES_A, json={"name": "HQ", "postcode": "AB1 2CD"})

    @pytest.mark.parametrize(
        "profile",
        [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF],
    )
    def test_client_may_not_create_a_facility_unless_collaborative(
        self, client, world, user_provider, live_tenants, profile
    ):
        _seed_relationship(world, profile=profile)
        user_provider.set_user(_owner())
        response = self._post_facility(client)
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL

    def test_retained_client_may_not_create_a_facility(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(world, profile=PROFILE_MANAGED, status="ended", retained=True)
        user_provider.set_user(_owner())
        assert self._post_facility(client).status_code == 403

    def test_collaborative_client_may_create_a_facility(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(world, profile=PROFILE_COLLABORATIVE)
        user_provider.set_user(_owner())
        assert self._post_facility(client).status_code == 201

    def test_direct_customer_may_create_a_facility(
        self, client, world, user_provider, live_tenants
    ):
        """REGRESSION — no consultant relationship → the ceiling does not apply."""
        user_provider.set_user(_owner())
        assert self._post_facility(client).status_code == 201

    def test_managed_client_may_not_create_an_asset(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(world, profile=PROFILE_MANAGED)
        user_provider.set_user(_owner())
        response = client.post(ASSETS_A, json={"name": "Boiler", "facility_id": "f-1"})
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL

    def test_managed_client_may_not_create_a_vehicle(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(world, profile=PROFILE_MANAGED)
        user_provider.set_user(_owner())
        response = client.post(VEHICLES, json={"organization_id": ORG_A, "name": "Van"})
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL


# ---------------------------------------------------------------------------
# Organisation-plane uploads — the single upload gate
#
# END-TO-END ALLOW is not exercised here: an admitted upload actually issues a
# Supabase signed URL, which the DB-free harness cannot reach. The DENY path is
# asserted over the real route (the ceiling is evaluated BEFORE storage), and the
# ALLOW path is asserted directly against the same ceiling function the route
# calls.
# ---------------------------------------------------------------------------
class TestUploadCeiling:
    def _upload(self, client, org=ORG_A):
        return client.post(
            UPLOAD_URL,
            json={"organization_id": org, "filename": "a.pdf", "size_bytes": 10},
        )

    @pytest.mark.parametrize(
        "profile", [PROFILE_MANAGED, PROFILE_READ_ONLY, PROFILE_OFF]
    )
    def test_client_may_not_upload_unless_collaborative(
        self, client, world, user_provider, live_tenants, profile
    ):
        _seed_relationship(world, profile=profile)
        user_provider.set_user(_owner())
        response = self._upload(client)
        assert response.status_code == 403
        assert _deny_message(response) == CLIENT_OPERATION_DENIED_DETAIL

    def test_collaborative_client_passes_the_upload_ceiling(self, world):
        _seed_relationship(world, profile=PROFILE_COLLABORATIVE)
        # ALLOW — does not raise.
        asyncio.run(
            enforce_client_operation(
                _owner(), world.bundle(), ORG_A, "upload_document"
            )
        )

    def test_managed_client_is_denied_by_the_upload_ceiling(self, world):
        from fastapi import HTTPException

        _seed_relationship(world, profile=PROFILE_MANAGED)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(
                enforce_client_operation(
                    _owner(), world.bundle(), ORG_A, "upload_document"
                )
            )
        assert exc.value.status_code == 403
        assert exc.value.detail == CLIENT_OPERATION_DENIED_DETAIL

    def test_direct_customer_passes_the_upload_ceiling(self, world):
        """REGRESSION — a direct customer is unaffected by the ceiling."""
        asyncio.run(
            enforce_client_operation(
                _owner(), world.bundle(), ORG_A, "upload_document"
            )
        )



# ---------------------------------------------------------------------------
# Tenant isolation + identity separation + /me/context view
# ---------------------------------------------------------------------------
class TestIsolation:
    def test_client_cannot_write_a_foreign_organisation(
        self, client, world, user_provider, live_tenants
    ):
        """The ceiling ignores a foreign org; the existing tenant guard denies."""
        _seed_relationship(world, profile=PROFILE_COLLABORATIVE, org=ORG_A)
        user_provider.set_user(_owner())
        response = client.post(
            f"/api/v3/organizations/{ORG_B}/facilities",
            json={"name": "HQ", "postcode": "AB1 2CD"},
        )
        assert response.status_code in (403, 422)
        assert CLIENT_OPERATION_DENIED_DETAIL not in response.text

    def test_me_context_exposes_the_ceiling_for_a_managed_client(
        self, client, world, user_provider, live_tenants
    ):
        _seed_relationship(world, profile=PROFILE_MANAGED)
        user_provider.set_user(_owner())
        body = client.get(ME_CONTEXT).json()
        assert body["actor_type"] == "customer"
        assert body["client_access"]["profile"] == PROFILE_MANAGED
        assert body["client_access"]["state"] == STATE_ACTIVE
        assert body["client_access"]["capabilities"]["upload_document"] is False
        assert body["client_access"]["capabilities"]["edit_master_data"] is False
        assert body["client_access"]["capabilities"]["map_factors"] is False

    def test_me_context_has_no_client_access_for_a_direct_customer(
        self, client, world, user_provider, live_tenants
    ):
        user_provider.set_user(_owner())
        body = client.get(ME_CONTEXT).json()
        assert body["actor_type"] == "customer"
        assert body.get("client_access") is None



