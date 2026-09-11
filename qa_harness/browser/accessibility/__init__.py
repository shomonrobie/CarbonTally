"""Accessibility QA (axe-core via Playwright, optional)."""

from qa_harness.browser.accessibility.axe import AxeAudit, AxeRunner, A11yResult

__all__ = ["A11yResult", "AxeAudit", "AxeRunner"]
