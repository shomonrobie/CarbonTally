"""Optional Playwright browser controller.

If Playwright/Chromium is unavailable the controller reports
``SKIPPED — TOOL UNAVAILABLE`` (spec §36) instead of crashing the harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.core.status import ToolUnavailable

try:
    from playwright.sync_api import (  # type: ignore
        Browser,
        BrowserContext,
        Page,
        TimeoutError as PlaywrightTimeoutError,
        sync_playwright,
    )
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised via optional-dep tests
    _PLAYWRIGHT_AVAILABLE = False
    Browser = Any  # type: ignore
    BrowserContext = Any  # type: ignore
    Page = Any  # type: ignore
    PlaywrightTimeoutError = TimeoutError  # type: ignore
    sync_playwright = None  # type: ignore


def browser_available() -> bool:
    """True when the playwright package is importable."""
    return _PLAYWRIGHT_AVAILABLE


@dataclass
class PageReadiness:
    """Explicit readiness condition — a screenshot is only captured AFTER the
    page satisfies this condition (spec §26)."""

    selector: str = ""                       # wait for this selector
    network_idle: bool = True                # wait for network idle
    min_content_length: int = 50             # visible text length threshold
    timeout_ms: int = 15000


@dataclass
class BrowserController:
    """Thin wrapper over Playwright sync API with readiness discipline."""

    headless: bool = True
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1440, "height": 900})
    _pw: Any = None
    _browser: Optional[Any] = None
    _context: Optional[Any] = None

    def __post_init__(self) -> None:
        if not _PLAYWRIGHT_AVAILABLE:
            raise ToolUnavailable("playwright", "pip package not installed")

    def start(self) -> "BrowserController":
        if self._browser is not None:
            return self
        try:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(headless=self.headless)
        except Exception as exc:
            raise ToolUnavailable("chromium", str(exc)) from exc
        return self

    def new_context(self, **kwargs: Any) -> Any:
        if self._browser is None:
            self.start()
        # viewport may be overridden per call (responsive sweeps) — pop it so it
        # is supplied exactly once to Playwright (a duplicate keyword would
        # raise "got multiple values for keyword argument 'viewport'").
        viewport = kwargs.pop("viewport", self.viewport)
        self._context = self._browser.new_context(viewport=viewport, **kwargs)
        return self._context

    def new_page(self) -> Any:
        if self._context is None:
            self.new_context()
        return self._context.new_page()

    def open(self, url: str, readiness: Optional[PageReadiness] = None) -> Any:
        """Navigate and wait for the explicit readiness condition."""
        page = self.new_page()
        page.goto(url, wait_until="domcontentloaded")
        condition = readiness or PageReadiness()
        if condition.selector:
            page.wait_for_selector(condition.selector, timeout=condition.timeout_ms)
        if condition.network_idle:
            try:
                page.wait_for_load_state("networkidle", timeout=condition.timeout_ms)
            except PlaywrightTimeoutError:
                pass  # network idle is a soft condition
        return page

    def capture_screenshot(self, page: Any, path: str) -> bool:
        """Capture only when the page has content (never a loading/blank shot)."""
        try:
            text = page.inner_text("body")
            if len(text.strip()) < 10:
                return False
            page.screenshot(path=path, full_page=True)
            return True
        except Exception:
            return False

    def stop(self) -> None:
        try:
            if self._browser is not None:
                self._browser.close()
            if self._pw is not None:
                self._pw.stop()
        finally:
            self._browser = None
            self._pw = None

    def __enter__(self) -> "BrowserController":
        return self.start()

    def __exit__(self, *exc: Any) -> None:
        self.stop()
