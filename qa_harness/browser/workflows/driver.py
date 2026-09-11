"""Browser workflow driver.

Executes a :class:`~qa_harness.workflows.base.Workflow` in the browser,
recording a step outcome per action with the expected-vs-actual status.
Persisted-state verification is delegated to the run layer (DB checks) — the
browser only observes the UI outcome.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.workflows.base import Workflow, WorkflowStep


@dataclass
class StepOutcome:
    step: WorkflowStep
    observed_status: str = "NOT RUN"
    ok: bool = False
    notes: str = ""
    screenshot_path: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "action": self.step.action,
            "expected_status": self.step.expected_status,
            "observed_status": self.observed_status,
            "ok": self.ok,
            "notes": self.notes,
            "screenshot_path": self.screenshot_path,
        }


class BrowserWorkflowDriver:
    """Drives a workflow through the browser.

    ``action_handlers`` maps action names to callables
    ``(page, step) -> observed_status_str``. Unmapped actions record
    ``NOT RUN — no handler`` rather than crashing.
    """

    def __init__(self, page: Any,
                 action_handlers: Optional[Dict[str, Any]] = None) -> None:
        self.page = page
        self.action_handlers = action_handlers or {}

    def run(self, workflow: Workflow, actor: str = "") -> List[StepOutcome]:
        outcomes: List[StepOutcome] = []
        for step in workflow.steps:
            if actor and step.actor and step.actor != actor:
                outcomes.append(StepOutcome(step=step, observed_status="SKIPPED — actor mismatch", ok=True))
                continue
            handler = self.action_handlers.get(step.action)
            if handler is None:
                outcomes.append(StepOutcome(
                    step=step, observed_status="NOT RUN — no handler",
                    ok=False, notes=f"no browser handler for action {step.action!r}",
                ))
                continue
            try:
                observed = str(handler(self.page, step))
            except Exception as exc:
                outcomes.append(StepOutcome(
                    step=step, observed_status="ERROR", ok=False, notes=str(exc)[:300],
                ))
                continue
            ok = observed == step.expected_status
            outcomes.append(StepOutcome(step=step, observed_status=observed, ok=ok))
        return outcomes
