"""Consultant branding domain — white-label presentation model (D21).

``consultant_profiles`` is the source of truth for a Consultant Firm's
branding configuration (D21.1). This module adds the pure presentation model on
top of that row: the editable branding projection and the resolved brand
context consumed by the API / frontend / report surfaces.

Presentation modes (D21.10 — mutually exclusive; white-label wins):

    carbon_tally   default — no branding configured / Managed Service
    consultant     ``white_label_enabled`` → CarbonTally invisible
    co_branded     ``co_branding_enabled`` (and white-label disabled)

No tenancy model is introduced. The branding belongs to the existing
``consultant_profiles`` row; ``organizations`` remains the data-tenancy anchor.
This is a presentation/commercial relationship layer only.

Security note (D21.4 / D21.14): this module is pure — it never authorizes.
Callers must already hold an authenticated, consultant-firm-scoped context.
The brand is always derived from the server-verified relationship, never from a
client-supplied ``consultant_id``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

#: CarbonTally's default presentation (the fallback for every surface — used
#: when no consultant branding applies or the caller is a Direct Customer).
CARBON_TALLY_BRAND: dict[str, Any] = {
    "kind": "carbon_tally",
    "display_name": "CarbonTally",
    "logo_url": None,
    "primary_color": "#0f766e",
    "secondary_color": "#0e7490",
    "footer_text": None,
    "email_from": None,
    "website": None,
    "client_portal_url": None,
    "support_email": None,
    "support_phone": None,
    "support_hours": None,
    "co_branded_with_carbontally": False,
}

BRAND_KINDS: tuple[str, ...] = ("carbon_tally", "consultant", "co_branded")


@dataclass(frozen=True, slots=True)
class ConsultantBranding:
    """The editable branding configuration of a Consultant Firm.

    A projection of the real ``consultant_profiles`` branding columns (the
    profile row is the source of truth). CarbonTally-controlled commercial
    fields (``partner_status`` / ``partner_tier`` / ``commission_rate``) are
    deliberately NOT part of the self-service branding surface.
    """

    profile_id: str
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    footer_text: Optional[str] = None
    email_from: Optional[str] = None
    website: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    support_hours: Optional[str] = None
    client_portal_url: Optional[str] = None
    white_label_enabled: bool = False
    co_branding_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BrandContext:
    """The resolved brand a customer-facing surface should present."""

    kind: str
    display_name: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    footer_text: Optional[str] = None
    email_from: Optional[str] = None
    website: Optional[str] = None
    client_portal_url: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    support_hours: Optional[str] = None
    co_branded_with_carbontally: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_brand_context() -> BrandContext:
    """The CarbonTally fallback presentation (D21.16 backward compatibility)."""
    return BrandContext(**CARBON_TALLY_BRAND)


def default_branding_dict(profile_id: str) -> dict[str, Any]:
    """A zero-config branding projection (every flag off, no branding set)."""
    branding = ConsultantBranding(profile_id=profile_id)
    return branding.to_dict()


def resolve_brand_context(
    branding: Optional[ConsultantBranding],
    fallback_name: str,
) -> BrandContext:
    """Resolve a firm's configured branding to a presentation brand.

    Pure function — no authorization lives here. The caller must already hold
    an authorized consultant context (the branding is the authenticated firm's
    OWN branding, never another firm's).

    * no branding / no flags        → CarbonTally fallback (D21.16)
    * ``white_label_enabled``       → consultant-only presentation
    * ``co_branding_enabled``       → consultant + CarbonTally presentation
    """
    if branding is None:
        return default_brand_context()

    display_name = (branding.brand_name or "").strip() or (fallback_name or "").strip() or "Consultant"

    if branding.white_label_enabled:
        kind = "consultant"
        co_branded = False
    elif branding.co_branding_enabled:
        kind = "co_branded"
        co_branded = True
    else:
        return default_brand_context()

    return BrandContext(
        kind=kind,
        display_name=display_name,
        logo_url=branding.logo_url,
        primary_color=branding.primary_color or CARBON_TALLY_BRAND["primary_color"],
        secondary_color=branding.secondary_color or CARBON_TALLY_BRAND["secondary_color"],
        footer_text=branding.footer_text,
        email_from=branding.email_from,
        website=branding.website,
        client_portal_url=branding.client_portal_url,
        support_email=branding.support_email,
        support_phone=branding.support_phone,
        support_hours=branding.support_hours,
        co_branded_with_carbontally=co_branded,
    )
