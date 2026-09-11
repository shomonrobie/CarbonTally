"""Workflow Analyst agent (optional AI layer)."""

from __future__ import annotations

from typing import Any, List

from qa_harness.agents.base import AgentObservation, BaseAgent


class WorkflowAgent(BaseAgent):
    role = "workflow_analyst"
    system_prompt = (
        "You are a workflow analyst for the CarbonTally QA harness. Review "
        "workflow findings (document processing, review, approval, reporting) "
        "and identify where the chain breaks and what must be fixed first."
    )

    def _deterministic_observation(self, finding: Any) -> AgentObservation:
        return AgentObservation(
            agent=self.role,
            finding_id=finding.id or "",
            summary=f"[{self.role}] Workflow blockage at {finding.workflow or 'unknown'}: {finding.title}",
            confidence="medium",
            suggested_fix=finding.suggested_fix or "Inspect the failing workflow step and its persisted state.",
            notes="Deterministic placeholder (LLM unavailable).",
        )


def workflow_agent_analyze(findings: List[Any]) -> List[AgentObservation]:
    return WorkflowAgent().analyze(findings)
