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
from domain.insight_quality import (
    CONDITION_CONTENT_HASH_MATCHES,
    CONDITION_EVIDENCE_RESOLVABLE,
    CONDITION_FACTOR_REFERENCE,
    CONDITION_INPUTS_RETAINED,
    CONDITION_METHODOLOGY_RETAINED,
    CONDITION_PROVENANCE_CONSISTENT,
    CONDITION_RECOMPUTATION_MATCHES,
    CONDITION_RESULT_RETAINED,
    CONDITION_SNAPSHOT_RETAINED,
    CONDITION_SOURCE_LINEAGE,
    MAX_QUALITY_RECORDS,
    QC_STATE_BASIS,
    QUALITY_SCAN_BASIS,
    REPRODUCIBILITY_BASIS,
    ReproducibilityCondition,
    TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
    TOOL_INSIGHT_DATA_QUALITY,
    snapshot_from_row,
    summarise_report,
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
from engines.calculation import CalculationEngine
from engines.validation import ValidationEngine

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
    # P3 — bounded data-quality scan (Insight family 14). Every finding comes from
    # the existing ValidationEngine over the organization's own stored snapshots;
    # P3 adds no rule, no weight and no composite score.
    ToolDefinition(
        name=TOOL_INSIGHT_DATA_QUALITY,
        purpose=(
            "Report deterministic data-quality findings for the stored calculations "
            "in one explicitly bounded period, as counts per authoritative validation "
            "code with the affected records."
        ),
        read_only=True,
        input=ToolInputSpec(required=("start_date", "end_date"), optional=("limit",)),
        authorization="i2-boundary: authorize_insight_scope + organisation-scoped query",
        output_fields=(
            "period",
            "records_checked",
            "records_with_findings",
            "records_passing",
            "finding_count",
            "distinct_finding_codes",
            "findings",
            "population_truncated",
            "population_exceeds_bound",
            "uncheckable_records",
            "checks_performed",
            "open_issue_count",
            "qc_state_basis",
            "scan_limit",
            "basis",
        ),
        reference_kinds=(),
    ),
    # P3 — record-level reproducibility/traceability for one identified
    # calculation. Reuses the existing CalculationEngine.verify and
    # ValidationEngine.validate_snapshot; it certifies nothing.
    ToolDefinition(
        name=TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
        purpose=(
            "Report the deterministic reproducibility and traceability conditions of "
            "one identified calculation from the data CarbonTally retains for it."
        ),
        read_only=True,
        input=ToolInputSpec(required=("snapshot_id",)),
        authorization="i2-boundary: authorize_insight_scope + object organisation re-check",
        output_fields=(
            "snapshot_id",
            "organization_id",
            "activity_type",
            "scope",
            "date",
            "co2e_kg",
            "factor_kind",
            "factor_id",
            "customer_factor_id",
            "methodology",
            "algorithm_version",
            "checkable",
            "reproducible",
            "conditions",
            "satisfied_conditions",
            "unsatisfied_conditions",
            "verification",
            "finding_codes",
            "evidence",
            "basis",
            "provenance_tool",
        ),
        reference_kinds=("calculation_snapshot", "evidence_line_item"),
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
        if tool.name == TOOL_INSIGHT_DATA_QUALITY:
            return await _data_quality(repos, access, payload)
        if tool.name == TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY:
            return await _calculation_reproducibility(repos, access, payload)
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


# --------------------------------------------------------------------------
# P3 — data quality and audit/reproducibility (Insight families 14 and 16)
#
# Authorization: PO P3 implementation authorization (2026-09-23).
#
# Both capabilities below are *aggregation and projection only*. Every finding
# they can report is produced by machinery that already exists in CarbonTally:
# ``ValidationEngine`` (A1 input completeness / A2 recomputation + content hash /
# A5 factor provenance) and ``CalculationEngine.verify`` (audit-time
# reproducibility). P3 adds no check, no severity, no weight and no score.
# --------------------------------------------------------------------------

#: The checks the scan states it performed — named so a reader can see exactly
#: what was and was not covered (never a claim about what was not checked).
_QUALITY_CHECKS: tuple[str, ...] = (
    "A1 input completeness (activity, quantity, unit, reporting year)",
    "A2 recomputation of quantity x multiplier against the stored result",
    "A2 content-hash tamper evidence",
    "A5 factor provenance consistency for batch-linked factors",
)


def _quality_engine(repos: RepositoryBundle) -> ValidationEngine:
    """The existing validation engine, built from the same repositories the API binds."""
    return ValidationEngine(
        repos.logs,
        repos.organizations,
        repos.factors,
        customer_factors=repos.customer_factors,
    )


def _validation_issue_dict(issue: Any, record_id: str) -> dict[str, Any]:
    """Project one authoritative ValidationIssue onto a bounded finding record.

    ``record_id`` is the stored calculation this finding belongs to (the identity
    an operator can act on). ``entity_id`` is kept as the engine's own subject,
    which differs by check family (the activity text for A1, the snapshot id for
    A2/A5) — both are reported so a finding stays explainable.
    """
    return {
        "code": str(issue.code),
        "severity": str(getattr(issue.severity, "value", issue.severity)),
        "message": str(issue.message),
        "entity_type": str(issue.entity_type),
        "entity_id": str(issue.entity_id),
        "record_id": str(record_id),
        "field": str(issue.field or ""),
    }


async def _data_quality(
    repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]
) -> ToolResult:
    """Bounded deterministic quality scan of the organisation's stored calculations."""
    start, end, reason = validate_period(payload.get("start_date"), payload.get("end_date"))
    if reason is not None or start is None or end is None:
        return _invalid_analytics(TOOL_INSIGHT_DATA_QUALITY, reason)
    limit, reason = validate_limit(
        payload.get("limit"), maximum=MAX_QUALITY_RECORDS, default=MAX_QUALITY_RECORDS
    )
    if reason is not None or limit is None:
        return _invalid_analytics(TOOL_INSIGHT_DATA_QUALITY, reason)

    org = access.organization_id
    filters = {"start_date": start.isoformat(), "end_date": end.isoformat()}
    # One extra row is requested so truncation is *detected*, and the count is
    # bounded by the same cap, so a large period can never force a full scan.
    rows = await repos.logs.search_snapshots(org, filters, limit + 1)
    truncated = len(rows) > limit
    rows = rows[:limit]
    counted = await repos.logs.count_matching_snapshots(org, filters, limit + 1)

    engine = _quality_engine(repos)
    issues: list[dict[str, Any]] = []
    checked = 0
    with_findings = 0
    uncheckable = 0
    unresolved_factor = 0
    for row in rows:
        snapshot = snapshot_from_row(row)
        if snapshot is None:
            # The stored row does not carry the fields the engine needs: reported
            # as not-checkable rather than silently counted as passing.
            uncheckable += 1
            continue
        checked += 1
        factor = None
        if snapshot.factor_kind == "emission_factor" and snapshot.factor_id:
            factor = await repos.factors.get(snapshot.factor_id)
            if factor is None:
                # The A1 unit rule and the A5 provenance context both need the
                # factor. Its absence is counted, never passed off as "no problem":
                # "not checked" must not read as "checked and fine".
                unresolved_factor += 1
        report = engine.validate_input(
            # The stored activity text exactly as retained — never a substitute
            # from another column, so the engine's own empty-activity rule sees
            # what is really stored.
            activity=str(row.get("activity") or ""),
            quantity=snapshot.quantity,
            reporting_year=snapshot.reporting_year,
            quantity_unit=snapshot.quantity_unit,
            factor=factor,
        )
        report = report.merge(
            engine.validate_snapshot(
                snapshot,
                factor,
                factor_source=row.get("factor_source"),
                factor_set=row.get("factor_set"),
                import_batch_id=row.get("import_batch_id"),
            )
        )
        if report.issues:
            with_findings += 1
        for issue in report.issues:
            issues.append(_validation_issue_dict(issue, snapshot.id))

    open_issues = await repos.issues.count_for_org(org)
    summary = summarise_report(
        issues, records_checked=checked, records_with_findings=with_findings
    )
    data: dict[str, Any] = {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        **summary,
        "population_truncated": truncated,
        "population_exceeds_bound": truncated or counted > limit,
        "uncheckable_records": uncheckable,
        "records_with_unresolved_factor": unresolved_factor,
        "checks_performed": list(_QUALITY_CHECKS),
        "open_issue_count": int(open_issues),
        "qc_state_basis": QC_STATE_BASIS,
        "scan_limit": int(limit),
        "basis": QUALITY_SCAN_BASIS,
    }
    if checked == 0 and uncheckable == 0:
        # Nothing stored in the period: an absence of records is not a "pass".
        return _result(
            TOOL_INSIGHT_DATA_QUALITY, ToolStatus.NO_DATA, reason="no_rows_in_period"
        )
    if with_findings == 0:
        return _result(
            TOOL_INSIGHT_DATA_QUALITY,
            ToolStatus.SUCCESS,
            reason="all_checks_passed",
            data=data,
            truncated=truncated,
        )
    # Findings are the answer, not an error: the scan succeeded and reports them.
    return _result(
        TOOL_INSIGHT_DATA_QUALITY,
        ToolStatus.SUCCESS,
        reason="findings_reported",
        data=data,
        truncated=truncated,
    )



#: The existing A5 provenance codes, used to report the provenance condition from
#: the validation engine's own vocabulary instead of inventing a new check.
_PROVENANCE_CODES: frozenset[str] = frozenset(
    {
        "VAL_SNAPSHOT_PROVENANCE_MISSING",
        "VAL_SNAPSHOT_BATCH_MISMATCH",
        "VAL_SNAPSHOT_SOURCE_MISMATCH",
        "VAL_FACTOR_ORPHAN",
    }
)


async def _calculation_reproducibility(
    repos: RepositoryBundle, access: InsightAccess, payload: dict[str, Any]
) -> ToolResult:
    """Record-level reproducibility/traceability for one identified calculation.

    Reuses the existing deterministic machinery end to end:

    * ``CalculationEngine.verify`` — the audit-time reproducibility check
      (``match`` / ``discrepancy`` / ``tampered``);
    * ``ValidationEngine.validate_snapshot`` — the A2/A5 codes over the same
      stored record.

    The result states what CarbonTally can technically demonstrate for this
    record. It certifies nothing: there is no "audit approved" field, and a
    limitation is reported as a limitation rather than as a failure.
    """
    snapshot_id = str(payload.get("snapshot_id") or "").strip()
    if not snapshot_id or len(snapshot_id) > MAX_IDENTIFIER_LENGTH:
        return _invalid_analytics(
            TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY, "missing_snapshot_id"
        )

    row = await repos.logs.get_snapshot(snapshot_id)
    if row is None:
        return _result(
            TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
            ToolStatus.NO_DATA,
            reason="snapshot_not_found",
        )
    if str(row.get("organization_id")) != access.organization_id:
        # A reference is a locator, never a grant: the object is re-checked here.
        return _result(
            TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
            ToolStatus.NOT_AUTHORIZED,
            reason="not_authorized",
        )

    refs = _dedupe_refs(
        [
            ("calculation_snapshot", snapshot_id),
            ("evidence_line_item", row.get("source_line_item_id", "")),
        ]
    )
    snapshot = snapshot_from_row(row)
    if snapshot is None:
        # The record exists but does not retain what a re-check needs: reported as
        # not-checkable, never as a pass and never as a verdict.
        payload_data = {
            "snapshot_id": snapshot_id,
            "organization_id": access.organization_id,
            "checkable": False,
            "reproducible": None,
            "conditions": [
                ReproducibilityCondition(
                    CONDITION_SNAPSHOT_RETAINED, True, "the stored snapshot row exists"
                ).as_dict(),
                ReproducibilityCondition(
                    CONDITION_INPUTS_RETAINED,
                    False,
                    "the stored row does not retain the inputs a re-check requires",
                ).as_dict(),
            ],
            "satisfied_conditions": [CONDITION_SNAPSHOT_RETAINED],
            "unsatisfied_conditions": [CONDITION_INPUTS_RETAINED],
            "verification": None,
            "finding_codes": [],
            "evidence": None,
            "basis": REPRODUCIBILITY_BASIS,
            "provenance_tool": TOOL_INSIGHT_AGGREGATE_PROVENANCE,
        }
        return _result(
            TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
            ToolStatus.SUCCESS,
            reason="snapshot_not_checkable",
            data=payload_data,
            references=refs,
        )

    verification = CalculationEngine(repos.logs).verify(snapshot)
    engine = _quality_engine(repos)
    factor = None
    if snapshot.factor_kind == "emission_factor" and snapshot.factor_id:
        factor = await repos.factors.get(snapshot.factor_id)
    report = engine.validate_snapshot(
        snapshot,
        factor,
        factor_source=row.get("factor_source"),
        factor_set=row.get("factor_set"),
        import_batch_id=row.get("import_batch_id"),
    )
    codes = {str(issue.code) for issue in report.issues}
    evidence_count = 0
    if snapshot.source_item_id:
        evidence_count = int(
            await repos.evidence_line_items.count_for_item(snapshot.source_item_id)
        )
    data = _reproducibility_data(
        snapshot=snapshot,
        access=access,
        row=row,
        verification=verification,
        codes=codes,
        evidence_count=evidence_count,
    )
    if data["unsatisfied_conditions"]:
        # A technical limitation of the retained data — never an accounting
        # judgement and never an audit outcome.
        return _result(
            TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
            ToolStatus.SUCCESS,
            reason="reproducibility_limitation",
            data=data,
            references=refs,
        )
    return _result(
        TOOL_INSIGHT_CALCULATION_REPRODUCIBILITY,
        ToolStatus.SUCCESS,
        data=data,
        references=refs,
    )



def _reproducibility_data(
    *,
    snapshot: Any,
    access: InsightAccess,
    row: dict[str, Any],
    verification: Any,
    codes: set[str],
    evidence_count: int,
) -> dict[str, Any]:
    """Build the bounded reproducibility payload from the deterministic checks.

    Every condition is a structural presence question or an existing engine
    result — none is a new quality rule.
    """
    inputs_retained = bool(snapshot.quantity_unit) and snapshot.quantity is not None
    factor_reference_retained = bool(
        (snapshot.factor_kind == "emission_factor" and snapshot.factor_id)
        or (snapshot.factor_kind == "customer_factor" and snapshot.customer_factor_id)
    )
    methodology_retained = bool(snapshot.methodology) and bool(snapshot.algorithm_version)
    lineage_retained = bool(snapshot.source_item_id or snapshot.source_line_item_id)
    provenance_codes = codes & _PROVENANCE_CODES
    conditions = [
        ReproducibilityCondition(
            CONDITION_SNAPSHOT_RETAINED, True, "the stored snapshot row exists"
        ),
        ReproducibilityCondition(
            CONDITION_RESULT_RETAINED, True, "the stored calculation result is present"
        ),
        ReproducibilityCondition(
            CONDITION_INPUTS_RETAINED,
            inputs_retained,
            None if inputs_retained else "the stored record has no quantity unit",
        ),
        ReproducibilityCondition(
            CONDITION_FACTOR_REFERENCE,
            factor_reference_retained,
            None
            if factor_reference_retained
            else "no factor reference retained on the stored calculation",
        ),
        ReproducibilityCondition(
            CONDITION_METHODOLOGY_RETAINED,
            methodology_retained,
            None
            if methodology_retained
            else "methodology and algorithm version are not both retained",
        ),
        ReproducibilityCondition(
            CONDITION_SOURCE_LINEAGE,
            lineage_retained,
            None
            if lineage_retained
            else "no source item or source line reference retained",
        ),
        ReproducibilityCondition(
            CONDITION_EVIDENCE_RESOLVABLE,
            evidence_count > 0,
            f"{evidence_count} evidence line item(s) resolve for the retained source item"
            if evidence_count
            else "no evidence line item resolves for this calculation",
        ),
        ReproducibilityCondition(
            CONDITION_RECOMPUTATION_MATCHES,
            bool(verification.match),
            None
            if verification.match
            else "the stored result differs from the recomputation by "
            f"{verification.discrepancy}",
        ),
        ReproducibilityCondition(
            CONDITION_CONTENT_HASH_MATCHES,
            not bool(verification.tampered),
            None
            if not verification.tampered
            else "the stored content hash does not match a fresh hash of the inputs",
        ),
        ReproducibilityCondition(
            CONDITION_PROVENANCE_CONSISTENT,
            not provenance_codes,
            None
            if not provenance_codes
            else "factor provenance findings: " + ", ".join(sorted(provenance_codes)),
        ),
    ]
    return {
        "snapshot_id": snapshot.id,
        "organization_id": access.organization_id,
        "activity_type": _json_safe(row.get("activity_type")),
        "scope": _json_safe(row.get("scope")),
        "date": _json_safe(row.get("date")),
        "co2e_kg": _json_safe(row.get("co2e_kg")),
        "factor_kind": snapshot.factor_kind,
        "factor_id": snapshot.factor_id,
        "customer_factor_id": snapshot.customer_factor_id,
        "methodology": snapshot.methodology,
        "algorithm_version": snapshot.algorithm_version,
        "checkable": True,
        "reproducible": bool(verification.match) and not bool(verification.tampered),
        "conditions": [c.as_dict() for c in conditions],
        "satisfied_conditions": [c.name for c in conditions if c.satisfied],
        "unsatisfied_conditions": [c.name for c in conditions if not c.satisfied],
        "verification": {
            "match": bool(verification.match),
            "tampered": bool(verification.tampered),
            "discrepancy": (
                str(verification.discrepancy)
                if verification.discrepancy is not None
                else None
            ),
        },
        "finding_codes": sorted(codes),
        "evidence": {
            "source_item_id": snapshot.source_item_id,
            "source_line_item_id": snapshot.source_line_item_id,
            "evidence_line_item_count": evidence_count,
        },
        "basis": REPRODUCIBILITY_BASIS,
        "provenance_tool": TOOL_INSIGHT_AGGREGATE_PROVENANCE,
    }

