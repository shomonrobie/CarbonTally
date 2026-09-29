"""Platform transactional-email **sender** configuration (CT-FINAL-01 notifications).

The ratified scope for notifications separates three things that must never be
conflated:

====================  ================================================================
``actor``             the authenticated user (or system) that performed the action
``acting_for``        the organisation/client/entity the actor acted on behalf of
                      (consultant operating model) — optional
``sender``            the From address of the outgoing platform email
====================  ================================================================

The sender is **platform configuration**, not the actor's mailbox: an email sent
because "Alice approved Acme's invoice" is sent by the CarbonTally notification
address, and the app records Alice as the actor.  D19 §13 fixes the boundary —
CarbonTally is not an email provider, so the platform sender may only be an
address on the platform domain; a customer/consultant domain requires an
externally verified sender row (``consultant_senders``) and is out of scope here.

No secret is ever handled by this module: it deals only with From display
addresses.  ``RESEND_API_KEY`` (the delivery credential) is never read, returned
or logged here.
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, Optional

#: The default CarbonTally transactional sender (unchanged behaviour when no
#: admin configuration exists).
DEFAULT_SENDER = "CarbonTally <notifications@carbontally.co.uk>"

#: ``system_settings.setting_key`` used for the notification configuration row.
NOTIFICATION_SENDER_SETTING_KEY = "platform_notifications"

#: Domains the platform configuration may send from.  CarbonTally-owned only —
#: customer/consultant domains are governed by the verified-sender mechanism
#: (D19 §13), never by this setting.
PLATFORM_EMAIL_DOMAINS: frozenset[str] = frozenset({"carbontally.co.uk"})

#: Characters that must never appear: header-injection and multi-recipient forms.
_FORBIDDEN = ("\r", "\n", "\t", ",", ";", ":", '"')

#: A bare address or a ``Display Name <address>`` form.
_ADDRESS_RE = re.compile(
    r"^(?P<name>[^<>@,]*)<(?P<addr>[^<>@,\s]+@[^<>@,\s]+)>$"
    r"|^(?P<bare>[^<>@,\s]+@[^<>@,\s]+)$"
)


def normalise_email_sender(
    raw: Optional[str],
    *,
    allowed_domains: Iterable[str] = PLATFORM_EMAIL_DOMAINS,
) -> Optional[str]:
    """Validate and canonicalise a configured sender address.

    Returns the canonical ``"Display Name <address>"`` (or the bare address when
    no display name was supplied), ``None`` when nothing was configured.

    Raises ``ValueError`` for anything unusable — an empty/invalid address, a
    header-injection attempt, a multi-address value, or a domain outside
    ``allowed_domains``.  A rejected value must never silently become a sender.
    """
    if raw is None:
        return None
    candidate = str(raw).strip()
    if not candidate:
        return None
    for char in _FORBIDDEN:
        if char in candidate:
            raise ValueError(
                "email_sender must be a single address with no separators or "
                "control characters"
            )
    match = _ADDRESS_RE.match(candidate)
    if match is None:
        raise ValueError("email_sender must be an address or 'Name <address>'")
    address = (match.group("addr") or match.group("bare") or "").strip()
    if "@" not in address:
        raise ValueError("email_sender must contain an '@'")
    local, _, domain = address.rpartition("@")
    if not local or not domain or "." not in domain:
        raise ValueError("email_sender must be a fully qualified email address")
    if domain.lower() not in {d.lower() for d in allowed_domains}:
        raise ValueError(
            "email_sender domain is not a CarbonTally platform domain; "
            "customer/consultant domains require an externally verified sender"
        )
    name = (match.group("name") or "").strip()
    if name:
        return f"{name} <{address}>"
    return address


def resolve_email_sender(
    configured: Optional[str],
    *,
    allowed_domains: Iterable[str] = PLATFORM_EMAIL_DOMAINS,
) -> str:
    """Return the effective sender: the configured value, else the default.

    Never raises: a missing or malformed configuration falls back to
    ``DEFAULT_SENDER`` so notification delivery degrades to the approved default
    rather than failing (or, worse, sending from an unvalidated address).
    """
    try:
        normalised = normalise_email_sender(configured, allowed_domains=allowed_domains)
    except ValueError:
        return DEFAULT_SENDER
    return normalised or DEFAULT_SENDER


def describe_email_sender(
    configured: Optional[str],
    *,
    allowed_domains: Iterable[str] = PLATFORM_EMAIL_DOMAINS,
) -> Dict[str, object]:
    """Describe the effective sender **without** touching any credential.

    Returns the effective sender, whether it is the platform default, and
    whether platform configuration is in force.  The delivery credential
    (``RESEND_API_KEY``) is never read, returned or logged by this module.
    """
    effective = resolve_email_sender(configured, allowed_domains=allowed_domains)
    return {
        "email_sender": effective,
        "is_default": effective == DEFAULT_SENDER,
        "configured": effective != DEFAULT_SENDER,
        "platform_domains": sorted({d.lower() for d in allowed_domains}),
    }


def notification_identity(
    *,
    actor_email: Optional[str],
    acting_for: Optional[str] = None,
    configured_sender: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Build the notification identity triple used by producers.

    Preserves the actor and the acting-for context while pinning the From
    address to the platform sender — the actor's own mailbox is never used as
    the sender (that would misattribute the email and bypass the D19 boundary).
    """
    sender = resolve_email_sender(configured_sender)
    return {
        "actor": actor_email,
        "acting_for": acting_for,
        "sender": sender,
    }
