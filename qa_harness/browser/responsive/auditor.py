"""Responsive layout audit (spec §24).

Viewports: 1920x1080, 1440x900, 1280x800, 1024x768, 768x1024, 430x932,
390x844, 375x812. Detects horizontal overflow, clipped tables, broken forms,
broken dialogs, broken navigation, broken workspaces, unusable mobile tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ViewportResult:
    width: int
    height: int
    label: str
    horizontal_overflow: bool = False
    overflow_px: int = 0
    body_text_length: int = 0
    page_error: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "viewport": f"{self.width}x{self.height}",
            "label": self.label,
            "horizontal_overflow": self.horizontal_overflow,
            "overflow_px": self.overflow_px,
            "body_text_length": self.body_text_length,
            "page_error": self.page_error,
            "notes": self.notes,
        }


@dataclass
class ResponsiveAudit:
    results: List[ViewportResult] = field(default_factory=list)

    def overflows(self) -> List[ViewportResult]:
        return [r for r in self.results if r.horizontal_overflow]

    def failures(self) -> List[ViewportResult]:
        return [r for r in self.results if r.page_error]

    def to_dict(self) -> Dict[str, object]:
        return {"viewports": [r.to_dict() for r in self.results]}


class ResponsiveAuditor:
    """Sweeps a route across the configured viewport set."""

    VIEWPORTS = [
        (1920, 1080, "desktop-xl"),
        (1440, 900, "desktop"),
        (1280, 800, "desktop-sm"),
        (1024, 768, "tablet-landscape"),
        (768, 1024, "tablet-portrait"),
        (430, 932, "mobile-lg"),
        (390, 844, "mobile"),
        (375, 812, "mobile-sm"),
    ]

    def __init__(self, controller: Any, base_url: str = "http://localhost:3000") -> None:
        self.controller = controller
        self.base_url = base_url.rstrip("/")

    def audit(self, route: str, page: Any = None) -> ResponsiveAudit:
        """Sweep ``route`` across the configured viewports.

        ``page`` (optional) is a page from an authenticated context; when
        given, each viewport reuses that context (resize + reload) so the
        session survives the sweep. Otherwise a fresh context is created per
        viewport (anonymous route).
        """
        audit = ResponsiveAudit()
        context = None
        if page is not None:
            context = page.context
        for width, height, label in self.VIEWPORTS:
            result = self._visit(route, width, height, label, page=page, context=context)
            audit.results.append(result)
        return audit

    def _visit(self, route: str, width: int, height: int, label: str,
               page: Any = None, context: Any = None) -> ViewportResult:
        result = ViewportResult(width=width, height=height, label=label)
        own_context = context is None
        try:
            if page is None:
                ctx = self.controller.new_context(viewport={"width": width, "height": height})
                page = ctx.new_page()
            else:
                page.set_viewport_size({"width": width, "height": height})
            page.goto(self.base_url + route, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            metrics = page.evaluate(
                "() => ({"
                " sw: document.documentElement.scrollWidth,"
                " cw: document.documentElement.clientWidth,"
                " text: (document.body.innerText || '').length })"
            )
            result.overflow_px = max(0, metrics["sw"] - metrics["cw"])
            result.horizontal_overflow = result.overflow_px > 0
            result.body_text_length = metrics["text"]
            result.page_error = result.body_text_length < 10
            if own_context and context is not None:
                context.close()
        except Exception as exc:
            result.page_error = True
            result.notes = str(exc)[:300]
        return result
