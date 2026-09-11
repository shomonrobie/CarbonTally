"""Run-status and tool-availability envelope.

Optional tools (Playwright, Chromium, axe, Schemathesis, pgTAP, OWASP ZAP,
OpenRouter) may be absent from the environment. The harness must degrade
gracefully and report ``SKIPPED — TOOL UNAVAILABLE`` instead of crashing
(spec §36). This module defines that vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RunStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"
    NOT_RUN = "NOT RUN"
    TOOL_UNAVAILABLE = "SKIPPED — TOOL UNAVAILABLE"
    MUTATION_NOT_AVAILABLE = "BLOCKED — SAFE MUTATION NOT AVAILABLE"


class ToolUnavailable(RuntimeError):
    """Raised when an optional tool cannot be loaded/started.

    Callers should catch this and record a ``SKIPPED — TOOL UNAVAILABLE``
    result rather than propagating a traceback.
    """

    def __init__(self, tool: str, reason: str = "") -> None:
        super().__init__(f"Tool unavailable: {tool}" + (f" ({reason})" if reason else ""))
        self.tool = tool
        self.reason = reason


@dataclass
class CheckResult:
    """Result envelope for a single QA check.

    ``details`` and ``evidence`` are redacted at serialization time by the
    report layer; this dataclass stores raw values.
    """

    name: str
    status: RunStatus
    details: str = ""
    evidence: List[str] = field(default_factory=list)
    finding: Optional[Any] = None  # qa_harness.core.findings.Finding

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "details": self.details,
            "evidence": list(self.evidence),
            "finding_id": getattr(self.finding, "id", None),
        }


@dataclass
class ModuleResult:
    """Aggregated result of one QA module (db, api, browser, ...)."""

    module: str
    status: RunStatus = RunStatus.NOT_RUN
    checks: List[CheckResult] = field(default_factory=list)
    findings: List[Any] = field(default_factory=list)
    skipped_reason: str = ""

    def add_check(self, check: CheckResult) -> None:
        self.checks.append(check)
        if check.finding is not None:
            self.findings.append(check.finding)

    def mark_skipped(self, tool: str, reason: str = "") -> None:
        self.status = RunStatus.TOOL_UNAVAILABLE
        self.skipped_reason = reason or tool

    def summary_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {status.value: 0 for status in RunStatus}
        for check in self.checks:
            counts[check.status.value] = counts.get(check.status.value, 0) + 1
        return counts
