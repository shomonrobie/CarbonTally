"""Deterministic factor-selection policy (PO decisions D-FS-1 … D-FS-6).

A pure, deterministic **semantic eligibility + preference** layer over an EXISTING
candidate list. It does not search, does not calculate, uses no AI/LLM, adds no
factor store and changes no factor data or schema.

Precedence (D-FS-6). A lower level NEVER overrides a higher-level semantic
incompatibility:

  1 activity semantic match        2 scope compatibility
  3 emissions boundary / purpose   4 methodology / treatment compatibility
  5 factor-set / source context    6 reporting year        7 geography
  8 unit compatibility             9 calorific basis (owned by D-A — untouched)
 10 aggregate CO2e over component  11 more specific over generic
 12 stable identifier ordering (reproducibility tie-break only, never an
    accounting preference)

Everything the policy needs already exists in the dataset: the taxonomy prefix in
``activity_type``, the ``WTT-`` prefix, the ``(kg CO2e of CH4|CO2|N2O per unit)``
markers, the treatment-route suffix, and the populated ``scope`` column — each
verified against the real 7,049-factor dataset in the 037 evidence report.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence

from core.units import unit_matches_with_qualifier

_COMPONENT_MARKERS = (
    "of ch4 per unit",
    "of co2 per unit",
    "of n2o per unit",
    "of co2e per unit",
)
_UPSTREAM_MARKERS = ("wtt-", "wtt ", "well-to-tank", "well to tank")
_UPSTREAM_REQUEST_MARKERS = ("wtt", "well-to-tank", "well to tank", "upstream")
_TREATMENT_REQUEST_MARKERS = (
    "disposal", "treatment", "landfill", "recycl", "compost", "incinerat",
    "energy recovery", "anaerob", "digest",
)
_TREATMENT_ROUTES = (
    "landfill", "recycl", "closed-loop", "closed loop", "open-loop", "open loop",
    "compost", "incinerat", "energy recovery", "anaerob", "digest",
)
_WASTE_FUEL_REQUEST = ("waste oil", "waste-oil", "waste oils")
_FUEL_REQUEST_MARKERS = (
    "gas", "diesel", "petrol", "gasoline", "kerosene", "lpg", "fuel", "oil",
    "electricity", "power", "energy", "coal", "biomass", "burning", "combustion",
)
_BIO_MARKERS = (
    "bioenergy", "biofuel", "biodiesel", "bioethanol", "development diesel",
    "off road biodiesel", "hvo",
)
_BIO_REQUEST_MARKERS = ("bio", "hvo", "renewable", "development", "off road")
_NON_FUEL_FAMILIES = ("waste disposal", "material use")
_TOKEN_STOPWORDS = frozenset(
    {
        "the", "and", "per", "unit", "for", "with", "from", "into", "of", "to",
        "kg", "kwh", "co2", "co2e", "ch4", "n2o", "tonnes", "tonne", "litres",
        "litre", "cubic", "metres", "metre", "miles", "mile", "avg", "average",
        "supply", "usage", "consumption", "primary", "material", "production",
    }
)


def _text(value: Any) -> str:
    return str(value or "").casefold()


def _tokens(value: Any) -> frozenset:
    cleaned = "".join(ch if (ch.isalpha() or ch.isspace()) else " " for ch in _text(value))
    return frozenset(t for t in cleaned.split() if len(t) > 2 and t not in _TOKEN_STOPWORDS)


def activity_of(factor: Any) -> str:
    return _text(getattr(factor, "activity_type", ""))


def family_of(factor: Any) -> str:
    """The taxonomy prefix — the dataset's own semantic-family marker."""
    return activity_of(factor).split(" > ")[0].strip()


def is_component(factor: Any) -> bool:
    """A single-greenhouse-gas contribution factor (D-FS-1 component class)."""
    return any(m in activity_of(factor) for m in _COMPONENT_MARKERS)


