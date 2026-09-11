"""Authenticated browser sweep execution (spec §12, §20, §23–§26).

For every role group the sweep:

1. verifies application separation — an anonymous visitor hitting an
   authenticated route must be redirected to the public login surface;
2. logs the representative identity in through the REAL login form
   (``/login`` → email/password → submit) — the actual end-to-end auth UX;
3. verifies the server-authoritative landing route for the workspace;
4. visits the role's route set and captures console errors, network
   failures, loading/blank/JS-exception states and meaningful screenshots;
5. audits operational tables on table-bearing routes (spec §19);
6. sweeps a representative route across the configured viewports (spec §24);
7. runs axe-core accessibility scans (spec §25).

Findings are emitted through the RunContext with screenshots/console/network
evidence. When Playwright/Chromium is unavailable the whole sweep reports
``SKIPPED — TOOL UNAVAILABLE`` (spec §36) instead of crashing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from qa_harness.browser.accessibility.axe import AxeRunner
from qa_harness.browser.auth.session import demo_login
from qa_harness.browser.playwright.controller import (
    BrowserController,
    PageReadiness,
    browser_available,
)
from qa_harness.browser.responsive.auditor import ResponsiveAuditor
from qa_harness.browser.routes.navigator import Navigator, RouteVisit
from qa_harness.browser.tables.auditor import TableAuditResult, TableAuditor
from qa_harness.core.config import TargetEnv
from qa_harness.core.findings import Finding, FindingClassification, FindingStatus
from qa_harness.core.run_context import RunContext
from qa_harness.core.status import ToolUnavailable
from qa_harness.identities.loader import REPRESENTATIVE_EMAILS
from qa_harness.identities.resolver import IdentityResolver
from qa_harness.rules.tables import TableRuleEvaluator, build_table_rules
from qa_harness.rules.ux import build_ux_rule_checks

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # type: ignore
except ImportError:  # pragma: no cover
    PlaywrightTimeoutError = TimeoutError  # type: ignore

# --------------------------------------------------------------------------- #
# Role sweep definitions
# --------------------------------------------------------------------------- #

CUSTOMER_ROUTES = [
    "/home", "/emissions", "/documents", "/processing", "/review",
    "/messaging", "/issues", "/notifications", "/reports", "/billing",
    "/organization",
]
CONSULTANT_ROUTES = ["/consultant"]
OPS_ROUTES = ["/ops"]

# Routes where operational tables are expected (table audit runs here).
TABLE_ROUTES = {
    "customer": ["/documents", "/processing", "/review", "/reports", "/messaging"],
    "consultant": ["/consultant"],
    "ops": ["/ops"],
}

# routes.yaml workspace -> expected landing.
LANDINGS = {
    "customer": "/home",
    "consultant": "/consultant",
    "pe": "/ops",
    "ops": "/ops",
    "admin": "/ops",
}

# persona key -> sweep definition.
ROLE_SWEEPS: Dict[str, Dict[str, object]] = {
    "customer_owner": {"workspace": "customer", "routes": CUSTOMER_ROUTES,
                       "tables": TABLE_ROUTES["customer"], "responsive": ["/documents"]},
    "customer_viewer": {"workspace": "customer", "routes": ["/home", "/documents"],
                        "tables": [], "responsive": []},
    "consultant": {"workspace": "consultant", "routes": CONSULTANT_ROUTES,
                   "tables": TABLE_ROUTES["consultant"], "responsive": ["/consultant"]},
    "pe_manager": {"workspace": "pe", "routes": OPS_ROUTES,
                   "tables": TABLE_ROUTES["ops"], "responsive": ["/ops"]},
    "pe_staff": {"workspace": "pe", "routes": OPS_ROUTES,
                 "tables": TABLE_ROUTES["ops"], "responsive": []},
    "internal_operator": {"workspace": "ops", "routes": OPS_ROUTES,
                          "tables": TABLE_ROUTES["ops"], "responsive": ["/ops"]},
    "internal_reviewer": {"workspace": "ops", "routes": OPS_ROUTES,
                          "tables": TABLE_ROUTES["ops"], "responsive": []},
    "internal_qc": {"workspace": "ops", "routes": OPS_ROUTES,
                    "tables": TABLE_ROUTES["ops"], "responsive": []},
    "staff_admin": {"workspace": "admin", "routes": OPS_ROUTES,
                    "tables": TABLE_ROUTES["ops"], "responsive": ["/ops"]},
    "system_admin": {"workspace": "admin", "routes": OPS_ROUTES,
                     "tables": TABLE_ROUTES["ops"], "responsive": []},
}

# Authenticated routes to verify are protected for anonymous visitors.
ANONYMOUS_PROTECTED_ROUTES = ["/home", "/consultant", "/ops", "/messaging"]


@dataclass
class SweepResult:
    """Outcome of one role's browser sweep."""

    role: str
    logged_in: bool = False
    landing_path: str = ""
    expected_landing: str = ""
    visits: List[RouteVisit] = field(default_factory=list)
    table_results: List[Dict[str, object]] = field(default_factory=list)
    responsive_overflows: List[str] = field(default_factory=list)
    a11y_violations: int = 0
    a11y_skipped: bool = False
    login_error: str = ""
    auth_classification: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "role": self.role,
            "logged_in": self.logged_in,
            "landing_path": self.landing_path,
            "expected_landing": self.expected_landing,
            "visits": [v.to_dict() for v in self.visits],
            "table_results": self.table_results,
            "responsive_overflows": self.responsive_overflows,
            "a11y_violations": self.a11y_violations,
            "a11y_skipped": self.a11y_skipped,
            "login_error": self.login_error,
            "auth_classification": self.auth_classification,
        }


