"""Run context: shared state for one QA run.

Every stage (db / api / workflows / browser) receives the same
:class:`RunContext`. It owns:

* the run id (deterministic timestamp + short git SHA),
* the :class:`~qa_harness.findings.store.FindingStore` (raw / normalized /
  deduplicated persistence),
* the :class:`~qa_harness.core.evidence.EvidenceStore` (screenshots, api,
  console, network, db evidence),
* the :class:`~qa_harness.core.secrets.Redactor` (never leaks secrets into
  findings or evidence),
* the per-category :class:`FindingIdAllocator` (stable ``QA-<CAT>-NNN`` ids
  at emit time),
* :meth:`emit` — the single entry point for creating a finding,
* :meth:`finish` — normalize + deduplicate + persist the run's findings.

The run layer never writes findings directly; it always goes through
:meth:`RunContext.emit` so redaction and id allocation are guaranteed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from qa_harness.core.config import TargetEnv
from qa_harness.core.credentials import DemoCredentials, load_demo_credentials
from qa_harness.core.evidence import EvidenceStore
from qa_harness.core.findings import (
    Finding,
    FindingClassification,
    FindingIdAllocator,
    FindingStatus,
    deduplicate_findings,
    normalize_finding,
)
from qa_harness.core.secrets import Redactor
from qa_harness.core.status import ToolUnavailable
from qa_harness.evidence.registry import EvidenceRegistry
from qa_harness.findings.store import FindingStore

HARNESS_ROOT = Path(__file__).resolve().parent.parent


def make_run_id(git_sha: str = "") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    short = git_sha[:7] if git_sha else "nosha"
    return f"{stamp}_{short}"


@dataclass
class RunContext:
    env: TargetEnv
    env_name: str = "local"
    git_sha: str = ""
    read_only: bool = True
    run_id: str = ""
    # Fresh instance per context so env secrets present at run start are caught.
    redactor: Redactor = field(default_factory=Redactor)
    store: FindingStore = field(default_factory=FindingStore)
    evidence: EvidenceStore = field(default_factory=EvidenceStore)
    registry: EvidenceRegistry = field(default_factory=EvidenceRegistry)
    credentials: Optional[DemoCredentials] = field(default=None, repr=False)
    _allocator: FindingIdAllocator = field(default_factory=FindingIdAllocator)
    _emitted: List[Finding] = field(default_factory=list)
    _checks_executed: int = 0

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = make_run_id(self.git_sha)
        if self.credentials is None:
            self.credentials = load_demo_credentials()
        # Rebuild the redactor with the demo password registered as a secret so
        # findings/evidence/log output can never contain it — regardless of
        # whether the credential came from the environment or the local file.
        if self.credentials.has_password:
            self.redactor = Redactor(extra_values=[self.credentials.password])

    # ------------------------------------------------------------------ #
    # Deterministic check counting (for honest report "tests executed")
    # ------------------------------------------------------------------ #

    def record_checks(self, n: int) -> None:
        """Accumulate the number of deterministic checks executed this run.

        Runners call this with the count of probes / rules / steps / routes
        they actually executed (SKIPPED checks are excluded), so reports can
        state real coverage instead of "Tests executed: 0".
        """
        self._checks_executed += max(0, int(n))

    @property
    def checks_executed(self) -> int:
        return self._checks_executed

    # Finding emission
    # ------------------------------------------------------------------ #

    def emit(self, category: str, severity: str, title: str, *,
             role: str = "", route: str = "", workflow: str = "",
             expected: str = "", actual: str = "", description: str = "",
             evidence: Optional[List[str]] = None,
             reproduction: Optional[List[str]] = None,
             business_impact: str = "", security_impact: str = "",
             root_cause: str = "", suggested_fix: str = "",
             status: str = FindingStatus.OPEN,
             related_cline_task: str = "",
             classification: str = FindingClassification.REAL,
             source: str = "") -> Finding:
        """Create a finding with a stable QA id and record it for this run.

        The title/description/evidence pass through the redactor so secrets
        (tokens, keys, signed URLs, passwords) can never reach reports.
        """
        finding = Finding(
            category=category,
            severity=severity,
            title=self.redactor.redact(title),
            role=role,
            route=route,
            workflow=workflow,
            expected=self.redactor.redact(expected),
            actual=self.redactor.redact(actual),
            description=self.redactor.redact(description),
            evidence=[self.redactor.redact(e) for e in (evidence or [])],
            reproduction=list(reproduction or []),
            business_impact=self.redactor.redact(business_impact),
            security_impact=self.redactor.redact(security_impact),
            root_cause=self.redactor.redact(root_cause),
            suggested_fix=self.redactor.redact(suggested_fix),
            status=status,
            related_cline_task=related_cline_task,
            classification=classification,
            source=source,
            git_sha=self.git_sha,
        )
        finding.id = self._allocator.allocate(category)
        self._emitted.append(finding)
        return finding

    def emit_skipped(self, category: str, title: str, *,
                     reason: str = "", role: str = "", route: str = "",
                     source: str = "") -> Finding:
        """Emit a non-failing SKIPPED record (never converted into PASS)."""
        return self.emit(
            category, "P3", title,
            role=role, route=route, source=source,
            expected="TOOL AVAILABLE AND EXECUTED",
            actual=f"SKIPPED — {reason or 'NOT EXECUTED'}",
            status=FindingStatus.NOT_TESTABLE,
        )

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def raw_findings(self) -> List[Finding]:
        return list(self._emitted)

    def finish(self) -> Dict[str, int]:
        """Normalize + deduplicate + persist all findings.

        Returns ``{raw, normalized, deduplicated}`` counts.
        """
        raw = self._emitted
        normalized = [normalize_finding(f) for f in raw]
        deduplicated = deduplicate_findings(raw)
        self.store.save_raw(raw)
        self.store.save_normalized(normalized)
        self.store.save_deduplicated(deduplicated)
        return {
            "raw": len(raw),
            "normalized": len(normalized),
            "deduplicated": len(deduplicated),
        }

    # ------------------------------------------------------------------ #
    # Evidence helpers
    # ------------------------------------------------------------------ #

    def api_evidence(self, role: str, name: str, payload: str,
                     route: str = "") -> Path:
        """Persist a redacted API response as evidence; returns the path."""
        path = self.evidence.write(
            "api", self.run_id, role, name, self.redactor.redact(payload),
            route=route,
        )
        self.registry.record("api", path, role=role, route=route, run_id=self.run_id)
        return path

    def console_evidence(self, role: str, name: str, payload: str,
                         route: str = "") -> Path:
        path = self.evidence.write(
            "console", self.run_id, role, name, self.redactor.redact(payload),
            route=route,
        )
        self.registry.record("console", path, role=role, route=route, run_id=self.run_id)
        return path

    def network_evidence(self, role: str, name: str, payload: str,
                         route: str = "") -> Path:
        path = self.evidence.write(
            "network", self.run_id, role, name, self.redactor.redact(payload),
            route=route,
        )
        self.registry.record("network", path, role=role, route=route, run_id=self.run_id)
        return path

    def screenshot(self, page: Any, role: str, route: str, name: str) -> str:
        """Capture a screenshot only when the page has content (spec §26).

        Returns the evidence-relative path, or "" when the capture was
        refused (blank/loading page).
        """
        try:
            text = page.inner_text("body")
            if len(text.strip()) < 10:
                return ""
            path = self.evidence.path(
                "screenshots", self.run_id, role, name, route=route, ext="png",
            )
            page.screenshot(path=str(path), full_page=True)
            self.registry.record(
                "screenshots", path, role=role, route=route, run_id=self.run_id
            )
            return str(path.relative_to(self.evidence.base_dir))
        except Exception:
            return ""

    # ------------------------------------------------------------------ #
    # Env / secrets access
    # ------------------------------------------------------------------ #

    def demo_password(self) -> str:
        """The shared demo password — environment override, then the local
        gitignored credentials file (spec V1.2). Never hard-coded.

        Raises :class:`ToolUnavailable` when no credential is available so
        callers can report ``SKIPPED — TOOL UNAVAILABLE`` (never guessed).
        """
        if not self.credentials.has_password:
            raise ToolUnavailable(
                "demo credentials",
                "no demo credential available — set CARBON_TALLY_DEMO_PASSWORD "
                "or provide the gitignored .local-demo-credentials.md file",
            )
        return self.credentials.password

    def demo_credentials_summary(self) -> Dict[str, str]:
        """Safe credential availability summary (no secret values)."""
        source_label = {
            "environment": "environment",
            "file": "local credentials file",
            "none": "NOT SET",
        }.get(self.credentials.source, self.credentials.source)
        return {
            "source": source_label,
            "password": "SET" if self.credentials.has_password else "NOT SET",
        }
