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
from typing import Any, Optional

from fastapi import HTTPException

from api.dependencies import RepositoryBundle
from api.insight_authz import InsightAccess, authorize_insight_scope
from auth import AuthUser
from domain.disclosure import IMMUTABLE_REPORT_VERSION_STATUSES
from domain.insight_tool import (
    MAX_IDENTIFIER_LENGTH,
    InsightReference,
    ToolDefinition,
    ToolInputSpec,
    ToolResult,
    ToolStatus,
    bounded,
)

TOOL_REPORT_LOOKUP = "report_lookup"
TOOL_REPORT_VERSION_LOOKUP = "report_version_lookup"
TOOL_REPORT_EVIDENCE_LOOKUP = "report_evidence_lookup"
TOOL_CALCULATION_SNAPSHOT_LOOKUP = "calculation_snapshot_lookup"

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
    if not tool.input.required:
        if not (tool_input.get("version_id") or (tool_input.get("report_id") and tool_input.get("version_number"))):
            return "missing_required_parameter"
    return None


async def _authorize(
    current_user: AuthUser, repos: RepositoryBundle, organization_id: str
) -> Optional[InsightAccess]:
    """Resolve the caller's scope through the closed I2 boundary (never re-implemented)."""
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
        return _result(tool.name, ToolStatus.INVALID_INPUT, reason="unratified_tool")
    except Exception:  # noqa: BLE001 - never leak internal detail to the caller
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
