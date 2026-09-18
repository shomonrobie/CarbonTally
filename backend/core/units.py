"""Unit alias normalisation for the calculation engine (CL-3 / PRC-2).

Human-entered activity units use abbreviations (``L``, ``t``, ``kg``, ``kWh``,
``m3``) while the authoritative ``emission_factors.unit`` vocabulary uses the
canonical long forms (``litres``, ``tonnes``, ``kilograms``… see the live
``emission_factors`` unit distribution). The engine's unit check is exact
(:meth:`domain.factor.EmissionFactor.calculate_emissions`), so aliases must be
normalised server-side before the factor is applied.

Design rules:

* We never invent a unit or weaken validation — an unknown unit is returned
  unchanged and the engine still rejects genuinely incompatible units with the
  established ``UNIT_MISMATCH`` error.
* Mapping is 1:1 alias → canonical; ``None``/empty passes through untouched.
* Qualifier-bearing factor units (``kWh (Gross CV)``) are handled by the
  callers (they compare the *base* unit first and fall back to the existing
  substring rule), so this module only needs the exact-alias table.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

#: Common alias → canonical unit table (lower-cased keys). Keys are matched
#: after ``strip().lower()``; unknown values pass through unchanged.
UNIT_ALIASES: dict[str, str] = {
    # volume
    "l": "litres",
    "litre": "litres",
    "liter": "litres",
    "liters": "litres",
    "ltr": "litres",
    "ltrs": "litres",
    "m3": "cubic metres",
    "m³": "cubic metres",
    "cu m": "cubic metres",
    "cubic meter": "cubic metres",
    "cubic meters": "cubic metres",
    # mass
    "t": "tonnes",
    "tonne": "tonnes",
    "ton": "tonnes",
    "tonnes": "tonnes",
    "metric ton": "tonnes",
    "metric tons": "tonnes",
    "mt": "tonnes",
    "kg": "kilograms",
    "kilogram": "kilograms",
    "kilograms": "kilograms",
    "kilo": "kilograms",
    "g": "grams",
    "gram": "grams",
    "grams": "grams",
    # energy
    "kwh": "kWh",
    "kwh (gross cv)": "kWh (Gross CV)",
    "kwh (net cv)": "kWh (Net CV)",
    "mwh": "MWh",
    "mj": "MJ",
    "gj": "GJ",
    # distance / freight
    "km": "km",
    "kilometre": "km",
    "kilometres": "km",
    "kilometer": "km",
    "kilometers": "km",
    "mile": "miles",
    "miles": "miles",
    "t.km": "tonne.km",
    "tkm": "tonne.km",
    "tonne km": "tonne.km",
    "tonne-km": "tonne.km",
    "tonnekilometre": "tonne.km",
    "pkm": "passenger.km",
    "passenger km": "passenger.km",
    "passenger-kilometre": "passenger.km",
}


def normalize_unit(value: Optional[str]) -> Optional[str]:
    """Map a human-entered unit to its canonical factor-unit spelling.

    ``None``/empty passes through; an unknown value is returned unchanged so
    the authoritative engine (not this helper) decides whether it matches.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return s
    return UNIT_ALIASES.get(s.lower(), s)


def units_equivalent(left: Optional[str], right: Optional[str]) -> bool:
    """Return ``True`` when two unit strings denote the same canonical unit.

    Both sides are normalised (aliases resolved); a substring containment
    check is NOT performed here (that stays in the callers that need the
    qualifier rule, e.g. ``kWh (Gross CV)``).
    """
    if left is None or right is None:
        return False
    a = normalize_unit(left)
    b = normalize_unit(right)
    return a == b


#: Qualifier syntax used by the factor vocabulary for a qualified unit:
#: the base unit, a single space, then a parenthetical qualifier
#: (``"kWh (Gross CV)"``).
_QUALIFIER_MARKER = " ("


