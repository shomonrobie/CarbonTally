"""V3 transactional email (D27 / D19 white-label email boundary).

CarbonTally is NOT an email provider. Consultant-owned domains/senders are
verified externally (Resend domain verification + DNS). This module:

* sends ONLY from the CarbonTally default sender OR a VERIFIED consultant
  sender row (``consultant_senders.status = 'verified'``) — arbitrary From
  addresses are never allowed (D19 §13);
* sends through the **admin-configured delivery provider**
  (``services.email_provider``, CT-FINAL-02 EMAIL-CONFIG-01: Resend or SMTP),
  never through a hard-coded provider;
* is a no-op stub when the selected provider's credential is not configured
  (local/dev), so callers can still exercise the full workflow and the
  delivery result is returned honestly (``delivered=False`` + reason);
* keeps the delivery dependency lazy and testable (the caller may inject a
  fake sender or client).
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from services.email_sender import DEFAULT_SENDER as DEFAULT_FROM_EMAIL

#: Sender types accepted by :func:`send_transactional_email`.
_ResendClient = Any


async def resolve_configured_sender(settings_repo: Any) -> str:
    """Return the admin-configured platform sender, or the platform default.

    CT-FINAL-01 notifications: the From address is platform configuration
    (``system_settings`` key ``platform_notifications``), never the acting
    user's mailbox.  The read is deliberately fail-open to the approved default:
    an unavailable settings row must not stop a transactional email, and it must
    never produce an unvalidated From address.
    """
    from services.email_sender import resolve_email_sender

    if settings_repo is None:
        return DEFAULT_FROM_EMAIL
    try:
        config = await settings_repo.get_notification_sender()
    except Exception:  # noqa: BLE001 — configuration read is best-effort
        return DEFAULT_FROM_EMAIL
    if not isinstance(config, dict):
        return DEFAULT_FROM_EMAIL
    return resolve_email_sender(config.get("email_sender"))


async def resolve_configured_provider(settings_repo: Any) -> dict:
    """Return the admin-configured email delivery provider configuration.

    CT-FINAL-02 EMAIL-CONFIG-01: the provider is platform configuration
    (``system_settings`` key ``email_provider``).  A missing/unreadable row
    yields ``{}`` so the documented default provider (Resend) applies — the
    provider can never be "none", and no credential is ever read from here.
    """
    from services.email_provider import resolve_provider_config

    return await resolve_provider_config(settings_repo)


def _resend_client() -> Optional[_ResendClient]:
    """Return the Resend client when configured, else ``None``.

    Import is lazy so the module (and every caller) imports without a network
    or API-key dependency.  Provider/credential resolution itself lives in
    ``services.email_provider`` — this helper is retained only for callers that
    inject nothing and rely on the default provider.
    """
    from services.email_provider import (
        DEFAULT_CREDENTIAL_ENV,
        _resend_client as provider_resend_client,
    )

    return provider_resend_client(DEFAULT_CREDENTIAL_ENV["resend"])


async def send_transactional_email(
    *,
    to_email: str,
    subject: str,
    html: str,
    from_email: Optional[str] = None,
    sender: Optional[Callable[..., bool]] = None,
    client: Optional[_ResendClient] = None,
    settings_repo: Any = None,
    provider_config: Optional[dict] = None,
) -> tuple[bool, str]:
    """Send one transactional email through the **configured** provider.

    Args:
        to_email: recipient address.
        subject: email subject.
        html: HTML body.
        from_email: the From address.  When omitted it is resolved from the
            admin-configured platform sender (``services.email_sender``), which
            itself fails closed to the approved CarbonTally default.
        sender: optional injected sender ``callable`` for tests (returns bool).
        client: optional injected Resend client for tests.
        settings_repo: the platform settings repository.  When supplied, the
            sender **and** the delivery provider are resolved from the
            persisted admin configuration — this is the canonical runtime path
            (Admin Dashboard → stored configuration → provider adapter).
        provider_config: an already-resolved provider configuration (avoids a
            second settings read when the caller has one).

    Returns:
        ``(delivered, reason)``. ``delivered=False`` when the selected provider
        is not configured (the caller should surface an honest "email could not
        be delivered" state rather than a fake success).  Delivery never falls
        back to another provider.
    """
    from services.email_provider import deliver_email

    if from_email is None:
        from_email = await resolve_configured_sender(settings_repo)
    if provider_config is None and settings_repo is not None:
        provider_config = await resolve_configured_provider(settings_repo)

    return await deliver_email(
        to_email=to_email,
        subject=subject,
        html=html,
        from_email=from_email,
        config=provider_config,
        client=client,
        sender=sender,
    )


async def send_platform_email(
    *,
    to_email: str,
    subject: str,
    html: str,
    from_email: Optional[str] = None,
) -> tuple[bool, str]:
    """Send a platform email from a caller with **no** request-scoped settings.

    This is the canonical entry point for legacy/background notification code
    (``utils.email``, ``routes.notifications``): it resolves the platform
    settings itself — so the admin-configured sender **and** delivery provider
    both apply — and then delivers through exactly the same path as every other
    notification.  A configuration that cannot be read degrades to the
    documented defaults, never to "no provider".
    """
    from services.email_provider import platform_settings_repo

    return await send_transactional_email(
        to_email=to_email,
        subject=subject,
        html=html,
        from_email=from_email,
        settings_repo=await platform_settings_repo(),
    )


def render_simple_html(*, brand_name: str, heading: str, body_html: str, footer: Optional[str] = None) -> str:
    """A minimal, safe HTML email shell (consultant-branded when required)."""
    footer_block = (
        f"<div style='margin-top:24px;padding-top:12px;border-top:1px solid #e2e8f0;"
        f"color:#64748b;font-size:12px'>{footer}</div>"
        if footer
        else ""
    )
    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"></head>
    <body style="margin:0;background:#f8fafc;font-family:'Segoe UI',Arial,sans-serif;color:#1e293b">
      <div style="max-width:600px;margin:0 auto;padding:24px">
        <div style="background:#0f172a;color:#fff;padding:20px;border-radius:8px 8px 0 0">
          <strong>{brand_name}</strong>
        </div>
        <div style="background:#fff;padding:24px;border-left:1px solid #e2e8f0;border-right:1px solid #e2e8f0">
          <h2 style="margin:0 0 12px">{heading}</h2>
          {body_html}
        </div>
        {footer_block}
      </div>
    </body></html>
    """
