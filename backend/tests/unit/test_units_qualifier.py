"""P2 EF-E (PO D-B **T2**) — the strict qualifier-aware unit-selection rule.

Locks the *selection-side* rule added to ``core.units`` for the P2 EF-E
remediation: the exact unit or a **qualified variant of the same unit**
(``kWh`` → ``kWh (Gross CV)``), case-insensitively, reusing the single D23
normaliser — and never a blanket substring.

The negative cases here are the ones that make T2 "strict": unrelated units and
short-unit over-match must be impossible.
"""

from __future__ import annotations

import pytest

from core.units import (
    normalize_unit,
    qualifier_match_clause,
    resolve_unit_for_factor,
    split_qualified_unit,
    unit_matches_with_qualifier,
    units_equivalent,
)


# ---------------------------------------------------------------- positive ---
@pytest.mark.parametrize(
    ("query", "candidate"),
    [
        ("kWh", "kWh"),
        ("kWh", "kWh (Gross CV)"),
        ("kWh", "kwh (Gross CV)"),          # D-C: case-insensitive on the selection side
        ("KWH", "kWh (Gross CV)"),
        ("kWh", "kWh (Net CV)"),
        ("L", "litres"),                     # alias equivalence still works
        ("t", "tonnes (Net CV)"),            # alias + qualifier
        ("m3", "cubic metres (estimated)"),
    ],
)
def test_exact_or_qualified_variant_matches(query: str, candidate: str) -> None:
    assert unit_matches_with_qualifier(query, candidate) is True


# ---------------------------------------------------------------- negative ---
@pytest.mark.parametrize(
    ("query", "candidate"),
    [
        ("litres", "kWh (Gross CV)"),        # different base — the headline negative
        ("kWh", "MWh"),                      # different base, similar text
        ("kg", "tonnes (Net CV)"),           # different mass unit
        ("m3", "litres"),
        ("kWh", ""),                         # empty never matches
        ("", "kWh (Gross CV)"),
        (None, "kWh"),
    ],
)
def test_unrelated_units_never_match(query, candidate) -> None:
    assert unit_matches_with_qualifier(query, candidate) is False


@pytest.mark.parametrize("short_unit", ["t", "l", "kg", "km"])
def test_short_units_do_not_over_match_by_substring(short_unit: str) -> None:
    """The substring trap T2 exists to avoid.

    A blanket ``ILIKE '%t%'`` rule would match almost any vocabulary; T2 compares
    *bases*, so a short normalised unit only matches its own base (or that base
    with a parenthetical qualifier).
    """
    assert unit_matches_with_qualifier(short_unit, "kWh (Gross CV)") is False
    assert unit_matches_with_qualifier(short_unit, "cubic metres") is False
    # ...and the same short unit still matches its own canonical/qualified form.
    assert unit_matches_with_qualifier("t", "tonnes") is True


@pytest.mark.parametrize(
    ("query", "candidate"),
    [("GBP", "kWh (Gross CV)"), ("£", "litres"), ("spend", "tonnes (Net CV)")],
)
def test_currency_never_selects_a_physical_factor(query: str, candidate: str) -> None:
    """ISC-9 / CL-32 — spend/currency separation is preserved."""
    assert unit_matches_with_qualifier(query, candidate) is False


# ------------------------------------------------------------- split helper ---
def test_split_qualified_unit() -> None:
    assert split_qualified_unit("kWh (Gross CV)") == ("kWh", "Gross CV")
    assert split_qualified_unit("cubic metres") == ("cubic metres", None)
    assert split_qualified_unit("litres") == ("litres", None)
    assert split_qualified_unit("") == ("", None)
    assert split_qualified_unit(None) == ("", None)
    # A malformed qualifier is NOT treated as one (no mis-splitting).
    assert split_qualified_unit("kWh (Gross CV") == ("kWh (Gross CV", None)


def test_rule_reuses_the_single_normaliser() -> None:
    """D23 — one normaliser, no second vocabulary."""
    assert normalize_unit("L") == "litres"
    assert split_qualified_unit("L (estimated)") == ("litres", "estimated")


# ------------------------------------------------------ unchanged mechanisms ---
def test_calculation_side_helper_is_untouched_by_this_remediation() -> None:
    """D-C — ``resolve_unit_for_factor`` keeps its existing tolerant behaviour."""
    assert resolve_unit_for_factor("kWh", "kWh (Gross CV)") == "kWh (Gross CV)"
    assert resolve_unit_for_factor("L", "litres") == "litres"
    assert resolve_unit_for_factor("litres", "kWh (Gross CV)") == "litres"


def test_units_equivalent_behaviour_is_unchanged() -> None:
    assert units_equivalent("L", "litres") is True
    assert units_equivalent("kWh", "kWh (Gross CV)") is False  # unchanged by design


# ------------------------------------------------------------ SQL predicate ---
def test_qualifier_match_clause_shape() -> None:
    clause = qualifier_match_clause("ef.unit", 2)
    # exact match first, then the qualifier form — and NO leading wildcard.
    assert "lower(ef.unit) = lower($2)" in clause
    assert "lower(ef.unit) LIKE lower($2) || ' (%'" in clause
    assert "%'" not in clause.split("LIKE")[0]
