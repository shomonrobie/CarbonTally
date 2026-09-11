"""API Analyst agent (optional AI layer)."""

from __future__ import annotations

from typing import Any, List

from qa_harness.agents.base import AgentObservation, BaseAgent


class ApiAgent(BaseAgent):
    role = "api_analyst"
    system_prompt = (
        "You are an API analyst for the CarbonTally QA harness. Review API "
        "contract and endpoint findings; identify the likely root cause "
        "(schema mismatch, missing constraint, stale cache) from the evidence."
    )

    def _deterministic_observation(self, finding: Any) -> AgentObservation:
        return AgentObservation(
            agent=self.role,
            finding_id=finding.id or "",
            summary=f"[{self.role}] API contract issue: {finding.title}",
            confidence="medium",
            suggested_fix=finding.suggested_fix or "Compare request/response against the OpenAPI schema and the endpoint inventory.",
            notes="Deterministic placeholder (LLM unavailable).",
        )


def api_agent_analyze(findings: List[Any]) -> List[AgentObservation]:
    return ApiAgent().analyze(findings)
