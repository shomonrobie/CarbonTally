"""Platform email **delivery provider** configuration (CT-FINAL-02 / EMAIL-CONFIG-01).

CarbonTally must not be hard-coded to one email provider.  This module is the
single canonical abstraction between notification business logic and the
delivery provider:

    Admin Dashboard (ops → Settings)
        → ``/api/v3/settings/email-provider`` (admin only)
        → persisted configuration (``system_settings`` key ``email_provider``)
        → secure credential resolution (ENVIRONMENT ONLY)
        → canonical mailer (``services.v3_email.send_transactional_email``)
        → selected provider adapter (Resend | SMTP)
        → configured sender identity (``services.email_sender``)

Two invariants are deliberately encoded here:

1. **No credential is ever persisted or returned.**  The configuration row
   stores only *which* provider is selected and *which allow-listed environment
   variable* holds the credential (the project's existing secret mechanism is
   the process environment — the same mechanism ``RESEND_API_KEY`` already
   uses).  A secret-looking field submitted through the API is rejected rather
   than stored, and no description produced by this module can contain a value.
   The credential environment variable may only be one of
   :data:`ALLOWED_CREDENTIAL_ENVS` — an administrator can therefore never point
   CarbonTally at an arbitrary variable and exfiltrate an unrelated secret to a
   host they chose.

2. **Fail closed, never fall back.**  A provider that cannot deliver reports
   ``delivered=False`` with a reason.  Delivery is never silently re-routed to
   a different (possibly unconfigured) provider, and a missing credential can
   never be interpreted as "send anyway".

Supported providers (both end-to-end: selection → persistence → runtime
adapter → delivery):

``resend``
    The CarbonTally platform provider (API key in the environment).
``smtp``
    Any SMTP submission service (A2Hosting, Gmail/Google Workspace SMTP, …)
    using the standard library — no new dependency, TLS by default.
"""
from __future__ import annotations

import logging
import os
import re
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr
from typing import Any, Dict, Mapping, Optional, Tuple

logger = logging.getLogger(__name__)

#: ``system_settings.setting_key`` used for the provider configuration row.
EMAIL_PROVIDER_SETTING_KEY = "email_provider"

#: Providers that are actually implemented end-to-end (never a UI-only list).
SUPPORTED_PROVIDERS: Tuple[str, ...] = ("resend", "smtp")

#: The provider in force when nothing has been configured.  Unchanged
#: behaviour for every existing deployment.
DEFAULT_PROVIDER = "resend"

#: Provider-specific default credential environment variable.
DEFAULT_CREDENTIAL_ENV: Dict[str, str] = {
    "resend": "RESEND_API_KEY",
    "smtp": "CT_SMTP_PASSWORD",
}

#: The ONLY environment variables a provider may be pointed at.  This is a
#: security control, not a convenience: an arbitrary variable name would let an
#: administrator cause an unrelated secret to be transmitted to a host of their
#: choosing.
ALLOWED_CREDENTIAL_ENVS: frozenset[str] = frozenset(
    {"RESEND_API_KEY", "CT_SMTP_PASSWORD", "SMTP_PASSWORD"}
)

#: Default SMTP submission port (STARTTLS).
DEFAULT_SMTP_PORT = 587

#: Connection timeout (seconds) for an SMTP submission.
SMTP_TIMEOUT_SECONDS = 20

#: Field names that would carry a credential.  A request containing one is
#: rejected: provider secrets belong in the environment, never in settings.
_SECRET_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "api_key",
        "apikey",
        "key",
        "password",
        "passwd",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "client_secret",
        "smtp_password",
        "smtp_pass",
        "resend_api_key",
        "credential",
        "credential_value",
    }
)

#: Credential env-var names must look like environment variables.
_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")

#: A hostname (optionally dotted), never a URL, never host:port.
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)

PROVIDER_FIELDS: Tuple[str, ...] = (
    "provider",
    "smtp_host",
    "smtp_port",
    "smtp_username",
    "smtp_use_tls",
    "credential_env",
)


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _positive_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed


