"""CarbonTally Insight — deterministic bounded query planner (Phase 8 analytics).

Authorization: PO Insight Discovery-Aggregation-Provenance package (2026-09-22),
under the D-01 rule that the LLM must never become a query engine. This planner
is therefore **deterministic regular-expression parsing only**:

* no provider/LLM call, no database access, no SQL, no authorization decision;
* it emits only the closed, predefined schema from ``domain.insight_query``;
* an unrecognised question is reported as ``unsupported`` and the caller falls
  back to the ratified four-tool keyword classifier (existing behaviour is
  preserved);
* a recognised analytics question that lacks a determinable parameter is
  reported as ``clarification`` — never guessed;
* a recognised analytics question with an explicitly invalid value is reported as
  ``invalid`` (a deterministic rejection, not a guess).

The planner's output is *advisory*: every produced parameter is re-validated by
``domain.insight_query`` inside the tool before any data is read, and the I2
boundary decides authorization independently.
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from domain.insight_quality import (
    TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
    TOOL_INSIGHT_DATA_QUALITY,
)
from domain.insight_query import (
    REASON_UNSUPPORTED_DIMENSION,
    TEMPORAL_COMPARISON_DIMENSIONS,
    TOOL_INSIGHT_AGGREGATE_PROVENANCE,
    TOOL_INSIGHT_AGGREGATION,
    TOOL_INSIGHT_DISCOVERY,
    TOOL_INSIGHT_TEMPORAL_COMPARISON,
    canonical_scope,
)

STATUS_PLANNED = "planned"
STATUS_CLARIFICATION = "clarification"
STATUS_UNSUPPORTED = "unsupported"
STATUS_INVALID = "invalid"

REASON_PERIOD_REQUIRED = "period_required"
REASON_GROUP_KEY_REQUIRED = "group_key_required"
REASON_TOLERANCE_REQUIRED = "amount_tolerance_required"
REASON_INVALID_SCOPE = "invalid_scope"
#: P2 — a comparison question whose two explicit periods cannot be determined.
REASON_COMPARISON_PERIODS_REQUIRED = "comparison_periods_required"
#: P3 — a reproducibility question naming no identifiable calculation.
REASON_SNAPSHOT_REQUIRED = "snapshot_identifier_required"

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_ISO_MONTH = re.compile(r"\b(\d{4})-(\d{2})\b")
_MONTH_YEAR = re.compile(r"\b(" + "|".join(_MONTHS) + r")\s+(\d{4})\b")
_YEAR = re.compile(r"\b(20\d{2})\b")
_AMOUNT_BEFORE = re.compile(
    r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:kg|kgs|kilograms?)?\s*(?:of\s+)?"
    r"(?:co2e|co2|carbon dioxide)\b"
)
_AMOUNT_AFTER = re.compile(
    r"\b(?:co2e|co2|carbon dioxide)\s*(?:of\s*|value\s+of\s*)?"
    r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:kg|kgs|kilograms?)?\b"
)
_APPROXIMATE = re.compile(r"\b(approximately|approx|about|around|roughly|circa)\b")
_TOLERANCE_KG = re.compile(
    r"(?:\+/-|\+-|\u00b1|plus or minus|within|tolerance of|tolerance)\s*"
    r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:kg|kgs|kilograms?)?\b"
)
_TOLERANCE_PCT = re.compile(
    r"(?:\+/-|\+-|\u00b1|plus or minus|within|tolerance of|tolerance)?\s*"
    r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:%|(?:percent|per cent)\b)"
)
_SCOPE = re.compile(r"\bscope\s*([0-9]{1,2})\b")
_SCOPE_CANONICAL = re.compile(r"\b(outside of scopes)\b")
_QUOTED = re.compile(r"[\"'\u201c\u2018]([^\"'\u201d\u2019]{3,128})[\"'\u201d\u2019]")
_ACTIVITY_LABEL = re.compile(r"\bactivity(?:\s+type)?\s*[:\-]\s*([^,.;?]{3,128})")
_REPORTING_YEAR = re.compile(r"\breporting\s+year\s*(?:of\s*)?(\d{4})\b")

#: P2 — a *neutral* comparison signal. Directional phrasings ("higher than",
#: "lower than", "up from", "down from") are deliberately **absent**: the planner
#: does not interpret comparative direction, so a question that depends on it
#: stays unsupported rather than being silently mapped onto a reversed baseline.
_COMPARISON = re.compile(
    r"\b(?:compare[sd]?|comparison|versus|vs|difference\s+between|change\s+(?:between|from))\b"
)

#: P3 — a data-quality signal. The scan is executed by the existing
#: ValidationEngine, so the planner contributes only the period.
_QUALITY = re.compile(
    r"\b(?:data\s+quality|quality|completeness|incomplete|missing|unmapped|"
    r"no\s+unit|missing\s+unit)\b"
)

#: P3 — a reproducibility signal. It names no accounting concept: it asks what
#: CarbonTally can technically demonstrate for an identified calculation.
_REPRODUCIBILITY = re.compile(
    r"\b(?:reproduc\w*|tamper\w*|audit\s+trail\s+for|verify\s+the\s+calculation)\b"
)

#: P3 — a well-formed record identifier (the same UUID form the ratified tools
#: accept). A bounded identifier pattern, not free-text parsing: the tool and the
#: organisation-scoped read re-validate whatever is extracted.
_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

#: P2 — the explicit periods a comparison may address, using only the vocabulary
#: the planner already understands (month name + year, ``YYYY-MM``, ``YYYY``).
#: No new date syntax, no time zone handling and no natural-language inference.
_COMPARISON_PERIOD = re.compile(
    r"(?:\b(?P<monthyear>" + "|".join(_MONTHS) + r")\s+(?P<myear>20\d{2})\b)"
    r"|(?:\b(?P<iso_year>20\d{2})-(?P<iso_month>0[1-9]|1[0-2])\b)"
    r"|(?:\b(?P<year>20\d{2})\b)"
)

_BY_DIMENSION = re.compile(
    r"\b(?:by|per|grouped\s+by|breakdown\s+by|split\s+by|for\s+each)\s+"
    r"(scope|month|monthly|year|yearly|activity|activity\s+type|supplier|"
    r"facility|facilities|site|sites|asset|assets)\b"
)
_BREAKDOWN = re.compile(
    r"\b(breakdown|break\s+down|totals?\s+by|compare\s+by|distribution)\b"
)
_PROVENANCE = re.compile(
    r"\b(based\s+on|made\s+up\s+of|contribut\w*|which\s+calculations?\s+"
    r"(?:make\s+up|are\s+behind|contribute)|evidence\s+behind|comes?\s+from)\b"
)
_DISCOVERY = re.compile(
    r"\b(which\s+calculation|which\s+calculations|which\s+record|which\s+line|"
    r"find|locate|why\s+did|what\s+happened|what\s+caused|trace)\b"
)

_DIMENSION_ALIASES = {
    "scope": "scope",
    "month": "month",
    "monthly": "month",
    "year": "year",
    "yearly": "year",
    "activity": "activity",
    "activity type": "activity",
    "supplier": "supplier",
    "facility": "facility",
    "facilities": "facility",
    "site": "facility",
    "sites": "facility",
    "asset": "asset",
    "assets": "asset",
}


def _result(status: str, **kwargs: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "tool": None,
        "tool_input": {},
        "operation": None,
        "reason": None,
    }
    payload.update(kwargs)
    return payload


def _decimal(raw: str) -> Optional[Decimal]:
    try:
        return Decimal(raw.replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def parse_period(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract an explicit calendar period (inclusive ISO date bounds).

    Deterministic precedence: ISO date range → single ISO date → ISO month →
    month-and-year → four-digit year. Returns ``(start, end)`` with ``None`` for
    anything the text does not state explicitly (nothing is defaulted).
    """
    dates = _ISO_DATE.findall(text)
    if len(dates) >= 2:
        first, second = dates[0], dates[1]
        try:
            start = date(int(first[0]), int(first[1]), int(first[2]))
            end = date(int(second[0]), int(second[1]), int(second[2]))
        except ValueError:
            return None, None
        if start <= end:
            return start.isoformat(), end.isoformat()
        return end.isoformat(), start.isoformat()
    if len(dates) == 1:
        year, month, day = dates[0]
        try:
            single = date(int(year), int(month), int(day))
        except ValueError:
            return None, None
        return single.isoformat(), single.isoformat()

    iso_month = _ISO_MONTH.search(text)
    if iso_month:
        return _month_bounds(int(iso_month.group(1)), int(iso_month.group(2)))

    named = _MONTH_YEAR.search(text)
    if named:
        return _month_bounds(int(named.group(2)), _MONTHS[named.group(1)])

    year = _YEAR.search(text)
    if year and not _REPORTING_YEAR.search(text):
        value = int(year.group(1))
        return f"{value:04d}-01-01", f"{value:04d}-12-31"
    return None, None


