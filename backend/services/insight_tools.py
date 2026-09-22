"""CarbonTally Insight I3 — ratified tool registry + deterministic execution.

Authorization: PO I3 Tool Catalogue Ratification Decision Record (2026-09-21).
The catalogue is closed at four tools; adding one requires a separate PO decision.
Nothing here is an authorization decision: every invocation resolves the caller's
scope through the closed I2 boundary (``api.insight_authz.authorize_insight_scope``)
and re-checks the resolved object's organisation against that scope. A reference or
id is never a grant.

Field exposure rule (PO §7): expose only fields the caller is already entitled to
see through the existing application model; where visibility is not established by
an existing projection, omit the field rather than infer permission. Allowlists
derive from already-authorized surfaces: ``api.contracts.ReportOut`` (report),
the existing report-version columns + REPORTING_LIFECYCLE_SPEC §30.3 (version and
state), the ratified CalculationSnapshot provenance set (PO §3.4), and the
disclosure projection (evidence identity + coverage counts).

Read-only, deterministic, no provider, no SQL, no mutation (PO §2/§13).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import logging
from typing import TYPE_CHECKING, Any, Optional

from fastapi import HTTPException

from core.types import DateRange
# OHD D-02 — the API packages are imported lazily/TYPE_CHECKING only: importing
# them at module load closed a cycle
# (services.insight_tools -> api.* -> services.insight_tools).
if TYPE_CHECKING:  # pragma: no cover - type-only
    from api.dependencies import RepositoryBundle
    from api.insight_authz import InsightAccess
    from auth import AuthUser
from domain.disclosure import IMMUTABLE_REPORT_VERSION_STATUSES
from domain.insight_query import (
    AGGREGATION_DIMENSIONS,
    DISCOVERY_FILTERS,
    MAX_AGGREGATE_GROUPS,
    MAX_DISCOVERY_RESULTS,
    MAX_PROVENANCE_SNAPSHOTS,
    REASON_TOLERANCE_REQUIRED,
    TEMPORAL_COMPARISON_DIMENSIONS,
    TOOL_INSIGHT_AGGREGATE_PROVENANCE,
    TOOL_INSIGHT_AGGREGATION,
    TOOL_INSIGHT_DISCOVERY,
    TOOL_INSIGHT_TEMPORAL_COMPARISON,
    canonical_scope,
    compare_totals,
    order_comparison_keys,
    parse_int,
    validate_comparison_dimension,
    validate_comparison_periods,
    validate_discovery,
    validate_group_by,
    validate_limit,
    validate_period,
)
from domain.insight_tool import (
    MAX_IDENTIFIER_LENGTH,
    InsightReference,
    ToolDefinition,
    ToolInputSpec,
    ToolResult,
    ToolStatus,
    bounded,
)

logger = logging.getLogger(__name__)

TOOL_REPORT_LOOKUP = "report_lookup"
TOOL_REPORT_VERSION_LOOKUP = "report_version_lookup"
TOOL_REPORT_EVIDENCE_LOOKUP = "report_evidence_lookup"
TOOL_CALCULATION_SNAPSHOT_LOOKUP = "calculation_snapshot_lookup"
# The Phase 8 Insight analytics tool names (``insight_discovery``,
# ``insight_aggregation``, ``insight_aggregate_provenance``) are imported from
# ``domain.insight_query`` so the contract module remains their single definition.

#: Report fields (api.contracts.ReportOut subset). Omitted: signed/artefact URLs
#: (AGENTS.md §68), internal actors, unbounded/internal content, progress internals.
_REPORT_FIELDS: tuple[str, ...] = (
    "id", "organization_id", "report_type", "reporting_year",
    "report_name", "status", "created_at", "completed_at",
)
#: Version identity + lifecycle state (§30.3). Omitted: content, file_url/file_name,
#: created_by, notes, change_summary.
_REPORT_VERSION_FIELDS: tuple[str, ...] = (
    "id", "report_id", "version_number", "status", "is_current", "created_at",
)
#: Evidence line identity/provenance only — raw extracted content omitted (PO §7).
_EVIDENCE_LINE_FIELDS: tuple[str, ...] = (
    "disclosure_value_id", "requirement_version_id", "calculation_snapshot_id",
    "evidence_line_item_id", "line_number", "materialisation_kind",
)
_COVERAGE_FIELDS: tuple[str, ...] = (
    "reference_count", "line_linked_count", "snapshot_linked_count",
)
#: Ratified CalculationSnapshot provenance set (PO §3.4). Omitted: internal actors,
#: internal ingest identifiers, source_file/source_page (not named — omitted, not inferred).
_SNAPSHOT_FIELDS: tuple[str, ...] = (
    "id", "organization_id", "activity", "activity_type", "quantity",
    "quantity_unit", "co2e_multiplier", "co2e_kg", "scope", "date",
    "reporting_year", "methodology", "algorithm_version", "content_hash",
    "factor_id", "factor_kind", "customer_factor_id", "factor_source",
    "source_item_id", "source_line_item_id",
)

TOOL_DEFINITIONS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        name=TOOL_REPORT_LOOKUP,
        purpose="Retrieve an authorized report instance with its version summary and lifecycle state.",
        read_only=True,
        input=ToolInputSpec(required=("report_id",)),
        authorization="i2-boundary: authorize_insight_scope + object organisation re-check",
        output_fields=_REPORT_FIELDS + ("versions", "current_version", "is_approved_or_final"),
        reference_kinds=("report", "report_version"),
    ),
    ToolDefinition(
        name=TOOL_REPORT_VERSION_LOOKUP,
        purpose="Retrieve an authorized report version and its lifecycle state.",
        read_only=True,
        input=ToolInputSpec(required=(), optional=("version_id", "report_id", "version_number")),
        authorization="i2-boundary: authorize_insight_scope + object organisation re-check",
        output_fields=_REPORT_VERSION_FIELDS + ("report_organization_id",),
        reference_kinds=("report_version", "report"),
    ),
    ToolDefinition(
        name=TOOL_REPORT_EVIDENCE_LOOKUP,
        purpose="Retrieve authorized evidence references linked to a report version.",
        read_only=True,
        input=ToolInputSpec(required=("report_version_id",)),
        authorization="i2-boundary: authorize_insight_scope + object organisation re-check",
        output_fields=("report_version", "lines", "coverage"),
        reference_kinds=("report_version", "evidence_line_item", "calculation_snapshot"),
    ),
    ToolDefinition(
        name=TOOL_CALCULATION_SNAPSHOT_LOOKUP,
        purpose="Retrieve an authorized authoritative CalculationSnapshot result and its provenance.",
        read_only=True,
        input=ToolInputSpec(required=("snapshot_id",)),
        authorization="i2-boundary: authorize_insight_scope + object organisation re-check",
        output_fields=_SNAPSHOT_FIELDS,
        reference_kinds=("calculation_snapshot", "evidence_line_item"),
    ),
    ToolDefinition(
        name=TOOL_INSIGHT_DISCOVERY,
        purpose=(
            "Find the authorized calculation records that match bounded typed criteria "
            "(date/date range, reporting year, CO2e amount with an explicit tolerance, "
            "activity, scope, supplier, facility, asset)."
        ),
        read_only=True,
        input=ToolInputSpec(optional=DISCOVERY_FILTERS + ("limit",)),
        authorization="i2-boundary: authorize_insight_scope + organisation-scoped query",
        output_fields=("match_count", "match_count_capped", "candidates", "basis"),
        reference_kinds=("calculation_snapshot", "evidence_line_item"),
    ),
    ToolDefinition(
        name=TOOL_INSIGHT_AGGREGATION,
        purpose=(
            "Sum authorized emissions in kg CO2e by one allowlisted dimension "
            "(scope, month, year, activity, supplier, facility, asset) over an "
            "explicit bounded period."
        ),
        read_only=True,
        input=ToolInputSpec(required=("group_by", "start_date", "end_date"), optional=("limit",)),
        authorization="i2-boundary: authorize_insight_scope + organisation-scoped query",
        output_fields=(
            "group_by",
            "period",
            "groups",
            "group_count",
            "groups_truncated",
            "row_count",
            "total_co2e_kg",
            "total_is_complete",
            "basis",
            "provenance_tool",
        ),
        reference_kinds=(),
    ),
    ToolDefinition(
        name=TOOL_INSIGHT_AGGREGATE_PROVENANCE,
        purpose=(
            "Identify the bounded set of authorized calculation snapshots that make up "
            "one aggregate result cell."
        ),
        read_only=True,
        input=ToolInputSpec(
            required=("group_by", "group_key", "start_date", "end_date"),
            optional=("limit",),
        ),
        authorization="i2-boundary: authorize_insight_scope + organisation-scoped query",
        output_fields=(
            "group_by",
            "group_key",
            "period",
            "snapshots",
            "snapshot_count",
            "snapshot_count_capped",
            "basis",
        ),
        reference_kinds=("calculation_snapshot", "evidence_line_item"),
    ),
    # P2 — bounded temporal comparison (Insight capability family 11). Two
    # explicitly bounded periods on the authoritative kg CO₂e basis; optional
    # grouping by a closed *category* dimension. No references are returned: the
    # contributing calculation records stay reachable through the existing
    # aggregate-provenance tool (and therefore the Shared Source Evidence
    # Viewer), so no second provenance path and no second reference kind exists.
    ToolDefinition(
        name=TOOL_INSIGHT_TEMPORAL_COMPARISON,
        purpose=(
            "Compare two explicitly bounded periods on the authoritative kg CO2e "
            "basis, returning both period totals, the absolute change, the "
            "percentage change (or a truthful zero-baseline result when the "
            "baseline is zero) and the direction; optionally grouped by one "
            "supported category dimension."
        ),
        read_only=True,
        input=ToolInputSpec(
            required=(
                "period_a_start",
                "period_a_end",
                "period_b_start",
                "period_b_end",
            ),
            optional=("group_by", "limit"),
        ),
        authorization="i2-boundary: authorize_insight_scope + organisation-scoped query",
        output_fields=(
            "group_by",
            "period_a",
            "period_b",
            "absolute_change_kg",
            "percentage_change",
            "percentage_change_available",
            "percentage_basis",
            "direction",
            "groups",
            "group_count",
            "groups_truncated",
            "empty_periods",
            "comparison_dimensions",
            "basis",
            "provenance_tool",
        ),
        reference_kinds=(),
    ),
)

#: The registry — exactly the four ratified tools (PO §4).
TOOL_REGISTRY: dict[str, ToolDefinition] = {d.name: d for d in TOOL_DEFINITIONS}


def registry_payload() -> list[dict[str, Any]]:
    """The ratified registry (definitions only; never executes anything)."""
    return [
        {
            "name": d.name,
            "purpose": d.purpose,
            "read_only": d.read_only,
            "required_inputs": list(d.input.required),
            "optional_inputs": list(d.input.optional),
            "authorization": d.authorization,
            "output_fields": list(d.output_fields),
            "reference_kinds": list(d.reference_kinds),
            "statuses": list(d.statuses),
        }
        for d in TOOL_DEFINITIONS
    ]


# --------------------------------------------------------------------------
# Deterministic intent classification (PO §12) — keyword routing, no LLM.
# Most specific intents first; a match on two tools is ambiguous and is refused
# explicitly rather than guessed into a tool call.
# --------------------------------------------------------------------------
_INTENT_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (TOOL_REPORT_VERSION_LOOKUP, ("version", "revision", "superseded", "which draft")),
    (TOOL_REPORT_EVIDENCE_LOOKUP, ("evidence", "source line", "backing", "supporting", "audit trail")),
    (TOOL_CALCULATION_SNAPSHOT_LOOKUP, ("calculation", "snapshot", "emission factor", "factor used", "co2e", "kg co2")),
    (TOOL_REPORT_LOOKUP, ("report", "summary document")),
)


def classify_intent(utterance: str) -> dict[str, Any]:
    """Route an utterance to exactly one ratified tool, or refuse explicitly.

    Deterministic. Refusals use the ratified ``invalid_input`` status with a
    machine-readable reason (no new status category is introduced).
    """
    text = (utterance or "").strip().lower()
    if not text:
        return {"status": ToolStatus.INVALID_INPUT.value, "tool": None, "reason": "empty_utterance"}
    if len(text) > 2000:
        return {"status": ToolStatus.INVALID_INPUT.value, "tool": None, "reason": "utterance_too_long"}
    matches = [t for t, kws in _INTENT_KEYWORDS if any(k in text for k in kws)]
    if len(matches) > 1:
        return {"status": ToolStatus.INVALID_INPUT.value, "tool": None, "reason": "ambiguous_intent", "considered_tools": sorted(matches)}
    if not matches:
        return {"status": ToolStatus.INVALID_INPUT.value, "tool": None, "reason": "unsupported_intent", "considered_tools": []}
    return {"status": ToolStatus.SUCCESS.value, "tool": matches[0], "reason": None, "considered_tools": matches}


# --------------------------------------------------------------------------
# Execution helpers
# --------------------------------------------------------------------------
def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _project(row: Optional[dict], fields: tuple[str, ...]) -> dict[str, Any]:
    """Project a stored row onto the allowlist — never a passthrough of the row."""
    if not row:
        return {}
    return {f: _json_safe(row.get(f)) for f in fields if f in row}


def _result(tool: str, status: ToolStatus, *, reason: Optional[str] = None, **kwargs: Any) -> ToolResult:
    return ToolResult(tool=tool, status=status, reason=reason, **kwargs)


def _validate_input(tool: ToolDefinition, tool_input: Any) -> Optional[str]:
    """Point 2 — validation rules and bounded input size. Returns a reason or None."""
    if tool_input is None:
        tool_input = {}
    if not isinstance(tool_input, dict):
        return "input_must_be_object"
    if set(tool_input) - set(tool.input.accepted):
        return "unknown_parameter"
    for key in tool.input.accepted:
        value = tool_input.get(key)
        if value is None or value == "":
            continue
        if not isinstance(value, (str, int)):
            return "invalid_parameter_type"
        if isinstance(value, str) and len(value) > MAX_IDENTIFIER_LENGTH:
            return "parameter_too_long"
    for key in tool.input.required:
        if not tool_input.get(key):
            return "missing_required_parameter"
    if tool.name == TOOL_REPORT_VERSION_LOOKUP:
        if not (tool_input.get("version_id") or (tool_input.get("report_id") and tool_input.get("version_number"))):
            return "missing_required_parameter"
    return None


async def _authorize(
    current_user: AuthUser, repos: RepositoryBundle, organization_id: str
) -> Optional[InsightAccess]:
    """Resolve the caller's scope through the closed I2 boundary (never re-implemented)."""
    from api.insight_authz import authorize_insight_scope  # deferred: OHD D-02

    try:
        return await authorize_insight_scope(current_user, repos, organization_id)
    except HTTPException:
        return None


