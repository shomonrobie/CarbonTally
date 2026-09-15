"""Phase 8 B4 — `DM-6` drill-down exposure rule (pure, no I/O).

The **ratified** decision `DM-6` fixes drill-down depth per role:

* **Owner/Admin** — full drill-down;
* **Viewer** — controlled drill-down;
* **Consultant** — bounded drill-down;
* **Processing Entity / cross-tenant** — denied.

This module turns that policy into one testable matrix and one redaction step, so
no route has to invent its own field list.

Implementation decisions (explicit, conservative, never wider than `DM-6`):

* A customer **Member** is not named by `DM-6`. Members are therefore treated as
  *controlled* (the same depth as Viewer) rather than full — least privilege, and
  consistent with the B3 posture where a member reads values but does not write.
* Anyone unrecognised, any Processing-Entity user and any CarbonTally internal
  staff user is **denied**, matching B3's read boundary (staff cannot read customer
  disclosures).
* Redaction is a **fail-closed allowlist**: below ``FULL`` only *structural* keys
  (and, at ``CONTROLLED``, recognised measurement keys) are returned. A new
  upstream column is therefore **never** exposed by default — it must be added to
  the allowlist deliberately. ``_DOCUMENT_KEY_MARKERS`` records the families that
  are never exposed below ``FULL`` (raw document/storage references, hashes, URLs).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from domain.disclosure import DisclosureViolation

#: Drill-down depths (most to least revealing).
DEPTH_FULL = "FULL"
DEPTH_CONTROLLED = "CONTROLLED"
DEPTH_BOUNDED = "BOUNDED"
DEPTH_DENIED = "DENIED"

DEPTHS: tuple[str, ...] = (DEPTH_FULL, DEPTH_CONTROLLED, DEPTH_BOUNDED, DEPTH_DENIED)

#: Roles recognised as a customer organisation Owner/Admin (full).
_FULL_ROLES: tuple[str, ...] = ("owner", "admin")
#: Roles treated as controlled (structural + amounts, no document/storage references).
#: ``user`` is this codebase's generic organisation-member role name
#: (``AuthUser.role_name`` for an ordinary member).
_CONTROLLED_ROLES: tuple[str, ...] = ("member", "viewer", "user")
#: Roles treated as bounded (structural only: no amounts, no document references).
_BOUNDED_ROLES: tuple[str, ...] = ("consultant", "consultant_member", "consultant_team_member")

#: Key families never exposed below FULL (raw document/storage pointers).
_DOCUMENT_KEY_MARKERS: tuple[str, ...] = (
    "document",
    "storage",
    "path",
    "bucket",
    "url",
    "file",
    "hash",
    "sha",
    "signed",
)
#: Key families additionally hidden at BOUNDED (quantities, amounts, factors).
_QUANTITY_KEY_MARKERS: tuple[str, ...] = (
    "amount",
    "value",
    "quantity",
    "qty",
    "unit",
    "factor",
    "kg",
    "co2",
    "co2e",
    "emission",
    "price",
    "cost",
    "total",
)

#: Keys that are always structurally safe to return at any non-denied depth.
_STRUCTURAL_KEYS: tuple[str, ...] = ("id", "line_number", "description", "notes")


@dataclass(frozen=True)
class ExposureRule:
    """The resolved exposure for one caller."""

    role: str
    depth: str
    allow_lines: bool
    allow_amounts: bool
    allow_document_refs: bool
    allow_download: bool
    rationale: str

    @property
    def denied(self) -> bool:
        return self.depth == DEPTH_DENIED


def _normalise_role(role: Optional[str]) -> str:
    normalised = (role or "").lower().strip()
    if normalised.startswith("org_"):
        normalised = normalised[len("org_") :]
    return normalised


def exposure_for_role(
    role: Optional[str],
    *,
    is_entity_staff: bool = False,
    is_internal_staff: bool = False,
) -> ExposureRule:
    """Resolve the ratified `DM-6` exposure for a caller.

    Processing-Entity users and CarbonTally internal staff are always denied: the
    first by the `DM-6` \"denied\" clause, the second by the B3 read boundary.
    """
    if is_entity_staff:
        return ExposureRule(
            "pe_staff", DEPTH_DENIED, False, False, False, False,
            "DM-6: Processing Entity users are denied drill-down access",
        )
    if is_internal_staff:
        return ExposureRule(
            "staff", DEPTH_DENIED, False, False, False, False,
            "CarbonTally staff cannot read customer disclosure detail (B3 boundary)",
        )

    name = _normalise_role(role)
    if name in _FULL_ROLES:
        return ExposureRule(
            name, DEPTH_FULL, True, True, True, True,
            "DM-6: organisation Owner/Admin have full drill-down",
        )
    if name in _CONTROLLED_ROLES:
        return ExposureRule(
            name, DEPTH_CONTROLLED, True, True, False, False,
            "DM-6: Viewer is controlled; a Member is treated as controlled (least privilege)",
        )
    if name in _BOUNDED_ROLES:
        return ExposureRule(
            name, DEPTH_BOUNDED, True, False, False, False,
            "DM-6: Consultant drill-down is bounded (structural evidence only)",
        )
    return ExposureRule(
        name or "unknown", DEPTH_DENIED, False, False, False, False,
        "Unrecognised role: drill-down denied by default",
    )


def assert_drilldown_allowed(rule: ExposureRule, *, what: str = "evidence drill-down") -> None:
    """Raise (never return a partial answer) when `DM-6` denies drill-down."""
    if rule.denied:
        raise DisclosureViolation(
            f"DM-6: {what} is denied for role {rule.role!r}"
        )


def _is_exposed(key: str, rule: ExposureRule) -> bool:
    """Fail-closed: below FULL only allowlisted key families are returned."""
    lowered = key.lower()
    if rule.depth == DEPTH_FULL:
        return True
    if lowered in _STRUCTURAL_KEYS:
        return True
    # Document/storage references are never exposed below FULL, even if a marker
    # would otherwise match the measurement allowance.
    if any(marker in lowered for marker in _DOCUMENT_KEY_MARKERS):
        return False
    if rule.depth == DEPTH_CONTROLLED and any(
        marker in lowered for marker in _QUANTITY_KEY_MARKERS
    ):
        return True
    return False


def redact_line(row: Mapping[str, Any] | Any, rule: ExposureRule) -> dict:
    """Project one evidence line for the caller's depth.

    Non-allowlisted keys are **removed** (not nulled) so that a response cannot
    leak the existence or shape of a redacted field, and ``redacted_fields``
    records which were withheld so the UI can explain itself honestly.
    """
    data = dict(row)
    if rule.depth == DEPTH_FULL:
        return dict(data)
    kept: dict[str, Any] = {}
    hidden: list[str] = []
    for key, value in data.items():
        if _is_exposed(str(key), rule):
            kept[key] = value
        else:
            hidden.append(str(key))
    if hidden:
        kept["redacted_fields"] = sorted(hidden)
    return kept


def project_lines(rows: Iterable[Mapping[str, Any] | Any], rule: ExposureRule) -> list[dict]:
    assert_drilldown_allowed(rule)
    return [redact_line(row, rule) for row in rows]
