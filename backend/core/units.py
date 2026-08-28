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

from typing import Optional

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


def resolve_unit_for_factor(extracted_unit: Optional[str], factor_unit: Optional[str]) -> str:
    """Normalise a human-typed unit against a factor's canonical unit.

    Returns the factor's canonical unit when the two are legitimate equivalent
    spellings of the same unit (``L`` ↔ ``litres``), or when the factor unit
    carries a qualifier the typed unit abbreviates (``kWh`` vs ``kWh (Gross
    CV)``). Any other value is returned unchanged so the authoritative engine
    still rejects genuinely incompatible units with ``UNIT_MISMATCH``.

    ``factor_unit`` may be ``None`` (unit-less factor): the typed unit is
    returned as-is.
    """
    unit = str(extracted_unit or "").strip()
    factor_unit_s = str(factor_unit or "").strip()
    if not unit or not factor_unit_s:
        return unit or factor_unit_s
    if unit == factor_unit_s:
        return unit
    if normalize_unit(unit) == normalize_unit(factor_unit_s):
        return factor_unit_s
    if unit in factor_unit_s or factor_unit_s in unit:
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
