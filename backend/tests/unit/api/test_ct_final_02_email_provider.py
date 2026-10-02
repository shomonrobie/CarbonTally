"""CT-FINAL-02 — email delivery provider/sender configuration (EMAIL-CONFIG-01).

Ratified scope: delivery provider (Resend | SMTP) and the From sender are
**administrator-configurable** and applied end-to-end through one canonical
mailer.  Two invariants are asserted here, ALLOW and DENY:

* no credential is ever persisted, returned by the API, or logged — the stored
  row holds only the provider selection and the *name* of an allow-listed
  environment variable; the credential value is read from the environment at
  delivery time;
* delivery fails closed.  A provider that is not configured reports
  ``delivered=False`` with a reason, is never silently re-routed to another
  provider, and no caller may report a fabricated success.

Covers the provider abstraction, the canonical mailer (``services.v3_email``),
the admin API (``/api/v3/settings/email-provider`` — GET / POST validate / PUT
with admin authorization) and the legacy call sites (``utils.email``,
``routes.notifications``, ``services.email_service``).
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from services.email_provider import (
    ALLOWED_CREDENTIAL_ENVS,
    DEFAULT_CREDENTIAL_ENV,
    DEFAULT_PROVIDER,
    SUPPORTED_PROVIDERS,
    configured_provider_name,
    credential_value,
    deliver_email_sync,
    describe_provider_config,
    normalise_provider_config,
    provider_readiness,
    resolve_credential_env,
    resolve_provider_config,
)

SETTINGS_PATH = "/api/v3/settings/email-provider"
VALIDATE_PATH = "/api/v3/settings/email-provider/validate"
SENDER_PATH = "/api/v3/settings/notification-sender"
BACKEND = Path(__file__).resolve().parents[3]

#: Sentinel credential values used to prove a credential never crosses a
#: response boundary.  They are set in ``monkeypatch`` only.
RESEND_SECRET = "re_final02_should_never_appear"
SMTP_SECRET = "smtp-final02-should-never-appear"


@pytest.fixture
def clean_email_env(monkeypatch):
    """No provider credential is configured unless a test sets one."""
    for key in sorted(ALLOWED_CREDENTIAL_ENVS):
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


class _FakeSettings:
    """Stand-in ``SettingsRepository`` for the non-request delivery path."""

    def __init__(self, **provider):
        self._provider = provider
        self.sender = None

    async def get_email_provider(self) -> dict:
        return dict(self._provider)

    async def get_notification_sender(self) -> dict:
        return {"email_sender": self.sender, "updated_at": None, "updated_by": None}


class _BrokenSettings:
    async def get_email_provider(self) -> dict:
        raise RuntimeError("settings unavailable")



# ---------------------------------------------------------------------------
# provider abstraction — configuration contract
# ---------------------------------------------------------------------------


def test_supported_providers_are_implemented_end_to_end() -> None:
    assert SUPPORTED_PROVIDERS == ("resend", "smtp")
    assert DEFAULT_PROVIDER == "resend"
    assert DEFAULT_CREDENTIAL_ENV == {
        "resend": "RESEND_API_KEY",
        "smtp": "CT_SMTP_PASSWORD",
    }
    assert ALLOWED_CREDENTIAL_ENVS == frozenset(
        {"RESEND_API_KEY", "CT_SMTP_PASSWORD", "SMTP_PASSWORD"}
    )


def test_only_allow_listed_credential_variables_are_readable(clean_email_env) -> None:
    """An arbitrary variable name must never be readable through the adapter."""
    clean_email_env.setenv("RESEND_API_KEY", RESEND_SECRET)
    clean_email_env.setenv("AWS_SECRET_ACCESS_KEY", "aws-should-never-be-read")

    assert credential_value("RESEND_API_KEY") == RESEND_SECRET
    assert credential_value("AWS_SECRET_ACCESS_KEY") is None
    assert credential_value("DATABASE_URL") is None
    assert credential_value("") is None


@pytest.mark.parametrize(
    "raw",
    [
        {"provider": "resend"},
        {"provider": "RESEND"},
        {"provider": "smtp", "smtp_host": "mail.example.com"},
        {"provider": "smtp", "smtp_host": "mail.example.com", "smtp_port": 465},
        {"provider": "smtp", "smtp_host": "smtp.eu.mailgun.org", "smtp_use_tls": False},
        {"provider": "resend", "credential_env": "RESEND_API_KEY"},
        {
            "provider": "smtp",
            "smtp_host": "mail.example.com",
            "credential_env": "SMTP_PASSWORD",
        },
    ],
)
def test_valid_configurations_are_accepted(raw) -> None:
    config = normalise_provider_config(raw)
    assert config["provider"] in SUPPORTED_PROVIDERS
    assert config["credential_env"] in ALLOWED_CREDENTIAL_ENVS


@pytest.mark.parametrize(
    "raw",
    [
        {"provider": "sendgrid"},
        {
            "provider": None,
            "smtp_host": "mail.example.com",
            "credential_env": "WEIRD_VAR",
        },
        {"provider": "smtp"},
        {"provider": "smtp", "smtp_host": "https://mail.example.com"},
        {"provider": "smtp", "smtp_host": "mail.example.com:587"},
        {"provider": "smtp", "smtp_host": "mail.example.com", "smtp_port": 0},
        {"provider": "smtp", "smtp_host": "mail.example.com", "smtp_port": 70000},
        {"provider": "smtp", "smtp_host": "mail.example.com", "smtp_port": "abc"},
        {"provider": "resend", "smtp_use_tls": "yes"},
        {
            "provider": "smtp",
            "smtp_host": "mail.example.com",
            "credential_env": "AWS_SECRET_ACCESS_KEY",
        },
        {
            "provider": "smtp",
            "smtp_host": "mail.example.com",
            "credential_env": "not a var",
        },
    ],
)
def test_invalid_configurations_are_refused(raw) -> None:
    with pytest.raises(ValueError):
        normalise_provider_config(raw)


@pytest.mark.parametrize(
    "field",
    ["api_key", "apiKey", "API_KEY", "password", "smtp_password", "secret", "credential"],
)
def test_a_credential_submitted_as_a_setting_is_refused(field) -> None:
    with pytest.raises(ValueError):
        normalise_provider_config({"provider": "resend", field: "super-secret"})


def test_invalid_stored_configuration_fails_closed_to_the_default() -> None:
    for broken in ({"provider": "nope"}, {"provider": 42}, {"provider": "sendgrid"}):
        assert configured_provider_name(broken) == "resend"
        assert resolve_credential_env(broken) in ALLOWED_CREDENTIAL_ENVS
    # An unreadable row is reported as the default provider, never as "none".
    assert configured_provider_name(None) == "resend"
    assert describe_provider_config(None)["provider"] == "resend"
    assert describe_provider_config({"provider": "nope"})["stored_invalid"]


def test_an_empty_provider_selection_falls_back_to_the_documented_default() -> None:
    """An empty selection clears the setting; it never yields "no provider"."""
    assert configured_provider_name({"provider": ""}) == "resend"
    assert normalise_provider_config({"provider": ""})["provider"] == "resend"


def test_a_stored_smtp_without_a_transport_is_reported_as_unready() -> None:
    """A hand-edited half-configured row is never presented as usable."""
    described = describe_provider_config({"provider": "smtp"})
    assert described["provider"] == "smtp"
    assert described["smtp"]["host"] is None

    readiness = provider_readiness({"provider": "smtp"})
    assert readiness["ready"] is False
    assert any("smtp_host" in issue for issue in readiness["blocking_issues"])


def test_describe_never_returns_a_credential_value(clean_email_env) -> None:
    clean_email_env.setenv("RESEND_API_KEY", RESEND_SECRET)
    clean_email_env.setenv("CT_SMTP_PASSWORD", SMTP_SECRET)
    described = describe_provider_config(
        {"provider": "smtp", "smtp_host": "mail.example.com", "smtp_username": "u@e.com"}
    )
    blob = json.dumps(described)
    assert RESEND_SECRET not in blob and SMTP_SECRET not in blob
    assert described["credential_env"] == "CT_SMTP_PASSWORD"
    assert described["credential_configured"] is True
    assert described["credential_source"] == "environment"
    assert described["smtp"] == {
        "host": "mail.example.com",
        "port": 587,
        "username": "u@e.com",
        "use_tls": True,
    }


def test_readiness_names_every_blocking_issue(clean_email_env) -> None:
    unready = provider_readiness({"provider": "smtp", "smtp_host": "mail.example.com"})
    assert unready["ready"] is False
    assert any("smtp_username" in issue for issue in unready["blocking_issues"])
    assert any("CT_SMTP_PASSWORD" in issue for issue in unready["blocking_issues"])

    clean_email_env.setenv("CT_SMTP_PASSWORD", SMTP_SECRET)
    ready = provider_readiness(
        {
            "provider": "smtp",
            "smtp_host": "mail.example.com",
            "smtp_username": "u@e.com",
        }
    )
    assert ready["ready"] is True and ready["blocking_issues"] == []


def test_readiness_reports_an_invalid_stored_configuration(clean_email_env) -> None:
    reported = provider_readiness({"provider": "sendgrid"})
    assert reported["provider"] == "resend"
    assert any("invalid" in issue for issue in reported["blocking_issues"])


# ---------------------------------------------------------------------------
# provider abstraction — delivery (adapter selection, fail-closed)
# ---------------------------------------------------------------------------


def test_delivery_uses_the_selected_smtp_adapter_and_env_credential(
    clean_email_env, monkeypatch
) -> None:
    from services import email_provider as provider

    clean_email_env.setenv("CT_SMTP_PASSWORD", SMTP_SECRET)
    captured = {}

    def fake_smtp(*, config, password, from_email, to_email, subject, html):
        captured.update(
            {
                "config": dict(config),
                "password": password,
                "from_email": from_email,
                "to_email": to_email,
                "subject": subject,
                "html": html,
            }
        )

    monkeypatch.setattr(provider, "_send_via_smtp", fake_smtp)

    delivered, reason = deliver_email_sync(
        to_email="customer@example.com",
        subject="Statement ready",
        html="<p>ready</p>",
        from_email="CarbonTally <notifications@carbontally.co.uk>",
        config={
            "provider": "smtp",
            "smtp_host": "mail.example.com",
            "smtp_port": 465,
            "smtp_username": "notifications@example.com",
            "credential_env": "CT_SMTP_PASSWORD",
        },
    )

    assert (delivered, reason) == (True, "sent")
    assert captured["password"] == SMTP_SECRET
    assert captured["config"]["smtp_host"] == "mail.example.com"
    assert captured["config"]["smtp_port"] == 465
    assert captured["from_email"] == "CarbonTally <notifications@carbontally.co.uk>"
    assert captured["to_email"] == "customer@example.com"


def test_delivery_uses_the_resend_adapter_when_resend_is_selected(
    clean_email_env, monkeypatch
) -> None:
    from services import email_provider as provider

    clean_email_env.setenv("RESEND_API_KEY", RESEND_SECRET)
    captured = {}

    class _Client:
        class Emails:  # noqa: N801 - mirrors the SDK shape
            @staticmethod
            def send(params):
                captured.update(params)

    monkeypatch.setattr(provider, "_resend_client", lambda env_name: _Client)

    delivered, reason = deliver_email_sync(
        to_email="customer@example.com",
        subject="Statement ready",
        html="<p>ready</p>",
        from_email="CarbonTally <notifications@carbontally.co.uk>",
        config={"provider": "resend"},
    )

    assert (delivered, reason) == (True, "sent")
    assert captured["from"] == "CarbonTally <notifications@carbontally.co.uk>"
    assert captured["to"] == ["customer@example.com"]


def test_delivery_is_fail_closed_and_never_falls_back_to_another_provider(
    clean_email_env, monkeypatch
) -> None:
    """SMTP selected + no SMTP credential ⇒ honest failure, never Resend."""
    from services import email_provider as provider

    clean_email_env.setenv("RESEND_API_KEY", RESEND_SECRET)
    monkeypatch.setattr(
        provider,
        "_resend_client",
        lambda env_name: pytest.fail("Resend must not be used as a fallback"),
    )

    delivered, reason = deliver_email_sync(
        to_email="customer@example.com",
        subject="Statement ready",
        html="<p>ready</p>",
        from_email="CarbonTally <notifications@carbontally.co.uk>",
        config={"provider": "smtp", "smtp_host": "mail.example.com"},
    )

    assert delivered is False
    assert "CT_SMTP_PASSWORD" in reason


def test_delivery_fails_closed_when_unconfigured(clean_email_env) -> None:
    delivered, reason = deliver_email_sync(
        to_email="customer@example.com",
        subject="s",
        html="<p>x</p>",
        from_email="CarbonTally <notifications@carbontally.co.uk>",
        config=None,
    )
    assert delivered is False and "RESEND_API_KEY" in reason


def test_delivery_never_leaks_the_credential_in_its_failure_reason(
    clean_email_env, monkeypatch
) -> None:
    from services import email_provider as provider

    clean_email_env.setenv("CT_SMTP_PASSWORD", SMTP_SECRET)

    def exploding_smtp(**kwargs):
        raise RuntimeError(f"535 auth failed for password {SMTP_SECRET}")

    monkeypatch.setattr(provider, "_send_via_smtp", exploding_smtp)

    delivered, reason = deliver_email_sync(
        to_email="customer@example.com",
        subject="s",
        html="<p>x</p>",
        from_email="CarbonTally <notifications@carbontally.co.uk>",
        config={
            "provider": "smtp",
            "smtp_host": "mail.example.com",
            "smtp_username": "u@e.com",
        },
    )

    assert delivered is False
    assert SMTP_SECRET not in reason
    assert "***" in reason


def test_resolve_provider_config_is_fail_closed_for_non_request_callers() -> None:
    assert asyncio.run(resolve_provider_config(None)) == {}
    assert asyncio.run(resolve_provider_config(_BrokenSettings())) == {}
    assert asyncio.run(resolve_provider_config(object())) == {}
    configured = asyncio.run(
        resolve_provider_config(
            _FakeSettings(provider="smtp", smtp_host="mail.example.com")
        )
    )
    assert configured["provider"] == "smtp"


# ---------------------------------------------------------------------------
# canonical mailer — the admin configuration is applied end-to-end
# ---------------------------------------------------------------------------


def test_canonical_mailer_applies_the_configured_sender_and_provider(
    clean_email_env, monkeypatch
) -> None:
    from services import email_provider as provider
    from services.v3_email import send_transactional_email

    clean_email_env.setenv("CT_SMTP_PASSWORD", SMTP_SECRET)
    captured = {}

    def fake_smtp(*, config, password, from_email, to_email, subject, html):
        captured.update({"from_email": from_email, "config": dict(config)})

    monkeypatch.setattr(provider, "_send_via_smtp", fake_smtp)

    settings = _FakeSettings(
        provider="smtp", smtp_host="mail.example.com", smtp_username="u@e.com"
    )
    settings.sender = "CarbonTally Notifications <no-reply@carbontally.co.uk>"

    delivered, reason = asyncio.run(
        send_transactional_email(
            to_email="customer@example.com",
            subject="s",
            html="<p>x</p>",
            settings_repo=settings,
        )
    )

    assert (delivered, reason) == (True, "sent")
    # The From address is platform configuration, never the actor's mailbox.
    assert (
        captured["from_email"] == "CarbonTally Notifications <no-reply@carbontally.co.uk>"
    )
    assert captured["config"]["provider"] == "smtp"


def test_canonical_mailer_is_honest_when_the_provider_is_unconfigured(
    clean_email_env,
) -> None:
    from services.v3_email import send_transactional_email

    delivered, reason = asyncio.run(
        send_transactional_email(
            to_email="customer@example.com",
            subject="s",
            html="<p>x</p>",
            settings_repo=_FakeSettings(),
        )
    )
    assert delivered is False and reason


def test_send_platform_email_resolves_settings_without_a_request(
    clean_email_env, monkeypatch
) -> None:
    """Legacy/background callers honour the stored provider (no request scope)."""
    from services import email_provider as provider
    from services import v3_email

    clean_email_env.setenv("CT_SMTP_PASSWORD", SMTP_SECRET)
    seen = {}

    async def fake_repo():
        return _FakeSettings(
            provider="smtp", smtp_host="mail.example.com", smtp_username="u@e.com"
        )

    def fake_smtp(*, config, password, from_email, to_email, subject, html):
        seen["provider"] = config["provider"]

    monkeypatch.setattr(provider, "platform_settings_repo", fake_repo)
    monkeypatch.setattr(provider, "_send_via_smtp", fake_smtp)

    delivered, _reason = asyncio.run(
        v3_email.send_platform_email(to_email="c@e.com", subject="s", html="<p>x</p>")
    )
    assert delivered is True and seen["provider"] == "smtp"


# ---------------------------------------------------------------------------
# legacy call sites route through the canonical mailer
# ---------------------------------------------------------------------------


def test_notification_route_helper_routes_through_the_platform_mailer(
    monkeypatch,
) -> None:
    from routes import notifications
    from services import v3_email

    captured = {}

    async def fake_platform_email(*, to_email, subject, html, from_email=None):
        captured.update({"to_email": to_email, "from_email": from_email})
        return True, "sent"

    monkeypatch.setattr(v3_email, "send_platform_email", fake_platform_email)

    assert asyncio.run(notifications.send_email("c@e.com", "Subject", "<p>x</p>")) is True
    assert captured["to_email"] == "c@e.com"
    # No hard-coded From: the admin-configured platform sender applies.
    assert captured["from_email"] is None


def test_notification_route_helper_never_fakes_a_success(monkeypatch) -> None:
    from routes import notifications
    from services import v3_email

    async def failing(*, to_email, subject, html, from_email=None):
        return False, "email delivery not configured (RESEND_API_KEY unset)"

    monkeypatch.setattr(v3_email, "send_platform_email", failing)

    assert asyncio.run(notifications.send_email("c@e.com", "s", "<p>x</p>")) is False


def test_utils_email_helper_routes_through_the_platform_mailer(monkeypatch) -> None:
    from services import v3_email
    from utils import email as utils_email

    seen = {}

    async def fake_platform_email(*, to_email, subject, html, from_email=None):
        seen["to"] = to_email
        return True, "sent"

    monkeypatch.setattr(v3_email, "send_platform_email", fake_platform_email)

    assert asyncio.run(utils_email.send_email("c@e.com", "s", "<p>x</p>")) is True
    assert seen["to"] == "c@e.com"


def test_email_service_module_routes_through_the_platform_mailer(monkeypatch) -> None:
    from services import email_service, v3_email

    calls = []

    async def fake_platform_email(*, to_email, subject, html, from_email=None):
        calls.append(to_email)
        return True, "sent"

    monkeypatch.setattr(v3_email, "send_platform_email", fake_platform_email)

    assert (
        asyncio.run(
            email_service.send_beta_confirmation_email("beta@example.com", "Beta User")
        )
        is True
    )
    # The user confirmation and the founder notification both go through the
    # canonical mailer.
    assert "beta@example.com" in calls and len(calls) == 2

    calls.clear()
    assert (
        asyncio.run(email_service.send_beta_invite_email("beta@example.com", "CODE-123"))
        is True
    )
    assert calls == ["beta@example.com"]


def test_no_module_outside_the_provider_adapter_imports_a_provider_sdk() -> None:
    """The provider SDK is only reachable through the single adapter."""
    offenders = []
    for package in ("services", "routes", "api", "utils", "data"):
        for path in sorted((BACKEND / package).rglob("*.py")):
            if path.name == "email_provider.py":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "import resend" in text or "resend.Emails" in text:
                offenders.append(str(path.relative_to(BACKEND)))
    assert offenders == []


# ---------------------------------------------------------------------------
# admin API — /api/v3/settings/email-provider (ALLOW / DENY / persistence)
# ---------------------------------------------------------------------------


def _admin(user_provider) -> None:
    from tests.unit.api.fakes import staff_user

    user_provider.set_user(
        staff_user("u-admin", email="admin@example.test", role_name="admin")
    )


def test_email_provider_route_is_registered() -> None:
    from api.router import router as v3_router
    from tests.unit.api.route_paths import flatten_router_paths

    paths = flatten_router_paths(v3_router)
    assert any(SETTINGS_PATH in path for path in paths)
    assert any(VALIDATE_PATH in path for path in paths)


def test_get_reports_the_default_provider_when_nothing_is_configured(
    client, world, user_provider, clean_email_env
) -> None:
    _admin(user_provider)
    response = client.get(SETTINGS_PATH)
    assert response.status_code == 200
    settings = response.json()["settings"]
    assert settings["provider"] == "resend"
    assert settings["is_default"] is True and settings["configured"] is False
    assert settings["supported_providers"] == ["resend", "smtp"]
    assert settings["default_provider"] == "resend"
    assert settings["credential_env"] == "RESEND_API_KEY"
    assert settings["credential_source"] == "environment"
    assert settings["credential_configured"] is False
    # The provider in force is described even though nothing is configured, and
    # readiness honestly reports that delivery would fail.
    assert settings["readiness"]["provider"] == "resend"
    assert settings["readiness"]["ready"] is False
    assert settings["readiness"]["blocking_issues"]
    assert settings["updated_at"] is None

    # The GET must never touch the environment credential's value.
    assert RESEND_SECRET not in response.text


def test_put_selects_smtp_persists_and_round_trips(
    client, world, user_provider, clean_email_env
) -> None:
    _admin(user_provider)
    put = client.put(
        SETTINGS_PATH,
        json={
            "provider": "smtp",
            "smtp_host": "mail.a2hosting.com",
            "smtp_username": "notifications@carbontally.co.uk",
        },
    )
    assert put.status_code == 200
    settings = put.json()["settings"]
    assert settings["provider"] == "smtp"
    assert settings["configured"] is True and settings["is_default"] is False
    assert settings["credential_env"] == "CT_SMTP_PASSWORD"
    assert settings["smtp"] == {
        "host": "mail.a2hosting.com",
        "port": 587,
        "username": "notifications@carbontally.co.uk",
        "use_tls": True,
    }
    assert settings["updated_by"] == "u-admin"

    stored = asyncio.run(world.bundle().settings.get_email_provider())
    assert stored["provider"] == "smtp" and stored["smtp_host"] == "mail.a2hosting.com"

    # Persistence: the following GET returns the stored configuration.
    again = client.get(SETTINGS_PATH).json()["settings"]
    assert again["provider"] == "smtp" and again["configured"] is True
    assert again["readiness"]["provider"] == "smtp"


@pytest.mark.parametrize(
    "payload",
    [
        {"provider": "sendgrid"},
        {"provider": "smtp"},
        {"provider": "smtp", "smtp_host": "https://mail.example.com"},
        {"provider": "smtp", "smtp_host": "mail.example.com", "smtp_port": 0},
        {"provider": "smtp", "smtp_host": "mail.example.com", "smtp_port": 99999},
        {"provider": "resend", "smtp_use_tls": "sometimes"},
        {"provider": "smtp", "smtp_host": "mail.example.com", "credential_env": "AWS_SECRET_ACCESS_KEY"},
        {"provider": "smtp", "smtp_host": "mail.example.com", "credential_env": "lower_case"},
    ],
)
def test_put_refuses_invalid_configuration_and_stores_nothing(
    client, world, user_provider, clean_email_env, payload
) -> None:
    _admin(user_provider)
    assert client.put(SETTINGS_PATH, json=payload).status_code == 422
    stored = asyncio.run(world.bundle().settings.get_email_provider())
    assert stored["provider"] is None  # nothing was written


@pytest.mark.parametrize(
    "payload",
    [
        {"provider": "resend", "api_key": "re_live_secret"},
        {"provider": "smtp", "smtp_host": "mail.example.com", "password": "hunter2"},
        {"provider": "smtp", "smtp_host": "mail.example.com", "credential": "hunter2"},
    ],
)
def test_put_refuses_a_credential_smuggled_in_as_a_setting(
    client, world, user_provider, clean_email_env, payload
) -> None:
    _admin(user_provider)
    assert client.put(SETTINGS_PATH, json=payload).status_code == 422
    stored = asyncio.run(world.bundle().settings.get_email_provider())
    assert stored["provider"] is None
    assert "hunter2" not in json.dumps(stored)


def test_switching_provider_re_points_the_credential_variable(
    client, world, user_provider, clean_email_env
) -> None:
    _admin(user_provider)
    client.put(
        SETTINGS_PATH,
        json={
            "provider": "smtp",
            "smtp_host": "mail.a2hosting.com",
            "smtp_username": "notifications@carbontally.co.uk",
        },
    )
    back = client.put(SETTINGS_PATH, json={"provider": "resend"})
    assert back.status_code == 200
    settings = back.json()["settings"]
    assert settings["provider"] == "resend"
    # A stale CT_SMTP_PASSWORD reference must not survive the switch.
    assert settings["credential_env"] == "RESEND_API_KEY"
    assert settings["readiness"]["credential_env"] == "RESEND_API_KEY"


def test_an_empty_string_clears_a_stored_transport_value(
    client, world, user_provider, clean_email_env
) -> None:
    _admin(user_provider)
    client.put(
        SETTINGS_PATH,
        json={
            "provider": "smtp",
            "smtp_host": "mail.a2hosting.com",
            "smtp_username": "notifications@carbontally.co.uk",
        },
    )
    # The SMTP provider is never half-configured: clearing the host while SMTP
    # is still selected is refused (and nothing is stored).
    assert client.put(SETTINGS_PATH, json={"smtp_host": ""}).status_code == 422
    assert (
        asyncio.run(world.bundle().settings.get_email_provider())["smtp_host"]
        == "mail.a2hosting.com"
    )

    # Clearing the transport together with selecting another provider succeeds.
    cleared = client.put(SETTINGS_PATH, json={"provider": "resend", "smtp_host": ""})
    assert cleared.status_code == 200
    stored = asyncio.run(world.bundle().settings.get_email_provider())
    assert stored["smtp_host"] is None
    assert cleared.json()["settings"]["provider"] == "resend"

    # With the transport gone, SMTP can no longer be selected without
    # re-supplying it.
    assert client.put(SETTINGS_PATH, json={"provider": "smtp"}).status_code == 422


def test_validate_reports_an_invalid_candidate_without_persisting(
    client, world, user_provider, clean_email_env
) -> None:
    _admin(user_provider)
    response = client.post(VALIDATE_PATH, json={"provider": "smtp"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"]
    # The configuration in force is described, not the rejected candidate.
    assert body["settings"]["provider"] == "resend"
    assert asyncio.run(world.bundle().settings.get_email_provider())["provider"] is None


def test_validate_reports_a_valid_candidate_with_readiness_without_persisting(
    client, world, user_provider, clean_email_env
) -> None:
    _admin(user_provider)
    response = client.post(
        VALIDATE_PATH,
        json={
            "provider": "smtp",
            "smtp_host": "mail.a2hosting.com",
            "smtp_username": "notifications@carbontally.co.uk",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True and body["errors"] == []
    assert body["settings"]["provider"] == "smtp"
    # No credential is configured in this environment: readiness says so
    # instead of pretending the provider is usable.
    assert body["settings"]["readiness"]["ready"] is False
    assert body["settings"]["readiness"]["blocking_issues"]
    assert asyncio.run(world.bundle().settings.get_email_provider())["provider"] is None


def test_no_credential_value_ever_appears_in_a_response(
    client, world, user_provider, clean_email_env
) -> None:
    _admin(user_provider)
    clean_email_env.setenv("RESEND_API_KEY", RESEND_SECRET)
    clean_email_env.setenv("CT_SMTP_PASSWORD", SMTP_SECRET)

    responses = [
        client.get(SETTINGS_PATH),
        client.put(SETTINGS_PATH, json={"provider": "resend"}),
        client.put(
            SETTINGS_PATH,
            json={
                "provider": "smtp",
                "smtp_host": "mail.a2hosting.com",
                "smtp_username": "notifications@carbontally.co.uk",
            },
        ),
        client.post(VALIDATE_PATH, json={"provider": "resend"}),
    ]
    for response in responses:
        assert response.status_code == 200, response.text
        assert RESEND_SECRET not in response.text
        assert SMTP_SECRET not in response.text

    # The stored row holds the variable NAME, never its value.
    stored = asyncio.run(world.bundle().settings.get_email_provider())
    blob = json.dumps(stored)
    assert RESEND_SECRET not in blob and SMTP_SECRET not in blob
    assert stored["credential_env"] == "CT_SMTP_PASSWORD"


def test_readiness_reports_the_configured_notification_sender(
    client, world, user_provider, clean_email_env
) -> None:
    _admin(user_provider)
    sender = "CarbonTally Notifications <no-reply@carbontally.co.uk>"
    assert client.put(SENDER_PATH, json={"email_sender": sender}).status_code == 200

    settings = client.get(SETTINGS_PATH).json()["settings"]
    assert settings["readiness"]["sender"] == sender


def test_denied_for_non_admin_and_anonymous(client, world, user_provider) -> None:
    from tests.unit.api.fakes import member_user

    user_provider.set_user(member_user("org-a", "u-member", "member@example.test"))
    assert client.get(SETTINGS_PATH).status_code == 403
    assert client.put(SETTINGS_PATH, json={"provider": "resend"}).status_code == 403
    assert client.post(VALIDATE_PATH, json={"provider": "resend"}).status_code == 403

    user_provider.set_unauthenticated()
    assert client.get(SETTINGS_PATH).status_code == 401
    assert client.put(SETTINGS_PATH, json={"provider": "resend"}).status_code == 401
    assert client.post(VALIDATE_PATH, json={"provider": "resend"}).status_code == 401


def test_an_organisation_owner_cannot_reach_the_platform_email_configuration(
    client, world, user_provider
) -> None:
    from tests.unit.api.fakes import org_owner_user

    user_provider.set_user(org_owner_user("org-a", "u-owner", "owner@example.test"))
    assert client.get(SETTINGS_PATH).status_code == 403
    assert client.put(SETTINGS_PATH, json={"provider": "resend"}).status_code == 403


def test_a_consultant_cannot_reach_the_platform_email_configuration(
    client, world, user_provider
) -> None:
    from tests.unit.api.fakes import consultant_user

    user_provider.set_user(consultant_user("u-consultant", "consultant@example.test"))
    assert client.get(SETTINGS_PATH).status_code == 403
    assert client.put(SETTINGS_PATH, json={"provider": "resend"}).status_code == 403


def test_processing_entity_staff_cannot_reach_the_platform_email_configuration(
    client, world, user_provider
) -> None:
    from tests.unit.api.fakes import entity_operator_user

    user_provider.set_user(entity_operator_user("entity-a"))
    assert client.get(SETTINGS_PATH).status_code == 403
    assert client.put(SETTINGS_PATH, json={"provider": "resend"}).status_code == 403
