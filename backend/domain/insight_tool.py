"""CarbonTally Insight I3 — controlled read-only tool contract (six-point).

Authorization: PO I3 Tool Catalogue Ratification Decision Record (2026-09-21),
which ratifies **four** read-only tools, the **six-point tool contract**,
references as locators (never grants), the status vocabulary, and the
report-reading rules (`REPORTING_LIFECYCLE_SPEC` §30.3). I3 only; I4+ unauthorized.

Pure contract/typing — no I/O, no authorization decision, no database, no
provider. Execution lives in ``services.insight_tools``; the HTTP surface in
``api.v3_insight_tools``. The only authorization input anywhere in I3 is an
``InsightAccess`` resolved by ``api.insight_authz.authorize_insight_scope``.

Six-point contract (PO §5) → where declared:

1. identity      → :class:`ToolDefinition` name/purpose/read-only classification
2. input         → :class:`ToolInputSpec` (parameters, required/optional, validation, bound)
3. authorization → :attr:`ToolDefinition.authorization` (+ ``services.insight_tools``)
4. output        → :attr:`ToolDefinition.output_fields` (explicit allowlist)
5. reference     → :attr:`ToolDefinition.reference_kinds` + :class:`InsightReference`
6. failure/status→ :class:`ToolStatus` + :class:`ToolResult`
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional, Sequence

#: Stamped on every result so a later canonical audit (I4) can attribute the
#: invocation to a known contract without redesigning it (PO §11).
TOOL_CONTRACT_VERSION = "i3-6point-v1"

#: Maximum accepted length of any identifier/reference string (bounded input).
MAX_IDENTIFIER_LENGTH = 128

#: Maximum number of items a single tool result may carry (bounded output).
MAX_RESULT_ITEMS = 200


class ToolStatus(StrEnum):
    """The ratified I3 status vocabulary (PO §9) — no other category may be added.

    ``provider_unavailable`` is reserved for future provider-dependent paths; the
    four I3 tools are not provider-dependent and never manufacture it.
    """

    SUCCESS = "success"
    NO_DATA = "no_data"
    NOT_AUTHORIZED = "not_authorized"
    INVALID_INPUT = "invalid_input"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    ERROR = "error"


#: The only reference domains I3 may address (PO §8) — locators, never grants.
REFERENCE_KINDS: tuple[str, ...] = (
    "report",
    "report_version",
    "evidence_line_item",
    "calculation_snapshot",
)


@dataclass(frozen=True, slots=True)
class InsightReference:
    """A typed locator returned by a tool (PO §8).

    Identifies an object; **not** an authorization grant. Resolving it later must
    pass through the same I2 boundary again.
    """

    kind: str
    id: str

    def __post_init__(self) -> None:
        if self.kind not in REFERENCE_KINDS:
            raise ValueError(f"unratified reference kind: {self.kind!r}")

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "id": self.id}


@dataclass(frozen=True, slots=True)
class ToolInputSpec:
    """Point 2 — accepted parameters of a tool."""

    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    max_length: int = MAX_IDENTIFIER_LENGTH

    @property
    def accepted(self) -> tuple[str, ...]:
        return tuple(self.required) + tuple(self.optional)


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """A ratified tool (points 1–5). Exactly four exist; adding one needs a PO decision."""

    name: str
    purpose: str
    read_only: bool
    input: ToolInputSpec
    #: Point 3 — authorization requirement (always the I2 boundary).
    authorization: str
    #: Point 4 — the only fields this tool may expose.
    output_fields: tuple[str, ...]
    #: Point 5 — reference kinds this tool may return.
    reference_kinds: tuple[str, ...]
    statuses: tuple[str, ...] = (
        ToolStatus.SUCCESS.value,
        ToolStatus.NO_DATA.value,
        ToolStatus.NOT_AUTHORIZED.value,
        ToolStatus.INVALID_INPUT.value,
        ToolStatus.ERROR.value,
    )


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Point 6 — bounded, deterministic structured result (PO §13/§14).

    Carries no timestamp and no random value, so an identical authorized request
    against unchanged data yields an identical result. ``invocation`` is the
    structured record I4 may later persist as canonical audit; I3 does not persist it.
    """

    tool: str
    status: ToolStatus
    contract_version: str = TOOL_CONTRACT_VERSION
    data: dict[str, Any] = field(default_factory=dict)
    references: tuple[InsightReference, ...] = ()
    #: Machine-readable reason for a non-success status (never free-form detail).
    reason: Optional[str] = None
    truncated: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "status": str(self.status),
            "contract_version": self.contract_version,
            "data": dict(self.data),
            "references": [r.as_dict() for r in self.references],
            "reason": self.reason,
            "truncated": self.truncated,
            "invocation": {
                "tool": self.tool,
                "contract_version": self.contract_version,
                "status": str(self.status),
                "authorization": "i2-boundary",
                "reference_kinds": sorted({r.kind for r in self.references}),
            },
        }


def bounded(items: Sequence[Any], limit: int = MAX_RESULT_ITEMS) -> tuple[list[Any], bool]:
    """Apply the output bound, reporting whether truncation occurred."""
    rows = list(items)
    if len(rows) <= limit:
        return rows, False
    return rows[:limit], True
