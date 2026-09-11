"""Navigation / application-separation rules (spec §12, §17).

The harness must explicitly distinguish PUBLIC WEBSITE / CUSTOMER APP /
CONSULTANT WORKSPACE / PE WORKSPACE / INTERNAL OPERATIONS / ADMIN CONTROL
PLANE and detect incorrect role routing, wrong dashboards, inappropriate
navigation, internal users exposed to customer UI, PE users exposed to
customer UI, customer users exposed to internal controls, and public-only
features leaking into the authenticated application.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

WORKSPACES = [
    "public",
    "customer",
    "consultant",
    "pe",
    "ops",
    "admin",
]

# Documented landing route per workspace (from DEMO_IDENTITIES.md).
EXPECTED_LANDING = {
    "customer": "/home",
    "consultant": "/consultant",
    "pe": "/ops",
    "ops": "/ops",
    "admin": "/ops",
}


@dataclass
class NavigationRule:
    id: str
    rule: str
    severity: str = "P1"
    historical: str = ""


def build_navigation_rules() -> List[NavigationRule]:
    R = NavigationRule
    return [
        R("NAV-1", "Customers land on the customer dashboard (/home), never /onboarding "
          "(existing users must not be redirected to onboarding).", "P1", "AUTH-1"),
        R("NAV-2", "Consultants land on /consultant.", "P1", "AUTH-1"),
        R("NAV-3", "PE staff and internal staff land on /ops with the correct surface "
          "(entity-scoped for PE).", "P1", "AUTH-1"),
        R("NAV-4", "Customers must not see internal controls (retention, commercial, staff).", "P1", "AUTH-2"),
        R("NAV-5", "PE users must not be exposed to customer UI or customer org data.", "P0", "PE-1/SEC-3"),
        R("NAV-6", "Public-only features (visitor assistant, marketing pages) must not appear "
          "as the authenticated messaging mechanism.", "P2", "AI-2/MSG-5"),
        R("NAV-7", "A customer calling staff surfaces (e.g. /api/v3/ops/me) must be denied "
          "(403) and handled gracefully, not crash the shell.", "P1", "AUTH-2"),
        R("NAV-8", "Role-probe 403 noise must not break page rendering (console noise is "
          "tracked but not a page failure).", "P3", "AUTH-3"),
        R("NAV-9", "The ops shell must differentiate PE workspace from internal operations "
          "workspace.", "P1", "D20"),
    ]


class NavigationRuleCatalog:
    def __init__(self, rules: Optional[List[NavigationRule]] = None) -> None:
        self.rules = rules or build_navigation_rules()

    def check_landing(self, workspace: str, observed_route: str) -> Dict[str, object]:
        expected = EXPECTED_LANDING.get(workspace)
        ok = expected is not None and observed_route == expected
        return {
            "workspace": workspace,
            "expected_landing": expected,
            "observed_route": observed_route,
            "ok": ok,
            "severity": "P1" if not ok else None,
        }
