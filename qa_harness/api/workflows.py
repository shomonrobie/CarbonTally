"""Workflow state-machine representation for API-driven QA (spec §13–§14).

The processing pipeline is a strict state machine
(``extracting → extracted → mapping → mapped → validating → validated →
calculating → calculated → ...``). The harness drives the API precisely and
verifies persisted state — never UI animations. This module encodes the
documented transition vocabulary and validates transition legality.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# Documented processing stages (from the backend processing_workflow engine
# and the persona audit's PRC-1 finding).
DOCUMENTED_STAGES = [
    "uploaded", "pending", "queued",
    "extracting", "extracted",
    "mapping", "mapped",
    "validating", "validated",
    "calculating", "calculated",
    "review", "approved", "rejected",
    "completed", "failed",
]

# Documented legal transitions (stage → allowed next stages). Encoded from the
# backend state machine; the run layer compares the API's behaviour to this.
DOCUMENTED_TRANSITIONS: Dict[str, Set[str]] = {
    "uploaded": {"pending"},
    "pending": {"queued", "extracting", "failed"},
    "queued": {"extracting", "ingesting", "failed"},
    "ingesting": {"extracting", "failed"},
    "extracting": {"extracted", "failed"},
    "extracted": {"mapping", "failed"},
    "mapping": {"mapped", "failed"},
    "mapped": {"validating", "failed"},
    "validating": {"validated", "failed"},
    "validated": {"calculating", "failed"},
    "calculating": {"calculated", "failed"},
    "calculated": {"review", "approved", "failed"},
    "review": {"approved", "rejected", "mapping", "failed"},
    "approved": {"completed"},
    "rejected": {"mapping", "failed"},
    "completed": {"archived"},
    "failed": {"queued", "extracting", "retry"},
    "retry": {"queued", "extracting"},
}

# The documented happy-path pipeline used by WorkflowStateMachine.pipeline().
MAINLINE: List[str] = [
    "queued", "extracting", "extracted", "mapping", "mapped",
    "validating", "validated", "calculating", "calculated",
    "review", "approved", "completed",
]

# Actions that map to stage transitions (start('calculation') etc.).
STAGE_ACTIONS: Dict[str, str] = {
    "extract": "extracting",
    "map": "mapping",
    "validate": "validating",
    "calculation": "calculating",
    "calculate": "calculating",
    "review": "review",
    "approve": "approved",
    "reject": "rejected",
    "complete": "completed",
}


@dataclass
class StateTransition:
    item_id: str
    from_stage: str
    action: str
    to_stage: Optional[str] = None
    http_status: Optional[int] = None
    legal: Optional[bool] = None
    note: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "item_id": self.item_id,
            "from_stage": self.from_stage,
            "action": self.action,
            "to_stage": self.to_stage,
            "http_status": self.http_status,
            "legal": self.legal,
            "note": self.note,
        }


class WorkflowStateMachine:
    """Validates transitions against the documented vocabulary."""

    def __init__(self, stages: Optional[List[str]] = None,
                 transitions: Optional[Dict[str, Set[str]]] = None) -> None:
        self.stages = stages or DOCUMENTED_STAGES
        self.transitions = transitions or DOCUMENTED_TRANSITIONS

    def is_stage(self, stage: str) -> bool:
        return stage in self.stages

    def legal_next(self, stage: str) -> Set[str]:
        return self.transitions.get(stage, set())

    def check(self, item_id: str, from_stage: str, action: str,
              observed_status: Optional[int] = None) -> StateTransition:
        """Record and validate one transition attempt.

        The transition is legal when ``action`` resolves to a stage reachable
        from ``from_stage``. A 409/422 on a legal transition is a WARNING; a
        409 on an illegal transition is expected behaviour.
        """
        to_stage = STAGE_ACTIONS.get(action, action)
        legal = to_stage in self.legal_next(from_stage)
        return StateTransition(
            item_id=item_id,
            from_stage=from_stage,
            action=action,
            to_stage=to_stage,
            http_status=observed_status,
            legal=legal,
            note="" if legal else f"transition {from_stage} → {to_stage} not documented",
        )

    def pipeline(self, start: str = "queued", end: str = "approved") -> List[str]:
        """Return the documented happy path through the pipeline for coverage.

        Deterministic: walks the documented mainline (queued → extracting →
        extracted → mapping → mapped → validating → validated → calculating →
        calculated → review → approved → completed), skipping only hops the
        state machine does not allow. Never loops on failure/retry edges.
        """
        path: List[str] = [start]
        current = start
        try:
            idx = MAINLINE.index(start)
        except ValueError:
            idx = 0
        while current != end and len(path) <= len(MAINLINE) + 2:
            legal = self.legal_next(current)
            if end in legal:
                path.append(end)
                break
            if idx + 1 < len(MAINLINE) and MAINLINE[idx + 1] in legal:
                idx += 1
                current = MAINLINE[idx]
                path.append(current)
            else:
                nxt = next((s for s in sorted(legal) if s not in path), None)
                if nxt is None:
                    break
                path.append(nxt)
                if nxt in MAINLINE:
                    idx = MAINLINE.index(nxt)
                current = nxt
        return path
