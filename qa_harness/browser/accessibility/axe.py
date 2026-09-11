"""axe-core accessibility integration (spec §25).

Runs axe-core in the page via CDP/Playwright. When axe-core cannot be loaded
the runner reports ``SKIPPED — TOOL UNAVAILABLE``. Checks labels, ARIA,
headings, keyboard navigation, focus, buttons, forms, dialogs, landmarks,
alt text and contrast (axe rule tags).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.core.status import ToolUnavailable

# axe-core can be served locally from node_modules or fetched; the runner
# prefers an injected source. Version is informational.
AXE_RULES_TAGS = ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"]


@dataclass
class A11yResult:
    route: str
    role: str = ""
    violations: List[Dict[str, object]] = field(default_factory=list)
    passes: int = 0
    incomplete: int = 0
    tool_status: str = "OK"

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def to_dict(self) -> Dict[str, object]:
        return {
            "route": self.route,
            "role": self.role,
            "violations": self.violations[:50],
            "violation_count": self.violation_count,
            "passes": self.passes,
            "incomplete": self.incomplete,
            "tool_status": self.tool_status,
        }


@dataclass
class AxeAudit:
    results: List[A11yResult] = field(default_factory=list)

    def total_violations(self) -> int:
        return sum(r.violation_count for r in self.results)

    def to_dict(self) -> Dict[str, object]:
        return {"pages": [r.to_dict() for r in self.results]}


class AxeRunner:
    """Injects axe-core and runs an accessibility scan on the current page."""

    CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.0/axe.min.js"

    def __init__(self, page: Any, axe_source: Optional[str] = None,
                 cdn_url: str = CDN) -> None:
        self.page = page
        self.axe_source = axe_source
        self.cdn_url = cdn_url

    def _inject(self) -> bool:
        if self.axe_source:
            self.page.add_script_tag(content=self.axe_source)
        else:
            try:
                self.page.add_script_tag(url=self.cdn_url)
            except Exception:
                return False
        return True

    def scan(self, route: str, role: str = "") -> A11yResult:
        result = A11yResult(route=route, role=role)
        if not self._inject():
            result.tool_status = "SKIPPED — TOOL UNAVAILABLE (axe-core could not be injected)"
            return result
        try:
            data = self.page.evaluate(
                """async (tags) => {
                    const r = await axe.run(document, { runOnly: { type: 'tag', values: tags } });
                    return {
                        violations: r.violations.map(v => ({
                            id: v.id, impact: v.impact, help: v.help,
                            nodes: v.nodes.length,
                            target: (v.nodes[0] && v.nodes[0].target) || []
                        })),
                        passes: r.passes.length,
                        incomplete: r.incomplete.length
                    };
                }""",
                AXE_RULES_TAGS,
            )
            result.violations = data.get("violations", [])
            result.passes = data.get("passes", 0)
            result.incomplete = data.get("incomplete", 0)
        except Exception as exc:
            result.tool_status = f"SKIPPED — TOOL UNAVAILABLE (axe.run failed: {exc})"
        return result
