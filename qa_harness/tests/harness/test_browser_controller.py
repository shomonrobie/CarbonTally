"""BrowserController self-tests — no live stack, no real browser.

Regression: ``Browser.new_context() got multiple values for keyword argument
'viewport'`` (V1.2 calibration). ``new_context`` must forward viewport to
Playwright exactly once — the controller default, or a per-call override —
never both.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from qa_harness.browser.playwright import controller as controller_module
from qa_harness.browser.playwright.controller import BrowserController


class RecordingBrowser:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def new_context(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return object()


def _controller(monkeypatch: pytest.MonkeyPatch, viewport: Dict[str, int] | None = None) -> tuple[BrowserController, RecordingBrowser]:
    monkeypatch.setattr(controller_module, "_PLAYWRIGHT_AVAILABLE", True)
    browser = RecordingBrowser()
    controller = BrowserController(viewport=viewport) if viewport else BrowserController()
    controller._browser = browser  # bypass start()/real chromium launch
    return controller, browser


def test_new_context_default_viewport_supplied_once(monkeypatch: pytest.MonkeyPatch) -> None:
    controller, browser = _controller(monkeypatch)
    controller.new_context()
    assert len(browser.calls) == 1
    call = browser.calls[0]
    assert "viewport" in call
    assert call["viewport"] == {"width": 1440, "height": 900}
    # exactly one viewport occurrence per call
    assert sum(k == "viewport" for k in call) == 1


def test_new_context_override_viewport_supplied_once(monkeypatch: pytest.MonkeyPatch) -> None:
    controller, browser = _controller(monkeypatch)
    controller.new_context(viewport={"width": 375, "height": 812})
    assert len(browser.calls) == 1
    call = browser.calls[0]
    assert call["viewport"] == {"width": 375, "height": 812}
    assert sum(k == "viewport" for k in call) == 1


def test_new_context_controller_default_overrideable(monkeypatch: pytest.MonkeyPatch) -> None:
    controller, browser = _controller(monkeypatch, viewport={"width": 1920, "height": 1080})
    controller.new_context()
    controller.new_context(viewport={"width": 430, "height": 932})
    assert browser.calls[0]["viewport"] == {"width": 1920, "height": 1080}
    assert browser.calls[1]["viewport"] == {"width": 430, "height": 932}


def test_new_context_passes_other_options_through(monkeypatch: pytest.MonkeyPatch) -> None:
    controller, browser = _controller(monkeypatch)
    controller.new_context(ignore_https_errors=True, locale="en-GB")
    call = browser.calls[0]
    assert call["ignore_https_errors"] is True
    assert call["locale"] == "en-GB"
    assert call["viewport"] == {"width": 1440, "height": 900}


def test_responsive_viewport_set_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every configured responsive viewport must still reach Playwright as an
    override after the fix (spec §24 viewport set is not weakened)."""
    from qa_harness.browser.responsive.auditor import ResponsiveAuditor
    viewports = ResponsiveAuditor.VIEWPORTS
    assert len(viewports) == 8
    controller, browser = _controller(monkeypatch)
    for width, height, _label in viewports:
        controller.new_context(viewport={"width": width, "height": height})
    supplied = [c["viewport"] for c in browser.calls]
    assert {(w, h) for w, h, _ in viewports} == {
        (vp["width"], vp["height"]) for vp in supplied}
    assert all(sum(k == "viewport" for k in call) == 1 for call in browser.calls)