async def invoke_tool(
    *,
    tool_name: str,
    current_user: AuthUser,
    repos: RepositoryBundle,
    organization_id: str,
    tool_input: Optional[dict[str, Any]] = None,
) -> ToolResult:
    """Deterministic execution path: validate → I2 authorize → read → bound → status."""
    tool = TOOL_REGISTRY.get(tool_name or "")
    if tool is None:
        return _result(tool_name or "", ToolStatus.INVALID_INPUT, reason="unratified_tool")
    reason = _validate_input(tool, tool_input)
    if reason is not None:
        return _result(tool.name, ToolStatus.INVALID_INPUT, reason=reason)
    if not organization_id:
        return _result(tool.name, ToolStatus.INVALID_INPUT, reason="missing_organization_id")
    access = await _authorize(current_user, repos, organization_id)
    if access is None:
        return _result(tool.name, ToolStatus.NOT_AUTHORIZED, reason="not_authorized")
    payload = dict(tool_input or {})
    try:
        if tool.name == TOOL_REPORT_LOOKUP:
            return await _report_lookup(repos, access, payload)
        if tool.name == TOOL_REPORT_VERSION_LOOKUP:
            return await _report_version_lookup(repos, access, payload)
        if tool.name == TOOL_REPORT_EVIDENCE_LOOKUP:
            return await _report_evidence_lookup(repos, access, payload)
        if tool.name == TOOL_CALCULATION_SNAPSHOT_LOOKUP:
            return await _snapshot_lookup(repos, access, payload)
        if tool.name == TOOL_INSIGHT_DISCOVERY:
            return await _discovery(repos, access, payload)
        if tool.name == TOOL_INSIGHT_AGGREGATION:
            return await _aggregation(repos, access, payload)
        if tool.name == TOOL_INSIGHT_AGGREGATE_PROVENANCE:
            return await _aggregate_provenance(repos, access, payload)
        if tool.name == TOOL_INSIGHT_TEMPORAL_COMPARISON:
            return await _temporal_comparison(repos, access, payload)
        return _result(tool.name, ToolStatus.INVALID_INPUT, reason="unratified_tool")
    except Exception:  # noqa: BLE001 - fail closed; diagnostics stay server-side
        # Logged server-side (tool name + exception) so genuine internal defects
        # stay diagnosable without exposing stack traces, SQL, DSNs or internals
        # through the public API (PO remediation §3). The external status
        # vocabulary is unchanged: `error` / `internal_error`.
        logger.exception("insight tool %s failed", tool.name)
        return _result(tool.name, ToolStatus.ERROR, reason="internal_error")


