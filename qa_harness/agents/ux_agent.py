"""UX Analyst agent (optional AI layer)."""

from __future__ import annotations

from typing import Any, List

from qa_harness.agents.base import AgentObservation, BaseAgent


class UxAgent(BaseAgent):
    role = "ux_analyst"
    system_prompt = (
        "You are a UX analyst for the CarbonTally QA harness. Review UX/UI "
        "findings, propose the highest-value fix, and flag severity changes "
        "only with strong justification. Be concise."
    )

    def _deterministic_observation(self, finding: Any) -> AgentObservation:
        return AgentObservation(
            agent=self.role,
            finding_id=finding.id or "",
            summary=f"[{self.role}] UX severity {finding.severity}: {finding.title}",
            confidence="medium",
            suggested_fix=finding.suggested_fix or "Review the workspace UX rule that triggered this finding.",
            notes="Deterministic placeholder (LLM unavailable).",
        )


def ux_agent_analyze(findings: List[Any]) -> List[AgentObservation]:
    return UxAgent().analyze(findings)
