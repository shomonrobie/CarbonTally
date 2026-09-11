"""Agent swarm orchestrator (spec §27).

Runs the role agents over deduplicated findings. Deterministic tests always
run; the swarm only adds analysis. Without the OpenRouter key the swarm
reports ``SKIPPED — TOOL UNAVAILABLE``. AI cost is minimized: only findings
are sent, never passing tests, and findings per agent are capped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.agents.api_agent import ApiAgent
from qa_harness.agents.base import AgentObservation, openrouter_available
from qa_harness.agents.judge_agent import JudgeAgent, JudgeVerdict, deterministic_verdict
from qa_harness.agents.security_agent import SecurityAgent
from qa_harness.agents.ux_agent import UxAgent
from qa_harness.agents.workflow_agent import WorkflowAgent
from qa_harness.core.status import RunStatus, ToolUnavailable


@dataclass
class SwarmRun:
    status: RunStatus = RunStatus.NOT_RUN
    observations: List[AgentObservation] = field(default_factory=list)
    verdict: Optional[JudgeVerdict] = None
    skipped_reason: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status.value,
            "observations": [o.to_dict() for o in self.observations],
            "verdict": self.verdict.to_dict() if self.verdict else None,
            "skipped_reason": self.skipped_reason,
        }


class AgentSwarm:
    """Runs the configured role agents over deduplicated findings."""

    def __init__(self, model: str = "openrouter/auto",
                 base_url: str = "https://openrouter.ai/api/v1",
                 max_findings_per_agent: int = 25) -> None:
        self.model = model
        self.base_url = base_url
        self.max_findings_per_agent = max_findings_per_agent
        self.agents = [
            UxAgent(model=model, base_url=base_url),
            WorkflowAgent(model=model, base_url=base_url),
            SecurityAgent(model=model, base_url=base_url),
            ApiAgent(model=model, base_url=base_url),
        ]

    def run(self, findings: List[Any],
            unverified_areas: Optional[List[str]] = None,
            judge: Optional[JudgeAgent] = None) -> SwarmRun:
        if not openrouter_available():
            return SwarmRun(
                status=RunStatus.TOOL_UNAVAILABLE,
                skipped_reason="OPENROUTER_AGEN_SWARM_V1_API_KEY not set",
                verdict=JudgeVerdict(
                    recommended=deterministic_verdict(findings, unverified_areas),
                    reasoning="Deterministic verdict (AI swarm unavailable).",
                ),
            )
        observations: List[AgentObservation] = []
        for agent in self.agents:
            try:
                observations.extend(agent.analyze(findings[: self.max_findings_per_agent]))
            except ToolUnavailable:
                continue
            except Exception:
                continue
        verdict = (judge or JudgeAgent(model=self.model, base_url=self.base_url)).judge(
            findings, unverified_areas=unverified_areas, observations=observations
        )
        return SwarmRun(status=RunStatus.PASS, observations=observations, verdict=verdict)