def is_upstream(factor: Any) -> bool:
    """A well-to-tank / upstream factor (D-FS-2 boundary class)."""
    name = activity_of(factor)
    return any(m in name[:24] for m in _UPSTREAM_MARKERS)


def scope_of(factor: Any) -> str:
    return _text(getattr(factor, "scope", ""))


def is_bio(factor: Any) -> bool:
    return any(m in activity_of(factor) for m in _BIO_MARKERS) or family_of(factor) == "bioenergy"


@dataclass(frozen=True)
class SelectionOutcome:
    """Outcome of the deterministic policy over one candidate list."""

    status: str  # selected | ambiguous | no_eligible_candidate | not_applicable
    factor: Any = None
    reason: str = ""
    eligible: tuple = ()
    excluded: tuple = ()  # (factor, reason) pairs
    groups: tuple = ()  # distinct semantic groups when ambiguous


def _request_class(activity: str) -> str:
    text = _text(activity)
    if any(m in text for m in _UPSTREAM_REQUEST_MARKERS):
        return "upstream"
    if any(m in text for m in _WASTE_FUEL_REQUEST):
        return "waste_fuel"
    if any(m in text for m in _TREATMENT_REQUEST_MARKERS):
        return "waste_treatment"
    if any(m in text for m in _FUEL_REQUEST_MARKERS):
        return "fuel"
    return "unclassified"


def _requested_route(activity: str) -> Optional[str]:
    text = _text(activity)
    for route in _TREATMENT_ROUTES:
        if route in text:
            return route
    return None


def _exclusion(
    factor: Any,
    *,
    request_class: str,
    request_unit: Optional[str],
    request_scope: Optional[str],
    request_tokens: frozenset,
) -> Optional[str]:
    """Mandatory semantic eligibility rules — never numeric, never lexical-only."""
    name = activity_of(factor)
    fam = family_of(factor)

    # 8 unit compatibility: the request unit must be a legitimate spelling/basis.
    # Exact equality is tested first because the tolerant qualifier helper
    # deliberately refuses qualified-vs-qualified comparisons (the D-A gate), so a
    # request for 'kWh (Net CV)' must still accept a 'kWh (Net CV)' factor.
    unit = getattr(factor, "unit", None)
    if request_unit and unit:
        if _text(unit) != _text(request_unit) and not unit_matches_with_qualifier(
            request_unit, unit
        ):
            return "unit incompatible"

    if request_class == "upstream":
        # 3 boundary: an upstream request is satisfied only by upstream factors.
        return None if is_upstream(factor) else "not an upstream/WTT factor for an upstream request"
    if is_upstream(factor):
        # 3 boundary (D-FS-2): WTT must not survive into a non-upstream request.
        return "upstream/WTT factor for a non-upstream request"

    # 2 scope compatibility (D-FS-3)
    fscope = scope_of(factor)
    if request_scope:
        if fscope and fscope != _text(request_scope):
            return "scope incompatible with the requested scope"
    elif request_class == "fuel" and fscope in ("scope 3", "outside of scopes"):
        return "non-combustion accounting scope for a fuel/energy request"

    # 1/4 activity semantics (D-FS-4): the shared token "waste" is not evidence.
    if request_class == "waste_treatment":
        if fam.startswith("fuel") or fam == "bioenergy":
            return "fuel concept where a waste treatment/disposal concept was requested"
        if fam not in _NON_FUEL_FAMILIES:
            return "outside the waste treatment/disposal taxonomy"
        return None
    if request_class == "waste_fuel":
        if fam in _NON_FUEL_FAMILIES:
            return "treatment/disposal concept where a waste-derived fuel was requested"
        if "waste" not in name:
            return "not a waste-derived fuel concept"
        return None

    # fuel / energy requests
    if fam in _NON_FUEL_FAMILIES:
        return "treatment/disposal concept for a fuel/energy request"
    if request_tokens and not (request_tokens & _tokens(name)):
        return "no shared activity concept token"
    return None

