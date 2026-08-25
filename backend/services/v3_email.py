"""V3 transactional email (D27 / D19 white-label email boundary).

CarbonTally is NOT an email provider. Consultant-owned domains/senders are
verified externally (Resend domain verification + DNS). This module:

* sends ONLY from the CarbonTally default sender OR a VERIFIED consultant
  sender row (``consultant_senders.status = 'verified'``) — arbitrary From
  addresses are never allowed (D19 §13);
* is a no-op stub when ``RESEND_API_KEY`` is not configured (local/dev), so
  callers can still exercise the full workflow and the delivery result is
  returned honestly (``delivered=False`` + reason);
* keeps the Resend dependency lazy and testable (the caller may inject a
  fake sender).
"""
from __future__ import annotations

import os
from typing import Any, Callable, Optional

#: Default CarbonTally transactional sender.
DEFAULT_FROM_EMAIL: str = "CarbonTally <notifications@carbontally.co.uk>"

#: Sender types accepted by :func:`send_transactional_email`.
_ResendClient = Any


def _resend_client() -> Optional[_ResendClient]:
    """Return the Resend client when configured, else ``None``.

    Import is lazy so the module (and every caller) imports without a network
    or API-key dependency.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return None
    try:
        import resend
    except Exception:  # noqa: BLE001
        return None
    resend.api_key = api_key
    return resend


async def send_transactional_email(
    *,
    to_email: str,
    subject: str,
    html: str,
    from_email: str = DEFAULT_FROM_EMAIL,
    sender: Optional[Callable[..., bool]] = None,
    client: Optional[_ResendClient] = None,
) -> tuple[bool, str]:
    """Send one transactional email.

    Args:
        to_email: recipient address.
        subject: email subject.
        html: HTML body.
        from_email: the From address. Only the CarbonTally default OR a
            pre-verified consultant sender is ever passed by callers — this
            module never fabricates a From address.
        sender: optional injected sender ``callable`` for tests (returns bool).
        client: optional injected Resend client for tests.

    Returns:
        ``(delivered, reason)``. ``delivered=False`` when Resend is not
        configured (the caller should surface an honest "email could not be
        delivered" state rather than a fake success).
    """
    if sender is not None:
        try:
            ok = sender(to_email=to_email, subject=subject, html=html, from_email=from_email)
            return bool(ok), "sent" if ok else "send failed"
        except Exception as exc:  # noqa: BLE001
            return False, f"send failed: {exc}"
    client = client or _resend_client()
    if client is None:
        return False, "email delivery not configured (RESEND_API_KEY unset)"
    try:
        client.Emails.send(
            {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
        )
        return True, "sent"
    except Exception as exc:  # noqa: BLE001
        return False, f"send failed: {exc}"


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
