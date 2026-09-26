"""P17-L — the canonical governed capability projection (pure, no I/O).

Why this module exists
----------------------
`P17-DECISION-03 §18.1` Tier 3 lists the two surfaces that may render a product
capability claim (customer, investor) and §18.3 defines the deterministic gates
(`AG-1`…`AG-8`) any such surface must pass. `P17-K` authored the governed
catalogue rows and verified them on real PostgreSQL, and explicitly deferred the
*rendering* branches of `AG-3`…`AG-8` because **no surface existed**.

This module is the one canonical projection those two surfaces share
(`§6` *"They must consume the SAME capability truth"*). It is deliberately:

* **pure** — no I/O, no pool, no tenant, no clock. It is handed persisted
  catalogue rows and returns the projection;
* **non-inventive** — it declares **no** vocabulary of its own. Every governed
  token it emits is imported from :mod:`domain.disclosure` /
  :mod:`domain.disclosure_projection`. It is a *projection*, not a second
  capability configuration file (`§5`, `F-2`);
* **tenant-free by construction** — it has no tenant parameter, so no tenant
  query can influence a capability value (`§13`, `CS-1`, `SEC-1`, `AG-5`).

What it must never do
---------------------
* **No applicability.** It never asks or answers *"does this apply to this
  customer?"* (`PO-3`, `F-1`). There is no applicability input and no
  applicability output. `derive_effective_class` is called with the neutral
  *"the requirement is in play"* posture P17-K's own `AG-2` test established,
  which is exactly `M-1`'s third column (*"when a requirement is in play"*) —
  and it can never yield `NOT_APPLICABLE`, because that outcome is reachable
  only from an applicability status, which this module never supplies.
* **No Axis-A rendering.** `PARTIAL` / `DEFERRED` / `NOT_IMPLEMENTED` are
  internal architecture tokens (`IV-1`, `M-4`, `F-3`). They are not referenced
  anywhere in this module's output, and
  :func:`assert_no_axis_a_status_token` re-checks that on the finished payload.
* **No result.** `result_presence` is always ``None``: a result is a property of
  an organisation's own persisted calculations, never of the product capability
  catalogue (`§8`, `§13`). The *absence-state name* is `PO-5`, still open, so
  this module deliberately does not label absence either (`IV-4`, `S3-5`).
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping, Optional, Sequence

from domain.disclosure import (
    CARBONTALLY_CAPABILITIES,
    REQUIREMENT_CLASSES,
    SCOPE2_METHODS,
    DisclosureViolation,
)
from domain.disclosure_projection import (
    UNSUPPORTED_CAPABILITIES,
    derive_effective_class,
)

# ---------------------------------------------------------------------------
# Requirement identity → governed dimensions
# ---------------------------------------------------------------------------
#: The governed Scope dimension. A property of the requirement (framework
#: truth), never of a tenant.
SCOPES: tuple[str, ...] = ("Scope 1", "Scope 2", "Scope 3")

#: The governed Scope 3 category taxonomy size. This is the *taxonomy* size
#: (P17-D), never a support count and never a coverage figure (`S3-1`, `S3-6`).
SCOPE3_CATEGORY_COUNT = 15

#: `M-1`'s third column is expressed by the existing engine, not re-implemented.
#: The posture is *"the requirement is in play"* — the product-level question.
_REQUIREMENT_IN_PLAY = "APPLIES"

_SCOPE1_CODE = re.compile(r"^GP-S1$")
_SCOPE2_CODE = re.compile(r"^GP-S2-(LB|MB)$")
_SCOPE3_CODE = re.compile(r"^GP-S3-CAT-(\d{2})$")

#: The catalogue's own method suffix → the governed Scope 2 method.
_SCOPE2_METHOD_BY_SUFFIX: Mapping[str, str] = {
    "LB": "LOCATION_BASED",
    "MB": "MARKET_BASED",
}

#: Axis-A (internal architecture) tokens. They must never be rendered on a
#: customer, consultant, PE, investor, report or export surface (`IV-1`, `F-3`).
#: Matched on **word boundaries**: `PARTIALLY_SUPPORTED` is a *governed* value
#: and must not be mistaken for the internal token `PARTIAL` (`IV-2`, `IV-5`).
AXIS_A_STATUS_PATTERN = re.compile(r"\b(PARTIAL|DEFERRED|NOT_IMPLEMENTED)\b", re.IGNORECASE)

#: Placeholder / fabricated-figure tokens `AG-4` forbids for a non-produced item
#: (`F-6`). `NOT_APPLICABLE_TO_PRODUCT` is unaffected: it is a governed value,
#: not the phrase "not applicable".
FORBIDDEN_PLACEHOLDER_PATTERN = re.compile(
    r"\bN/A\b|\bnot applicable\b|\bnon-applicable\b|\bexcluded\b|\bcoming soon\b"
    r"|\bTBC\b|\bTBD\b|\b0\s*(?:kg|t|tonnes?|tco2e)\b",
    re.IGNORECASE,
)

#: Any CO₂e quantity — a capability surface never carries one (`AG-4`, `§14`).
EMISSIONS_FIGURE_PATTERN = re.compile(
    r"\d[\d,]*(?:\.\d+)?\s*(?:kg|t|tonnes?|tco2e|kgco2e)\b", re.IGNORECASE
)

#: Field names that would turn capability truth into an applicability,
#: coverage, materiality or assurance claim (`F-1`, `F-2`, `F-8`, `AG-7`).
FORBIDDEN_FIELD_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"applicab", re.IGNORECASE),
    re.compile(r"materiality", re.IGNORECASE),
    re.compile(r"coverage", re.IGNORECASE),
    re.compile(r"completeness", re.IGNORECASE),
    re.compile(r"assurance", re.IGNORECASE),
    re.compile(r"total", re.IGNORECASE),
    re.compile(r"percentage", re.IGNORECASE),
    re.compile(r"architecture_status", re.IGNORECASE),
)



# ---------------------------------------------------------------------------
# Per-capability explanation (quoted from the frozen `M-6` claim wording)
# ---------------------------------------------------------------------------
#: Truthful, non-upgrading human-readable explanation per governed capability
#: value (`IV-2` says the governed value IS the claim; this prose accompanies
#: it and never replaces it). Wording is taken from the frozen claim table
#: (`DECISION-03 §5.3 M-6`, `§5.5`) and from `§12.2(2)` for the two
#: input-limited values. Nothing here asserts a scope, a figure, a date, a
#: coverage level or a compliance conclusion.
_CAPABILITY_EXPLANATION: Mapping[str, str] = {
    "SUPPORTED": (
        "CarbonTally supports this requirement, within the defined acceptance path."
    ),
    "PARTIALLY_SUPPORTED": (
        "CarbonTally supports this requirement within a bounded scope. The scope, "
        "and what lies outside it, are stated on the requirement itself."
    ),
    "STRUCTURED_INPUT_REQUIRED": (
        "CarbonTally supports this requirement, but producing a value depends on "
        "the required structured input being supplied. The requirement remains "
        "expected until that input exists."
    ),
    "EXTERNAL_INPUT_REQUIRED": (
        "CarbonTally supports this requirement, but producing a value depends on "
        "the required external input being supplied. The requirement remains "
        "expected until that input exists."
    ),
    "MISSING_CAPABILITY": (
        "CarbonTally does not currently support this requirement. It requires the "
        "prerequisite named on the requirement."
    ),
    "FUTURE": (
        "CarbonTally has not yet delivered this requirement. It is pending the "
        "named decision or prerequisite recorded on the requirement, and no value "
        "is produced for it today."
    ),
    "NOT_APPLICABLE_TO_PRODUCT": (
        "This requirement is not the product's own to produce. It is a statement "
        "about the product and never a statement about any customer."
    ),
}

#: The four-way Scope 3 capability split (`S3-1`, §11.1). The rollup is reported
#: in exactly these keys and never collapsed into a total.
ROLLUP_KEYS: tuple[str, ...] = (
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "FUTURE",
    "MISSING_CAPABILITY",
)

#: Top-level prose making §8 structural rather than a presentation choice.
RESULT_PRESENCE_NOTE = (
    "Capability and results are different facts. This projection states what the "
    "product supports; it carries no result for any organisation. A requirement "
    "with no current result is not an unsupported requirement, and an unmeasured "
    "requirement is never zero emissions."
)


def _dicts(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalise the incoming rows to plain dicts (repository rows or fixtures)."""
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            out.append(dict(row))
        except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise DisclosureViolation(
                f"P17-L: capability projection received a non-mapping catalogue row ({exc})"
            ) from exc
    return out