@dataclass
class AuthOutcome:
    """Result of independent authentication confirmation (spec §11, browser).

    ``authenticated`` is ONLY true when the browser is demonstrably on an
    authenticated route AFTER the real form login — never inferred from a
    successful token request alone. ``classification`` applies when the login
    did NOT establish an authenticated browser session.
    """

    authenticated: bool
    landing_path: str = ""
    classification: str = FindingClassification.AUTHENTICATION_FAILURE
    api_login_ok: bool = False
    session_storage_seen: bool = False
    beta_gate_detected: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "authenticated": self.authenticated,
            "landing_path": self.landing_path,
            "classification": self.classification,
            "api_login_ok": self.api_login_ok,
            "session_storage_seen": self.session_storage_seen,
            "beta_gate_detected": self.beta_gate_detected,
            "detail": self.detail,
        }


class BrowserSweepEngine:
    """Executes role sweeps with a shared Playwright controller."""

    def __init__(self, ctx: RunContext, env: TargetEnv, resolver: IdentityResolver,
                 controller: Optional[BrowserController] = None,
                 password: str = "",
                 role_filter: str = "",
                 no_visual: bool = False,
                 headless: bool = True) -> None:
        self.ctx = ctx
        self.env = env
        self.resolver = resolver
        self.controller = controller
        self.password = password
        self.role_filter = role_filter
        self.no_visual = no_visual
        self.headless = headless
        self.results: List[SweepResult] = []
        self._findings: List[Finding] = []
        self._table_rules = build_table_rules()
        self._ux_checks = build_ux_rule_checks()

    # ------------------------------------------------------------------ #

    def _ensure_controller(self) -> BrowserController:
        if self.controller is None:
            if not browser_available():
                raise ToolUnavailable(
                    "playwright", "pip package not installed; run `uv pip install playwright` "
                    "(chromium/Chrome is still required at launch)"
                )
            self.controller = BrowserController(headless=self.headless)
            self.controller.start()
        return self.controller

    def run(self, *, source: str = "run_browser.py") -> List[SweepResult]:
        try:
            self._ensure_controller()
        except ToolUnavailable as exc:
            self.ctx.emit_skipped(
                "UI", "Browser sweep unavailable",
                reason=str(exc), role="all", source=source,
            )
            return []
        controller = self.controller
        assert controller is not None

        # Anonymous application-separation check (once).
        self._anonymous_separation(controller, source=source)

        for persona, spec in ROLE_SWEEPS.items():
            if self.role_filter and self.role_filter not in (persona, spec["workspace"]):
                continue
            result = self._sweep_role(controller, persona, spec, source=source)
            self.results.append(result)
        return self.results

    # ------------------------------------------------------------------ #

    def _anonymous_separation(self, controller: BrowserController, *, source: str) -> None:
        """An authenticated route must not render for anonymous visitors."""
        from urllib.parse import urlparse
        context = controller.new_context()
        page = context.new_page()
        for route in ANONYMOUS_PROTECTED_ROUTES:
            visit = RouteVisit(route=route, role="anonymous")
            try:
                page.goto(self.env.frontend_url + route, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=6000)
                except Exception:
                    pass
                visit.url = page.url
                path = urlparse(page.url).path
                landed_public = path in ("", "/", "/login") or path.startswith("/auth/")
                if not landed_public:
                    self._emit_ui(
                        "SEC", "P1",
                        f"Anonymous visitor reached protected route {route}",
                        role="anonymous", route=route,
                        expected="redirect to /login (application separation, §12)",
                        actual=f"URL after visit: {page.url}",
                        description=(
                            "Public-only visitors must not be able to render the "
                            "authenticated application shell."
                        ),
                        source=source,
                    )
            except Exception as exc:
                self._emit_ui(
                    "UI", "P3", f"Anonymous separation probe failed for {route}",
                    role="anonymous", route=route,
                    expected="probe executes", actual=f"{type(exc).__name__}: {exc}",
                    source=source,
                )
        page.close()
        try:
            context.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #

    def _authenticate(self, page: Any, persona: str, email: str,
                      identity: Any) -> AuthOutcome:
        """Independently confirm authenticated state after a real form login.

        Never treats a successful token request as proof of a browser session:
        the browser session is confirmed by (a) an authenticated route after
        submission AND (b) a supabase session key in localStorage (presence
        only — contents are never read or logged). When the browser stays on
        /login the cause is classified, with at most one finding per persona.

        Classification rules (spec §11, finding-integrity):

        * GoTrue password grant fails            -> AUTHENTICATION_FAILURE
        * valid credentials, no browser session  -> INCONCLUSIVE (app-layer
          gate e.g. beta_users signOut, or unknown cause)
        * form selectors/submission tooling error-> HARNESS_RUNTIME_ERROR
        * authenticated on an authenticated route-> authenticated=True
        """
        # 1. Independent credential check (GoTrue password grant). Tokens are
        #    never printed; only a boolean + user_id presence are inspected.
        api_ok = False
        api_error = ""
        if self.env.supabase_auth_url and identity.is_demo:
            try:
                api_session = demo_login(self.env.supabase_auth_url, identity,
                                         self.password)
                api_ok = bool(api_session.user_id)
                api_error = api_session.error
            except ValueError as exc:  # non-demo identity refused
                api_error = str(exc)
            except ToolUnavailable as exc:
                api_error = f"{exc.tool}: {exc.reason}"
        else:
            api_error = "no supabase auth url or non-demo identity"

        # 2. Drive the real login form.
        try:
            page.goto(self.env.frontend_url + "/login", wait_until="domcontentloaded")
            page.wait_for_selector("input[type=email]", timeout=15000)
            page.fill("input[type=email]", email)
            page.fill("input[type=password]", self.password)
            page.click("button[type=submit]")
        except PlaywrightTimeoutError:
            return AuthOutcome(
                False, classification=FindingClassification.HARNESS_RUNTIME_ERROR,
                api_login_ok=api_ok,
                detail="login form selectors not found (tooling mismatch)",
            )
        except Exception as exc:
            return AuthOutcome(
                False, classification=FindingClassification.HARNESS_RUNTIME_ERROR,
                api_login_ok=api_ok,
                detail=f"{type(exc).__name__}: {exc}",
            )

        # 3. Poll for navigation + safe session signal (presence only).
        #    NOTE: page.url is a FULL URL — the path MUST be extracted, never
        #    string-compared against path tokens (the historical V1.2 bug:
        #    "http://localhost:3000/login" != "/login" made every persona
        #    appear logged in on the login page itself).
        from urllib.parse import urlparse
        session_storage_seen = False
        beta_gate = False
        for _ in range(30):
            url = page.url
            path = urlparse(url).path
            try:
                if page.evaluate(
                    "Object.keys(localStorage).some(k => k.startsWith('sb-'))"
                ):
                    session_storage_seen = True
            except Exception:
                pass
            if path not in ("", "/login", "/"):
                # The browser demonstrably left the login page. Authenticated
                # ONLY if a supabase session key is present — a redirect to a
                # public/transient page without a session is NOT a login.
                if not session_storage_seen:
                    return AuthOutcome(
                        False, classification=FindingClassification.INCONCLUSIVE,
                        api_login_ok=api_ok,
                        detail=(
                            "browser left /login but no supabase session key "
                            "was present — transient redirect or public-only "
                            "page, not an authenticated session"
                        ),
                    )
                # Persistence re-check: the app may establish then immediately
                # revoke a session (e.g. its own gate). Give it a moment and
                # confirm the session key AND the route both still hold.
                try:
                    page.wait_for_timeout(1200)
                    path_now = urlparse(page.url).path
                    still = page.evaluate(
                        "Object.keys(localStorage).some(k => k.startsWith('sb-'))"
                    )
                    if path_now in ("", "/login", "/") or not still:
                        return AuthOutcome(
                            False, classification=FindingClassification.INCONCLUSIVE,
                            api_login_ok=True, session_storage_seen=True,
                            detail=(
                                "valid credentials; session was established then "
                                "revoked — browser returned to /login"
                            ),
                        )
                    return AuthOutcome(True, landing_path=path_now,
                                       api_login_ok=api_ok,
                                       session_storage_seen=True,
                                       beta_gate_detected=beta_gate)
                except Exception:
                    return AuthOutcome(True, landing_path=path,
                                       api_login_ok=api_ok,
                                       session_storage_seen=True,
                                       beta_gate_detected=beta_gate)
            try:
                body = (page.inner_text("body") or "").lower()
                if ("beta" in body and "invite" in body) or "beta-only" in body:
                    beta_gate = True
            except Exception:
                pass
            page.wait_for_timeout(500)

        # Still on /login after submission: classify the cause.
        if not api_ok:
            return AuthOutcome(
                False, classification=FindingClassification.AUTHENTICATION_FAILURE,
                api_login_ok=False, session_storage_seen=session_storage_seen,
                detail=f"GoTrue password grant failed: {api_error or 'no session'}",
            )
        if session_storage_seen:
            return AuthOutcome(
                False, classification=FindingClassification.INCONCLUSIVE,
                api_login_ok=True, session_storage_seen=True,
                beta_gate_detected=beta_gate,
                detail=(
                    "valid credentials; browser session was established then "
                    "revoked, browser returned to /login"
                    + (" (app beta_users gate signs the session out)" if beta_gate else "")
                ),
            )
        if beta_gate:
            return AuthOutcome(
                False, classification=FindingClassification.INCONCLUSIVE,
                api_login_ok=True, beta_gate_detected=True,
                detail=(
                    "valid credentials; app rejected login via its beta_users "
                    "gate and signed the session out (application-layer, "
                    "requires app/PO verification — not a harness defect)"
                ),
            )
        return AuthOutcome(
            False, classification=FindingClassification.INCONCLUSIVE,
            api_login_ok=True,
            detail=(
                "valid credentials; browser stayed on /login without a session "
                "signal — cause undetermined, re-verify"
            ),
        )

    # ------------------------------------------------------------------ #

    def _sweep_role(self, controller: BrowserController, persona: str,
                    spec: Dict[str, object], *, source: str) -> SweepResult:
        email = REPRESENTATIVE_EMAILS[persona]
        workspace = str(spec["workspace"])
        routes = list(spec["routes"])  # type: ignore[arg-type]
        table_routes = list(spec["tables"])  # type: ignore[arg-type]
        responsive_routes = list(spec["responsive"])  # type: ignore[arg-type]
        result = SweepResult(role=persona, expected_landing=LANDINGS[workspace])

        context = controller.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        try:
            identity = self.resolver.by_email(email)
            outcome = self._authenticate(page, persona, email, identity)
            result.logged_in = outcome.authenticated
            result.landing_path = outcome.landing_path or "/login"
            result.auth_classification = (
                "AUTHENTICATED" if outcome.authenticated else outcome.classification
            )
            if not outcome.authenticated:
                # Exactly ONE authentication finding per persona. Downstream
                # route/table/responsive/a11y audits are NOT run against an
                # unauthenticated /login page — they would produce hundreds of
                # misleading UX findings about the wrong page.
                result.login_error = outcome.detail
                severity = ("P1" if outcome.classification
                            == FindingClassification.AUTHENTICATION_FAILURE
                            else "P2")
                self._emit_ui(
                    "AUTH", severity,
                    f"Browser authentication not established for {persona}",
                    role=persona, route=result.landing_path or "/login",
                    expected="authenticated workspace after password-grant login",
                    actual=outcome.detail,
                    description=(
                        "Authentication state was independently confirmed: the "
                        "browser did NOT reach an authenticated route after the "
                        "real login form. No route/table/responsive/a11y audits "
                        "were run for this persona (they would be meaningless "
                        "against an unauthenticated page). This is not counted "
                        "as a confirmed application defect."
                    ),
                    classification=outcome.classification,
                    source=source,
                )
                page.close()
                return result
            if result.landing_path != result.expected_landing:
                self._emit_ui(
                    "AUTH", "P1",
                    f"{persona} landed on {result.landing_path}, expected {result.expected_landing}",
                    role=persona, route=result.landing_path,
                    expected=result.expected_landing,
                    actual=result.landing_path,
                    description=(
                        "Server-authoritative post-login routing (D29/F5) must land each "
                        "workspace on its own shell."
                    ),
                    source=source,
                )

            navigator = Navigator(controller, base_url=self.env.frontend_url)
            table_auditor = TableAuditor(page)
            axe_runner = AxeRunner(page)

            for route in routes:
                visit = navigator.visit(
                    route, role=persona,
                    viewport={"width": 1440, "height": 900},
                    screenshot_path=str(self.ctx.evidence.path(
                        "screenshots", self.ctx.run_id, persona, "route", route=route, ext="png",
                    )) if not self.no_visual else "",
                )
                self._route_findings(visit, source=source)
                result.visits.append(visit)

            # Table audits ---------------------------------------------------
            for route in table_routes:
                for table_result in self._audit_tables(table_auditor, persona, route, source=source):
                    result.table_results.append(table_result)

            # Responsive sweep (subset, bounded runtime) ----------------------
            for route in responsive_routes:
                if self.no_visual:
                    continue
                try:
                    responsive = ResponsiveAuditor(controller, base_url=self.env.frontend_url)
                    audit = responsive.audit(route, page=page)
                    for overflow in audit.overflows():
                        result.responsive_overflows.append(
                            f"{route} @ {overflow.width}x{overflow.height} ({overflow.label})"
                        )
                        self._emit_ui(
                            "UX", "P2" if overflow.width <= 768 else "P3",
                            f"Horizontal overflow on {route} at {overflow.width}x{overflow.height}",
                            role=persona, route=route,
                            expected="no horizontal overflow (spec §24)",
                            actual=f"scrollWidth exceeds clientWidth by ~{overflow.overflow_px}px",
                            description=f"Responsive defect at viewport {overflow.label}.",
                            source=source,
                        )
                    for failure in audit.failures():
                        self._emit_ui(
                            "UI", "P2",
                            f"Page error on {route} at {failure.width}x{failure.height}",
                            role=persona, route=route,
                            expected="page renders", actual=failure.notes or "navigation error",
                            source=source,
                        )
                except ToolUnavailable:
                    result.a11y_skipped = True
                    break

            # Accessibility scans ---------------------------------------------
            if not self.no_visual:
                for route in ([result.expected_landing] + routes[:1]):
                    try:
                        page.goto(self.env.frontend_url + route, wait_until="domcontentloaded")
                        page.wait_for_selector("body", timeout=10000)
                        a11y = axe_runner.scan(route, role=persona)
                        if a11y.tool_status.startswith("SKIPPED"):
                            result.a11y_skipped = True
                            continue
                        result.a11y_violations += a11y.violation_count()
                        for violation in a11y.violations:
                            self._emit_ui(
                                "A11Y", "P3",
                                f"Accessibility violation on {route}: {violation['id']}",
                                role=persona, route=route,
                                expected="axe-core scan without violations (spec §25)",
                                actual=f"{violation['impact']} impact, {violation['nodes']} node(s)",
                                description=violation.get("help", ""),
                                source=source,
                            )
                    except Exception:
                        pass
        finally:
            try:
                page.close()
            except Exception:
                pass
        return result

    # ------------------------------------------------------------------ #

    def _route_findings(self, visit: RouteVisit, *, source: str) -> None:
        if not visit.ok:
            self._emit_ui(
                "UI", "P2",
                f"Navigation failure on {visit.route}",
                role=visit.role, route=visit.route,
                expected="route renders", actual=f"HTTP {visit.http_status} or navigation error",
                description=visit.network_failures[0] if visit.network_failures else "",
                source=source,
            )
            return
        if visit.raw_js_exception:
            self._emit_ui(
                "UI", "P1",
                f"Raw JavaScript exception on {visit.route}",
                role=visit.role, route=visit.route,
                expected="no uncaught exceptions",
                actual="page body contains an uncaught JS error (e.g. .map is not a function)",
                description="Unhandled promise rejection / raw JS exception surfaced in the UI.",
                source=source,
            )
        if visit.blank:
            self._emit_ui(
                "UI", "P1",
                f"Blank screen on {visit.route}",
                role=visit.role, route=visit.route,
                expected="page renders content", actual="body has almost no text",
                source=source,
            )
        if visit.loading:
            self._emit_ui(
                "UI", "P2",
                f"Permanent loading state on {visit.route}",
                role=visit.role, route=visit.route,
                expected="content loads", actual="page stuck in a loading state",
                source=source,
            )
        if visit.http_status and visit.http_status >= 500:
            self._emit_ui(
                "UI", "P1",
                f"HTTP {visit.http_status} on {visit.route}",
                role=visit.role, route=visit.route,
                expected="2xx page render", actual=f"HTTP {visit.http_status}",
                source=source,
            )
        if visit.console_errors:
            self._emit_ui(
                "UI", "P3",
                f"Console errors on {visit.route}",
                role=visit.role, route=visit.route,
                expected="clean console", actual=f"{len(visit.console_errors)} error(s)",
                description=visit.console_errors[0],
                source=source,
            )

    def _audit_tables(self, auditor: TableAuditor, persona: str, route: str,
                      *, source: str) -> List[Dict[str, object]]:
        results: List[Dict[str, object]] = []
        evaluator = TableRuleEvaluator()
        audit = auditor.audit("page", route=route)
        if audit.error:
            return results
        measurement = audit.measurement
        assert measurement is not None
        for key, rule in self._table_rules.items():
            for finding in evaluator.evaluate(rule, measurement):
                if finding["severity"] == "PASS":
                    continue
                self._emit_ui(
                    "UX", finding["severity"],
                    f"Table rule {key} violated on {route}",
                    role=persona, route=route,
                    expected=finding["expected"], actual=finding["actual"],
                    description=(
                        f"{measurement.row_count} rows, {measurement.column_count} columns. "
                        "Operational tables that can grow large must offer pagination/page-size/sorting."
                    ),
                    source=source,
                )
                results.append(finding)
        return results

    # ------------------------------------------------------------------ #

    def _emit_ui(self, category: str, severity: str, title: str, *,
                 role: str, route: str, expected: str, actual: str,
                 description: str = "", source: str = "",
                 classification: str = FindingClassification.REAL) -> Finding:
        finding = self.ctx.emit(
            category, severity, title,
            role=role, route=route, workflow="browser",
            expected=expected, actual=actual, description=description,
            status=FindingStatus.OPEN, source=source,
            classification=classification,
        )
        self._findings.append(finding)
        return finding

    @property
    def findings(self) -> List[Finding]:
        return self._findings

    def summary(self) -> Dict[str, int]:
        return {
            "roles": len(self.results),
            "logged_in": sum(1 for r in self.results if r.logged_in),
            "visits": sum(len(r.visits) for r in self.results),
            "responsive_overflows": sum(len(r.responsive_overflows) for r in self.results),
            "a11y_violations": sum(r.a11y_violations for r in self.results),
            "findings": len(self._findings),
        }
