"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — product modes and firm entitlement
(F-5, F-6, F-9; PO-1, PO-3B, PO-4, PO-5).

Source of truth: ``docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md``

* §5.2  the three product modes (STANDARD / CO-BRANDED / WHITE-LABEL);
* §6.1  the five boundaries — PRODUCT MODE, COMMERCIAL ENTITLEMENT, CONSULTANT
        RBAC, CLIENT ACCESS PROFILE, CARBONTALLY AUTHORITY — must not collapse;
* §6.2  the mandatory server-side resolution order (fail closed if nothing is
        configured);
* §6.5  FM-1..FM-5 mandatory failure modes (never assume enabled; the MODE wins
        over a contradicting stored flag; fail closed when the service is
        unavailable);
* §12.2 brand availability by mode (BR-5 — a stored white-label flag that
        contradicts the mode is CAPPED, and never destroyed).

This module is PURE. It resolves what a firm IS (mode) and what that mode
ENTITLES (client plane, managed profile, custom domain, white-label
presentation). It never authorizes an actor and never grants capability:
entitlement and capability are different axes (§6.1, INV-G).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

MODE_STANDARD = "standard"
MODE_CO_BRANDED = "co_branded"
MODE_WHITE_LABEL = "white_label"

PRODUCT_MODES: tuple[str, ...] = (MODE_STANDARD, MODE_CO_BRANDED, MODE_WHITE_LABEL)

_ALIASES: dict[str, str] = {
    "standard": MODE_STANDARD,
    "co_branded": MODE_CO_BRANDED,
    "co-branded": MODE_CO_BRANDED,
    "cobranded": MODE_CO_BRANDED,
    "white_label": MODE_WHITE_LABEL,
    "white-label": MODE_WHITE_LABEL,
    "whitelabel": MODE_WHITE_LABEL,
}


def normalise_mode(value: Optional[str]) -> str:
    """Coerce a stored mode to a known value — FAIL CLOSED to STANDARD.

    An unknown/absent mode resolves to ``standard`` (the least-entitled mode),
    never to white-label (§6.5 FM-1).
    """
    key = (value or "").strip().lower()
    return _ALIASES.get(key, MODE_STANDARD)


def derive_mode_from_flags(
    white_label_enabled: bool, co_branding_enabled: bool
) -> str:
    """Backward-compatible derivation from the legacy D21 boolean flags.

    Used ONLY when ``commercial_mode`` is not stored (pre-migration rows / a
    repository projection that predates the column). It reproduces the D21
    "white-label wins" precedence exactly so existing firms are unchanged.
    """
    if white_label_enabled:
        return MODE_WHITE_LABEL
    if co_branding_enabled:
        return MODE_CO_BRANDED
    return MODE_STANDARD


def resolve_mode(
    commercial_mode: Optional[str],
    white_label_enabled: bool = False,
    co_branding_enabled: bool = False,
) -> str:
    """Resolve the firm's effective mode.

    IMPL-3 / FM-2 / BR-5 — the stored MODE is authoritative: when a valid
    ``commercial_mode`` is present it WINS over the legacy boolean flags, which
    are then merely capped at presentation/enforcement time. The stored flags
    are never destroyed. When no mode is stored we fall back to the ratified
    D21 derivation so existing firms keep their current presentation.
    """
    if commercial_mode is not None and commercial_mode.strip() != "":
        return normalise_mode(commercial_mode)
    return derive_mode_from_flags(white_label_enabled, co_branding_enabled)


@dataclass(frozen=True, slots=True)
class FirmEntitlements:
    """What a product mode entitles a firm to (§5.2, §6.1, §8.4, §12.2)."""

    mode: str
    #: Plane C exists at all for this firm (§8.4, MUSTNOT-5).
    client_plane: bool
    #: MANAGED profile is permitted (§8.4 / PO-4: Co-Branded + White-Label only).
    managed_profile: bool
    #: A custom domain may be created/activated (§12.2: White-Label only).
    custom_domain: bool
    #: A white-label (CarbonTally-absent) client experience is permitted (PO-3B).
    white_label_presentation: bool
    #: A co-branded experience is permitted.
    co_branded_presentation: bool
    #: The firm's brand may appear on CLIENT surfaces (PO-3A firm-level only).
    firm_brand_on_client_surfaces: bool


_MATRIX: dict[str, dict[str, bool]] = {
    MODE_STANDARD: {
        "client_plane": False,
        "managed_profile": False,
        "custom_domain": False,
        "white_label_presentation": False,
        "co_branded_presentation": False,
        "firm_brand_on_client_surfaces": False,
    },
    MODE_CO_BRANDED: {
        "client_plane": True,
        "managed_profile": True,
        "custom_domain": False,
        "white_label_presentation": False,
        "co_branded_presentation": True,
        "firm_brand_on_client_surfaces": True,
    },
    MODE_WHITE_LABEL: {
        "client_plane": True,
        "managed_profile": True,
        "custom_domain": True,
        "white_label_presentation": True,
        "co_branded_presentation": False,
        "firm_brand_on_client_surfaces": True,
    },
}


def resolve_entitlements(mode: Optional[str]) -> FirmEntitlements:
    """The entitlement set of a mode. Unknown modes resolve to STANDARD."""
    resolved = normalise_mode(mode)
    return FirmEntitlements(mode=resolved, **_MATRIX[resolved])


def _mode(
    commercial_mode: Optional[str],
    white_label_enabled: bool,
    co_branding_enabled: bool,
) -> str:
    return resolve_mode(commercial_mode, white_label_enabled, co_branding_enabled)


def client_plane_available(
    commercial_mode: Optional[str],
    white_label_enabled: bool = False,
    co_branding_enabled: bool = False,
) -> bool:
    """Whether Plane C is routable for a firm (§8.4, MUSTNOT-5).

    STANDARD firms expose NO client login/portal plane — ENFORCED, not hidden.
    """
    return resolve_entitlements(
        _mode(commercial_mode, white_label_enabled, co_branding_enabled)
    ).client_plane


def managed_profile_available(
    commercial_mode: Optional[str],
    white_label_enabled: bool = False,
    co_branding_enabled: bool = False,
) -> bool:
    """PO-4 — MANAGED is available in Co-Branded and White-Label only."""
    return resolve_entitlements(
        _mode(commercial_mode, white_label_enabled, co_branding_enabled)
    ).managed_profile


def custom_domain_available(
    commercial_mode: Optional[str],
    white_label_enabled: bool = False,
    co_branding_enabled: bool = False,
) -> bool:
    """PO-4 / §12.2 — a custom domain is available in WHITE-LABEL mode only."""
    return resolve_entitlements(
        _mode(commercial_mode, white_label_enabled, co_branding_enabled)
    ).custom_domain
