"""Phase 8 B4 — narrative overlay and finalisation domain model (pure, no I/O).

Implements the **already-ratified** B4 policy spine (contract
``CARBONTALLY_PHASE8_B4_IMPLEMENTATION_CONTRACT_20260913.md`` §§7–8):

* ``A1`` — narrative is requirement-bound; Owner/Admin authoring; no report-wide path.
* ``A3`` — **no arbitrary character limits**; plain text; only real content required.
* ``P3`` — narrative can never touch calculated values, provenance or factor data.
* ``DM-5`` — finalisation gates on unresolved ``REQUIRED``;
  ``CUSTOMER_INPUT_REQUIRED`` **blocks**, ``NOT_SUPPORTED`` is **surfaced**,
  and the two are **never collapsed**.
* ``D15`` — an ``APPROVED``/``FINAL`` version is immutable (no authoring).

No database access, no calculation, no AI.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional

from domain.disclosure import DisclosureViolation, is_immutable_report_version

#: Closed kind vocabulary (no generic rules engine — D4).
NARRATIVE_KINDS: tuple[str, ...] = ("CUSTOMER_COMMENTARY", "METHODOLOGY_NOTE", "EXPLANATION")

#: Narrative lifecycle: authoring only in DRAFT; supersession is the only transition.
NARRATIVE_STATES: tuple[str, ...] = ("DRAFT", "SUPERSEDED")

#: Markup that must never be accepted (plain text only — lifecycle spec §10.3).
_FORBIDDEN_MARKUP = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>|&lt;script|javascript:", re.IGNORECASE)

#: Authoring roles (A1 / P3 / D5).
NARRATIVE_AUTHOR_ROLES: tuple[str, ...] = ("owner", "admin")


def validate_narrative_kind(kind: str) -> str:
    if kind not in NARRATIVE_KINDS:
        raise DisclosureViolation(
            f"B4 narrative: unknown narrative_kind {kind!r} (allowed: {list(NARRATIVE_KINDS)})"
        )
    return kind


def validate_narrative_body(body: Optional[str]) -> str:
    """Non-empty plain text. Deliberately imposes **no** length limit (A3)."""
    if body is None:
        raise DisclosureViolation("B4 narrative: body is required")
    text = body.strip()
    if not text:
        raise DisclosureViolation("B4 narrative: body must not be empty")
    if _FORBIDDEN_MARKUP.search(text):
        raise DisclosureViolation("B4 narrative: body must be plain text (no markup)")
    return text


def assert_narrative_binding(requirement_version_id: Optional[str]) -> str:
    """A1: narrative is requirement-specific; a report-wide entry is impossible."""
    if not requirement_version_id:
        raise DisclosureViolation(
            "B4 narrative: a requirement_version_id is required - report-wide narrative is not permitted (A1)"
        )
    return str(requirement_version_id)


def assert_can_author(report_version_status: Optional[str]) -> None:
    """D15: never author against an APPROVED/FINAL (immutable) version."""
    if is_immutable_report_version(str(report_version_status or "")):
        raise DisclosureViolation(
            f"B4 narrative: report version status {report_version_status!r} is immutable - authoring is refused"
        )


def assert_author_role(role: Optional[str]) -> str:
    """A1/P3: only Customer Owner/Admin may author narrative."""
    normalised = (role or "").lower()
    if normalised.startswith("org_"):
        normalised = normalised[len("org_") :]
    if normalised not in NARRATIVE_AUTHOR_ROLES:
        raise DisclosureViolation(
            f"B4 narrative: role {role!r} may not author narrative (Owner/Admin only)"
        )
    return normalised


# ---------------------------------------------------------------------------
# DM-5 finalisation gate
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FinalisationItem:
    requirement_version_id: str
    effective_class: str
    value_status: str
    reason: Optional[str] = None


@dataclass(frozen=True)
class FinalisationAssessment:
    """The gate result. ``blocking`` and ``surfaced`` are NEVER merged (DM-5)."""

    can_finalise: bool
    blocking: list[FinalisationItem] = field(default_factory=list)
    surfaced: list[FinalisationItem] = field(default_factory=list)
    informational: list[FinalisationItem] = field(default_factory=list)

    @property
    def blocked_by_customer_input(self) -> list[FinalisationItem]:
        return [i for i in self.blocking if i.effective_class == "CUSTOMER_INPUT_REQUIRED"]

    @property
    def blocked_by_unresolved_required(self) -> list[FinalisationItem]:
        return [i for i in self.blocking if i.effective_class == "REQUIRED"]


def _coerce(item: Any) -> FinalisationItem:
    if isinstance(item, FinalisationItem):
        return item
    data: Mapping[str, Any] = item
    return FinalisationItem(
        requirement_version_id=str(
            data.get("requirement_version_id") or data.get("id") or "unknown"
        ),
        effective_class=str(data.get("effective_class") or ""),
        value_status=str(data.get("value_status") or ""),
        reason=data.get("reason"),
    )


def evaluate_finalisation(values: Iterable[Any]) -> FinalisationAssessment:
    """The ratified DM-5 gate.

    * unresolved ``REQUIRED``                          → **blocks**;
    * unresolved ``CUSTOMER_INPUT_REQUIRED``           → **blocks** (resolvable by input);
    * applicable required ``NOT_SUPPORTED``            → **surfaced**, never blocking-hidden
      and never presented as satisfied;
    * ``NOT_APPLICABLE`` / ``UNDETERMINED`` / resolved items → informational.
    """
    blocking: list[FinalisationItem] = []
    surfaced: list[FinalisationItem] = []
    informational: list[FinalisationItem] = []

    for raw in values:
        item = _coerce(raw)
        resolved = item.value_status == "RESOLVED"
        if resolved:
            informational.append(item)
            continue
        if item.effective_class == "CUSTOMER_INPUT_REQUIRED":
            blocking.append(item)
        elif item.effective_class == "REQUIRED":
            blocking.append(item)
        elif item.effective_class == "NOT_SUPPORTED":
            surfaced.append(item)
        else:
            informational.append(item)

    return FinalisationAssessment(
        can_finalise=not blocking,
        blocking=blocking,
        surfaced=surfaced,
        informational=informational,
    )


def assert_states_are_not_collapsed(assessment: FinalisationAssessment) -> None:
    """Guard the DM-5 distinction: no id may appear in both lists."""
    blocking_ids = {i.requirement_version_id for i in assessment.blocking}
    surfaced_ids = {i.requirement_version_id for i in assessment.surfaced}
    overlap = blocking_ids & surfaced_ids
    if overlap:
        raise DisclosureViolation(
            f"B4 finalisation: CUSTOMER_INPUT_REQUIRED/REQUIRED and NOT_SUPPORTED were collapsed for {sorted(overlap)}"
        )