def _dedupe_refs(kinds_and_ids: list[tuple[str, str]]) -> tuple[InsightReference, ...]:
    seen: dict[tuple[str, str], None] = {}
    for kind, identifier in kinds_and_ids:
        if identifier:
            seen[(kind, str(identifier))] = None
    return tuple(InsightReference(kind, identifier) for kind, identifier in seen)


async def _report_lookup(repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]) -> ToolResult:
    report_id = str(payload["report_id"])
    report = await repos.reports.get_full(report_id)
    if report is None:
        return _result(TOOL_REPORT_LOOKUP, ToolStatus.NO_DATA, reason="report_not_found")
    if str(report.get("organization_id")) != access.organization_id:
        return _result(TOOL_REPORT_LOOKUP, ToolStatus.NOT_AUTHORIZED, reason="not_authorized")
    versions = await repos.report_versions.list_for_report(report_id)
    current = await repos.report_versions.get_current(report_id)
    shown, truncated = bounded([_project(v, _REPORT_VERSION_FIELDS) for v in versions])
    current_projection = _project(current, _REPORT_VERSION_FIELDS)
    data = {
        **_project(report, _REPORT_FIELDS),
        "versions": shown,
        "current_version": current_projection or None,
        "is_approved_or_final": bool(
            current_projection and str(current_projection.get("status")) in IMMUTABLE_REPORT_VERSION_STATUSES
        ),
    }
    refs = _dedupe_refs([("report", report_id)] + [("report_version", v.get("id", "")) for v in shown])
    return _result(TOOL_REPORT_LOOKUP, ToolStatus.SUCCESS, data=data, references=refs, truncated=truncated)


