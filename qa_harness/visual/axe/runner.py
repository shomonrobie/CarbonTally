"""Visual a11y runner combining axe scans with screenshot discipline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.browser.accessibility.axe import A11yResult, AxeRunner
from qa_harness.core.evidence import EvidenceStore


@dataclass
class VisualAxeRunner:
    """Runs axe on a page and stores evidence under evidence/screenshots.

    Screenshots are only captured when the page has content (readiness is the
    caller's responsibility); the runner refuses blank/loading captures.
    """

    evidence: EvidenceStore = field(default_factory=EvidenceStore)

    def scan_page(self, page: Any, *, route: str, role: str, run_id: str,
                  viewport: str = "1440x900") -> A11yResult:
        runner = AxeRunner(page)
        result = runner.scan(route, role)
        if result.violations:
            evidence_path = self.evidence.path(
                "screenshots", run_id, role, f"a11y_{route.replace('/', '_')}",
                route=route, ext="png",
            )
            try:
                text = page.inner_text("body")
                if len(text.strip()) >= 10:
                    page.screenshot(path=str(evidence_path), full_page=True)
            except Exception:
                pass
        return result