def _month_bounds(year: int, month: int) -> tuple[Optional[str], Optional[str]]:
    if not (1 <= month <= 12):
        return None, None
    start = date(year, month, 1)
    following = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    last = date.fromordinal(following.toordinal() - 1)
    return start.isoformat(), last.isoformat()


def _comparison_period_bounds(text: str) -> list[tuple[str, str]]:
    """The explicit periods a comparison question names, in textual order (P2).

    Only the planner's existing month/year vocabulary is recognised. An
    out-of-range month is skipped rather than corrected, and a repeated mention of
    the same period collapses to a single entry, so an identical-period
    comparison cannot masquerade as a two-period comparison.
    """
    periods: list[tuple[str, str]] = []
    for match in _COMPARISON_PERIOD.finditer(text):
        if match.group("monthyear"):
            bounds = _month_bounds(
                int(match.group("myear")), _MONTHS[match.group("monthyear")]
            )
        elif match.group("iso_year"):
            bounds = _month_bounds(
                int(match.group("iso_year")), int(match.group("iso_month"))
            )
        else:
            year = int(match.group("year"))
            bounds = (f"{year:04d}-01-01", f"{year:04d}-12-31")
        if bounds[0] is None or bounds[1] is None:
            continue
        if bounds not in periods:
            periods.append(bounds)
    return periods