async def _report_version_lookup(repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]) -> ToolResult:
    if payload.get("version_id"):
        version = await repos.report_versions.get(str(payload["version_id"]))
    else:
        try:
            number = int(payload["version_number"])
        except (TypeError, ValueError):
            return _result(TOOL_REPORT_VERSION_LOOKUP, ToolStatus.INVALID_INPUT, reason="invalid_version_number")
        version = await repos.report_versions.get_by_number(str(payload["report_id"]), number)
    if version is None:
        return _result(TOOL_REPORT_VERSION_LOOKUP, ToolStatus.NO_DATA, reason="version_not_found")
    report = await repos.reports.get_full(str(version.get("report_id")))
    if report is None:
        return _result(TOOL_REPORT_VERSION_LOOKUP, ToolStatus.NO_DATA, reason="report_not_found")
    if str(report.get("organization_id")) != access.organization_id:
        return _result(TOOL_REPORT_VERSION_LOOKUP, ToolStatus.NOT_AUTHORIZED, reason="not_authorized")
    data = {**_project(version, _REPORT_VERSION_FIELDS), "report_organization_id": access.organization_id}
    refs = _dedupe_refs([("report_version", str(version.get("id"))), ("report", str(report.get("id")))])
    return _result(TOOL_REPORT_VERSION_LOOKUP, ToolStatus.SUCCESS, data=data, references=refs)


