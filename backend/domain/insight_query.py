"""CarbonTally Insight — bounded typed analytics query contract (I3 analytics).

Authorization: PO Insight Discovery / Aggregation / Provenance implementation
authorization (2026-09-22), bounded by the PO decision matrix (C-01, C-02, C-04,
C-05, C-14) and the preflight record
``docs/architecture/CT-P8-INSIGHT-DISCOVERY-AGGREGATION-PREFLIGHT-20260922.md``.

Pure contract/typing — no I/O, no database, no provider, no authorization
decision, **no SQL**. This module defines only:

* the closed filter/dimension vocabularies a bounded analytics operation may use;
* the hard bounds (results, groups, provenance references, period span);
* deterministic validation helpers returning machine-readable reason codes;
* the explicit numeric matching rule (exact = zero tolerance; an approximate
  amount must carry an explicit tolerance).

Design rules preserved here (PO D-01/D-03):

* the vocabulary is a **closed allowlist**; an unknown key is a rejection, not a
  pass-through (no arbitrary query surface exists anywhere);
* matching semantics are explicit and deterministic: an activity filter is a
  case-insensitive *containment* test on the stored activity text (no fuzzy
  scoring, no similarity threshold, no model inference);
* dates are the stored calendar dates (``DATE`` columns carry no time zone), so a
  single day is an inclusive one-day range;
* amounts are compared on ``calculation_snapshots.co2e_kg`` in kg CO₂e — the same
  basis the existing emissions surfaces use.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional, Sequence

from core.types import Scope

#: Stamped on every analytics result so Layer-2 audit can attribute it.
ANALYTICS_CONTRACT_VERSION = "i3-analytics-v1"

#: The three authorized analytics tool names (Phase 8 Insight analytics).
TOOL_INSIGHT_DISCOVERY = "insight_discovery"
TOOL_INSIGHT_AGGREGATION = "insight_aggregation"
TOOL_INSIGHT_AGGREGATE_PROVENANCE = "insight_aggregate_provenance"

#: Tool name → authorized operation (the only operations that exist).
ANALYTICS_OPERATIONS: dict[str, str] = {
    TOOL_INSIGHT_DISCOVERY: "discovery",
    TOOL_INSIGHT_AGGREGATION: "aggregation",
    TOOL_INSIGHT_AGGREGATE_PROVENANCE: "provenance",
}

#: Hard bounds (bounded output is part of the contract, not a preference).
MAX_DISCOVERY_RESULTS = 25
MAX_AGGREGATE_GROUPS = 50
MAX_PROVENANCE_SNAPSHOTS = 100
#: Longest period an analytics operation may address (10 years, inclusive).
MAX_PERIOD_DAYS = 3_660
#: Activity containment terms shorter than this would scan without discriminating.
MIN_ACTIVITY_TERM_LENGTH = 3
MAX_TEXT_FILTER_LENGTH = 128
#: An absolute tolerance may not exceed this (defensive; kg CO₂e).
MAX_TOLERANCE_KG = Decimal("1000000000")
#: A relative tolerance may not exceed this percentage.
MAX_TOLERANCE_PERCENT = Decimal("100")

#: The closed discovery filter vocabulary.
DISCOVERY_FILTERS: tuple[str, ...] = (
    "start_date",
    "end_date",
    "reporting_year",
    "co2e_kg",
    "co2e_tolerance_kg",
    "co2e_tolerance_pct",
    "co2e_approx",
    "activity",
    "scope",
    "supplier_id",
    "facility_id",
    "asset_id",
)

#: The closed aggregation / provenance group-by vocabulary (PO D-03 initial set
#: plus supplier, which the same authorization explicitly includes).
AGGREGATION_DIMENSIONS: tuple[str, ...] = (
    "scope",
    "month",
    "year",
    "activity",
    "supplier",
    "facility",
    "asset",
)

#: Reason codes (machine-readable; never free-form prose).
REASON_NO_FILTERS = "no_discovery_filters"
REASON_UNKNOWN_PARAMETER = "unknown_parameter"
REASON_INVALID_DATE = "invalid_date"
REASON_INVALID_RANGE = "invalid_date_range"
REASON_PERIOD_TOO_LONG = "period_too_long"
REASON_INVALID_NUMBER = "invalid_number"
REASON_NEGATIVE_AMOUNT = "negative_amount"
REASON_TOLERANCE_REQUIRED = "amount_tolerance_required"
REASON_TOLERANCE_CONFLICT = "conflicting_tolerance"
REASON_INVALID_SCOPE = "invalid_scope"
REASON_ACTIVITY_TOO_SHORT = "activity_term_too_short"
REASON_TEXT_TOO_LONG = "text_parameter_too_long"
REASON_UNSUPPORTED_DIMENSION = "unsupported_group_by"
REASON_GROUP_KEY_REQUIRED = "missing_group_key"
REASON_MISSING_PERIOD = "missing_period"


@dataclass(frozen=True, slots=True)
class AmountBounds:
    """The inclusive kg CO₂e range a discovery amount filter resolves to."""

    low: Decimal
    high: Decimal
    exact: bool


def _coerce_decimal(value: Any) -> Optional[Decimal]:
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        try:
            return Decimal(value.strip())
        except (InvalidOperation, ValueError):
            return None
    return None


def parse_iso_date(value: Any) -> Optional[date]:
    """Parse an ISO calendar date (``YYYY-MM-DD``); ``None`` when not a date."""
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def parse_int(value: Any) -> Optional[int]:
    """Parse a bounded integer parameter; ``None`` when not an integer."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def parse_bool(value: Any) -> Optional[bool]:
    """Parse a boolean parameter expressed as a bool or ``"true"``/``"false"``."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("true", "1", "yes"):
            return True
        if text in ("false", "0", "no"):
            return False
    return None


def canonical_scope(value: Any) -> Optional[str]:
    """Normalise a scope filter onto the canonical stored vocabulary.

    Accepts the canonical values verbatim, the historical UI aliases
    (``scope1``/``scope 1``) and the bare digits ``1``/``2``/``3``. Unknown values
    return ``None`` and the caller rejects them — nothing is guessed.
    """
    if value is None:
        return None
    text = " ".join(str(value).strip().lower().replace("_", " ").split())
    if text in ("1", "2", "3"):
        return f"Scope {text}"
    if text.startswith("scope") and text[5:].strip() in ("1", "2", "3"):
        return f"Scope {text[5:].strip()}"
    for scope in Scope:
        if text == scope.value.lower():
            return scope.value
    return None


def validate_limit(value: Any, *, maximum: int, default: int) -> tuple[Optional[int], Optional[str]]:
    """Validate a bounded result limit (an out-of-range limit is a rejection)."""
    if value is None or value == "":
        return default, None
    parsed = parse_int(value)
    if parsed is None or parsed < 1 or parsed > maximum:
        return None, REASON_INVALID_NUMBER
    return parsed, None


def validate_discovery(filters: Mapping[str, Any]) -> Optional[str]:
    """Validate a discovery filter set against the closed vocabulary.

    Returns a machine-readable reason code, or ``None`` when acceptable. Unknown
    keys are rejected (there is no pass-through surface).
    """
    if not isinstance(filters, Mapping):
        return REASON_UNKNOWN_PARAMETER
    if set(filters) - set(DISCOVERY_FILTERS):
        return REASON_UNKNOWN_PARAMETER

    supplied = {k: v for k, v in filters.items() if v is not None and v != ""}
    if not supplied:
        return REASON_NO_FILTERS

    for key in ("start_date", "end_date"):
        if key in supplied and parse_iso_date(supplied[key]) is None:
            return REASON_INVALID_DATE
    start = parse_iso_date(supplied.get("start_date"))
    end = parse_iso_date(supplied.get("end_date"))
    if start and end:
        if end < start:
            return REASON_INVALID_RANGE
        if (end - start) > timedelta(days=MAX_PERIOD_DAYS):
            return REASON_PERIOD_TOO_LONG

    if "reporting_year" in supplied:
        year = parse_int(supplied["reporting_year"])
        if year is None or not (1900 <= year <= 2999):
            return REASON_INVALID_NUMBER

    amount = _coerce_decimal(supplied.get("co2e_kg"))
    if "co2e_kg" in supplied:
        if amount is None:
            return REASON_INVALID_NUMBER
        if amount < 0:
            return REASON_NEGATIVE_AMOUNT
    tolerance_kg = _coerce_decimal(supplied.get("co2e_tolerance_kg"))
    tolerance_pct = _coerce_decimal(supplied.get("co2e_tolerance_pct"))
    if "co2e_tolerance_kg" in supplied and (
        tolerance_kg is None or tolerance_kg < 0 or tolerance_kg > MAX_TOLERANCE_KG
    ):
        return REASON_INVALID_NUMBER
    if "co2e_tolerance_pct" in supplied and (
        tolerance_pct is None or tolerance_pct < 0 or tolerance_pct > MAX_TOLERANCE_PERCENT
    ):
        return REASON_INVALID_NUMBER
    if tolerance_kg is not None and tolerance_pct is not None:
        return REASON_TOLERANCE_CONFLICT
    if (tolerance_kg is not None or tolerance_pct is not None) and amount is None:
        return REASON_TOLERANCE_REQUIRED
    approximate = parse_bool(supplied.get("co2e_approx"))
    if "co2e_approx" in supplied and approximate is None:
        return REASON_INVALID_NUMBER
    # An approximate amount without an explicit, determinable tolerance is a
    # clarification, never a guess (PO D-02).
    if approximate and amount is not None and tolerance_kg is None and tolerance_pct is None:
        return REASON_TOLERANCE_REQUIRED

    if "scope" in supplied and canonical_scope(supplied["scope"]) is None:
        return REASON_INVALID_SCOPE

    if "activity" in supplied:
        term = str(supplied["activity"]).strip()
        if len(term) < MIN_ACTIVITY_TERM_LENGTH:
            return REASON_ACTIVITY_TOO_SHORT
        if len(term) > MAX_TEXT_FILTER_LENGTH:
            return REASON_TEXT_TOO_LONG

    for key in ("supplier_id", "facility_id", "asset_id"):
        if key in supplied and len(str(supplied[key]).strip()) > MAX_TEXT_FILTER_LENGTH:
            return REASON_TEXT_TOO_LONG
    return None


def resolve_amount_bounds(filters: Mapping[str, Any]) -> Optional[AmountBounds]:
    """Resolve the inclusive kg CO₂e bounds for a validated filter set.

    Exact matching is zero tolerance; an explicit tolerance (absolute, or
    relative to the stated amount) widens the range symmetrically. Returns
    ``None`` when no amount filter was supplied.
    """
    amount = _coerce_decimal(filters.get("co2e_kg"))
    if amount is None:
        return None
    tolerance_kg = _coerce_decimal(filters.get("co2e_tolerance_kg"))
    tolerance_pct = _coerce_decimal(filters.get("co2e_tolerance_pct"))
    if tolerance_kg is not None:
        delta = tolerance_kg
    elif tolerance_pct is not None:
        delta = (amount * tolerance_pct / Decimal("100")).quantize(Decimal("0.000001"))
    else:
        delta = Decimal("0")
    low = amount - delta
    if low < 0:
        low = Decimal("0")
    return AmountBounds(low=low, high=amount + delta, exact=delta == 0)


def validate_group_by(dimension: Any) -> Optional[str]:
    """Validate a group-by dimension against the closed allowlist."""
    if dimension is None or str(dimension) == "":
        return REASON_UNSUPPORTED_DIMENSION
    if str(dimension) not in AGGREGATION_DIMENSIONS:
        return REASON_UNSUPPORTED_DIMENSION
    return None


def validate_period(start: Any, end: Any) -> tuple[Optional[date], Optional[date], Optional[str]]:
    """Validate an explicit, bounded period (both ends required, inclusive)."""
    start_date = parse_iso_date(start)
    end_date = parse_iso_date(end)
    if start_date is None or end_date is None:
        return None, None, REASON_MISSING_PERIOD if not (start or end) else REASON_INVALID_DATE
    if end_date < start_date:
        return None, None, REASON_INVALID_RANGE
    if (end_date - start_date) > timedelta(days=MAX_PERIOD_DAYS):
        return None, None, REASON_PERIOD_TOO_LONG
    return start_date, end_date, None


@dataclass(frozen=True, slots=True)
class InsightQueryPlan:
    """A bounded, typed analytics plan (the only thing a planner may produce).

    The plan is *not* authoritative: the deterministic execution layer
    re-validates every dimension, filter and bound before any data is read, and
    the I2 boundary decides authorization.
    """

    operation: str
    tool: str
    tool_input: dict[str, Any] = field(default_factory=dict)
    reason: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "tool": self.tool,
            "tool_input": dict(self.tool_input),
            "reason": self.reason,
            "contract_version": ANALYTICS_CONTRACT_VERSION,
        }


def bounded_pair(items: Sequence[Any], limit: int) -> tuple[list[Any], bool]:
    """Apply a bound and report whether truncation occurred."""
    rows = list(items)
    if len(rows) <= limit:
        return rows, False
    return rows[:limit], True
