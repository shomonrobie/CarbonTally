"""CT-FINAL-01 — notifications: actor vs platform email sender.

Ratified scope: the notification From address is **platform configuration**
(admin-configurable, defaulting to ``CarbonTally <notifications@carbontally.co.uk>``),
never the acting user's mailbox; the app must preserve the actor and the
"acting for" context; and no provider secret may be exposed by the settings
surface.

Covers:

* the sender-primitive contract (validation, fail-closed resolution, identity);
* the admin-only settings API (``/api/v3/settings/notification-sender``) —
  ALLOW for an admin, DENY for a non-admin/unauthenticated caller, 422 for an
  invalid or non-platform address, and no secret in any response body;
* the single source of truth for the default sender (``services.email_sender``).
"""
from __future__ import annotations

import pytest

from services.email_sender import (
    DEFAULT_SENDER,
    PLATFORM_EMAIL_DOMAINS,
    describe_email_sender,
    normalise_email_sender,
    notification_identity,
    resolve_email_sender,
)

_FAKE_SECRET = "re_ct_final_01_secret_value"


# ---------------------------------------------------------------------------
# sender primitive contract
# ---------------------------------------------------------------------------


def test_default_sender_is_the_approved_carbontally_address() -> None:
    assert DEFAULT_SENDER == "CarbonTally <notifications@carbontally.co.uk>"
    assert PLATFORM_EMAIL_DOMAINS == frozenset({"carbontally.co.uk"})


def test_default_sender_is_a_single_source_of_truth() -> None:
    """``services.v3_email`` must not carry a second, divergent default."""
    from services import v3_email

    assert v3_email.DEFAULT_FROM_EMAIL == DEFAULT_SENDER


def test_normalise_accepts_bare_and_display_forms() -> None:
    assert (
        normalise_email_sender("notifications@carbontally.co.uk")
        == "notifications@carbontally.co.uk"
    )
    assert (
        normalise_email_sender("CarbonTally <no-reply@carbontally.co.uk>")
        == "CarbonTally <no-reply@carbontally.co.uk>"
    )
    assert (
        normalise_email_sender("  Billing <billing@CARBONTALLY.CO.UK>  ")
        == "Billing <billing@CARBONTALLY.CO.UK>"
    )


def test_normalise_treats_empty_as_unset() -> None:
    assert normalise_email_sender(None) is None
    assert normalise_email_sender("   ") is None


@pytest.mark.parametrize(
    "value",
    [
        "attacker@evil.example",
        "CarbonTally <x@evil.example>",
        "not-an-address",
        "a@b",
        "one@carbontally.co.uk, two@carbontally.co.uk",  # multi-address
        "notifications@carbontally.co.uk\nBcc: attacker@evil.example",  # injection
        'Quoted "Name" <notifications@carbontally.co.uk>',
        "CarbonTally: ops <notifications@carbontally.co.uk>",
    ],
)
def test_normalise_rejects_unusable_or_non_platform_senders(value: str) -> None:
    with pytest.raises(ValueError):
        normalise_email_sender(value)


def test_resolution_fails_closed_to_the_approved_default() -> None:
    assert resolve_email_sender(None) == DEFAULT_SENDER
    assert resolve_email_sender("") == DEFAULT_SENDER
    # An invalid/malicious stored value can never become the effective sender.
    assert resolve_email_sender("attacker@evil.example") == DEFAULT_SENDER
    assert (
        resolve_email_sender("Billing <billing@carbontally.co.uk>")
        == "Billing <billing@carbontally.co.uk>"
    )


def test_describe_reports_configuration_without_exposing_a_secret(
    monkeypatch,
) -> None:
    monkeypatch.setenv("RESEND_API_KEY", _FAKE_SECRET)
    described = describe_email_sender(None)
    assert described["email_sender"] == DEFAULT_SENDER
    assert described["is_default"] is True
    assert described["configured"] is False
    assert described["platform_domains"] == ["carbontally.co.uk"]
    assert _FAKE_SECRET not in repr(described)


def test_identity_preserves_actor_and_acting_for_but_not_as_sender() -> None:
    identity = notification_identity(
        actor_email="consultant@partner.example",
        acting_for="Acme Ltd",
    )
    assert identity["actor"] == "consultant@partner.example"
    assert identity["acting_for"] == "Acme Ltd"
    assert identity["sender"] == DEFAULT_SENDER
    assert identity["sender"] != identity["actor"]


def test_identity_uses_the_configured_platform_sender() -> None:
    identity = notification_identity(
        actor_email="ops@carbontally.co.uk",
        acting_for=None,
        configured_sender="Billing <billing@carbontally.co.uk>",
    )
    assert identity["sender"] == "Billing <billing@carbontally.co.uk>"
    assert identity["acting_for"] is None



# ---------------------------------------------------------------------------
# admin-only settings API (ALLOW + DENY + validation + no secret exposure)
# ---------------------------------------------------------------------------