async def _report_evidence_lookup(repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]) -> ToolResult:
    version_id = str(payload["report_version_id"])
    context = await repos.disclosure_projection.report_context(version_id)
    if context is None:
        return _result(TOOL_REPORT_EVIDENCE_LOOKUP, ToolStatus.NO_DATA, reason="report_version_not_found")
    if str(context.get("organization_id")) != access.organization_id:
        return _result(TOOL_REPORT_EVIDENCE_LOOKUP, ToolStatus.NOT_AUTHORIZED, reason="not_authorized")
    raw_lines = await repos.disclosure_projection.value_lines(report_version_id=version_id)
    lines, truncated = bounded([_project(line, _EVIDENCE_LINE_FIELDS) for line in raw_lines])
    value_ids = sorted({str(line["disclosure_value_id"]) for line in lines if line.get("disclosure_value_id")})
    coverage: list[dict[str, Any]] = []
    for value_id in value_ids:
        counts = await repos.disclosure_projection.evidence_coverage(disclosure_value_id=value_id)
        coverage.append({"disclosure_value_id": value_id, **_project(counts, _COVERAGE_FIELDS)})
    data = {
        "report_version": {
            "id": version_id,
            "status": _json_safe(context.get("status")),
            "reporting_year": _json_safe(context.get("reporting_year")),
        },
        "lines": lines,
        "coverage": coverage,
    }
    refs = _dedupe_refs(
        [("report_version", version_id)]
        + [("evidence_line_item", line.get("evidence_line_item_id", "")) for line in lines]
        + [("calculation_snapshot", line.get("calculation_snapshot_id", "")) for line in lines]
    )
    return _result(TOOL_REPORT_EVIDENCE_LOOKUP, ToolStatus.SUCCESS, data=data, references=refs, truncated=truncated)


async def _snapshot_lookup(repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]) -> ToolResult:
    row = await repos.logs.get_snapshot(str(payload["snapshot_id"]))
    if row is None:
        return _result(TOOL_CALCULATION_SNAPSHOT_LOOKUP, ToolStatus.NO_DATA, reason="snapshot_not_found")
    if str(row.get("organization_id")) != access.organization_id:
        return _result(TOOL_CALCULATION_SNAPSHOT_LOOKUP, ToolStatus.NOT_AUTHORIZED, reason="not_authorized")
    data = _project(row, _SNAPSHOT_FIELDS)
    refs = _dedupe_refs(
        [("calculation_snapshot", str(row.get("id"))), ("evidence_line_item", row.get("source_line_item_id", ""))]
    )
    return _result(TOOL_CALCULATION_SNAPSHOT_LOOKUP, ToolStatus.SUCCESS, data=data, references=refs)


# --------------------------------------------------------------------------
# Phase 8 Insight analytics — bounded discovery / aggregation / provenance
#
# Authorization: PO Insight Discovery-Aggregation-Provenance package
# (2026-09-22). These tools read only through the bounded, organization-scoped
# repository methods; every parameter is validated against the closed
# vocabulary in ``domain.insight_query`` before a single row is read, and the
# I2 boundary above has already authorized the caller's organisation.
# --------------------------------------------------------------------------

#: The aggregation basis, stated in the result so a figure can never be
#: presented without its unit/basis.
_BASIS_CO2E = "kg CO2e from emissions_logs.calculated_kg_co2e (organization-scoped)"
_BASIS_PROVENANCE = "calculation_snapshots linked by emissions_logs.snapshot_id"
#: P2 — the comparison basis is exactly the aggregation basis, applied to two
#: explicitly bounded periods; stated in the result for the same reason.
_BASIS_COMPARISON = (
    "kg CO2e from emissions_logs.calculated_kg_co2e (organization-scoped), "
    "compared across two explicitly bounded periods"
)


def _invalid_analytics(tool: str, reason: Optional[str]) -> ToolResult:
    return _result(tool, ToolStatus.INVALID_INPUT, reason=reason)


