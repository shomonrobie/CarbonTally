"""Final Judge agent (optional AI layer).

Aggregates deterministic findings + analyst observations into an acceptance
recommendation. The judge NEVER overrides the deterministic verdict; it only
adds context. Acceptance is never claimed merely because tests were
incomplete.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.agents.base import AgentObservation, BaseAgent, openrouter_available


@dataclass
class JudgeVerdict:
    recommended: str = "UNVERIFIED"      # ACCEPTED | ACCEPTED WITH CONDITIONS | NOT ACCEPTED | UNVERIFIED
    reasoning: str = ""
    observations: List[AgentObservation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "recommended": self.recommended,
            "reasoning": self.reasoning,
            "observations": [o.to_dict() for o in self.observations],
        }


def deterministic_verdict(findings: List[Any], unverified_areas: Optional[List[str]] = None) -> str:
    """The deterministic acceptance verdict (spec §31).

    NOT ACCEPTED when any verdict-counted P0/P1 exists; UNVERIFIED when core
    areas were not tested; ACCEPTED WITH CONDITIONS when only P2s remain;
    ACCEPTED otherwise.

    Only findings classified REAL or RE-VERIFY count toward the verdict
    (V1.2 calibration). HARNESS_CONTRACT_DEFECT / INCONCLUSIVE / SKIPPED /
    BLOCKED findings are harness artifacts, not app defects, and must never
    drive an acceptance decision.
    """
    from qa_harness.core.findings import FindingClassification

    counted = [
        f for f in findings
        if getattr(f, "classification", FindingClassification.REAL)
        in FindingClassification.VERDICT_COUNTED
    ]
    severities = {f.severity for f in counted}
    if "P0" in severities or "P1" in severities:
        return "NOT ACCEPTED"
    if unverified_areas:
        return "UNVERIFIED"
    if "P2" in severities:
        return "ACCEPTED WITH CONDITIONS"
    return "ACCEPTED"


class JudgeAgent(BaseAgent):
    role = "final_judge"
    system_prompt = (
        "You are the final acceptance judge for the CarbonTally QA harness. "
        "Given deterministic findings and analyst observations, write a short "
        "investor-ready summary. Never claim acceptance for untested areas."
    )

    def judge(self, findings: List[Any],
              unverified_areas: Optional[List[str]] = None,
              observations: Optional[List[AgentObservation]] = None) -> JudgeVerdict:
        base = deterministic_verdict(findings, unverified_areas)
        if not openrouter_available():
            return JudgeVerdict(
                recommended=base,
                reasoning="Deterministic verdict (AI judge unavailable — OPENROUTER key not set).",
                observations=observations or [],
            )
        # LLM path: build a compact prompt from findings only.
        try:
            prompt = self._build_prompt(findings, base)
            reasoning = self._call_llm(prompt)
            return JudgeVerdict(recommended=base, reasoning=reasoning, observations=observations or [])
        except Exception as exc:
            return JudgeVerdict(
                recommended=base,
                reasoning=f"AI judge call failed ({exc}); deterministic verdict retained.",
                observations=observations or [],
            )

    def _build_prompt(self, findings: List[Any], base: str) -> str:
        lines = [f"Deterministic verdict: {base}"]
        for finding in findings[:40]:
            lines.append(
                f"- [{finding.severity}] {finding.category} {finding.id}: {finding.title}"
            )
        return "\n".join(lines)

    def _call_llm(self, prompt: str) -> str:
        import json

        import requests  # type: ignore

        response = requests.post(
            self.base_url.rstrip("/") + "/chat/completions",
            headers=self._headers(),
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": self.max_tokens,
            },
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        return body["choices"][0]["message"]["content"]
