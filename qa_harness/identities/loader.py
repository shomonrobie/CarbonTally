"""Deterministic loader for the complete demo identity population.

The demo identities are generated from a fixed email scheme (see
``tools/seed_investor_demo/DEMO_IDENTITIES.md``), so the full list is
reproducible without contacting the database:

* customer owner/admin/member/viewer: ``{role}.demo{N:04d}``  N = 1..50
* client owners:                      ``client.owner.demo{C:04d}.{K}``
* consultants:                        ``consultant.demo{C:04d}``
* PE manager/staff:                   ``pe-manager-{E}.demo`` / ``pe-staff-{E}.demo``
* internal staff:                     ``{role}.demo``
* legacy demo fixtures:               ``{role}@demo.carbontally.local`` (11)
* OHD audit accounts:                 ``ohd.{owner|admin|member|viewer|consultant}.{a|b}@test.carbontally.local``
* system/selftest fixtures:           enumerated constants (non-demo domains)

Demo identities are exactly the ``@demo.carbontally.local`` population (1183
live-verified; one shared password). Audit/fixture identities at other
domains are modelled for completeness but are NEVER authenticated with the
demo password. No password is ever stored on :class:`Identity`; the shared
demo password is resolved at authentication time by
:mod:`qa_harness.core.credentials` (environment override, then the
gitignored ``.local-demo-credentials.md`` file).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

DEMO_DOMAIN = "demo.carbontally.local"
TEST_DOMAIN = "test.carbontally.local"
SELFTEST_DOMAIN = "rev2-selftest.test"

# Live-verified identity classes (read-only check of auth.users, 2026-08-24):
#   @demo.carbontally.local  1183 users  — every demo actor, one shared password
#   @test.carbontally.local     7 users  — OHD audit (6) + Cline probe (1); NOT demo
#   @rev2-selftest.test         2 users  — selftest system accounts; NOT demo
# There are NO users at the bare @carbontally.local domain.

# The 11 legacy fixture accounts that exist at the demo domain (pre-date the
# investor demo; authenticate with the shared demo password).
LEGACY_DEMO_LOCALS: Sequence[str] = (
    "owner", "admin", "member", "viewer", "consultant",
    "consultant-member", "entity-staff", "operator", "qc",
    "reviewer", "staff-admin",
)

# OHD audit accounts at the test domain (separate credentials — never demo).
OHD_AUDIT_LOCALS: Sequence[str] = (
    "ohd.owner.a", "ohd.owner.b", "ohd.admin.a",
    "ohd.member.a", "ohd.viewer.a", "ohd.consultant",
)

# Non-demo system/fixture accounts at other domains.
SYSTEM_FIXTURE_EMAILS: Sequence[str] = (
    "cline.con.probe@test.carbontally.local",
    "rv2.new1787494916@rev2-selftest.test",
    "rv2.owner1787494916@rev2-selftest.test",
)

HARNESS_ROOT = Path(__file__).resolve().parent.parent


def resolve_manifest_path(manifest: str) -> Path:
    """Resolve an identity-manifest path relative to the harness root.

    ``config.identity.manifest`` is written relative to ``qa_harness/``
    (e.g. ``../tools/seed_investor_demo/demo_manifest.json``); the manifest
    itself lives in the CarbonTally repo (gitignored — never committed).
    """
    path = Path(manifest)
    if path.is_absolute():
        return path
    return (HARNESS_ROOT / path).resolve()

# Client counts per consultant firm (K_C). From the investor demo dataset:
# each of the 50 consultants has a portfolio of 5–30 client orgs (total 911).
# The seeder assigns deterministic counts; this table encodes the documented
# distribution used by tools/seed_investor_demo (5 clients + per-consultant
# growth to a total of 911 across 50 firms).
#
# The seeder's exact per-consultant distribution is derived at seed time; the
# harness conservatively generates the MAXIMUM documented portfolio (30 per
# consultant) and, when a manifest file is available, uses the manifest's
# representative entries as ground truth for sampling.
_CLIENT_COUNT_DEFAULT = 30
_TOTAL_CLIENTS_DOCUMENTED = 911


@dataclass(frozen=True)
class Identity:
    """One demo identity. Immutable; never carries a password."""

    email: str
    role_key: str            # matches config/roles.yaml keys
    persona: str             # owner | admin | member | viewer | client_owner | consultant | pe_manager | pe_staff | operator | reviewer | qc | staff_admin | system_admin | legacy
    org: str = ""            # organization name or identifier (empty for internal staff)
    org_index: int = 0       # deterministic org index (1..50) for direct customer orgs
    consultant_index: int = 0
    client_number: int = 0
    entity_index: int = 0    # 1..3 for PE identities
    landing_route: str = ""
    workspace: str = ""
    representative: bool = False   # True for the documented representative set
    tags: List[str] = field(default_factory=list)

    @property
    def username(self) -> str:
        return self.email.split("@")[0]

    @property
    def domain(self) -> str:
        return self.email.split("@")[1]

    @property
    def is_demo(self) -> bool:
        """True when the identity authenticates with the shared demo password."""
        return self.email.endswith(f"@{DEMO_DOMAIN}")


def _landing(workspace: str) -> str:
    return {  # per DEMO_IDENTITIES.md
        "customer": "/home",
        "consultant": "/consultant",
        "pe": "/ops",
        "ops": "/ops",
    }.get(workspace, "")


def _identity(email: str, persona: str, *, org: str = "", org_index: int = 0,
              consultant_index: int = 0, client_number: int = 0,
              entity_index: int = 0, representative: bool = False,
              tags: Optional[Sequence[str]] = None) -> Identity:
    role_map = {
        "owner": "customer_owner",
        "admin": "customer_admin",
        "member": "customer_member",
        "viewer": "customer_viewer",
        "client_owner": "client_owner",
        "consultant": "consultant",
        "pe_manager": "pe_manager",
        "pe_staff": "pe_staff",
        "operator": "internal_operator",
        "reviewer": "internal_reviewer",
        "qc": "internal_qc",
        "staff-admin": "staff_admin",
        "staff_admin": "staff_admin",
        "system-admin": "system_admin",
        "system_admin": "system_admin",
        "legacy": "legacy_fixture",
        "audit": "audit_fixture",
        "fixture": "system_fixture",
    }
    role_key = role_map.get(persona, "legacy_fixture")
    workspace_map = {
        "owner": "customer", "admin": "customer", "member": "customer",
        "viewer": "customer", "client_owner": "customer",
        "consultant": "consultant", "pe_manager": "pe", "pe_staff": "pe",
        "operator": "ops", "reviewer": "ops", "qc": "ops",
        "staff-admin": "ops", "staff_admin": "ops",
        "system-admin": "ops", "system_admin": "ops",
        "legacy": "mixed", "audit": "mixed", "fixture": "mixed",
    }
    workspace = workspace_map.get(persona, "mixed")
    return Identity(
        email=email,
        role_key=role_key,
        persona=persona,
        org=org,
        org_index=org_index,
        consultant_index=consultant_index,
        client_number=client_number,
        entity_index=entity_index,
        landing_route=_landing(workspace),
        workspace=workspace,
        representative=representative,
        tags=list(tags or []),
    )


# Live per-consultant client counts (read-only capture of auth.users,
# 2026-08-24): index = consultant 1..50, value = number of client-owner
# accounts (client numbers are contiguous 1..K per consultant). Sum = 911.
# This mirrors the investor-demo seeder's randomised 5..30 distribution
# exactly, so authenticated QA never selects a client owner that does not
# exist. It is not derived from secrets and may be refreshed the same way.
CLIENT_COUNTS_BY_CONSULTANT: Sequence[int] = (
    14, 10, 16, 27, 23, 24, 26, 18, 29, 12,
    25, 25, 25, 18, 17, 29, 12, 9, 16, 24,
    7, 24, 20, 23, 27, 22, 25, 18, 10, 17,
    17, 12, 5, 8, 29, 6, 30, 19, 15, 16,
    7, 23, 25, 28, 19, 23, 5, 13, 5, 14,
)


def _client_count_for(consultant_index: int, total: int = _TOTAL_CLIENTS_DOCUMENTED,
                      default: int = _CLIENT_COUNT_DEFAULT) -> int:
    """Per-consultant client count from the live-mirrored table (sum 911)."""
    if 1 <= consultant_index <= len(CLIENT_COUNTS_BY_CONSULTANT):
        return CLIENT_COUNTS_BY_CONSULTANT[consultant_index - 1]
    return default


def generate_full_population() -> List[Identity]:
    """Generate the complete deterministic demo identity population."""
    identities: List[Identity] = []

    def email(local: str) -> str:
        return f"{local}@{DEMO_DOMAIN}"

    # Direct customer orgs 1..50 (owner/admin/member/viewer).
    for n in range(1, 51):
        for persona in ("owner", "admin", "member", "viewer"):
            identities.append(
                _identity(
                    email(f"{persona}.demo{n:04d}"),
                    persona,
                    org=f"Direct Customer Org {n}",
                    org_index=n,
                )
            )

    # Consultants 1..50.
    for c in range(1, 51):
        identities.append(
            _identity(email(f"consultant.demo{c:04d}"), "consultant",
                      org=f"Consultant Firm {c}", consultant_index=c)
        )
        # Client owners for this consultant (deterministic K_C).
        k_count = _client_count_for(c)
        for k in range(1, k_count + 1):
            identities.append(
                _identity(
                    email(f"client.owner.demo{c:04d}.{k}"),
                    "client_owner",
                    org=f"Client Org {c}.{k}",
                    consultant_index=c,
                    client_number=k,
                    tags=["consultant_client"],
                )
            )

    # PE entities 1..3.
    for e in range(1, 4):
        identities.append(
            _identity(email(f"pe-manager-{e}.demo"), "pe_manager",
                      org=f"Processing Entity {e}", entity_index=e)
        )
        identities.append(
            _identity(email(f"pe-staff-{e}.demo"), "pe_staff",
                      org=f"Processing Entity {e}", entity_index=e)
        )

    # Internal staff.
    for persona, local in (
        ("operator", "operator"),
        ("reviewer", "reviewer"),
        ("qc", "qc"),
        ("staff-admin", "staff-admin"),
        ("system-admin", "system-admin"),
    ):
        identities.append(_identity(email(f"{local}.demo"), persona, org="CarbonTally"))

    # Legacy fixture accounts (11) — live-verified at the DEMO domain. They
    # pre-date the investor demo, are part of the 1183 @demo population and
    # authenticate with the shared demo password.
    for local in LEGACY_DEMO_LOCALS:
        identities.append(
            _identity(email(local), "legacy", tags=["legacy", "demo_fixture"])
        )
    # OHD audit accounts (6) at the TEST domain — separate credentials; never
    # part of the demo population and never authenticated with the shared
    # demo password.
    for local in OHD_AUDIT_LOCALS:
        identities.append(
            _identity(f"{local}@{TEST_DOMAIN}", "audit", tags=["ohd_audit"])
        )
    # System/selftest fixture accounts (3) at other domains — not demo.
    for mail in SYSTEM_FIXTURE_EMAILS:
        identities.append(
            _identity(mail, "fixture", tags=["system_fixture"])
        )

    return identities


# Representative set documented in DEMO_IDENTITIES.md ("persona quick-reference").
REPRESENTATIVE_EMAILS: Dict[str, str] = {
    "customer_owner": "owner.demo0001@demo.carbontally.local",
    "customer_admin": "admin.demo0001@demo.carbontally.local",
    "customer_member": "member.demo0001@demo.carbontally.local",
    "customer_viewer": "viewer.demo0001@demo.carbontally.local",
    "client_owner": "client.owner.demo0001.1@demo.carbontally.local",
    "consultant": "consultant.demo0001@demo.carbontally.local",
    "pe_manager": "pe-manager-1.demo@demo.carbontally.local",
    "pe_staff": "pe-staff-1.demo@demo.carbontally.local",
    "internal_operator": "operator.demo@demo.carbontally.local",
    "internal_reviewer": "reviewer.demo@demo.carbontally.local",
    "internal_qc": "qc.demo@demo.carbontally.local",
    "staff_admin": "staff-admin.demo@demo.carbontally.local",
    "system_admin": "system-admin.demo@demo.carbontally.local",
}


class IdentityLoader:
    """Loads identities from the generated population and/or a manifest.

    ``manifest_path`` (optional) points at the gitignored
    ``tools/seed_investor_demo/demo_manifest.json`` representative subset.
    Identities from the manifest are merged by email; manifest entries mark
    ``representative=True``.
    """

    def __init__(self, manifest_path: Optional[Path] = None) -> None:
        self.manifest_path = Path(manifest_path) if manifest_path else None
        self._population: Optional[Dict[str, Identity]] = None

    def load(self) -> Dict[str, Identity]:
        if self._population is not None:
            return self._population
        by_email: Dict[str, Identity] = {
            identity.email: identity for identity in generate_full_population()
        }
        if self.manifest_path and self.manifest_path.exists():
            try:
                data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                entries = (
                    data.get("personas")
                    or data.get("identities")
                    or (data if isinstance(data, list) else [])
                )
                for entry in entries:
                    mail = entry.get("email", "")
                    if not mail:
                        continue
                    identity = by_email.get(mail)
                    if identity is None:
                        continue
                    landing = (
                        entry.get("landing") or entry.get("landing_route") or identity.landing_route
                    )
                    by_email[mail] = Identity(
                        email=identity.email,
                        role_key=identity.role_key,
                        persona=identity.persona,
                        org=entry.get("org") or identity.org,
                        org_index=identity.org_index,
                        consultant_index=identity.consultant_index,
                        client_number=identity.client_number,
                        entity_index=identity.entity_index,
                        landing_route=landing or identity.landing_route,
                        workspace=identity.workspace,
                        representative=True,
                        tags=list(identity.tags),
                    )
            except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover
                raise ValueError(f"invalid identity manifest {self.manifest_path}: {exc}")
        self._population = by_email
        return by_email

    def by_role(self, role_key: str) -> List[Identity]:
        return [i for i in self.load().values() if i.role_key == role_key]

    def representative(self) -> List[Identity]:
        """The documented representative set (13 personas)."""
        population = self.load()
        result = []
        for role_key, mail in REPRESENTATIVE_EMAILS.items():
            identity = population.get(mail)
            if identity is None:
                # Fall back to any identity of that role.
                matches = self.by_role(role_key)
                if matches:
                    identity = matches[0]
            if identity is not None:
                result.append(identity)
        return result


def load_identity_population(manifest_path: Optional[Path] = None) -> Dict[str, Identity]:
    """Convenience: load the full population (see :class:`IdentityLoader`)."""
    return IdentityLoader(manifest_path=manifest_path).load()


def parse_identity_scheme(identity_doc_text: str) -> Dict[str, object]:
    """Parse DEMO_IDENTITIES.md and return the documented scheme counts.

    Used by preflight to cross-check the generated population against the
    documented totals without touching the database.
    """
    counts: Dict[str, object] = {}
    text = identity_doc_text
    # More specific patterns are consumed first so overlapping substrings
    # (e.g. "client.owner.demo0001" also contains "owner.demo") are never
    # double-counted.
    for pattern, key in (
        (r"client\.owner\.demo", "client_owner"),
        (r"pe-manager-", "pe_manager"),
        (r"pe-staff-", "pe_staff"),
        (r"consultant\.demo", "consultant"),
        (r"owner\.demo", "customer_owner"),
        (r"admin\.demo", "customer_admin"),
        (r"member\.demo", "customer_member"),
        (r"viewer\.demo", "customer_viewer"),
    ):
        count = 0
        remaining: List[str] = []
        last = 0
        for match in re.finditer(pattern, text):
            count += 1
            remaining.append(text[last:match.start()])
            last = match.end()
        remaining.append(text[last:])
        text = "".join(remaining)
        counts[key] = count
    return counts