async def _discovery(repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]) -> ToolResult:
    """Bounded discovery: zero, one or several matching calculation records."""
    filters = {
        key: payload[key]
        for key in DISCOVERY_FILTERS
        if payload.get(key) is not None and payload.get(key) != ""
    }
    limit, reason = validate_limit(
        payload.get("limit"), maximum=MAX_DISCOVERY_RESULTS, default=MAX_DISCOVERY_RESULTS
    )
    if reason is not None or limit is None:
        return _invalid_analytics(TOOL_INSIGHT_DISCOVERY, reason)
    reason = validate_discovery(filters)
    if reason is not None:
        return _invalid_analytics(TOOL_INSIGHT_DISCOVERY, reason)

    org = access.organization_id
    rows = await repos.logs.search_snapshots(org, filters, limit)
    rows, truncated = bounded(rows, limit)
    # Bounded count: at most ``limit + 1``, so a huge match set never forces a
    # full count and the caller still learns that more than the bound matched.
    counted = await repos.logs.count_matching_snapshots(org, filters, limit + 1)
    match_count_capped = counted > limit
    match_count = min(counted, limit + 1) if counted else 0
    candidates = [_project(r, _SNAPSHOT_FIELDS) for r in rows]
    refs = _dedupe_refs(
        [("calculation_snapshot", str(r.get("id"))) for r in rows]
        + [("evidence_line_item", r.get("source_line_item_id", "")) for r in rows]
    )
    data = {
        "match_count": match_count,
        "match_count_capped": match_count_capped,
        "candidates": candidates,
        "basis": "kg CO2e from calculation_snapshots.co2e_kg (organization-scoped)",
    }
    if counted == 0:
        return _result(TOOL_INSIGHT_DISCOVERY, ToolStatus.NO_DATA, reason="no_matches")
    if match_count > 1 or match_count_capped:
        # Several records match: the ambiguity is reported explicitly (I4
        # ``multiple_matches``) rather than silently choosing one.
        return _result(
            TOOL_INSIGHT_DISCOVERY,
            ToolStatus.SUCCESS,
            reason="multiple_matches",
            data=data,
            references=refs,
            truncated=truncated or match_count_capped,
        )
    return _result(
        TOOL_INSIGHT_DISCOVERY,
        ToolStatus.SUCCESS,
        data=data,
        references=refs,
        truncated=truncated,
    )


async def _aggregation(repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]) -> ToolResult:
    """Bounded aggregation in kg CO₂e by one allowlisted dimension."""
    dimension = str(payload.get("group_by") or "")
    reason = validate_group_by(dimension)
    if reason is not None:
        return _invalid_analytics(TOOL_INSIGHT_AGGREGATION, reason)
    start, end, reason = validate_period(payload.get("start_date"), payload.get("end_date"))
    if reason is not None or start is None or end is None:
        return _invalid_analytics(TOOL_INSIGHT_AGGREGATION, reason)
    limit, reason = validate_limit(
        payload.get("limit"), maximum=MAX_AGGREGATE_GROUPS, default=MAX_AGGREGATE_GROUPS
    )
    if reason is not None or limit is None:
        return _invalid_analytics(TOOL_INSIGHT_AGGREGATION, reason)

    org = access.organization_id
    period = DateRange(start_date=start, end_date=end)
    # One extra row is requested so truncation is *detected* rather than assumed.
    raw_groups = await repos.logs.aggregate_groups(org, period, dimension, limit + 1)
    shown = raw_groups[:limit]
    groups_truncated = len(raw_groups) > limit
    keys = [str(r["group_key"]) for r in shown]
    labels = await repos.logs.group_labels(org, dimension, keys)
    groups = [
        {
            "key": str(r["group_key"]),
            "label": labels.get(str(r["group_key"])),
            "co2e_kg": str(r["co2e_kg"]) if r.get("co2e_kg") is not None else "0",
            "row_count": int(r["row_count"]),
        }
        for r in shown
    ]
    # The period total comes from the existing organization-scoped aggregate, so
    # it stays complete even when the group list is truncated. Its basis is the
    # same column, so the total and the groups always reconcile.
    totals = await repos.logs.aggregate(org, period, "scope")
    data = {
        "group_by": dimension,
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "groups": groups,
        "group_count": len(groups),
        "groups_truncated": groups_truncated,
        "row_count": int(totals.total_rows),
        "total_co2e_kg": str(totals.total_co2e_kg),
        "total_is_complete": not groups_truncated,
        "basis": _BASIS_CO2E,
        "provenance_tool": TOOL_INSIGHT_AGGREGATE_PROVENANCE,
    }
    if int(totals.total_rows) == 0:
        return _result(TOOL_INSIGHT_AGGREGATION, ToolStatus.NO_DATA, reason="no_rows_in_period")
    if Decimal(str(totals.total_co2e_kg)) == 0:
        # Records were found and the calculated total is genuinely zero.
        return _result(
            TOOL_INSIGHT_AGGREGATION,
            ToolStatus.SUCCESS,
            reason="zero_total",
            data=data,
            truncated=groups_truncated,
        )
    return _result(
        TOOL_INSIGHT_AGGREGATION,
        ToolStatus.SUCCESS,
        data=data,
        truncated=groups_truncated,
    )