def dimensions_for_requirement_code(requirement_code: str) -> dict[str, Any]:
    """Derive the governed dimensions of a catalogue requirement code.

    The code is the catalogue's own frozen identity (`P17-K`). An unrecognised
    code raises rather than yielding a guessed scope or category — a surface that
    invents a dimension is a claim defect, not a rendering defect.
    """
    if not requirement_code:
        raise DisclosureViolation("P17-L: requirement_code is required")
    code = str(requirement_code)
    if _SCOPE1_CODE.match(code):
        return {"scope": "Scope 1", "scope2_method": None, "scope3_category": None}
    match2 = _SCOPE2_CODE.match(code)
    if match2:
        method = _SCOPE2_METHOD_BY_SUFFIX[match2.group(1)]
        if method not in SCOPE2_METHODS:  # pragma: no cover - registry is closed
            raise DisclosureViolation(f"P17-L: unknown Scope 2 method suffix in {code!r}")
        return {"scope": "Scope 2", "scope2_method": method, "scope3_category": None}
    match3 = _SCOPE3_CODE.match(code)
    if match3:
        category = int(match3.group(1))
        if not 1 <= category <= SCOPE3_CATEGORY_COUNT:
            raise DisclosureViolation(
                f"P17-L: requirement {code!r} names Scope 3 category {category}, "
                f"outside the governed 1..{SCOPE3_CATEGORY_COUNT} taxonomy"
            )
        return {"scope": "Scope 3", "scope2_method": None, "scope3_category": category}
    raise DisclosureViolation(
        f"P17-L: requirement code {code!r} is not a governed disclosure requirement "
        "identity (GP-S1 / GP-S2-LB / GP-S2-MB / GP-S3-CAT-NN); refusing to invent "
        "a scope or category for it"
    )


