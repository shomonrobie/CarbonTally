"""Playwright controller with graceful degradation."""

from qa_harness.browser.playwright.controller import BrowserController, browser_available

__all__ = ["BrowserController", "browser_available"]
