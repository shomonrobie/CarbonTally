"""CT-CONSULTANT-CLIENT-IDENTITY-04 — client-user identity lifecycle.

Ratified design under test:

* **PD-1A** — a client Workspace user can only appear through a CarbonTally
  controlled, single-use invitation. Neither a consultant nor the client may
  bypass the invitation step and self-insert a client user.
* **PD-2A** — dual authority with explicit boundaries: WHILE the relationship is
  ACTIVE, the client Organisation owner/admin may administer their OWN
  organisation's users, and the consultant firm MAY create/manage those users on
  the client's behalf WITHIN the permitted client-role boundary — without the
  firm thereby gaining client DATA access.
* **White-label email (D19 §13 / D21)** — the invitation email presents the
  inviting party's brand and sends from the firm's own VERIFIED custom sender
  when one exists, otherwise the platform sender.

The route tests drive the REAL routers over the in-memory world
(``tests.unit.api.conftest``) so they assert the real HTTP decision plus the
resulting membership — an ALLOW is only evidence when the client user actually
appears in the authorised organisation (AGENTS.md §45/§74).
"""
from __future__ import annotations

import asyncio
import pathlib
from datetime import datetime, timedelta, timezone

import pytest

from auth import AuthUser
from domain import client_identity
from services.client_invitations import (
    describe_invitation,
    invitation_accept_url,
    render_invitation_email,
    resolve_invitation_sender,
)
from tests.unit.api.fakes import (
    InMemoryWorld,
    consultant_user,
    member_user,
    org_admin_user,
    org_owner_user,
)

ORG_A = "org-a"
ORG_B = "org-b"
FIRM_ID = "firm-c1"
CONSULTANT_ID = "u-c1"
INVITATIONS = "/api/v3/organizations/{org_id}/invitations"
ACCEPT = "/api/v3/organizations/invitations/accept"


def _invitee(user_id: str, email: str) -> AuthUser:
    """A brand-new authenticated identity that is not yet an org member."""
    return AuthUser(
        user_id=user_id,
        email=email,
        role="user",
        role_name="user",
        is_org_member=False,
        is_active=True,
    )


def _create(client, user_provider, org_id=ORG_A, *, email, role="member", admin="admin-a"):
    user_provider.set_user(org_admin_user(org_id, admin, f"{admin}@a.test"))
    return client.post(
        INVITATIONS.format(org_id=org_id), json={"email": email, "role": role}
    )


# ---------------------------------------------------------------------------
# PD-1A / PD-2A — pure policy (domain.client_identity)
# ---------------------------------------------------------------------------
class TestClientIdentityPolicy:
    def test_role_vocabulary_matches_the_membership_check(self):
        assert client_identity.CLIENT_ROLES == ("owner", "admin", "member", "viewer")
        assert client_identity.ASSIGNABLE_CLIENT_ROLES == client_identity.CLIENT_ROLES

    @pytest.mark.parametrize("role", ["owner", "admin", "member", "viewer", "ADMIN"])
    def test_valid_roles_normalise(self, role):
        assert client_identity.validate_client_role(role) in client_identity.CLIENT_ROLES

    def test_invalid_role_raises(self):
        with pytest.raises(client_identity.ClientIdentityError):
            client_identity.validate_client_role("ceo")

    def test_expired_is_derived_not_a_stored_state(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)
        assert client_identity.resolve_invitation_state("pending", past) == "expired"
        assert client_identity.resolve_invitation_state("pending", future) == "pending"
        # Terminal states are reported verbatim, never re-derived.
        assert client_identity.resolve_invitation_state("accepted", past) == "accepted"
        assert client_identity.resolve_invitation_state("revoked", past) == "revoked"
        assert "expired" not in (
            client_identity.INVITATION_PENDING,
            client_identity.INVITATION_ACCEPTED,
            client_identity.INVITATION_REVOKED,
        )

    def test_only_pending_and_unexpired_is_consumable(self):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)
        assert client_identity.invitation_is_consumable("pending", future)
        assert not client_identity.invitation_is_consumable("pending", past)
        assert not client_identity.invitation_is_consumable("accepted", future)

    def test_only_owner_and_admin_may_manage_client_users(self):
        assert client_identity.may_manage_client_users("owner")
        assert client_identity.may_manage_client_users("admin")
        assert not client_identity.may_manage_client_users("member")
        assert not client_identity.may_manage_client_users("viewer")
        assert client_identity.permitted_assignable_roles("member") == ()


