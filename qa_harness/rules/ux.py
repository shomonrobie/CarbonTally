"""Reusable UX rules (spec §20–§21).

Each rule turns measured browser data into a finding. The heavy lifting
(measuring queue length, workspace position, scroll distance, route change)
is done by the browser layer; these rules decide whether the measurement is a
defect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class UxRuleCheck:
    key: str
    label: str
    severity: str = "P2"
    description: str = ""
    # Numeric thresholds used by the evaluator.
    max_queue_height_before_workspace_px: int = 1200
    max_scroll_to_workspace_px: int = 800

    def evaluate_queue_workspace(self, *, queue_height_px: int,
                                 workspace_y_px: int, scroll_px: int,
                                 route_changed: bool, is_modal_or_drawer: bool,
                                 back_navigation_present: bool) -> List[Dict[str, object]]:
        """Evaluate the 'long queue → workspace far below' rule.

        Preferred pattern: Queue page → Open Workspace → focused workspace
        page/route → Back to Queue. Returns a list of findings (usually 0 or 1).
        """
        findings: List[Dict[str, object]] = []
        buried = workspace_y_px > self.max_queue_height_before_workspace_px
        if buried:
            findings.append({
                "key": self.key,
                "severity": self.severity,
                "expected": (
                    "Open Workspace navigates to a focused workspace page/route with "
                    "Back to Queue navigation."
                ),
                "actual": (
                    f"Workspace appears at y≈{workspace_y_px}px below a "
                    f"{queue_height_px}px queue; scroll distance ≈{scroll_px}px; "
                    f"route_changed={route_changed}; modal_or_drawer={is_modal_or_drawer}; "
                    f"back_navigation={back_navigation_present}."
                ),
                "measurements": {
                    "queue_height_px": queue_height_px,
                    "workspace_y_px": workspace_y_px,
                    "scroll_px": scroll_px,
                    "route_changed": route_changed,
                    "modal_or_drawer": is_modal_or_drawer,
                    "back_navigation_present": back_navigation_present,
                },
            })
        return findings

    def evaluate_loading_error_empty(self, *, loading: bool, blank: bool,
                                     raw_js_exception: bool, raw_backend_exception: bool,
                                     unhandled_promise_rejection: bool,
                                     broken_retry: bool, meaningless_error: bool,
                                     missing_empty_state: bool,
                                     console_errors: Optional[List[str]] = None,
                                     network_errors: Optional[List[str]] = None) -> List[Dict[str, object]]:
        """Evaluate loading / error / empty state rules.

        Each enabled symptom produces one finding with captured console and
        network evidence attached.
        """
        findings: List[Dict[str, object]] = []
        console_errors = console_errors or []
        network_errors = network_errors or []

        def emit(key: str, severity: str, expected: str, actual: str) -> None:
            findings.append({
                "key": key,
                "severity": severity,
                "expected": expected,
                "actual": actual,
                "console_errors": list(console_errors[:20]),
                "network_errors": list(network_errors[:20]),
            })

        if loading:
            emit("permanent_loading", "P1",
                 "Page resolves to a rendered state.",
                 "Page stuck in a loading state / spinner without progress.")
        if blank:
            emit("blank_screen", "P1",
                 "Route renders content.",
                 "Blank screen while the API is healthy.")
        if raw_js_exception:
            emit("raw_js_exception", "P1",
                 "UI renders without JavaScript exceptions.",
                 "Raw JavaScript exception rendered on screen (e.g. 'orgs.map is not a function').")
        if raw_backend_exception:
            emit("raw_backend_exception", "P2",
                 "Backend errors surface as friendly messages.",
                 "Raw backend exception text surfaced to the client.")
        if unhandled_promise_rejection:
            emit("unhandled_promise_rejection", "P2",
                 "No unhandled promise rejections.",
                 "Browser console captured an unhandled promise rejection.")
        if broken_retry:
            emit("broken_retry", "P2",
                 "Retry re-issues the request and resolves.",
                 "Retry does not re-issue the request or re-renders the same error.")
        if meaningless_error:
            emit("meaningless_error", "P2",
                 "Errors identify the cause.",
                 "Generic error message hides the real failure (e.g. 'Network error' for a 500).")
        if missing_empty_state:
            emit("missing_empty_state", "P3",
                 "Empty data shows a designed empty state.",
                 "Empty data renders as a broken/blank area without an empty state.")
        return findings


def build_ux_rule_checks() -> List[UxRuleCheck]:
    """UX checks derived from config/ux_rules.yaml (static defaults)."""
    return [
        UxRuleCheck(
            key="queue_workspace_position",
            label="Long queue → workspace appears far below the queue",
            severity="P1",
            description="Queue → Open Workspace → focused workspace page/route → Back to Queue.",
        ),
        UxRuleCheck(
            key="permanent_loading",
            label="Permanent loading / spinner without progress",
            severity="P1",
        ),
        UxRuleCheck(
            key="blank_screen",
            label="Blank screen",
            severity="P1",
        ),
        UxRuleCheck(
            key="raw_js_exception",
            label="Raw JavaScript exception",
            severity="P1",
        ),
        UxRuleCheck(
            key="raw_backend_exception",
            label="Raw backend exception",
            severity="P2",
        ),
        UxRuleCheck(
            key="unhandled_promise_rejection",
            label="Unhandled promise rejection",
            severity="P2",
        ),
        UxRuleCheck(
            key="broken_retry",
            label="Broken retry",
            severity="P2",
        ),
        UxRuleCheck(
            key="meaningless_error",
            label="Meaningless error message",
            severity="P2",
        ),
        UxRuleCheck(
            key="missing_empty_state",
            label="Missing empty state",
            severity="P3",
        ),
    ]