def extract_amount(text: str) -> tuple[Optional[str], bool, Optional[str], Optional[str]]:
    """Extract ``(amount, approximate, tolerance_kg, tolerance_pct)`` as strings."""
    match = _AMOUNT_BEFORE.search(text) or _AMOUNT_AFTER.search(text)
    amount = match.group(1).replace(",", "") if match else None
    approximate = bool(_APPROXIMATE.search(text))
    tolerance_kg: Optional[str] = None
    tolerance_pct: Optional[str] = None
    pct = _TOLERANCE_PCT.search(text)
    if pct:
        value = _decimal(pct.group(1))
        if value is not None and value > 0:
            tolerance_pct = str(value)
    if tolerance_pct is None:
        kg = _TOLERANCE_KG.search(text)
        if kg:
            value = _decimal(kg.group(1))
            if value is not None and value > 0:
                tolerance_kg = str(value)
    return amount, approximate, tolerance_kg, tolerance_pct


def extract_scope(text: str) -> tuple[Optional[str], bool]:
    """Extract a scope filter → ``(canonical_scope, invalid)``."""
    canonical = _SCOPE_CANONICAL.search(text)
    if canonical:
        scope = canonical_scope(canonical.group(1))
        return scope, scope is None
    match = _SCOPE.search(text)
    if not match:
        return None, False
    scope = canonical_scope(match.group(1))
    return scope, scope is None


def extract_activity(text: str) -> Optional[str]:
    """Extract an activity term (quoted, or explicitly labelled ``activity:``)."""
    labelled = _ACTIVITY_LABEL.search(text)
    if labelled:
        return labelled.group(1).strip()
    quoted = _QUOTED.search(text)
    if quoted:
        return quoted.group(1).strip()
    return None


def detect_dimension(text: str) -> Optional[str]:
    """The aggregated dimension a question asks for, or ``None``."""
    match = _BY_DIMENSION.search(text)
    if match:
        raw = " ".join(match.group(1).split())
        return _DIMENSION_ALIASES.get(raw)
    if _BREAKDOWN.search(text):
        for word, dimension in _DIMENSION_ALIASES.items():
            if re.search(rf"\b{re.escape(word)}\b", text):
                return dimension
    return None


def _provenance_group_key(
    dimension: str, scope: Optional[str], start: Optional[str]
) -> Optional[str]:
    """The explicit group key a provenance question names, or ``None``."""
    if dimension == "scope":
        return scope
    if dimension == "month" and start is not None:
        return start[:7]
    if dimension == "year" and start is not None:
        return start[:4]
    return None