def normalise_provider_config(
    raw: Optional[Mapping[str, Any]],
    *,
    allow_partial: bool = False,
) -> Dict[str, Any]:
    """Validate and canonicalise a provider configuration.

    Returns the canonical configuration (``None`` for an unset field).  Raises
    ``ValueError`` for anything unusable — an unknown provider, a malformed
    host/port, a credential variable outside :data:`ALLOWED_CREDENTIAL_ENVS`,
    or a secret submitted as an ordinary setting.

    ``allow_partial`` is used while merging a partial update: the shape is
    still validated, but "the SMTP provider selected without its transport
    details" is not yet an error (the *merged* row is validated before it is
    persisted).
    """
    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        raise ValueError("email provider configuration must be an object")

    # Refuse a credential smuggled in as configuration, whatever it is called.
    for key in raw:
        if str(key).strip().lower() in _SECRET_FIELD_NAMES:
            raise ValueError(
                "provider credentials must never be stored as settings; "
                "supply the secret through the referenced environment variable"
            )

    supplied_provider = _clean(raw.get("provider"))
    provider = (supplied_provider or DEFAULT_PROVIDER).lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("provider must be one of: " + ", ".join(SUPPORTED_PROVIDERS))

    host = _clean(raw.get("smtp_host"))
    if host is not None:
        if host.lower().startswith(("http://", "https://", "smtp://")) or ":" in host:
            raise ValueError("smtp_host must be a hostname only (no scheme and no port)")
        if not _HOSTNAME_RE.match(host):
            raise ValueError("smtp_host is not a valid hostname")

    port = raw.get("smtp_port")
    if port is not None and _clean(port) is not None:
        parsed_port = _positive_int(port)
        if parsed_port is None or not 1 <= parsed_port <= 65535:
            raise ValueError("smtp_port must be an integer between 1 and 65535")
        port = parsed_port

    username = _clean(raw.get("smtp_username"))
    if username is not None and re.search(r"[\r\n\t]", username):
        raise ValueError("smtp_username must be a single value")

    use_tls = raw.get("smtp_use_tls")
    if use_tls is None:
        use_tls = True
    elif not isinstance(use_tls, bool):
        raise ValueError("smtp_use_tls must be a boolean")

    credential_env = _clean(raw.get("credential_env"))
    if credential_env is not None:
        credential_env = credential_env.upper()
        if not _ENV_NAME_RE.match(credential_env):
            raise ValueError("credential_env must be an environment variable name")
        if credential_env not in ALLOWED_CREDENTIAL_ENVS:
            raise ValueError(
                "credential_env must be one of: "
                + ", ".join(sorted(ALLOWED_CREDENTIAL_ENVS))
            )

    config: Dict[str, Any] = {
        "provider": provider,
        "smtp_host": host,
        "smtp_port": port or (DEFAULT_SMTP_PORT if provider == "smtp" else None),
        "smtp_username": username,
        "smtp_use_tls": bool(use_tls),
        "credential_env": credential_env or DEFAULT_CREDENTIAL_ENV[provider],
    }

    if provider == "smtp" and not allow_partial and not config["smtp_host"]:
        raise ValueError(
            "smtp_host is required when the SMTP provider is selected "
            "(the SMTP provider is never half-configured)"
        )
    return config


def configured_provider_name(raw: Optional[Mapping[str, Any]]) -> str:
    """The effective provider name, fail-closed to the documented default.

    An unreadable or unusable stored configuration never becomes an unknown
    provider state: the default provider applies.
    """
    try:
        return normalise_provider_config(raw, allow_partial=True)["provider"]
    except (ValueError, TypeError):
        return DEFAULT_PROVIDER


def resolve_credential_env(raw: Optional[Mapping[str, Any]]) -> str:
    """The (allow-listed) environment variable holding the provider credential."""
    try:
        config = normalise_provider_config(raw, allow_partial=True)
    except (ValueError, TypeError):
        return DEFAULT_CREDENTIAL_ENV[DEFAULT_PROVIDER]
    provider = config["provider"]
    return config.get("credential_env") or DEFAULT_CREDENTIAL_ENV[provider]