async def _aggregate_provenance(
    repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]
) -> ToolResult:
    """Bounded provenance: the calculation snapshots behind one aggregate cell."""
    dimension = str(payload.get("group_by") or "")
    reason = validate_group_by(dimension)
    if reason is not None:
        return _invalid_analytics(TOOL_INSIGHT_AGGREGATE_PROVENANCE, reason)
    start, end, reason = validate_period(payload.get("start_date"), payload.get("end_date"))
    if reason is not None or start is None or end is None:
        return _invalid_analytics(TOOL_INSIGHT_AGGREGATE_PROVENANCE, reason)
    limit, reason = validate_limit(
        payload.get("limit"), maximum=MAX_PROVENANCE_SNAPSHOTS, default=MAX_PROVENANCE_SNAPSHOTS
    )
    if reason is not None or limit is None:
        return _invalid_analytics(TOOL_INSIGHT_AGGREGATE_PROVENANCE, reason)
    group_key = str(payload.get("group_key") or "").strip()
    if not group_key or len(group_key) > MAX_IDENTIFIER_LENGTH:
        return _invalid_analytics(TOOL_INSIGHT_AGGREGATE_PROVENANCE, "missing_group_key")

    org = access.organization_id
    period = DateRange(start_date=start, end_date=end)
    rows = await repos.logs.list_group_snapshots(org, period, dimension, group_key, limit)
    rows, truncated = bounded(rows, limit)
    counted = await repos.logs.count_group_snapshots(org, period, dimension, group_key, limit + 1)
    count_capped = counted > limit
    snapshots = [
        {
            "id": str(r["id"]),
            "date": _json_safe(r.get("date")),
            "activity_type": _json_safe(r.get("activity_type")),
            "scope": _json_safe(r.get("scope")),
            "co2e_kg": _json_safe(r.get("co2e_kg")),
            "source_line_item_id": _json_safe(r.get("source_line_item_id")),
        }
        for r in rows
    ]
    refs = _dedupe_refs(
        [("calculation_snapshot", str(r["id"])) for r in rows]
        + [("evidence_line_item", r.get("source_line_item_id", "")) for r in rows]
    )
    if counted == 0:
        return _result(
            TOOL_INSIGHT_AGGREGATE_PROVENANCE,
            ToolStatus.NO_DATA,
            reason="no_contributing_snapshots",
        )
    data = {
        "group_by": dimension,
        "group_key": group_key,
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "snapshots": snapshots,
        "snapshot_count": len(snapshots),
        "snapshot_count_capped": count_capped,
        "basis": _BASIS_PROVENANCE,
    }
    return _result(
        TOOL_INSIGHT_AGGREGATE_PROVENANCE,
        ToolStatus.SUCCESS,
        data=data,
        references=refs,
        truncated=truncated or count_capped,
    )


async def _attach_comparison_groups(
    repos: RepositoryBundle,
    org: str,
    period_a: DateRange,
    period_b: DateRange,
    dimension: Optional[str],
    limit: int,
    data: dict[str, Any],
) -> bool:
    """Fill the grouped comparison block; return whether the group list truncated.

    One extra row is requested per period so truncation is *detected* rather than
    assumed, and the union is ordered by the deterministic two-period convention
    (largest of the two period totals, then key). A group present in only one
    period is still reported, with the other side's authoritative total as zero —
    the absence is visible in the per-period row counts rather than hidden.
    """
    if dimension is None:
        return False
    raw_a = await repos.logs.aggregate_groups(org, period_a, dimension, limit + 1)
    raw_b = await repos.logs.aggregate_groups(org, period_b, dimension, limit + 1)
    a_more = len(raw_a) > limit
    b_more = len(raw_b) > limit
    a_groups = {str(r["group_key"]): r for r in raw_a[:limit]}
    b_groups = {str(r["group_key"]): r for r in raw_b[:limit]}
    ordered = order_comparison_keys(list(a_groups.values()), list(b_groups.values()))
    truncated = a_more or b_more or len(ordered) > limit
    ordered = ordered[:limit]
    labels = await repos.logs.group_labels(org, dimension, ordered)
    groups: list[dict[str, Any]] = []
    for key in ordered:
        row_a = a_groups.get(key)
        row_b = b_groups.get(key)
        group_a = _group_total(row_a)
        group_b = _group_total(row_b)
        groups.append(
            {
                "key": key,
                "label": labels.get(key),
                "period_a_co2e_kg": str(group_a),
                "period_b_co2e_kg": str(group_b),
                "period_a_row_count": int(row_a["row_count"]) if row_a else 0,
                "period_b_row_count": int(row_b["row_count"]) if row_b else 0,
                **compare_totals(group_a, group_b).as_dict(),
            }
        )
    data["groups"] = groups
    data["group_count"] = len(groups)
    data["groups_truncated"] = truncated
    return truncated