def split_qualified_unit(unit: Optional[str]) -> tuple[str, Optional[str]]:
    """Split a possibly qualified factor unit into ``(base, qualifier)``.

    ``"kWh (Gross CV)"`` → ``("kWh", "Gross CV")``; an unqualified unit →
    ``(normalised unit, None)``. Only the **trailing parenthetical** form counts as a
    qualifier, so a real unit such as ``"cubic metres"`` is never mis-split. The base
    is resolved through :func:`normalize_unit` — the single D23 normaliser; this
    helper adds a *rule*, never a second unit vocabulary.
    """
    s = str(unit or "").strip()
    if not s:
        return ("", None)
    idx = s.find(_QUALIFIER_MARKER)
    if idx <= 0 or not s.endswith(")"):
        return (normalize_unit(s) or s, None)
    base = s[:idx].strip()
    qualifier = s[idx + len(_QUALIFIER_MARKER) : -1].strip()
    if not base or not qualifier:
        return (normalize_unit(s) or s, None)
    return (normalize_unit(base) or base, qualifier)


def unit_matches_with_qualifier(
    query_unit: Optional[str], candidate_unit: Optional[str]
) -> bool:
    """Strict qualifier-aware unit match for **factor selection** (P2 EF-E, D-B **T2**).

    ``True`` when ``candidate_unit`` is the same unit as ``query_unit`` **or** a
    *qualified variant of it*, compared case-insensitively (D-C) after alias
    normalisation:

    * ``kWh`` vs ``kWh``            → ``True``  (identical)
    * ``kWh`` vs ``kWh (Gross CV)`` → ``True``  (qualified variant of the same base)
    * ``L``   vs ``litres``         → ``True``  (alias equivalence)
    * ``litres`` vs ``kWh (Gross CV)`` → ``False`` (**negative** — different bases)
    * ``t``   vs ``tonnes (Net CV)``   → ``True`` (alias + qualifier)

    Deliberately **not** a substring rule: a short or unrelated unit can never match
    merely because its text appears inside the candidate. Currency units never match
    physical factors (ISC-9 / CL-32).

    This is the *selection-side* counterpart of :func:`resolve_unit_for_factor`, which
    already tolerates qualifiers and is deliberately **unchanged** (D-C).
    """
    q = str(query_unit or "").strip()
    c = str(candidate_unit or "").strip()
    if not q or not c:
        return False
    # ISC-9 / CL-32: a spend/currency activity must never select a physical factor.
    if is_currency_unit(q) != is_currency_unit(c):
        return False
    q_base = normalize_unit(q) or q
    c_base, qualifier = split_qualified_unit(c)
    if q_base.casefold() != c_base.casefold():
        return False
    return True if qualifier is None else bool(qualifier)


def qualifier_match_clause(column: str, param_index: int) -> str:
    """SQL predicate implementing the same T2 rule for factor selection.

    ``<column> = <unit>`` **or** ``<column>`` starts a parenthetical qualifier after the
    same unit — i.e. ``lower(unit) LIKE lower($n) || ' (%'``. The pattern has **no
    leading wildcard**, so an unrelated unit can never match by substring coincidence;
    the qualifier is built from the already-normalised parameter, and exact matches
    still rank first via the caller's unchanged ``ORDER BY``.

    Kept beside the Python predicate so the *rule* has exactly one definition
    (D23: never add a second unit vocabulary).
    """
    safe_index = int(param_index)
    return (
        f"(lower({column}) = lower(${safe_index}) "
        f"OR lower({column}) LIKE lower(${safe_index}) || ' (%')"
    )


