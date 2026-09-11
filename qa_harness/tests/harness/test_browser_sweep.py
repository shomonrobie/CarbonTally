"""Browser sweep engine self-tests — no live stack, no real browser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from qa_harness.browser import sweep as sweep_module
from qa_harness.browser.routes.navigator import RouteVisit
from qa_harness.browser.sweep import (
    ANONYMOUS_PROTECTED_ROUTES,
    ROLE_SWEEPS,
    BrowserSweepEngine,
)
from qa_harness.core.config import TargetEnv
from qa_harness.core.evidence import EvidenceStore
from qa_harness.core.run_context import RunContext
from qa_harness.evidence.registry import EvidenceRegistry
from qa_harness.findings.store import FindingStore
from qa_harness.identities.loader import generate_full_population
from qa_harness.identities.resolver import IdentityResolver

ENV = TargetEnv(name="local", frontend_url="http://localhost:3000")


class FakePage:
    url = "/home"

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def wait_for_load_state(self, *args: Any, **kwargs: Any) -> None:
        pass

    def close(self) -> None:
        pass


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self._page = page

    def new_page(self) -> FakePage:
        return self._page

    def close(self) -> None:
        pass


class FakeController:
    def __init__(self, page: FakePage) -> None:
        self._page = page

    def new_context(self, **kwargs: Any) -> FakeContext:
        return FakeContext(self._page)

    def new_page(self) -> FakePage:
        return self._page

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


def _ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RunContext:
    monkeypatch.setenv("CARBON_TALLY_DEMO_PASSWORD", "demo-pass-2026!")
    return RunContext(
        env=ENV, env_name="local", git_sha="abc1234",
        store=FindingStore(tmp_path / "findings"),
        evidence=EvidenceStore(tmp_path / "evidence"),
        registry=EvidenceRegistry(EvidenceStore(tmp_path / "evidence2")),
    )


def _resolver() -> IdentityResolver:
    population = {i.email: i for i in generate_full_population()}
    return IdentityResolver(population=population)


def test_role_sweeps_cover_all_workspaces() -> None:
    workspaces = {spec["workspace"] for spec in ROLE_SWEEPS.values()}
    assert workspaces == {"customer", "consultant", "pe", "ops", "admin"}
    assert set(ANONYMOUS_PROTECTED_ROUTES) >= {"/home", "/consultant", "/ops"}
    # every sweep has at least one route and an expected landing
    for persona, spec in ROLE_SWEEPS.items():
        assert spec["routes"], persona
        assert sweep_module.LANDINGS[spec["workspace"]]


def test_anonymous_protected_route_flags_leak(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Anonymous visitor landing on an authenticated shell must be a finding."""
    ctx = _ctx(tmp_path, monkeypatch)
    controller = FakeController(FakePage())   # page.url stays "/home"
    engine = BrowserSweepEngine(ctx, ENV, _resolver(), controller=controller,
                                password="x")
    engine._anonymous_separation(controller, source="test")
    finding = next((f for f in engine.findings
                    if f.route == "/home" and f.category == "SEC"), None)
    assert finding is not None
    assert "protected route" in finding.title.lower()


def test_anonymous_redirect_is_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)

    class RedirectPage(FakePage):
        url = "http://localhost:3000/login"

        def goto(self, url: str, **kwargs: Any) -> None:
            # simulate ProtectedRoute redirecting to the public login surface
            self.url = "http://localhost:3000/login"

    engine = BrowserSweepEngine(ctx, ENV, _resolver(),
                                controller=FakeController(RedirectPage()),
                                password="x")
    engine._anonymous_separation(engine.controller, source="test")
    assert engine.findings == []


def test_route_findings_raw_js_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    engine = BrowserSweepEngine(ctx, ENV, _resolver(), controller=None, password="x")
    visit = RouteVisit(route="/home", role="customer_owner", ok=True,
                       raw_js_exception=True, body_text_length=100)
    engine._route_findings(visit, source="test")
    finding = next((f for f in engine.findings if f.category == "UI"), None)
    assert finding is not None
    assert finding.severity == "P1"


def test_route_findings_blank_screen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    engine = BrowserSweepEngine(ctx, ENV, _resolver(), controller=None, password="x")
    visit = RouteVisit(route="/home", role="customer_owner", ok=True, blank=True)
    engine._route_findings(visit, source="test")
    assert any("Blank screen" in f.title for f in engine.findings)


def test_sweep_skips_cleanly_when_playwright_missing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(tmp_path, monkeypatch)
    monkeypatch.setattr(sweep_module, "browser_available", lambda: False)
    engine = BrowserSweepEngine(ctx, ENV, _resolver(), controller=None, password="x")
    results = engine.run(source="test")
    assert results == []
    skipped = [f for f in ctx.raw_findings() if f.status == "NOT TESTABLE"]
    assert any("Browser sweep unavailable" in f.title for f in skipped)
