"""Browser QA layer (Playwright-based, gracefully optional)."""

from qa_harness.browser.playwright.controller import BrowserController, browser_available

__all__ = ["BrowserController", "browser_available"]