def is_governed_requirement_code(requirement_code: Optional[str]) -> bool:
    """Is ``requirement_code`` a governed disclosure requirement identity?

    The **single** definition of the grammar: implemented in terms of
    :func:`dimensions_for_requirement_code`, so the surface can never select a
    framework version whose rows are not governed requirements while an unknown
    code continues to raise everywhere it is actually projected.
    """
    try:
        dimensions_for_requirement_code(str(requirement_code or ""))
    except DisclosureViolation:
        return False
    return True


# ---------------------------------------------------------------------------
# The governed catalogue's own identity (`P17-M2`, fixing `DEF-1`)
# ---------------------------------------------------------------------------
#: The **complete** governed requirement-identity set of the capability
#: catalogue: Scope 1, the two governed Scope 2 methods, and the 15 Scope 3
#: categories. It is derived from the closed registries already declared above
#: (`_SCOPE2_METHOD_BY_SUFFIX`, `SCOPE3_CATEGORY_COUNT`) rather than re-typed, so
#: the identity grammar and the identity set cannot drift apart.
def governed_requirement_identities() -> frozenset[str]:
    """Every governed disclosure requirement identity, as one closed set."""
    identities = {"GP-S1"}
    identities.update(f"GP-S2-{suffix}" for suffix in _SCOPE2_METHOD_BY_SUFFIX)
    identities.update(
        f"GP-S3-CAT-{category:02d}" for category in range(1, SCOPE3_CATEGORY_COUNT + 1)
    )
    for identity in sorted(identities):  # pragma: no cover - closed registry
        if not is_governed_requirement_code(identity):
            raise DisclosureViolation(
                f"P17-M2: {identity!r} is in the governed identity set but is not a "
                "governed requirement identity"
            )
    return frozenset(identities)


#: The frozen identity of the governed capability catalogue (`P17-K`). A
#: framework version is the capability catalogue **only** if its requirement rows
#: are exactly this identity set — never because it happens to carry one
#: governed-looking code (`P17-M2` `DEF-1`).
GOVERNED_CATALOGUE_IDENTITIES: frozenset[str] = governed_requirement_identities()


