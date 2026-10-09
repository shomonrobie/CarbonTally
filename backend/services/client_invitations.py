"""Client-user invitation email composition + white-label sender resolution.

CT-CONSULTANT-CLIENT-IDENTITY-04 (PD-1A / PD-2A / D19 §13).

This is the single place that turns a durable ``user_invitations`` row into a
delivered, correctly-branded email. It is deliberately small and I/O-light so
both the organisation plane (``api/v3_organizations.py``) and the consultant
plane (``api/v3_consultants.py``) call the SAME composition and sender rules
rather than re-implementing them:

* the presentation brand is the INVITING party's brand — the consultant firm's
  own branding (D21) when the firm invited the client user on the client's
  behalf, otherwise the CarbonTally fallback;
* the From address is the firm's own **VERIFIED** custom sender
  (``consultant_senders``, D19 §13) when one exists, otherwise the
  admin-configured platform sender. An UNVERIFIED consultant address is never
  used as a sender — a customer/consultant domain requires an externally
  verified sender row, exactly as ``services.email_sender`` documents.

Nothing here grants authority: the caller must already have been authorised by
the API guard family before composing an invitation email.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

from domain.branding import BrandContext, default_brand_context, resolve_brand_context
from domain.client_identity import resolve_invitation_state
from services.email_sender import normalise_email_sender
from services.v3_email import render_simple_html, send_transactional_email

__all__ = [
    "APP_BASE_URL",
    "parse_invitation_expiry",
    "describe_invitation",
    "invitation_accept_url",
    "render_invitation_email",
    "resolve_invitation_sender",
    "send_invitation_email",
]

#: The authenticated application base URL the accept link resolves against.
#: Overridable per environment; defaults to the approved platform surface.
APP_BASE_URL = os.environ.get(
    "CARBONTALLY_APP_BASE_URL", "https://carbontally.co.uk"
)

#: Only a sender in this status may be used as a From address (D19 §13).
_VERIFIED_SENDER_STATUS = "verified"


def invitation_accept_url(token: str) -> str:
    """The single-use acceptance link for an invitation token."""
    return f"{APP_BASE_URL.rstrip('/')}/accept-invitation?token={token}"


def parse_invitation_expiry(value: Any) -> Optional[datetime]:
    """Best-effort ISO-8601 → aware datetime (repository rows carry ISO strings)."""
    if value is None or isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def describe_invitation(
    invitation: dict, *, include_accept_url: bool = False, redact_token: bool = False
) -> dict:
    """Add the DERIVED ``state`` (optionally the accept link) to a stored row.

    ``expired`` is computed here (pending + past ``expires_at``) and never read
    from storage — the durable column only holds pending/accepted/revoked.

    ``redact_token=True`` removes the single-use token from the projection. The
    CONSULTANT plane uses this: PD-1A states the consultant never receives the
    invitation token (the invitee receives it by email); the client's own
    owner/admin may see their organisation's invitation link.
    """
    view = dict(invitation)
    view["state"] = resolve_invitation_state(
        invitation.get("status"),
        parse_invitation_expiry(invitation.get("expires_at")),
    )
    if redact_token:
        view.pop("token", None)
        view.pop("accept_url", None)
        return view
    if include_accept_url and invitation.get("token"):
        view["accept_url"] = invitation_accept_url(invitation["token"])
    return view


def _role_label(role: Optional[str]) -> str:
    labels = {
        "owner": "an owner",
        "admin": "an administrator",
        "member": "a member",
        "viewer": "a viewer",
    }
    return labels.get((role or "").strip().lower(), "a team member")


def render_invitation_email(
    *,
    brand_name: str,
    organization_name: str,
    role: Optional[str],
    accept_url: str,
    footer: Optional[str] = None,
) -> tuple[str, str]:
    """Render the (subject, html) of a client-user invitation email.

    Pure/synchronous so it can be unit-tested without a mail transport.
    """
    org = (organization_name or "").strip() or "the organisation"
    subject = f"You have been invited to {org}"
    heading = f"Join {org}"
    body_html = (
        f"<p>You have been invited to join <strong>{org}</strong> as "
        f"{_role_label(role)} on {brand_name}.</p>"
        "<p>This invitation is single-use and expires automatically. If you "
        "were not expecting it you can safely ignore this email.</p>"
        f'<p><a href="{accept_url}">Accept your invitation</a></p>'
        f'<p style="word-break:break-all;color:#666">{accept_url}</p>'
    )
    return subject, render_simple_html(
        brand_name=brand_name,
        heading=heading,
        body_html=body_html,
        footer=footer,
    )



async def _resolve_brand(repos: Any, firm_id: Optional[str]) -> BrandContext:
    """Resolve the inviting party's brand (D21). No authorization here."""
    if not firm_id:
        return default_brand_context()
    branding = await repos.consultants.get_branding(firm_id)
    profile = await repos.consultants.get_profile_by_id(firm_id)
    fallback = getattr(profile, "company_name", None) or ""
    return resolve_brand_context(branding, fallback)


async def resolve_invitation_sender(
    repos: Any, firm_id: Optional[str]
) -> Optional[str]:
    """A VERIFIED custom sender for the firm, or ``None`` (→ platform sender).

    Returns the bare address of the first ``verified`` sender the firm owns.
    An unverified/removed sender never becomes a From address.
    """
    if not firm_id:
        return None
    senders = await repos.whitelabel.list_senders(firm_id)
    for sender in senders:
        if getattr(sender, "status", None) != _VERIFIED_SENDER_STATUS:
            continue
        address = (getattr(sender, "email", "") or "").strip()
        if not address:
            continue
        domain = (getattr(sender, "domain", None) or "").strip()
        if not domain:
            continue
        try:
            # Validate against the sender's OWN domain (D19 §13) and reject
            # header-injection / malformed values before they reach delivery.
            return normalise_email_sender(address, allowed_domains={domain})
        except ValueError:
            continue
    return None


async def send_invitation_email(
    repos: Any,
    *,
    to_email: str,
    organization_name: str,
    role: Optional[str],
    token: str,
    firm_id: Optional[str] = None,
    settings_repo: Any = None,
) -> tuple[bool, str]:
    """Compose and deliver a client-user invitation email.

    Returns ``(delivered, reason)`` — never raises for a delivery failure, so an
    invitation row is still created truthfully even when mail is not configured
    (the caller records the honest ``email_delivered`` outcome).
    """
    brand = await _resolve_brand(repos, firm_id)
    from_email = await resolve_invitation_sender(repos, firm_id)
    subject, html = render_invitation_email(
        brand_name=brand.display_name,
        organization_name=organization_name,
        role=role,
        accept_url=invitation_accept_url(token),
        footer=brand.footer_text,
    )
    if settings_repo is None:
        settings_repo = getattr(repos, "settings", None)
    return await send_transactional_email(
        to_email=to_email,
        subject=subject,
        html=html,
        from_email=from_email,
        settings_repo=settings_repo,
    )