def select_factor(
    candidates: Sequence[Any],
    *,
    activity: str,
    unit: Optional[str] = None,
    scope: Optional[str] = None,
    preferred_unit: Optional[str] = None,
) -> SelectionOutcome:
    """Apply D-FS-1 … D-FS-6 to *candidates* and return a deterministic outcome.

    ``preferred_unit`` is the unit already decided upstream (e.g. the calorific
    basis chosen by the closed D-A policy). It only ranks candidates that are
    already eligible; it can never admit an ineligible one, so D-A's basis
    decision cannot be overridden by this policy.

    ``not_applicable`` means the request falls outside the policy's semantic
    classes and the caller must leave existing behaviour untouched.
    """
    request_class = _request_class(activity)
    if request_class == "unclassified" or not candidates:
        return SelectionOutcome(
            status="not_applicable", reason="request outside the policy's semantic classes"
        )

    request_tokens = _tokens(activity)
    eligible: list[Any] = []
    excluded: list[tuple[Any, str]] = []
    for factor in candidates:
        reason = _exclusion(
            factor,
            request_class=request_class,
            request_unit=unit,
            request_scope=scope,
            request_tokens=request_tokens,
        )
        if reason:
            excluded.append((factor, reason))
        else:
            eligible.append(factor)

    if not eligible:
        return SelectionOutcome(
            status="no_eligible_candidate",
            reason="every candidate was semantically ineligible",
            excluded=tuple(excluded),
        )

    # 10 aggregate over component — only inside an equivalent semantic context
    # (an aggregate exists for the same family/unit), exactly as D-FS-1 requires.
    aggregates = [f for f in eligible if not is_component(f)]
    if aggregates and len(aggregates) != len(eligible):
        eligible = aggregates

    # 4 methodology: non-bio families preferred for non-bio requests (D-FS-4/C).
    if request_class in ("fuel", "waste_fuel") and not any(
        m in _text(activity) for m in _BIO_REQUEST_MARKERS
    ):
        non_bio = [f for f in eligible if not is_bio(f)]
        if non_bio:
            eligible = non_bio

    # 4 treatment-route compatibility (D-FS-4).
    route = _requested_route(activity)
    if request_class == "waste_treatment" and route:
        routed = [f for f in eligible if route in activity_of(f)]
        if routed:
            eligible = routed

    def rank(factor: Any) -> tuple:
        """11 specificity, then the already-decided unit, then 12 stable id order."""
        tokens = _tokens(activity_of(factor))
        coverage = len(request_tokens & tokens) / max(1, len(request_tokens))
        excess = len(tokens - request_tokens)
        same_unit = 0 if (preferred_unit or unit) and _text(getattr(factor, "unit", "")) == _text(
            preferred_unit or unit
        ) else 1
        return (-coverage, same_unit, excess, str(getattr(factor, "id", "")))

    ordered = sorted(eligible, key=rank)
    best = ordered[0]
    # 5 ambiguity: candidates tied on request-token COVERAGE (the semantic strength
    # of the match) that sit in materially different semantic groups are NOT
    # resolved by magnitude, row order or accidental lexical ordering.
    tie_coverage = rank(best)[0]
    groups = tuple(
        sorted(
            {
                (family_of(f), _requested_route(activity_of(f)) or "")
                for f in eligible
                if rank(f)[0] == tie_coverage
            }
        )
    )
    if len(groups) > 1:
        # 5 ambiguity: equally ranked candidates from materially different semantic
        # groups are NOT resolved by magnitude, row order or lexical accident.
        return SelectionOutcome(
            status="ambiguous",
            reason="multiple equally ranked, materially different candidates",
            eligible=tuple(eligible),
            excluded=tuple(excluded),
            groups=groups,
        )
    return SelectionOutcome(
        status="selected",
        factor=best,
        reason=f"deterministic policy selection ({request_class})",
        eligible=tuple(eligible),
        excluded=tuple(excluded),
        groups=groups,
    )
