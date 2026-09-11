"""Shared workflow step model.

A workflow is a list of :class:`WorkflowStep` records. Each step names an
action, an expected HTTP status, the actor role, and whether persisted state
must be verified afterward. The run layer executes steps against the live
stack; the definitions here are declarative and application-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowStep:
    action: str
    expected_status: str = "200"       # "200" | "201" | "403" | "deny" | "no_path"
    actor: str = ""
    verify_persisted: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "action": self.action,
            "expected_status": self.expected_status,
            "actor": self.actor,
            "verify_persisted": self.verify_persisted,
            "description": self.description,
        }


@dataclass
class Workflow:
    key: str
    label: str
    personas: List[str]
    steps: List[WorkflowStep]
    description: str = ""
    checks: List[str] = field(default_factory=list)   # named cross-cutting checks

    def to_dict(self) -> Dict[str, object]:
        return {
            "key": self.key,
            "label": self.label,
            "personas": list(self.personas),
            "steps": [s.to_dict() for s in self.steps],
            "checks": list(self.checks),
            "description": self.description,
        }


def step(action: str, expected_status: str = "200", actor: str = "",
         verify_persisted: bool = True, description: str = "") -> WorkflowStep:
    return WorkflowStep(
        action=action,
        expected_status=expected_status,
        actor=actor,
        verify_persisted=verify_persisted,
        description=description,
    )