def credential_value(env_name: str) -> Optional[str]:
    """Read the provider credential from the environment (never from settings).

    The name is re-checked against the allow-list here so no caller can widen
    the set of readable variables by passing an unvalidated name.
    """
    if env_name not in ALLOWED_CREDENTIAL_ENVS:
        return None
    value = os.environ.get(env_name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def describe_provider_config(
    raw: Optional[Mapping[str, Any]],
    *,
    stored: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Describe the effective provider configuration **without any secret**.

    Returns the selected provider, whether platform configuration is in force,
    the referenced credential variable and whether it is *present* (a boolean —
    the value is never read into the response), and the non-secret SMTP
    transport fields.  A malformed stored configuration is reported as the
    default provider so the Admin Dashboard shows what will actually happen.
    """
    try:
        config = normalise_provider_config(raw, allow_partial=True)
        invalid_reason = None
    except (ValueError, TypeError) as exc:
        config = normalise_provider_config(None)
        invalid_reason = str(exc)

    provider = config["provider"]
    env_name = config.get("credential_env") or DEFAULT_CREDENTIAL_ENV[provider]
    is_default = provider == DEFAULT_PROVIDER and not (
        raw.get("provider") if isinstance(raw, Mapping) else None
    )
    stored = stored or {}
    return {
        "provider": provider,
        "is_default": bool(is_default),
        "configured": not is_default,
        "supported_providers": list(SUPPORTED_PROVIDERS),
        "default_provider": DEFAULT_PROVIDER,
        "credential_env": env_name,
        "credential_source": "environment",
        "credential_configured": credential_value(env_name) is not None,
        "smtp": (
            {
                "host": config.get("smtp_host"),
                "port": config.get("smtp_port"),
                "username": config.get("smtp_username"),
                "use_tls": config.get("smtp_use_tls"),
            }
            if provider == "smtp"
            else None
        ),
        "stored_invalid": invalid_reason,
        "updated_at": stored.get("updated_at"),
        "updated_by": stored.get("updated_by"),
    }


def provider_readiness(
    raw: Optional[Mapping[str, Any]],
    *,
    sender: Optional[str] = None,
) -> Dict[str, Any]:
    """Report whether the configured provider could actually deliver.

    This performs **no** network call and sends **no** email: it evaluates the
    configuration and the presence of the referenced credential, which is what
    "validate configuration" can honestly assert without a real sender domain.
    Every blocking issue is named, so an administrator is never told
    "ready" for a provider that would fail at the first delivery attempt.
    """
    description = describe_provider_config(raw)
    issues = []
    if description["stored_invalid"]:
        issues.append(
            "the stored configuration is invalid and the default provider is in "
            f"force: {description['stored_invalid']}"
        )
    if description["provider"] == "smtp":
        smtp = description["smtp"] or {}
        if not smtp.get("host"):
            issues.append("smtp_host is not configured")
        if not smtp.get("username"):
            issues.append("smtp_username is not configured")
    if not description["credential_configured"]:
        issues.append(
            f"the credential variable {description['credential_env']} is not set in "
            "the server environment"
        )
    return {
        "provider": description["provider"],
        "ready": not issues,
        "blocking_issues": issues,
        "credential_env": description["credential_env"],
        "credential_configured": description["credential_configured"],
        "sender": sender,
    }


# ---------------------------------------------------------------------------
# Provider adapters
# ---------------------------------------------------------------------------


def _resend_client(env_name: str) -> Optional[Any]:
    """Return a Resend client when the credential is configured, else ``None``.

    The import stays lazy so no module (and no test) needs the package or a
    network at import time.
    """
    api_key = credential_value(env_name)
    if not api_key:
        return None
    try:
        import resend  # type: ignore
    except Exception:  # noqa: BLE001 — an absent library is "not configured"
        return None
    resend.api_key = api_key
    return resend


def _send_via_resend(*, client: Any, from_email, to_email, subject, html) -> None:
    client.Emails.send(
        {"from": from_email, "to": [to_email], "subject": subject, "html": html}
    )


def _send_via_smtp(
    *, config: Mapping[str, Any], password: str, from_email, to_email, subject, html
) -> None:
    """Submit one message over SMTP using the standard library.

    STARTTLS is used unless the configuration explicitly disables it.  The
    credential is never included in any error text returned to a caller.
    """
    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content("This message requires an HTML-capable email client.")
    message.add_alternative(html, subtype="html")

    host = config.get("smtp_host")
    port = int(config.get("smtp_port") or DEFAULT_SMTP_PORT)
    username = config.get("smtp_username")
    use_tls = bool(config.get("smtp_use_tls", True))

    with smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        if username:
            smtp.login(username, password)
        smtp.send_message(message)


def _scrub(reason: str, *secrets: Optional[str]) -> str:
    """Remove any credential from a reason string before it is returned/logged."""
    for secret in secrets:
        if secret:
            reason = reason.replace(secret, "***")
    return reason


def deliver_email_sync(
    *,
    to_email: str,
    subject: str,
    html: str,
    from_email: str,
    config: Optional[Mapping[str, Any]] = None,
    client: Optional[Any] = None,
    sender: Optional[Any] = None,
) -> Tuple[bool, str]:
    """Deliver one email through the **configured** provider.

    Returns ``(delivered, reason)``.  Delivery never falls back to another
    provider: an unconfigured or unusable provider reports ``False`` with a
    reason the caller can surface honestly.
    """
    try:
        effective = normalise_provider_config(config, allow_partial=True)
    except (ValueError, TypeError) as exc:
        return False, f"provider configuration is invalid: {exc}"

    provider = effective["provider"]
    env_name = effective.get("credential_env") or DEFAULT_CREDENTIAL_ENV[provider]

    if sender is not None:
        # Programmatic/injected delivery (used by tests and by callers that
        # bring their own transport).
        try:
            ok = sender(
                to_email=to_email, subject=subject, html=html, from_email=from_email
            )
            return bool(ok), "sent" if ok else "send failed"
        except Exception as exc:  # noqa: BLE001
            return False, f"send failed: {exc}"

    if provider == "smtp":
        host = effective.get("smtp_host")
        if not host:
            return False, (
                "email delivery not configured (SMTP provider selected without "
                "smtp_host)"
            )
        password = credential_value(env_name)
        if not password:
            return False, f"email delivery not configured ({env_name} unset)"
        try:
            _send_via_smtp(
                config=effective,
                password=password,
                from_email=from_email,
                to_email=to_email,
                subject=subject,
                html=html,
            )
            return True, "sent"
        except Exception as exc:  # noqa: BLE001
            return False, _scrub(f"send failed: {exc}", password)

    resend_client = client or _resend_client(env_name)
    if resend_client is None:
        return False, f"email delivery not configured ({env_name} unset)"
    try:
        _send_via_resend(
            client=resend_client,
            from_email=from_email,
            to_email=to_email,
            subject=subject,
            html=html,
        )
        return True, "sent"
    except Exception as exc:  # noqa: BLE001
        return False, f"send failed: {exc}"


async def deliver_email(**kwargs: Any) -> Tuple[bool, str]:
    """Async wrapper: the SMTP transport is blocking, so it runs off-loop."""
    import asyncio

    return await asyncio.to_thread(deliver_email_sync, **kwargs)


async def resolve_provider_config(settings_repo: Any) -> Dict[str, Any]:
    """Read the persisted provider configuration (best-effort, fail-closed).

    An unavailable or unreadable settings row yields ``{}`` — the documented
    default provider then applies.  It can never yield an unknown provider or
    an unvalidated credential variable.
    """
    if settings_repo is None:
        return {}
    reader = getattr(settings_repo, "get_email_provider", None)
    if reader is None:
        return {}
    try:
        config = await reader()
    except Exception:  # noqa: BLE001 — configuration read is best-effort
        return {}
    return dict(config) if isinstance(config, Mapping) else {}


async def platform_settings_repo() -> Any:
    """Best-effort platform settings repository for **non-request** callers.

    Legacy notification helpers (``utils.email``, ``routes.notifications``) run
    outside a FastAPI request, so they resolve platform settings through the
    process-wide service pool.  Any failure yields ``None``, in which case the
    documented defaults apply — configuration being unavailable must never stop
    configuration being *safe*.
    """
    try:
        from data.settings import SettingsRepository
        from infra.supabase import get_service_pool

        return SettingsRepository(await get_service_pool())
    except Exception:  # noqa: BLE001 — no pool ⇒ defaults apply
        return None