def resolve_unit_for_factor(extracted_unit: Optional[str], factor_unit: Optional[str]) -> str:
    """Normalise a human-typed unit against a factor's canonical unit.

    Returns the factor's canonical unit when the two are legitimate equivalent
    spellings of the **same** unit (``L`` ↔ ``litres``), or when the factor unit is a
    qualified form of the same base unit (``kWh`` vs ``kWh (Gross CV)``). Any other
    value is returned unchanged so the authoritative engine still rejects genuinely
    incompatible units with ``UNIT_MISMATCH``.

    ``CL-3`` / ``027`` — equivalence is established by exact canonical normalisation
    (:func:`normalize_unit`) plus the trailing-qualifier rule
    (:func:`split_qualified_unit`). A raw substring fallback is deliberately **not**
    used: it coerced across physical families (``"t" in "litres"`` → ``"litres"``, i.e. a
    mass unit silently became a volume unit). This helper resolves *spellings*, never
    *conversions* — two different units of the same family (``litres`` vs
    ``cubic metres``) are not interchangeable here, because the quantity is not
    converted and the factor multiplier is per-unit.

    ``factor_unit`` may be ``None`` (unit-less factor): the typed unit is returned as-is.
    """
    unit = str(extracted_unit or "").strip()
    factor_unit_s = str(factor_unit or "").strip()
    if not unit or not factor_unit_s:
        return unit or factor_unit_s
    if unit == factor_unit_s:
        return unit
    if normalize_unit(unit) == normalize_unit(factor_unit_s):
        return factor_unit_s
    unit_base, unit_qualifier = split_qualified_unit(unit)
    factor_base, factor_qualifier = split_qualified_unit(factor_unit_s)
    if unit_base and unit_base == factor_base:
        # Same base unit. The factor's spelling may be adopted only when the two are NOT
        # differently qualified: an unqualified ``kWh`` may take a qualified spelling
        # (``kWh`` ↔ ``kWh (Gross CV)``), and identical qualifiers agree. But two DIFFERENT
        # qualifiers (``kWh (Gross CV)`` vs ``kWh (Net CV)``) are methodological bases, not
        # spellings — adopting one would silently change reported emissions, so the source
        # unit is returned unchanged and the basis policy (`034` D-A) selects the candidate.
        if not unit_qualifier or not factor_qualifier:
            return factor_unit_s
        if unit_qualifier.lower() == factor_qualifier.lower():
            return factor_unit_s
    return unit


#: Currency / spend-denominated activity units. The DEFRA/SEAI factor sets are
#: physical-unit based; a currency unit has no applicable factor and must never
#: be silently mapped onto a physical factor (ISC-9 / CL-32).
CURRENCY_UNITS: frozenset[str] = frozenset(
    {
        "gbp", "eur", "usd", "aud", "cad", "chf", "jpy",
        "£", "$", "€", "us $", "us$", "gb £", "gbp £",
        "pounds", "sterling", "spend", "spend based", "spend-based",
    }
)


def is_currency_unit(unit: Optional[str]) -> bool:
    """Return ``True`` when ``unit`` denotes spend/currency activity."""
    if not unit:
        return False
    s = str(unit).strip().lower()
    if not s:
        return False
    return s in CURRENCY_UNITS or any(currency in s for currency in CURRENCY_UNITS)


#: Explicit calorific-basis declarations a source document may carry (`034` D-A).
#: Gross/Net are METHODOLOGICAL bases, not unit aliases: they select between two different
#: authoritative factors; they never convert a quantity (027 unit-family semantics stay intact).
_GROSS_BASIS_TOKENS = ("gross cv", "gcv", "gross calorific value")
_NET_BASIS_TOKENS = ("net cv", "ncv", "net calorific value")

#: The factor set's documented default basis for an unqualified natural-gas energy quantity
#: (PO decision `034`: DEFRA and SEAI both resolve unqualified `kWh` to Net CV / NCV).
DEFAULT_CALORIFIC_BASIS = "net"


def source_calorific_basis(evidence: Optional[str]) -> Optional[str]:
    """The calorific basis a source document **explicitly** states, else ``None``.

    Returns ``"gross"`` for ``Gross CV`` / ``GCV`` / ``Gross calorific value`` and ``"net"`` for
    ``Net CV`` / ``NCV`` / ``Net calorific value``. Prose that merely contains the words "gross"
    or "net" (e.g. "gross tonnage") yields ``None``, and a document that declares both bases is
    treated as ambiguous (``None``) — the caller then applies the factor set's default basis
    rather than guessing.
    """
    text = str(evidence or "").lower()
    if not text:
        return None
    gross = any(token in text for token in _GROSS_BASIS_TOKENS)
    net = any(token in text for token in _NET_BASIS_TOKENS)
    if gross and net:
        return None
    if gross:
        return "gross"
    if net:
        return "net"
    return None