def is_governed_catalogue_version(candidate: Mapping[str, Any]) -> bool:
    """Is this framework version the governed capability catalogue?

    The rule is **identity-anchored and order-free** (`P17-M2`, fixing `DEF-1`):

    * every requirement row on the version must be a governed requirement
      identity — a version carrying any other row is not a capability catalogue,
      and serving it would mean stating a claim built on non-governed rows;
    * the version must carry the **complete** governed identity set
      (:data:`GOVERNED_CATALOGUE_IDENTITIES`), because a *subset* is a narrower
      statement dressed as the canonical one.

    Consequently a competing version that carries merely *one* governed
    requirement code can never become the catalogue, whatever its ``status``,
    ``source_tier`` or ``version_label`` sorting (`DEF-1`).
    """
    codes = [str(code) for code in (candidate.get("requirement_codes") or [])]
    if not codes:
        return False
    if not all(is_governed_requirement_code(code) for code in codes):
        return False
    return GOVERNED_CATALOGUE_IDENTITIES <= set(codes)


def select_governed_catalogue_version(
    candidates: Sequence[Mapping[str, Any]],
) -> Optional[dict[str, Any]]:
    """The **one** governed capability catalogue version among ``candidates``.

    * ``None`` — no candidate is the governed catalogue. The surface then makes
      no claim at all (`CS-3`, `IV-4`).
    * one candidate — that candidate is the catalogue, **regardless of its
      position** in ``candidates``. Row order therefore cannot decide a product
      claim (`DEF-1`).
    * more than one candidate — the governed catalogue is *ambiguous*. That is a
      governance fault, not a presentation choice, so this raises
      :class:`DisclosureViolation` and the surface fails closed rather than
      choosing (`CS-3`, `AGENTS.md §62` — a catalogue transition is a PO
      decision, never an ordering side effect).
    """
    governed = [
        dict(candidate)
        for candidate in _dicts(candidates)
        if is_governed_catalogue_version(candidate)
    ]
    if not governed:
        return None
    if len(governed) > 1:
        labels = ", ".join(
            sorted(str(item.get("version_label") or "") for item in governed)
        )
        raise DisclosureViolation(
            "P17-M2: "
            f"{len(governed)} framework versions each carry the complete governed "
            f"requirement identity set ({labels}); the governed capability catalogue "
            "is ambiguous, so no capability statement can be made until an explicit "
            "governed catalogue transition resolves it"
        )
    return governed[0]


def capability_explanation(capability: str) -> str:
    """The truthful human-readable explanation for a governed capability value."""
    if capability not in CARBONTALLY_CAPABILITIES:
        raise DisclosureViolation(
            f"P17-L: {capability!r} is not a governed CarbonTally capability "
            f"(governed: {list(CARBONTALLY_CAPABILITIES)})"
        )
    return _CAPABILITY_EXPLANATION[capability]


def capability_glossary() -> list[dict[str, str]]:
    """The governed capability vocabulary with its meaning, in governed order.

    Shared by both surfaces so no consumer hardcodes capability semantics (and
    so no consumer can re-word a governed value into a stronger claim).
    """
    return [
        {"value": value, "explanation": _CAPABILITY_EXPLANATION[value]}
        for value in CARBONTALLY_CAPABILITIES
    ]