def _group_total(row: Optional[dict[str, Any]]) -> Decimal:
    """The authoritative kg CO₂e total for one group side (zero when absent)."""
    if row is None or row.get("co2e_kg") is None:
        return Decimal("0")
    return Decimal(str(row["co2e_kg"]))


async def _temporal_comparison(
    repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]
) -> ToolResult:
    """Bounded comparison of two explicitly bounded periods (P2, family 11).

    Deterministic by construction:

    * both period totals come from the *existing* organization-scoped aggregate,
      so they stay complete even when the optional group list is truncated;
    * the deltas come from the pure ``domain.insight_query.compare_totals``
      helper — the absolute change is ``period_B - period_A`` and the percentage
      is computed only when the baseline is non-zero;
    * grouped output is ordered by the deterministic two-period convention and
      carries an explicit truncation flag.

    No reference is returned and no contributing record is inlined: the
    comparison stays traceable through the existing aggregate-provenance tool,
    which is named in the result together with the exact period bounds it needs.
    """
    dimension_raw = payload.get("group_by")
    dimension = str(dimension_raw).strip() if dimension_raw not in (None, "") else None
    reason = validate_comparison_dimension(dimension)
    if reason is not None:
        return _invalid_analytics(TOOL_INSIGHT_TEMPORAL_COMPARISON, reason)

    a_start, a_end, b_start, b_end, reason = validate_comparison_periods(
        payload.get("period_a_start"),
        payload.get("period_a_end"),
        payload.get("period_b_start"),
        payload.get("period_b_end"),
    )
    if (
        reason is not None
        or a_start is None
        or a_end is None
        or b_start is None
        or b_end is None
    ):
        return _invalid_analytics(TOOL_INSIGHT_TEMPORAL_COMPARISON, reason)

    limit, reason = validate_limit(
        payload.get("limit"), maximum=MAX_AGGREGATE_GROUPS, default=MAX_AGGREGATE_GROUPS
    )
    if reason is not None or limit is None:
        return _invalid_analytics(TOOL_INSIGHT_TEMPORAL_COMPARISON, reason)

    org = access.organization_id
    period_a = DateRange(start_date=a_start, end_date=a_end)
    period_b = DateRange(start_date=b_start, end_date=b_end)

    totals_a = await repos.logs.aggregate(org, period_a, "scope")
    totals_b = await repos.logs.aggregate(org, period_b, "scope")
    a_total = Decimal(str(totals_a.total_co2e_kg))
    b_total = Decimal(str(totals_b.total_co2e_kg))
    a_rows = int(totals_a.total_rows)
    b_rows = int(totals_b.total_rows)

    empty_periods = [
        label
        for label, rows in (("period_a", a_rows), ("period_b", b_rows))
        if rows == 0
    ]
    if a_rows == 0 and b_rows == 0:
        # An absence of records is never presented as a "0 vs 0" comparison:
        # there is nothing authoritative to compare.
        return _result(
            TOOL_INSIGHT_TEMPORAL_COMPARISON,
            ToolStatus.NO_DATA,
            reason="no_rows_in_periods",
        )

    delta = compare_totals(a_total, b_total)
    data: dict[str, Any] = {
        "group_by": dimension,
        "period_a": {
            "start_date": a_start.isoformat(),
            "end_date": a_end.isoformat(),
            "total_co2e_kg": str(a_total),
            "row_count": a_rows,
        },
        "period_b": {
            "start_date": b_start.isoformat(),
            "end_date": b_end.isoformat(),
            "total_co2e_kg": str(b_total),
            "row_count": b_rows,
        },
        **delta.as_dict(),
        "groups": [],
        "group_count": 0,
        "groups_truncated": False,
        "empty_periods": empty_periods,
        "comparison_dimensions": list(TEMPORAL_COMPARISON_DIMENSIONS),
        "basis": _BASIS_COMPARISON,
        "provenance_tool": TOOL_INSIGHT_AGGREGATE_PROVENANCE,
    }
    truncated = await _attach_comparison_groups(
        repos, org, period_a, period_b, dimension, limit, data
    )

    if a_total == 0 and b_total == 0:
        # Records exist and both calculated totals are genuinely zero — the same
        # truthful convention the aggregation tool uses (``zero_total``).
        return _result(
            TOOL_INSIGHT_TEMPORAL_COMPARISON,
            ToolStatus.SUCCESS,
            reason="zero_total",
            data=data,
            truncated=truncated,
        )
    return _result(
        TOOL_INSIGHT_TEMPORAL_COMPARISON,
        ToolStatus.SUCCESS,
        data=data,
        truncated=truncated,
    )