def select_basis_factor(
    candidates: Iterable[Any],
    *,
    source_basis: Optional[str] = None,
    default_basis: str = DEFAULT_CALORIFIC_BASIS,
) -> Optional[Any]:
    """Deterministically select the qualified-basis candidate for one base unit (`034` D-A).

    Acts **only** when the candidate set genuinely offers more than one distinct qualifier of the
    same base unit (the Gross/Net case). In every other situation — electricity, water, diesel,
    waste, or any single-qualifier family — it returns ``None`` so those selections are untouched.

    Selection is by the source's explicit basis when there is one, otherwise the factor set's
    ``default_basis`` (Net/NCV for the currently supported DEFRA and SEAI sets). Enumeration order
    can never decide the result: candidates are ordered by factor id before the qualifier map is
    built and the winning qualifier is chosen, so repeated runs are identical.
    """
    ordered = sorted(candidates, key=lambda factor: str(getattr(factor, "id", "")))
    by_qualifier: dict[str, Any] = {}
    for factor in ordered:
        _base, qualifier = split_qualified_unit(getattr(factor, "unit", None))
        if qualifier:
            by_qualifier.setdefault(qualifier.lower(), factor)
    if len(by_qualifier) < 2:
        return None
    wanted = "gross" if (source_basis or default_basis) == "gross" else "net"
    for qualifier in sorted(by_qualifier):
        if qualifier.startswith(wanted):
            return by_qualifier[qualifier]
    return None


def mapping_no_factors_reason(
    activity: Optional[str], unit: Optional[str], has_factors: bool
) -> Optional[str]:
    """Honest, human-facing reason when the factor search returns nothing.

    Returns ``None`` when factors were found (nothing to explain). For a
    currency/spend activity with no factors the message explains that the
    current DEFRA/SEAI factor set is physical-unit based and points at the
    supported paths (enter a physical unit, or use a customer factor). For any
    other empty result it gives a neutral no-match explanation.
    """
    if has_factors:
        return None
    if is_currency_unit(unit):
        return (
            f"Spend-based activity ({unit or 'currency'}) has no emission factor in the "
            "current factor set — the DEFRA/SEAI factors are physical-unit based "
            "(litres, kWh, tonnes, km …). Enter the physical quantity and unit from the "
            "document, or ask your consultant to add a customer emission factor."
        )
    return (
        "No matching emission factor found. Check the activity description or enter a "
        "physical quantity and unit (e.g. litres, kWh, tonnes, km) from the document."
    )


def spend_mapping_suggestion(
    activity: Optional[str], unit: Optional[str], has_factors: bool
) -> Optional[dict]:
    """Machine-readable mapping guidance for spend/currency activities (CL-47).

    When a currency activity has no applicable factor the response carries an
    explicit, actionable payload instead of silently returning an empty list.
    The correct supported workflow for spend data is: create an approved
    **customer factor** for the activity in the currency unit, then map the
    item to it (spend_based calculation). ``None`` means no suggestion applies.
    """
    if has_factors:
        return None
    if is_currency_unit(unit):
        return {
            "kind": "spend_based",
            "activity": activity or "",
            "unit": unit or "GBP",
            "message": (
                "Spend-based activity — create an approved customer factor for this "
                "activity in the currency unit, then map the item to it."
            ),
            "action": "create_customer_factor",
        }
    return None


def relevant_customer_factors(
    customer_factors: list[dict], activity: Optional[str], unit: Optional[str]
) -> list[dict]:
    """Filter approved customer factors to those applicable to the item.

    Used by the mapping-options endpoints so the ``no_factors_reason`` /
    ``spend_suggestion`` guidance reflects whether ANY factor (system or
    customer) actually covers THIS activity/unit — an unrelated approved
    customer factor (e.g. a Diesel factor) must not mask the spend dead-end.
    """
    a = (activity or "").strip().lower()
    u = (unit or "").strip().lower()
    out = []
    for f in customer_factors:
        fa = str(f.get("activity_type") or f.get("activity") or "").lower()
        fu = str(f.get("unit") or "").lower()
        activity_ok = (not a) or (a in fa) or (fa in a)
        unit_ok = (not u) or (fu == u) or (u in fu) or (fu in u)
        if activity_ok and unit_ok:
            out.append(f)
    return out