def _route_dependencies(router, path_fragment: str) -> list:
    found: list = []
    for route in getattr(router, "routes", []):
        path = getattr(route, "path", None)
        original = getattr(route, "original_router", None)
        if path and path_fragment in path:
            dependant = getattr(route, "dependant", None)
            if dependant is not None:
                methods = sorted(getattr(route, "methods", []) or [])
                for dep in dependant.dependencies:
                    found.append((methods, dep.call))
        if original is not None:
            found.extend(_route_dependencies(original, path_fragment))
    return found


def test_notification_sender_routes_are_registered() -> None:
    from api.router import router as v3_router
    from tests.unit.api.route_paths import flatten_router_paths

    paths = flatten_router_paths(v3_router)
    assert any("/api/v3/settings/notification-sender" in path for path in paths)


def test_notification_sender_routes_require_admin() -> None:
    """Guarded by ``require_admin()`` — and the parentheses really are there."""
    from api.v3_settings import router as settings_router

    names: set[str] = set()
    for _methods, call in _route_dependencies(
        settings_router, "/api/v3/settings/notification-sender"
    ):
        names.add(getattr(call, "__name__", ""))
    assert "admin_checker" in names, (
        "require_admin() must be applied with parentheses (CT-FINAL-01 F-05-R1 hazard)"
    )


def test_notification_sender_get_defaults_without_exposing_a_secret(
    client, world, user_provider, monkeypatch
) -> None:
    from tests.unit.api.fakes import staff_user

    monkeypatch.setenv("RESEND_API_KEY", _FAKE_SECRET)
    user_provider.set_user(
        staff_user("u-admin", email="admin@example.test", role_name="admin")
    )
    response = client.get("/api/v3/settings/notification-sender")
    assert response.status_code == 200
    settings = response.json()["settings"]
    assert settings["email_sender"] == DEFAULT_SENDER
    assert settings["is_default"] is True
    assert settings["default_sender"] == DEFAULT_SENDER
    # The delivery credential is never part of the configuration response.
    assert _FAKE_SECRET not in response.text



def test_notification_sender_put_round_trips(client, world, user_provider) -> None:
    from tests.unit.api.fakes import staff_user

    user_provider.set_user(
        staff_user("u-admin", email="admin@example.test", role_name="admin")
    )
    put = client.put(
        "/api/v3/settings/notification-sender",
        json={"email_sender": "Billing <billing@carbontally.co.uk>"},
    )
    assert put.status_code == 200
    assert put.json()["settings"]["email_sender"] == "Billing <billing@carbontally.co.uk>"
    assert put.json()["settings"]["is_default"] is False

    get = client.get("/api/v3/settings/notification-sender")
    assert get.status_code == 200
    assert get.json()["settings"]["email_sender"] == "Billing <billing@carbontally.co.uk>"


def test_notification_sender_put_rejects_non_platform_address(
    client, world, user_provider
) -> None:
    """A customer/consultant domain needs an externally verified sender (D19 §13)."""
    from tests.unit.api.fakes import staff_user

    user_provider.set_user(
        staff_user("u-admin", email="admin@example.test", role_name="admin")
    )
    response = client.put(
        "/api/v3/settings/notification-sender",
        json={"email_sender": "attacker@evil.example"},
    )
    assert response.status_code == 422
    # A rejected value is never stored: the default is still in force.
    assert (
        client.get("/api/v3/settings/notification-sender").json()["settings"][
            "email_sender"
        ]
        == DEFAULT_SENDER
    )


def test_notification_sender_put_clears_back_to_the_default(
    client, world, user_provider
) -> None:
    from tests.unit.api.fakes import staff_user

    user_provider.set_user(
        staff_user("u-admin", email="admin@example.test", role_name="admin")
    )
    client.put(
        "/api/v3/settings/notification-sender",
        json={"email_sender": "Billing <billing@carbontally.co.uk>"},
    )
    cleared = client.put(
        "/api/v3/settings/notification-sender", json={"email_sender": None}
    )
    assert cleared.status_code == 200
    assert cleared.json()["settings"]["email_sender"] == DEFAULT_SENDER
    assert cleared.json()["settings"]["is_default"] is True


def test_notification_sender_read_denied_for_non_admin(client, world, user_provider) -> None:
    """DENY: an ordinary authenticated member must not read platform settings."""
    from tests.unit.api.fakes import member_user

    user_provider.set_user(member_user("org-a", "u-member", "member@example.test"))
    assert client.get("/api/v3/settings/notification-sender").status_code in (401, 403)


def test_notification_sender_write_denied_for_non_admin(client, world, user_provider) -> None:
    """DENY: an ordinary authenticated member must not change the platform sender."""
    from tests.unit.api.fakes import member_user

    user_provider.set_user(member_user("org-a", "u-member", "member@example.test"))
    response = client.put(
        "/api/v3/settings/notification-sender",
        json={"email_sender": "Billing <billing@carbontally.co.uk>"},
    )
    assert response.status_code in (401, 403)


def test_notification_sender_read_denied_when_unauthenticated(client, user_provider) -> None:
    user_provider.set_unauthenticated()
    assert client.get("/api/v3/settings/notification-sender").status_code == 401
