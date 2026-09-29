# backend/utils/factor_catalogue.py
"""Canonical emission-factor catalogue access helpers (PD-3 / PD-5).

CT-FINAL-01 continuation — the ratified Product Owner decisions PD-3 (admin
factor management) and PD-5 (manual-entry factor lookup) both require the SAME
canonical source of truth:

    public.emission_factors

The retired DEFRA conversion-factor table is not addressed by any helper here and
must never be recreated to keep legacy code working (CT-SCHEMA-03 F-01: its
recreation is structurally forbidden).

This module exists so that the canonical table name, the canonical column
projection and the canonical natural-key rule live in exactly ONE place
(AGENTS.md §23: do not duplicate unit/alias/normalisation logic across the
application).  It contains no business policy of its own: the natural key is the
one enforced by the canonical uniqueness rule
(``emission_factors_year_activity_country_uniq``).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

#: The canonical factor store.  This is the ONLY factor table any production
#: runtime path may address.
CANONICAL_FACTOR_TABLE = "emission_factors"

#: Explicit canonical column projection (never ``SELECT *``).
CANONICAL_FACTOR_COLUMNS = (
    "id, reporting_year, activity_type, co2e_multiplier, unit, scope, "
    "factor_source, factor_set, country, import_batch_id, created_at, updated_at"
)

#: NULL sentinels the canonical uniqueness rule coalesces to.  Mirrored so the
#: Python-side natural-key comparison has identical semantics to the index.
NO_UNIT = "{no-unit}"
NO_SCOPE = "{no-scope}"
DEFAULT_COUNTRY = "GB"

#: Provenance recorded on an administrator-authored factor, so its origin is
#: never ambiguous against an imported provider set.
ADMIN_FACTOR_SOURCE = "CARBONTALLY_ADMIN"
ADMIN_FACTOR_SET = "ADMIN_MANUAL"
#: Provenance recorded on a factor that arrived through the administrator CSV
#: import on the reporting surface.
ADMIN_IMPORT_FACTOR_SET = "ADMIN_IMPORT"


def clean(value: Optional[str]) -> Optional[str]:
    """Strip a supplied textual value; empty becomes ``None``."""
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def natural_key_matches(
    row: Dict[str, Any],
    *,
    reporting_year: int,
    activity_type: str,
    unit: Optional[str] = None,
    scope: Optional[str] = None,
    country: Optional[str] = None,
) -> bool:
    """Exact, NULL-safe comparison against the canonical natural key.

    The canonical unique index coalesces NULL country to ``GB`` and NULL
    unit/scope to their sentinels, so a duplicate is detected identically here
    and in the database (no reliance on PostgREST expression indexes).
    """
    return (
        int(row.get("reporting_year")) == int(reporting_year)
        and str(row.get("activity_type")) == str(activity_type)
        and str(row.get("country") or DEFAULT_COUNTRY) == str(country or DEFAULT_COUNTRY)
        and str(row.get("unit") or NO_UNIT) == str(unit or NO_UNIT)
        and str(row.get("scope") or NO_SCOPE) == str(scope or NO_SCOPE)
    )


def find_canonical_factor(
    supabase_client,
    *,
    reporting_year: int,
    activity_type: str,
    unit: Optional[str] = None,
    scope: Optional[str] = None,
    country: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return the canonical factor with this natural key, or ``None``."""
    result = supabase_client.from_(CANONICAL_FACTOR_TABLE) \
        .select("id, reporting_year, activity_type, unit, scope, country") \
        .eq("reporting_year", reporting_year) \
        .eq("activity_type", activity_type) \
        .execute()

    for row in (result.data or []):
        if natural_key_matches(
            row,
            reporting_year=reporting_year,
            activity_type=activity_type,
            unit=unit,
            scope=scope,
            country=country,
        ):
            return row
    return None


def is_unique_violation(exc: Exception) -> bool:
    """True when the database rejected the write on the canonical unique index."""
    text = str(exc).lower()
    return "duplicate key" in text or "23505" in text or "unique constraint" in text


def canonical_factor_payload(
    *,
    reporting_year: int,
    activity_type: str,
    co2e_multiplier: float,
    unit: Optional[str] = None,
    scope: Optional[str] = None,
    country: Optional[str] = None,
    factor_source: Optional[str] = None,
    factor_set: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the canonical ``emission_factors`` write payload.

    Provenance is always written: an administrator-authored factor records the
    CarbonTally-admin source/set rather than leaving the origin blank.
    """
    return {
        "reporting_year": int(reporting_year),
        "activity_type": str(activity_type),
        "co2e_multiplier": float(co2e_multiplier),
        "unit": clean(unit),
        "scope": clean(scope),
        "factor_source": clean(factor_source) or ADMIN_FACTOR_SOURCE,
        "factor_set": clean(factor_set) or ADMIN_FACTOR_SET,
        "country": (clean(country) or DEFAULT_COUNTRY).upper(),
    }