# ---------------------------------------------------------------------------
# D19 §13 / D21 — invitation email + white-label sender
# ---------------------------------------------------------------------------
class TestInvitationEmail:
    def test_accept_url_carries_the_single_use_token(self):
        assert invitation_accept_url("tok-123").endswith("token=tok-123")

    def test_render_uses_the_inviting_brand_and_role(self):
        subject, html = render_invitation_email(
            brand_name="Acme Advisory",
            organization_name="Org A",
            role="admin",
            accept_url="https://carbontally.co.uk/accept-invitation?token=t",
        )
        assert "Org A" in subject
        assert "Acme Advisory" in html
        assert "administrator" in html

    def test_unverified_sender_is_never_used(self):
        world = InMemoryWorld()
        asyncio.run(
            world.whitelabel.create_sender(
                consultant_id=FIRM_ID, email="noreply@acme.test"
            )
        )
        assert asyncio.run(resolve_invitation_sender(world, FIRM_ID)) is None

    def test_verified_sender_is_used(self):
        world = InMemoryWorld()
        sender = asyncio.run(
            world.whitelabel.create_sender(
                consultant_id=FIRM_ID, email="noreply@acme.test"
            )
        )
        asyncio.run(world.whitelabel.verify_sender(sender.id, FIRM_ID))
        assert (
            asyncio.run(resolve_invitation_sender(world, FIRM_ID))
            == "noreply@acme.test"
        )

    def test_no_firm_means_no_custom_sender(self):
        world = InMemoryWorld()
        assert asyncio.run(resolve_invitation_sender(world, None)) is None

    def test_describe_invitation_exposes_derived_state(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        view = describe_invitation(
            {"status": "pending", "expires_at": past, "token": "t"}
        )
        assert view["state"] == "expired"
        assert "accept_url" not in view  # only when explicitly requested
        view = describe_invitation(
            {"status": "pending", "expires_at": past, "token": "t"},
            include_accept_url=True,
        )
        assert view["accept_url"].endswith("token=t")


# ---------------------------------------------------------------------------
# Organisation plane — create / list / revoke / accept (PD-1A, PD-2A)
# ---------------------------------------------------------------------------
class TestOrganisationInvitationLifecycle:
    def test_create_persists_the_requested_role(self, client, world, user_provider):
        """The role the inviter chose is persisted (it drives acceptance)."""
        response = _create(client, user_provider, email="New@Example.Test", role="admin")
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "new@example.test"
        assert body["role"] == "admin"
        assert body["state"] == "pending"
        assert body["token"]
        assert body["accept_url"].endswith(f"token={body['token']}")
        assert isinstance(body["email_delivered"], bool)

    def test_create_rejects_unknown_role(self, client, user_provider):
        response = _create(client, user_provider, email="x@example.test", role="ceo")
        assert response.status_code == 422

    def test_create_requires_admin(self, client, user_provider):
        user_provider.set_user(member_user(ORG_A, "user-a", "user.a@test"))
        response = client.post(
            INVITATIONS.format(org_id=ORG_A),
            json={"email": "x@example.test", "role": "member"},
        )
        assert response.status_code == 403

    def test_list_reports_derived_state(self, client, world, user_provider):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        asyncio.run(
            world.invitations.create(
                org_id=ORG_A,
                email="expired@example.test",
                token="tok-expired",
                status="pending",
                expires_at=past,
            )
        )
        _create(client, user_provider, email="pending@example.test")
        user_provider.set_user(org_admin_user(ORG_A, "admin-a", "admin.a@test"))
        response = client.get(INVITATIONS.format(org_id=ORG_A))
        assert response.status_code == 200
        states = {i["email"]: i["state"] for i in response.json()["invitations"]}
        assert states["expired@example.test"] == "expired"
        assert states["pending@example.test"] == "pending"

    def test_accept_creates_the_membership_with_the_invited_role(
        self, client, world, user_provider
    ):
        created = _create(
            client, user_provider, email="invitee@example.test", role="viewer"
        ).json()

        user_provider.set_user(_invitee("u-invitee", "invitee@example.test"))
        response = client.post(ACCEPT, json={"token": created["token"]})
        assert response.status_code == 200
        body = response.json()
        assert body["organization_id"] == ORG_A
        assert body["role"] == "viewer"
        assert body["status"] == "accepted"

        # The client user now really exists in the authorised organisation.
        user_provider.set_user(org_admin_user(ORG_A, "admin-a", "admin.a@test"))
        members = client.get(f"/api/v3/organizations/{ORG_A}/members").json()["members"]
        entry = next(m for m in members if m.get("user_id") == "u-invitee")
        assert entry["role"] == "viewer"

    def test_accept_is_single_use(self, client, world, user_provider):
        created = _create(client, user_provider, email="invitee@example.test").json()
        user_provider.set_user(_invitee("u-invitee", "invitee@example.test"))
        assert client.post(ACCEPT, json={"token": created["token"]}).status_code == 200
        second = client.post(ACCEPT, json={"token": created["token"]})
        assert second.status_code == 409

    def test_accept_denies_a_different_email(self, client, world, user_provider):
        created = _create(client, user_provider, email="invitee@example.test").json()
        user_provider.set_user(_invitee("u-other", "attacker@example.test"))
        assert client.post(ACCEPT, json={"token": created["token"]}).status_code == 403

    def test_accept_denies_expired_invitation(self, client, world, user_provider):
        past = datetime.now(timezone.utc) - timedelta(days=1)
        asyncio.run(
            world.invitations.create(
                org_id=ORG_A,
                email="invitee@example.test",
                token="tok-expired",
                status="pending",
                expires_at=past,
                role="member",
            )
        )
        user_provider.set_user(_invitee("u-invitee", "invitee@example.test"))
        assert client.post(ACCEPT, json={"token": "tok-expired"}).status_code == 410

    def test_accept_denies_revoked_invitation(self, client, world, user_provider):
        created = _create(client, user_provider, email="invitee@example.test").json()
        user_provider.set_user(org_admin_user(ORG_A, "admin-a", "admin.a@test"))
        client.delete(f"/api/v3/organizations/invitations/{created['id']}")
        user_provider.set_user(_invitee("u-invitee", "invitee@example.test"))
        assert client.post(ACCEPT, json={"token": created["token"]}).status_code == 409

    def test_accept_unknown_token_is_404(self, client, user_provider):
        user_provider.set_user(_invitee("u-invitee", "invitee@example.test"))
        assert client.post(ACCEPT, json={"token": "nope"}).status_code == 404

    def test_accept_requires_authentication(self, client, world, user_provider):
        created = _create(client, user_provider, email="invitee@example.test").json()
        user_provider.set_unauthenticated()
        assert client.post(ACCEPT, json={"token": created["token"]}).status_code == 401

    def test_revoke_requires_admin(self, client, world, user_provider):
        created = _create(client, user_provider, email="invitee@example.test").json()
        user_provider.set_user(member_user(ORG_A, "user-a", "user.a@test"))
        assert (
            client.delete(
                f"/api/v3/organizations/invitations/{created['id']}"
            ).status_code
            == 403
        )


class TestClientRoleAdministration:
    """PD-2A — the organisation owner/admin administer their OWN users."""

    def test_role_change_is_org_scoped(self, client, world, user_provider):
        world.organizations.add_member_record(
            {
                "id": "member-b",
                "organization_id": ORG_B,
                "user_id": "u-b",
                "role": "member",
                "is_active": True,
            }
        )
        user_provider.set_user(org_admin_user(ORG_A, "admin-a", "admin.a@test"))
        response = client.put(
            "/api/v3/organizations/members/member-b", json={"role": "viewer"}
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Consultant plane — invite / list / revoke client users + role admin (PD-2A)
# ---------------------------------------------------------------------------
@pytest.fixture
def live_tenants(monkeypatch):
    """Pin the D-7 tenant-liveness predicate to 'all tenants are live'."""
    import auth

    monkeypatch.setattr(auth, "is_organization_active", lambda organization_id: True)
    monkeypatch.setattr(
        "api.dependencies.is_organization_active", lambda organization_id: True
    )


def _seed_consultant(
    world, *, user_id=CONSULTANT_ID, firm_id=FIRM_ID, can_manage_clients=True,
    grant_status="active", org_id=ORG_A, client_id="cc-a",
):
    world.consultants.seed_profile(firm_id, user_id, "C1 Advisory", is_active=True)
    world.consultants.seed_firm_member(
        firm_id,
        user_id,
        role="owner",
        can_manage_clients=can_manage_clients,
        can_view_client=True,
    )
    world.consultants.seed_client(
        client_id, firm_id, org_id, f"Client {org_id}", status=grant_status
    )
    return consultant_user(user_id, f"{user_id}@example.test")


class TestConsultantClientInvitations:
    """PD-1A / PD-2A — the firm invites/manages client users within boundary."""

    def test_consultant_creates_a_single_use_client_invitation(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_consultant(world))
        response = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "Client.User@Example.Test", "role": "admin"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["email"] == "client.user@example.test"
        assert body["role"] == "admin"
        assert body["state"] == "pending"
        assert body["invited_by_firm_id"] == FIRM_ID
        # PD-1A: the consultant never receives the invitation TOKEN — the
        # invitee receives it by email; possession alone would be insufficient
        # anyway (acceptance is bound to the invited email).
        assert "token" not in body
        assert "accept_url" not in body

        # The invitation is durable and carries the firm provenance + role, but
        # the invitee is NOT yet a member — PD-1A forbids self-insertion.
        rows = asyncio.run(world.invitations.list_for_org(ORG_A))
        assert rows[0]["invited_by_firm_id"] == FIRM_ID
        assert rows[0]["role"] == "admin"
        assert rows[0]["token"]  # the durable single-use token exists server-side
        members = asyncio.run(world.organizations.list_members_with_email(ORG_A))
        assert members == []

    def test_consultant_list_shows_the_invitation(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_consultant(world))
        client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "client.user@example.test", "role": "member"},
        )
        response = client.get("/api/v3/consultants/clients/cc-a/invitations")
        assert response.status_code == 200
        emails = [i["email"] for i in response.json()["invitations"]]
        assert "client.user@example.test" in emails

    def test_consultant_revoke_sets_revoked_state(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_consultant(world))
        created = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "client.user@example.test", "role": "member"},
        ).json()
        path = f"/api/v3/consultants/clients/cc-a/invitations/{created['id']}/revoke"
        assert client.post(path).status_code == 204
        listed = client.get("/api/v3/consultants/clients/cc-a/invitations").json()
        assert listed["invitations"][0]["state"] == "revoked"

    def test_consultant_without_manage_clients_is_denied(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_consultant(world, can_manage_clients=False))
        response = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "client.user@example.test", "role": "member"},
        )
        assert response.status_code == 403

    def test_client_user_is_denied_on_the_consultant_endpoint(
        self, world, client, user_provider, live_tenants
    ):
        """CT-CONSULTANT-CLIENT-ACCESS-UX-01 §15 — a CLIENT organisation member is
        not a consultant: the consultant-plane endpoint must deny (no tenant hop
        from the client's own membership)."""
        user_provider.set_user(member_user(ORG_A, "u-client", "client@a.test"))
        response = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "someone@example.test", "role": "member"},
        )
        assert response.status_code == 403

    def test_unauthenticated_is_rejected_on_the_consultant_endpoint(
        self, world, client, user_provider, live_tenants
    ):
        """CT-CONSULTANT-CLIENT-ACCESS-UX-01 §15 — unauthenticated → 401."""
        user_provider.set_unauthenticated()
        response = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "someone@example.test", "role": "member"},
        )
        assert response.status_code == 401


    def test_inactive_grant_denies_consultant_invitation(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_consultant(world, grant_status="ended"))
        response = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "client.user@example.test", "role": "member"},
        )
        assert response.status_code == 403

    def test_consultant_cannot_touch_another_firms_client(
        self, world, client, user_provider, live_tenants
    ):
        _seed_consultant(world)  # firm-c1 owns cc-a
        user_provider.set_user(
            _seed_consultant(
                world, user_id="u-c2", firm_id="firm-c2", org_id=ORG_B, client_id="cc-b"
            )
        )
        response = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "client.user@example.test", "role": "member"},
        )
        assert response.status_code == 403

    def test_consultant_invalid_role_is_rejected(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_consultant(world))
        response = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "client.user@example.test", "role": "ceo"},
        )
        assert response.status_code == 422

    def test_consultant_assigns_a_client_user_role(
        self, world, client, user_provider, live_tenants
    ):
        world.organizations.add_member_record(
            {
                "id": "member-1",
                "organization_id": ORG_A,
                "user_id": "u-client",
                "role": "member",
                "is_active": True,
            }
        )
        world.tenant.seed_member(
            {
                "id": "member-1",
                "organization_id": ORG_A,
                "user_id": "u-client",
                "role": "member",
                "is_active": True,
            }
        )
        user_provider.set_user(_seed_consultant(world))
        response = client.patch(
            "/api/v3/consultants/clients/cc-a/users/member-1", json={"role": "viewer"}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "viewer"

    def test_consultant_cannot_role_change_a_member_outside_the_client(
        self, world, client, user_provider, live_tenants
    ):
        world.organizations.add_member_record(
            {
                "id": "member-b",
                "organization_id": ORG_B,
                "user_id": "u-b",
                "role": "member",
                "is_active": True,
            }
        )
        user_provider.set_user(_seed_consultant(world))
        response = client.patch(
            "/api/v3/consultants/clients/cc-a/users/member-b", json={"role": "viewer"}
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PD-1A — invitation token security (closure verification of the CT04 contract)
#
# The CT04 contract states the CONSULTANT never receives the invitation token.
# These tests lock that invariant to the exact HTTP response bodies plus the
# two properties that make token possession insufficient on its own (email
# binding and single-use consumption).
# ---------------------------------------------------------------------------
class TestInvitationTokenSecurity:
    """The consultant never receives the raw bearer token (PD-1A)."""

    def test_consultant_list_never_exposes_token_or_accept_url(
        self, world, client, user_provider, live_tenants
    ):
        user_provider.set_user(_seed_consultant(world))
        client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "client.user@example.test", "role": "member"},
        )
        listed = client.get("/api/v3/consultants/clients/cc-a/invitations").json()
        assert listed["invitations"], "the firm must see its own invitations"
        for row in listed["invitations"]:
            assert "token" not in row
            assert "accept_url" not in row

    def test_org_admin_may_see_the_accept_link_but_only_for_their_org(
        self, client, world, user_provider
    ):
        """The inviting AUTHORITY (client owner/admin) may issue the link.

        The asymmetry is deliberate: the client owner/admin is the party that
        invites, so it may hand the invitee a link; the consultant plane — which
        acts on the client's behalf — never receives the bearer token.
        """
        created = _create(client, user_provider, email="invitee@example.test").json()
        assert "accept_url" in created and "token=" in created["accept_url"]
        assert "token" in created  # the org plane's own response (admin-gated)
        listed = client.get(INVITATIONS.format(org_id=ORG_A)).json()["invitations"]
        assert listed and "accept_url" in listed[0]

    def test_ordinary_member_cannot_see_the_accept_link(self, client, user_provider):
        user_provider.set_user(member_user(ORG_A, "user-a", "user.a@test"))
        assert (
            client.get(INVITATIONS.format(org_id=ORG_A)).status_code == 403
        )

    def test_consultant_cannot_accept_even_holding_the_raw_token(
        self, world, client, user_provider, live_tenants
    ):
        """Possession of the token is not authority — acceptance is email-bound."""
        user_provider.set_user(_seed_consultant(world))
        created = client.post(
            "/api/v3/consultants/clients/cc-a/invitations",
            json={"email": "client.user@example.test", "role": "member"},
        ).json()
        assert "token" not in created  # the consultant response is redacted

        # The durable token exists server-side only; even if the consultant
        # obtained it out-of-band, the consultant's identity is not the invitee.
        token = asyncio.run(world.invitations.list_for_org(ORG_A))[0]["token"]
        response = client.post(ACCEPT, json={"token": token})
        assert response.status_code == 403
        assert asyncio.run(world.organizations.list_members_with_email(ORG_A)) == []

    def test_consume_sql_is_a_single_use_conditional_update(self):
        """The single-use guarantee must be the atomic UPDATE, not read-then-write."""
        source = (
            pathlib.Path(__file__).resolve().parents[3] / "data" / "invitations.py"
        ).read_text()
        sql = source[source.index("async def consume") : source.index("async def revoke")]
        assert "UPDATE public.user_invitations" in sql
        assert "status = 'pending'" in sql
        assert "expires_at IS NULL OR expires_at > NOW()" in sql
        # No SELECT before the UPDATE → no read-then-write race to lose.
        assert "SELECT" not in sql

    def test_concurrent_acceptance_yields_exactly_one_winner(self, world):
        """Two simultaneous consumers → at most one accepted invitation.

        The fake mirrors the repository's conditional UPDATE; the real
        single-use atomicity is asserted above at the SQL level.
        """
        asyncio.run(
            world.invitations.create(
                org_id=ORG_A,
                email="invitee@example.test",
                token="tok-concurrent",
                status="pending",
                role="member",
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
        )

        async def race():
            return await asyncio.gather(
                world.invitations.consume("tok-concurrent", accepted_by="u-1"),
                world.invitations.consume("tok-concurrent", accepted_by="u-2"),
            )

        results = asyncio.run(race())
        assert len([r for r in results if r is not None]) == 1


class TestClientRoleAdministrationBoundaries:
    """PD-2A — client owner/admin authority is bounded to client roles only."""

    @staticmethod
    def _seed_client_member(world):
        row = {
            "id": "member-1",
            "organization_id": ORG_A,
            "user_id": "u-client",
            "role": "member",
            "is_active": True,
        }
        world.organizations.add_member_record(dict(row))
        world.tenant.seed_member(dict(row))

    def test_owner_may_change_a_member_role(self, client, world, user_provider):
        self._seed_client_member(world)
        user_provider.set_user(org_owner_user(ORG_A, "owner-a", "owner.a@test"))
        response = client.put(
            "/api/v3/organizations/members/member-1", json={"role": "admin"}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    def test_ordinary_member_cannot_change_a_role(self, client, world, user_provider):
        self._seed_client_member(world)
        user_provider.set_user(member_user(ORG_A, "user-a", "user.a@test"))
        response = client.put(
            "/api/v3/organizations/members/member-1", json={"role": "admin"}
        )
        assert response.status_code == 403

    @pytest.mark.parametrize("role", ["consultant", "super_admin", "staff", "ceo"])
    def test_client_role_cannot_be_escalated_beyond_the_client_model(
        self, client, world, user_provider, role
    ):
        """A client membership can never be granted a consultant/staff role."""
        self._seed_client_member(world)
        user_provider.set_user(org_admin_user(ORG_A, "admin-a", "admin.a@test"))
        response = client.put(
            "/api/v3/organizations/members/member-1", json={"role": role}
        )
        assert response.status_code == 422
