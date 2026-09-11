"""Browser authentication confirmation self-tests (V1.2 first-run calibration).

The live first run reported ``logged_in=True landing=/login`` for every
persona. The root cause was harness-side: login "success" was inferred from
the token flow, not from an authenticated browser session, and the app's own
beta_users gate signs sessions back out — so the browser genuinely stayed on
/login. These tests pin the independent confirmation: authenticated ONLY when
the browser demonstrably reaches an authenticated route, with at most one
correctly-classified auth finding and NO downstream UX findings from an
unauthenticated /login page.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from qa_harness.browser import sweep as sweep_module
from qa_harness.browser.routes.navigator import RouteVisit
from qa_harness.browser.sweep import BrowserSweepEngine
from qa_harness.core.config import TargetEnv
from qa_harness.core.evidence import EvidenceStore
from qa_harness.core.findings import FindingClassification
from qa_harness.core.run_context import RunContext
from qa_harness.evidence.registry import EvidenceRegistry
from qa_harness.findings.store import FindingStore
from qa_harness.identities.loader import generate_full_population
from qa_harness.identities.resolver import IdentityResolver

ENV = TargetEnv(name="local", frontend_url="http://localhost:3000",
                supabase_auth_url="http://127.0.0.1:54425")

FAKE_ACCESS_TOKEN = "fake-access-token-never-printed-xyz"


class FakePage:
    """Configurable stand-in for a Playwright page.

    ``post_submit_path``: URL the page lands on after submit (None = stay on
    /login). ``beta_gate_text``: body text shown on /login. ``evaluate``
    simulates localStorage containing a supabase session key when
    ``session_storage`` is True.
    """

    def __init__(self, post_submit_path: Optional[str] = None,
                 body_text: str = "Sign in to CarbonTally",
                 session_storage: bool = True,
                 form_timeout: bool = False) -> None:
        self.url = "http://localhost:3000/login"
        self._post_submit_path = post_submit_path
        self._body_text = body_text
        self._session_storage = session_storage
        self._form_timeout = form_timeout
        self.submitted = False

    def goto(self, url: str, **kwargs: Any) -> None:
        self.url = url

    def wait_for_selector(self, selector: str, timeout: int = 0) -> None:
        if self._form_timeout:
            from playwright.sync_api import TimeoutError as PwTimeout
            raise PwTimeout("timeout 15000ms exceeded")

    def fill(self, selector: str, value: str) -> None:
        pass

    def click(self, selector: str) -> None:
        self.submitted = True
        if self._post_submit_path is not None:
            self.url = "http://localhost:3000" + self._post_submit_path

    def wait_for_timeout(self, ms: int) -> None:
        pass

    def inner_text(self, selector: str) -> str:
        return self._body_text

    def evaluate(self, script: str) -> bool:
        # script = "Object.keys(localStorage).some(k => k.startsWith('sb-'))"
        return self._session_storage

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


def _engine(ctx: RunContext, page: FakePage, password: str = "demo-pass-2026!",
            no_visual: bool = True) -> BrowserSweepEngine:
    return BrowserSweepEngine(ctx, ENV, _resolver(),
                              controller=FakeController(page),
                              password=password, no_visual=no_visual)


def _patch_demo_login(monkeypatch: pytest.MonkeyPatch, *, user_id: str,
                      error: str = "") -> None:
    def fake(auth_url: str, identity: Any, password: str,
             timeout: int = 15) -> Any:
        from qa_harness.browser.auth.session import AuthSession
        return AuthSession(email=identity.email, access_token=FAKE_ACCESS_TOKEN,
                           user_id=user_id, error=error)

    monkeypatch.setattr(sweep_module, "demo_login", fake)


def _patch_downstream_audits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace Navigator/TableAuditor/AxeRunner with benign fakes so an
    authenticated sweep produces no downstream findings by construction."""

    class FakeNavigator:
        def __init__(self, controller: Any, base_url: str = "") -> None:
            pass

        def visit(self, route: str, *, role: str = "", viewport: Optional[Dict[str, int]] = None,
                  screenshot_path: str = "") -> RouteVisit:
            return RouteVisit(route=route, role=role, ok=True, http_status=200,
                              body_text_length=200)

    class FakeTableAuditor:
        def __init__(self, page: Any) -> None:
            self.error = "skipped"
            self.measurement = None

        def audit(self, *args: Any, **kwargs: Any) -> "FakeTableAuditor":
            return self

    class FakeAxeRunner:
        def __init__(self, page: Any) -> None:
            self.tool_status = "SKIPPED — TOOL UNAVAILABLE"
            self.violations: List[Any] = []

        def scan(self, route: str, role: str = "") -> "FakeAxeRunner":
            return self

        def violation_count(self) -> int:
            return 0

    monkeypatch.setattr(sweep_module, "Navigator", FakeNavigator)
    monkeypatch.setattr(sweep_module, "TableAuditor", FakeTableAuditor)
    monkeypatch.setattr(sweep_module, "AxeRunner", FakeAxeRunner)


# --------------------------------------------------------------------------- #
# _authenticate unit tests
# --------------------------------------------------------------------------- #