def _implies_unresolvable_dimension(question: str) -> bool:
    """Whether the question names a dimension whose key cannot be resolved here.

    Facility, supplier and asset identities are organisation-owned catalogue ids;
    a question that names one of those dimensions without naming a resolvable key
    is a clarification, never an inferred identity.
    """
    return any(
        re.search(rf"\b{word}\b", question)
        for word in (
            "facility",
            "facilities",
            "site",
            "sites",
            "supplier",
            "suppliers",
            "asset",
            "assets",
            "activity",
        )
    )


def _implied_provenance_dimension(
    question: str, scope: Optional[str], start: Optional[str]
) -> Optional[str]:
    """The dimension implied by the group key the question names, or ``None``.

    Only deterministic implications are used: an explicit scope, an explicit
    month, or an explicit year. Nothing is guessed from free text.
    """
    if scope:
        return "scope"
    if start is None:
        return None
    if re.search(r"\b(month|monthly)\b", question) or _MONTH_YEAR.search(question):
        return "month"
    if _ISO_DATE.search(question) or _ISO_MONTH.search(question):
        return "month"
    return "year"


def plan_question(text: str) -> dict[str, Any]:
    """Plan a bounded analytics question deterministically.

    Returns exactly one of four statuses:

    * ``planned`` — a bounded tool input was produced;
    * ``clarification`` — an analytics question missing a determinable parameter;
    * ``invalid`` — an analytics question containing an explicitly invalid value;
    * ``unsupported`` — not an analytics question (the caller keeps existing
      behaviour, so no previously-working question changes meaning).
    """
    question = " ".join((text or "").strip().lower().split())
    if not question:
        return _result(STATUS_UNSUPPORTED)

    start, end = parse_period(question)
    amount, approximate, tolerance_kg, tolerance_pct = extract_amount(question)
    scope, scope_invalid = extract_scope(question)
    activity = extract_activity(question)
    dimension = detect_dimension(question)
    reporting_year = _REPORTING_YEAR.search(question)
    wants_provenance = bool(_PROVENANCE.search(question))
    wants_discovery = bool(_DISCOVERY.search(question))
    # P2 — a neutral comparison word plus two explicit periods is the only shape
    # the planner will map onto the temporal-comparison contract.
    wants_comparison = bool(_COMPARISON.search(question))
    comparison_periods = _comparison_period_bounds(question) if wants_comparison else []
    # P3 — quality and reproducibility signals (both are answered only by the
    # existing deterministic machinery; the planner contributes the period or the
    # identifier and nothing else).
    wants_quality = bool(_QUALITY.search(question))
    wants_reproducibility = bool(_REPRODUCIBILITY.search(question))

    analytics_signal = bool(
        dimension
        or amount
        or start
        or scope
        or activity
        or reporting_year
        or wants_provenance
        or wants_discovery
        or wants_comparison
        or wants_quality
        or wants_reproducibility
    )
    if not analytics_signal:
        return _result(STATUS_UNSUPPORTED)
    if scope_invalid:
        return _result(STATUS_INVALID, reason=REASON_INVALID_SCOPE)

    # P2 — temporal comparison. A *neutral* comparison word always routes to the
    # comparison contract: fewer than two explicit periods is a clarification
    # ("which two periods?"), never a silent single-period aggregation of a
    # question that asked for a comparison.
    if wants_comparison:
        if len(comparison_periods) != 2:
            return _result(
                STATUS_CLARIFICATION, reason=REASON_COMPARISON_PERIODS_REQUIRED
            )
        # A dimension the comparison contract cannot express is an explicit
        # rejection, never a silently dropped grouping.
        if dimension is not None and dimension not in TEMPORAL_COMPARISON_DIMENSIONS:
            return _result(STATUS_INVALID, reason=REASON_UNSUPPORTED_DIMENSION)
        (a_start, a_end), (b_start, b_end) = comparison_periods
        comparison_input: dict[str, Any] = {
            "period_a_start": a_start,
            "period_a_end": a_end,
            "period_b_start": b_start,
            "period_b_end": b_end,
        }
        if dimension is not None:
            comparison_input["group_by"] = dimension
        return _result(
            STATUS_PLANNED,
            tool=TOOL_INSIGHT_TEMPORAL_COMPARISON,
            operation="temporal_comparison",
            tool_input=comparison_input,
        )

    # P3 — data-quality scan (family 14). A quality keyword plus an explicit
    # bounded period; the scan itself is executed entirely by the existing
    # ValidationEngine, so the planner supplies nothing but the period.
    if _QUALITY.search(question):
        if start is None or end is None:
            return _result(STATUS_CLARIFICATION, reason=REASON_PERIOD_REQUIRED)
        return _result(
            STATUS_PLANNED,
            tool=TOOL_INSIGHT_DATA_QUALITY,
            operation="data_quality",
            tool_input={"start_date": start, "end_date": end},
        )

    # P3 — reproducibility of one identified calculation (family 16). Requires a
    # well-formed identifier; without one the truthful answer is a clarification,
    # because nothing may be guessed and no record may be searched for.
    if _REPRODUCIBILITY.search(question):
        identifiers = _UUID.findall(question)
        if not identifiers:
            return _result(STATUS_CLARIFICATION, reason=REASON_SNAPSHOT_REQUIRED)
        return _result(
            STATUS_PLANNED,
            tool=TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
            operation="calculation_reproducibility",
            tool_input={"snapshot_id": identifiers[0]},
        )

    # Provenance — the contributing calculations behind one aggregate cell. It
    # requires both an explicit dimension and an explicit group key; neither is
    # guessed, and no identifier is invented.
    if wants_provenance:
        # The dimension may be implied by the group key the question names
        # (scope 1, February 2024, the 2024 total); nothing is invented beyond
        # that, and an unresolvable key stays a clarification.
        provenance_dimension = dimension or _implied_provenance_dimension(question, scope, start)
        if provenance_dimension is None or (
            dimension is None and _implies_unresolvable_dimension(question)
        ):
            return _result(STATUS_CLARIFICATION, reason=REASON_GROUP_KEY_REQUIRED)
        group_key = _provenance_group_key(provenance_dimension, scope, start)
        if group_key is None:
            return _result(STATUS_CLARIFICATION, reason=REASON_GROUP_KEY_REQUIRED)
        if start is None or end is None:
            return _result(STATUS_CLARIFICATION, reason=REASON_PERIOD_REQUIRED)
        return _result(
            STATUS_PLANNED,
            tool=TOOL_INSIGHT_AGGREGATE_PROVENANCE,
            operation="provenance",
            tool_input={
                "group_by": provenance_dimension,
                "group_key": group_key,
                "start_date": start,
                "end_date": end,
            },
        )

    # Aggregation — an explicit dimension and an explicit bounded period.
    if dimension is not None:
        if start is None or end is None:
            return _result(STATUS_CLARIFICATION, reason=REASON_PERIOD_REQUIRED)
        return _result(
            STATUS_PLANNED,
            tool=TOOL_INSIGHT_AGGREGATION,
            operation="aggregation",
            tool_input={
                "group_by": dimension,
                "start_date": start,
                "end_date": end,
            },
        )

    # Discovery — at least one typed filter.
    filters: dict[str, Any] = {}
    if start is not None:
        filters["start_date"] = start
        filters["end_date"] = end
    if reporting_year:
        filters["reporting_year"] = reporting_year.group(1)
    if amount is not None:
        filters["co2e_kg"] = amount
        if tolerance_kg is not None:
            filters["co2e_tolerance_kg"] = tolerance_kg
        if tolerance_pct is not None:
            filters["co2e_tolerance_pct"] = tolerance_pct
        if approximate:
            filters["co2e_approx"] = True
    if scope:
        filters["scope"] = scope
    if activity:
        filters["activity"] = activity
    if not filters:
        return _result(STATUS_UNSUPPORTED)
    # An approximate amount without a determinable tolerance is a clarification,
    # never a silently invented tolerance (PO D-02).
    if (
        amount is not None
        and approximate
        and tolerance_kg is None
        and tolerance_pct is None
    ):
        return _result(STATUS_CLARIFICATION, reason=REASON_TOLERANCE_REQUIRED)
    return _result(
        STATUS_PLANNED,
        tool=TOOL_INSIGHT_DISCOVERY,
        operation="discovery",
        tool_input=filters,
    )
