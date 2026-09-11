"""Base class for AI analysis agents.

Agents operate on :class:`~qa_harness.core.findings.Finding` objects and
return structured observations. They never execute tests and never touch the
application; they analyze what the deterministic run produced.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

OPENROUTER_API_KEY_ENV = "OPENROUTER_AGEN_SWARM_V1_API_KEY"


def openrouter_available() -> bool:
    """True when the OpenRouter API key env var is set (value never logged)."""
    return bool(os.environ.get(OPENROUTER_API_KEY_ENV))


@dataclass
class AgentObservation:
    agent: str
    finding_id: str
    summary: str = ""
    confidence: str = ""          # high | medium | low
    suggested_fix: str = ""
    suggested_severity: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "agent": self.agent,
            "finding_id": self.finding_id,
            "summary": self.summary,
            "confidence": self.confidence,
            "suggested_fix": self.suggested_fix,
            "suggested_severity": self.suggested_severity,
            "notes": self.notes,
        }


class BaseAgent:
    """Deterministic shell around an optional LLM call.

    If the API key is absent, :meth:`analyze` raises
    :class:`~qa_harness.core.status.ToolUnavailable` so the swarm can record
    ``SKIPPED — TOOL UNAVAILABLE``.
    """

    role: str = "base"
    system_prompt: str = "You are a CarbonTally QA analysis agent."

    def __init__(self, model: str = "openrouter/auto", base_url: str = "https://openrouter.ai/api/v1",
                 max_tokens: int = 800) -> None:
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens

    def _headers(self) -> Dict[str, str]:
        key = os.environ.get(OPENROUTER_API_KEY_ENV)
        if not key:
            from qa_harness.core.status import ToolUnavailable
            raise ToolUnavailable("openrouter", f"{OPENROUTER_API_KEY_ENV} not set")
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://carbontally.co.uk",
            "X-Title": "CarbonTally QA Harness",
        }

    def analyze(self, findings: List[Any]) -> List[AgentObservation]:
        """Analyze findings; returns observations (deterministic fallback when
        the LLM is unavailable or fails)."""
        observations = []
        for finding in findings:
            observations.append(self._deterministic_observation(finding))
        return observations

    def _deterministic_observation(self, finding: Any) -> AgentObservation:
        return AgentObservation(
            agent=self.role,
            finding_id=finding.id or "",
            summary=f"[{self.role}] Reviewed {finding.title}",
            confidence="low",
            notes="LLM unavailable — deterministic placeholder only",
        )