def test_authenticate_success_only_when_browser_reaches_authenticated_route(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_demo_login(monkeypatch, user_id="u-1")
    page = FakePage(post_submit_path="/home")
    engine = _engine(_ctx(tmp_path, monkeypatch), page)
    identity = _resolver().by_email("owner.demo0001@demo.carbontally.local")
    outcome = engine._authenticate(page, "customer_owner", identity.email, identity)
    assert outcome.authenticated is True
    assert outcome.landing_path == "/home"
    assert outcome.api_login_ok is True
    assert outcome.session_storage_seen is True


def test_authenticate_stays_login_with_beta_gate_is_inconclusive(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_demo_login(monkeypatch, user_id="u-1")
    page = FakePage(body_text="❌ This is a beta-only application. Please use your beta invite.")
    engine = _engine(_ctx(tmp_path, monkeypatch), page)
    identity = _resolver().by_email("owner.demo0001@demo.carbontally.local")
    outcome = engine._authenticate(page, "customer_owner", identity.email, identity)
    assert outcome.authenticated is False
    assert outcome.classification == FindingClassification.INCONCLUSIVE
    assert outcome.api_login_ok is True
    assert outcome.beta_gate_detected is True


def test_authenticate_stays_login_session_revoked_is_inconclusive(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_demo_login(monkeypatch, user_id="u-1")
    page = FakePage(session_storage=True)  # token key seen, then back on /login
    engine = _engine(_ctx(tmp_path, monkeypatch), page)
    identity = _resolver().by_email("owner.demo0001@demo.carbontally.local")
    outcome = engine._authenticate(page, "customer_owner", identity.email, identity)
    assert outcome.authenticated is False
    assert outcome.classification == FindingClassification.INCONCLUSIVE
    assert outcome.session_storage_seen is True


def test_authenticate_api_login_failure_is_auth_failure(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_demo_login(monkeypatch, user_id="", error="login failed: HTTP 400")
    page = FakePage()
    engine = _engine(_ctx(tmp_path, monkeypatch), page)
    identity = _resolver().by_email("owner.demo0001@demo.carbontally.local")
    outcome = engine._authenticate(page, "customer_owner", identity.email, identity)
    assert outcome.authenticated is False
    assert outcome.classification == FindingClassification.AUTHENTICATION_FAILURE
    assert outcome.api_login_ok is False


def test_authenticate_form_timeout_is_harness_runtime_error(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_demo_login(monkeypatch, user_id="u-1")
    page = FakePage(form_timeout=True)
    engine = _engine(_ctx(tmp_path, monkeypatch), page)
    identity = _resolver().by_email("owner.demo0001@demo.carbontally.local")
    outcome = engine._authenticate(page, "customer_owner", identity.email, identity)
    assert outcome.authenticated is False
    assert outcome.classification == FindingClassification.HARNESS_RUNTIME_ERROR


# --------------------------------------------------------------------------- #
# _sweep_role gating tests
# --------------------------------------------------------------------------- #

def test_sweep_role_beta_gate_emits_one_finding_and_skips_audits(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_demo_login(monkeypatch, user_id="u-1")
    page = FakePage(body_text="❌ This is a beta-only application. Please use your beta invite.")
    ctx = _ctx(tmp_path, monkeypatch)
    engine = _engine(ctx, page)
    spec = sweep_module.ROLE_SWEEPS["customer_owner"]
    result = engine._sweep_role(engine.controller, "customer_owner", spec, source="test")
    assert result.logged_in is False
    assert result.landing_path == "/login"
    assert result.visits == []  # no downstream audits ran
    assert len(engine.findings) == 1  # exactly ONE auth finding
    finding = engine.findings[0]
    assert finding.category == "AUTH"
    assert finding.classification == FindingClassification.INCONCLUSIVE
    assert "beta" in finding.actual.lower()


def test_sweep_role_authenticated_runs_route_audits(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_demo_login(monkeypatch, user_id="u-1")
    _patch_downstream_audits(monkeypatch)
    page = FakePage(post_submit_path="/home")
    ctx = _ctx(tmp_path, monkeypatch)
    engine = _engine(ctx, page)
    spec = sweep_module.ROLE_SWEEPS["customer_owner"]
    result = engine._sweep_role(engine.controller, "customer_owner", spec, source="test")
    assert result.logged_in is True
    assert result.landing_path == "/home"
    assert len(result.visits) == len(spec["routes"])
    assert [f for f in engine.findings if f.category == "AUTH"] == []


def test_auth_never_logs_access_token(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_demo_login(monkeypatch, user_id="u-1")
    page = FakePage(body_text="❌ This is a beta-only application. Please use your beta invite.")
    ctx = _ctx(tmp_path, monkeypatch)
    engine = _engine(ctx, page)
    spec = sweep_module.ROLE_SWEEPS["customer_owner"]
    result = engine._sweep_role(engine.controller, "customer_owner", spec, source="test")
    serialized = str(result.to_dict()) + "".join(str(f.to_dict()) for f in engine.findings)
    assert FAKE_ACCESS_TOKEN not in serialized
    assert engine.password not in serialized