def project_requirement(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project one persisted catalogue row into its governed surface shape."""
    requirement_code = str(row.get("requirement_code") or "")
    dimensions = dimensions_for_requirement_code(requirement_code)

    capability = str(row.get("carbontally_capability") or "")
    if capability not in CARBONTALLY_CAPABILITIES:
        raise DisclosureViolation(
            f"P17-L: requirement {requirement_code!r} carries {capability!r}, which is "
            "not a governed CarbonTally capability value"
        )
    requirement_class = str(row.get("requirement_class") or "")
    if requirement_class not in REQUIREMENT_CLASSES:
        raise DisclosureViolation(
            f"P17-L: requirement {requirement_code!r} carries requirement class "
            f"{requirement_class!r}, which is not a governed requirement class"
        )

    # `M-1`'s third column, derived by the existing engine — never re-implemented,
    # and never an applicability outcome (no applicability status is supplied).
    class_expression = derive_effective_class(
        requirement_class=requirement_class,
        applicability_status=_REQUIREMENT_IN_PLAY,
        carbontally_capability=capability,
    )

    return {
        # --- `§7` required minimum: identifier + name + framework context -----
        "requirement_code": requirement_code,
        "requirement_name": str(row.get("title") or ""),
        "framework_code": str(row.get("framework_code") or ""),
        "framework_version_label": str(row.get("framework_version_label") or ""),
        # --- `§7` required minimum: governed dimensions -----------------------
        "scope": dimensions["scope"],
        "scope2_method": dimensions["scope2_method"],
        "scope3_category": dimensions["scope3_category"],
        # --- `§7` required minimum: the governed claim ------------------------
        # `IV-2` — the governed value is quoted verbatim and is the claim.
        "carbontally_capability": capability,
        "capability_explanation": capability_explanation(capability),
        # The framework's own class for the requirement (framework truth).
        "requirement_class": requirement_class,
        # `M-1` col 3: what the product produces *when the requirement is in play*.
        # This is a requirement-class outcome, never an applicability outcome.
        "requirement_class_expression": class_expression,
        # `§7` supported/unsupported distinction, using the governed engine's own
        # notion of "not producible". `PARTIALLY_SUPPORTED` is bounded support and
        # is never an upgrade (`IV-5`); the two input-limited values remain
        # expected (`§12.2`), so neither is collapsed into "unsupported".
        "supported": capability not in UNSUPPORTED_CAPABILITIES,
        # --- `§7`/`§12` provenance -------------------------------------------
        "provenance": {
            "source_locator": row.get("source_locator"),
            "authoritative_text_ref": row.get("authoritative_text_ref"),
            "source_tier": row.get("source_tier"),
            "official_identifier": row.get("official_identifier"),
            "identifier_status": row.get("identifier_status"),
        },
        # The catalogue's own description, verbatim: it carries the bounded-scope
        # statement and the named prerequisite that `M-6`/`IT-3`/`IT-5` require.
        "capability_detail": row.get("description"),
        # --- `§8` capability ≠ result ----------------------------------------
        # Always null: a result belongs to an organisation's persisted
        # calculations, never to the product catalogue. Never `0`, never a
        # placeholder (`F-6`, `S3-5`).
        "result_presence": None,
    }


def scope3_capability_rollup(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """The four-way Scope 3 capability split, recomputed from the rows.

    Never hardcoded, never a total, never a coverage score (`S3-1`, `AG-7`).
    """
    counts: dict[str, int] = {key: 0 for key in ROLLUP_KEYS}
    for row in _dicts(rows):
        code = str(row.get("requirement_code") or "")
        if not _SCOPE3_CODE.match(code):
            continue
        capability = str(row.get("carbontally_capability") or "")
        if capability not in counts:
            # A Scope 3 category carrying a capability outside the frozen four-way
            # split is a governance finding, not a rendering choice.
            raise DisclosureViolation(
                f"P17-L: Scope 3 requirement {code!r} carries capability "
                f"{capability!r}, which is outside the four-way rollup "
                f"({list(ROLLUP_KEYS)})"
            )
        counts[capability] += 1
    return counts




def assert_no_axis_a_status_token(payload: Any) -> None:
    """Raise if an Axis-A token is renderable anywhere in the payload (`IV-1`).

    Runs on the serialised payload so it covers prose and nested values alike,
    and matches on word boundaries so the governed value
    ``PARTIALLY_SUPPORTED`` is never mistaken for the internal token ``PARTIAL``.
    """
    text = json.dumps(payload, default=str)
    match = AXIS_A_STATUS_PATTERN.search(text)
    if match is not None:
        raise DisclosureViolation(
            f"P17-L: Axis-A token {match.group(0)!r} is renderable on a capability "
            "surface (IV-1 / F-3); internal architecture statuses are never a "
            "customer, consultant, PE or investor status"
        )


def assert_no_placeholder_or_figure(payload: Any) -> None:
    """Raise if a placeholder or a CO₂e figure is renderable (`AG-4`, `F-6`)."""
    text = json.dumps(payload, default=str)
    placeholder = FORBIDDEN_PLACEHOLDER_PATTERN.search(text)
    if placeholder is not None:
        raise DisclosureViolation(
            f"P17-L: placeholder {placeholder.group(0)!r} is renderable on a capability "
            "surface; absence renders as absence (S3-5 / AG-4)"
        )
    figure = EMISSIONS_FIGURE_PATTERN.search(text)
    if figure is not None:
        raise DisclosureViolation(
            f"P17-L: emissions figure {figure.group(0)!r} is renderable on a capability "
            "surface; a capability surface carries no result (AG-4 / §8)"
        )


def _deep_keys(payload: Any) -> list[str]:
    """Every mapping key in a nested payload (used by the guard below)."""
    keys: list[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            keys.append(str(key))
            keys.extend(_deep_keys(value))
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            keys.extend(_deep_keys(item))
    return keys


def assert_no_forbidden_field(payload: Mapping[str, Any]) -> None:
    """Raise if the projection grew an applicability/coverage-style field."""
    for key in _deep_keys(payload):
        for pattern in FORBIDDEN_FIELD_PATTERNS:
            if pattern.search(key):
                raise DisclosureViolation(
                    f"P17-L: field {key!r} is forbidden on a capability surface "
                    "(F-1 / F-2 / F-8 / AG-7): no applicability, coverage, "
                    "materiality, assurance or total field may exist"
                )


def project_capability_catalogue(
    *,
    framework: Mapping[str, Any],
    framework_version: Mapping[str, Any],
    requirement_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """The canonical capability truth, shared by every consumer (`§6`).

    `framework` and `framework_version` are the persisted catalogue rows; the
    projection adds no fact that is not already persisted (`§5`, `AG-8`).
    """
    requirements = [project_requirement(row) for row in _dicts(requirement_rows)]

    payload: dict[str, Any] = {
        "surface": "CAPABILITY_TRUTH",
        "framework": {
            "code": framework.get("code"),
            "name": framework.get("name"),
            "publisher": framework.get("publisher"),
            "kind": framework.get("kind"),
        },
        "framework_version": {
            "version_label": framework_version.get("version_label"),
            "status": framework_version.get("status"),
            "source_tier": framework_version.get("source_tier"),
            "source_url": framework_version.get("source_url"),
            "authoritative_source_date": framework_version.get("authoritative_source_date"),
        },
        # The governed claim vocabulary, quoted from the code constant the
        # database CHECK constraint is asserted equal to (P17-K `AG-1`).
        "capability_vocabulary": list(CARBONTALLY_CAPABILITIES),
        "capability_glossary": capability_glossary(),
        "requirements": requirements,
        # `S3-1` — the four-way split is shown; there is no total anywhere.
        "scope3_capability_rollup": scope3_capability_rollup(requirement_rows),
        "scope3_rollup_basis": (
            "Derived from the persisted governed catalogue rows. The split is shown in "
            "full and is never aggregated into a total, a coverage figure or a count of "
            "supported categories."
        ),
        # `§8` — capability and result are different facts, structurally.
        "result_presence_note": RESULT_PRESENCE_NOTE,
    }

    assert_no_axis_a_status_token(payload)
    assert_no_placeholder_or_figure(payload)
    assert_no_forbidden_field(payload)
    return payload


def capability_for_scope3(payload: Mapping[str, Any], category: int) -> Optional[dict[str, Any]]:
    """The projected requirement for one Scope 3 category (1..15), or ``None``."""
    for item in payload.get("requirements", []):
        if item.get("scope3_category") == category:
            return dict(item)
    return None


def capability_for_scope2(payload: Mapping[str, Any], method: str) -> Optional[dict[str, Any]]:
    """The projected requirement for one governed Scope 2 method, or ``None``."""
    if method not in SCOPE2_METHODS:  # pragma: no cover - closed registry
        raise DisclosureViolation(f"P17-L: unknown Scope 2 method {method!r}")
    for item in payload.get("requirements", []):
        if item.get("scope2_method") == method:
            return dict(item)
    return None

