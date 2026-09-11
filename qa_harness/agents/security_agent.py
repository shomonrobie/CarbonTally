"""Security Analyst agent (optional AI layer)."""

from __future__ import annotations

from typing import Any, List

from qa_harness.agents.base import AgentObservation, BaseAgent


class SecurityAgent(BaseAgent):
    role = "security_analyst"
    system_prompt = (
        "You are a security analyst for the CarbonTally QA harness. Review "
        "security/RLS/authorization findings. Assess real exploitability and "
        "business impact; never inflate severity without evidence."
    )

    def _deterministic_observation(self, finding: Any) -> AgentObservation:
        return AgentObservation(
            agent=self.role,
            finding_id=finding.id or "",
            summary=f"[{self.role}] Security check on {finding.title}",
            confidence="medium",
            suggested_fix=finding.suggested_fix or "Verify the RLS/authorization expectation against the denied/allowed matrix.",
            notes="Deterministic placeholder (LLM unavailable).",
        )


def security_agent_analyze(findings: List[Any]) -> List[AgentObservation]:
    return SecurityAgent().analyze(findings)
