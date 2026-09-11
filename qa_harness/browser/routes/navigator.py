"""Route visiting with readiness + state capture (spec §23, §26).

Prioritizes authenticated workspaces; does not waste screenshots on the
public homepage unless the route itself is under test. A visit records the
URL, role, viewport, screenshot path, console errors, network failures and
loading/error/empty state signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from qa_harness.browser.playwright.controller import BrowserController, PageReadiness


@dataclass
class RouteVisit:
    route: str
    role: str = ""
    viewport: Dict[str, int] = field(default_factory=dict)
    title: str = ""
    url: str = ""
    body_text_length: int = 0
    screenshot_path: str = ""
    console_errors: List[str] = field(default_factory=list)
    network_failures: List[str] = field(default_factory=list)
    loading: bool = False
    blank: bool = False
    raw_js_exception: bool = False
    http_status: Optional[int] = None
    ok: bool = True

    def to_dict(self) -> Dict[str, object]:
        return {
            "route": self.route,
            "role": self.role,
            "viewport": self.viewport,
            "title": self.title,
            "url": self.url,
            "body_text_length": self.body_text_length,
            "screenshot_path": self.screenshot_path,
            "console_errors": self.console_errors[:20],
            "network_failures": self.network_failures[:20],
            "loading": self.loading,
            "blank": self.blank,
            "raw_js_exception": self.raw_js_exception,
            "http_status": self.http_status,
            "ok": self.ok,
        }


class Navigator:
    """Visits routes under a browser context and captures state."""

    def __init__(self, controller: BrowserController, base_url: str = "http://localhost:3000",
                 readiness: Optional[PageReadiness] = None) -> None:
        self.controller = controller
        self.base_url = base_url.rstrip("/")
        self.readiness = readiness or PageReadiness(
            selector="body", network_idle=True, min_content_length=20
        )

    def visit(self, route: str, role: str = "", viewport: Optional[Dict[str, int]] = None,
              screenshot_path: str = "") -> RouteVisit:
        visit = RouteVisit(route=route, role=role, viewport=viewport or {})
        console_errors: List[str] = []
        network_failures: List[str] = []

        def on_console(message: Any) -> None:
            text = str(message.text)
            if message.type == "error":  # type: ignore[attr-defined]
                console_errors.append(text[:500])

        def on_requestfailed(request: Any) -> None:
            network_failures.append(f"{request.method} {request.url} — {request.failure}")

        page = self.controller.new_page()
        page.on("console", on_console)
        page.on("requestfailed", on_requestfailed)
        try:
            page.goto(self.base_url + route, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            visit.title = page.title()
            visit.url = page.url
            try:
                body_text = page.inner_text("body")
            except Exception:
                body_text = ""
            visit.body_text_length = len(body_text.strip())
            visit.loading = self._is_loading(body_text)
            visit.blank = len(body_text.strip()) < 10
            visit.raw_js_exception = self._has_js_exception(body_text)
            visit.console_errors = console_errors
            visit.network_failures = network_failures
            if screenshot_path and visit.body_text_length >= 10:
                try:
                    page.screenshot(path=screenshot_path, full_page=True)
                    visit.screenshot_path = screenshot_path
                except Exception:
                    pass
        except Exception as exc:  # navigation failure itself
            visit.ok = False
            visit.console_errors = console_errors
            visit.network_failures = network_failures
            visit.http_status = getattr(exc, "status", None)
        finally:
            try:
                page.close()
            except Exception:
                pass
        return visit

    @staticmethod
    def _is_loading(body_text: str) -> bool:
        lowered = body_text.lower()
        return "loading" in lowered and "error" not in lowered

    @staticmethod
    def _has_js_exception(body_text: str) -> bool:
        lowered = body_text.lower()
        return (
            ".map is not a function" in lowered
            or "is not a function" in lowered
            or "cannot read properties of undefined" in lowered
            or "referenceerror" in lowered
        )
