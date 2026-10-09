#!/usr/bin/env python3
"""F-NAV-1 — BROWSER verification of consultant reach to ``/api/v3/reporting/*``.

F-NAV-1 (found in the CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 audit) is an
AUTHORIZATION gap, not a visual one: an authorised consultant operating a managed
client through the Client Operating Plane (``/consultant/clients/:clientId/*``)
was refused the three organisation-plane reporting endpoints —

    GET /api/v3/reporting/customer-dashboard?organization_id=...
    GET /api/v3/reporting/emissions-trend?organization_id=...
    GET /api/v3/reporting/member-activity?organization_id=...

— because those routes were gated by ``get_current_user`` only, and
``ensure_org_access`` refuses a consultant principal (a consultant is NOT an
``organization_members`` row, PD-12) before the consultant-aware admission step
runs. The consultant therefore saw the shared customer Home page with its
"Reporting overview" card replaced by an error message and its "Monthly emissions
trend" panel stuck on "Loading trend…" forever — on a client the consultant is
explicitly authorised to operate (PD-3/PD-7).

This script drives the REAL frontend at http://localhost:3000 with real headless
Chrome and a REAL password login against the lab GoTrue (no token injection) and
verifies the business outcome a human consultant now sees, plus the security
boundary that must NOT have been widened:

1. ``authorised_consultant`` (``consultant.owner``, firm owner; the firm holds
   ACTIVE grants for client_a and client_b): the client workspace Home page
   RENDERS the "Reporting overview" card (proves customer-dashboard 200), the
   trend panel is NOT stuck on "Loading trend…", no denial message is shown, and
   all three reporting routes were observed returning 200 for the CLIENT org.
2. ``consultant_scope`` — the SAME session's bearer token (the app's own, never
   printed) used directly against the API reaches the firm's ACTIVE grants
   (client_a AND client_b -> 200) and is still refused direct-customer
   organisations the firm does not manage (org_a, org_b -> 403). Knowing an
   organisation id grants nothing.
3. ``restricted_consultant_member`` (``consultant.member``, CAP-VIEW-CLIENT only):
   admitted to the client plane and reaches reporting — the F-1 admission
   CAPABILITY, not a relationship row, is what admits.
4. ``direct_customer`` regression (``owner.clienta``, an ordinary organisation
   owner): the member path is UNCHANGED — reporting renders and returns 200, while
   the same token is refused another tenant's organisation (org_a -> 403).

Reads only; writes only screenshots into the lab evidence directory. It never
prints a token, never prints a signed URL, and never mutates lab or demo data.

Usage::

    ~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_fnav1_reporting_scope_browser.py
    ~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_fnav1_reporting_scope_browser.py --json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

FRONTEND = "http://localhost:3000"
# The lab release backend is 127.0.0.1:8070 and the running CRA frontend is built
# with REACT_APP_API_URL=http://localhost:8070 (frontend/.env.local), so :8000 is
# only the CRA default and is NOT what this lab talks to. The real base is
# DISCOVERED from the app's own network traffic at run time (``current_api``);
# this constant is only the fallback when the app makes no API call at all.
API_FALLBACK = "http://localhost:8070"
CHROME = "/usr/bin/google-chrome"
REALTIME_NOISE = "realtime/v1/websocket"

CONSULTANT_OWNER_EMAIL = "consultant.owner@demo-lab.carbontally.local"
CONSULTANT_MEMBER_EMAIL = "consultant.member@demo-lab.carbontally.local"
CLIENT_A_OWNER_EMAIL = "owner.clienta@demo-lab.carbontally.local"

# The three F-NAV-1 endpoints (organisation plane, ``organization_id`` query param).
REPORTING_ROUTES = ("customer-dashboard", "emissions-trend", "member-activity")

# Deterministic Demo Lab entity ids (``lab.deterministic_uuid``) — the same ids
# every other lab fixture and verifier resolves, so no UUID is scraped from the UI.
ORG_A = lab.deterministic_uuid("org:org_a")            # direct customer, NOT a firm client
ORG_B = lab.deterministic_uuid("org:org_b")            # direct customer, NOT a firm client
CLIENT_A_ORG = lab.deterministic_uuid("org:client_a")  # consultant-managed client A
CLIENT_B_ORG = lab.deterministic_uuid("org:client_b")  # consultant-managed client B
CLIENT_A_ENGAGEMENT = lab.deterministic_uuid("engagement:client_a")

# The DashboardPage renders the D30 "Reporting overview" card ONLY when
# ``/reporting/customer-dashboard`` succeeded — the exact business outcome F-NAV-1
# broke. A failed trend request is swallowed by the page (``catch(() => undefined)``)
# and leaves the panel on "Loading trend…" forever, so that string is a reliable
# pre-fix failure signature.
DASHBOARD_MARKER = "Reporting overview"
TREND_LOADING_MARKER = "Loading trend…"
DENIED_ERROR_MARKERS = (
    "Organization access denied",
    "Organization member access required",
    "Consultant access required",
)

# The in-browser probe: replay the THREE real reporting URLs with the app's OWN
# session token. It returns status codes and the API error MESSAGE only — never a
# token, never a signed URL, never a body dump.
PROBE_JS = """
async (arg) => {
  let token = null;
  for (let i = 0; i < localStorage.length; i += 1) {
    const key = localStorage.key(i);
    if (!key || !key.endsWith('-auth-token')) continue;
    try {
      const raw = JSON.parse(localStorage.getItem(key) || 'null');
      if (raw && raw.access_token) token = raw.access_token;
      else if (raw && raw.currentSession && raw.currentSession.access_token) {
        token = raw.currentSession.access_token;
      }
    } catch (_e) { /* other localStorage keys are not our business */ }
  }
  if (!token) return { token: false, org: arg.orgId, results: [] };
  const results = [];
  for (const route of arg.routes) {
    let status = 0;
    let message = '';
    try {
      const url = arg.api + '/api/v3/reporting/' + route
        + '?organization_id=' + encodeURIComponent(arg.orgId);
      const resp = await fetch(url, { headers: { Authorization: 'Bearer ' + token } });
      status = resp.status;
      try {
        const body = await resp.json();
        message = (body && body.error && body.error.message) || '';
      } catch (_e) { message = ''; }
    } catch (_e) {
      status = -1;
      message = 'network';
    }
    results.push({ route: route, status: status, message: message });
  }
  return { token: true, org: arg.orgId, results: results };
}
"""


def shot(page, name: str) -> str:
    lab.ensure_dirs()
    out = lab.EVIDENCE_DIR / "browser" / f"fnav1_reporting_{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=True)
    return str(out)


def login(page, email: str, password: str) -> None:
    page.goto(f"{FRONTEND}/login", wait_until="domcontentloaded")
    page.wait_for_selector('input[type="email"]', timeout=30000)
    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_function("() => !location.pathname.startsWith('/login')", timeout=60000)


def watch_reporting(page) -> list[dict]:
    """Record every ``/api/v3/reporting/*`` response the app itself makes."""
    seen: list[dict] = []

    def on_response(response) -> None:
        url = response.url
        if "/api/v3/reporting/" not in url:
            return
        route = url.split("/api/v3/reporting/", 1)[1].split("?", 1)[0]
        if route not in REPORTING_ROUTES:
            return
        seen.append({"route": route, "status": response.status})

    page.on("response", on_response)
    return seen


def probe(page, org_id: str, api_base: str) -> dict:
    """Replay the three reporting URLs in-page with the app's own session token."""
    return page.evaluate(
        PROBE_JS, {"api": api_base, "orgId": org_id, "routes": list(REPORTING_ROUTES)}
    )


def statuses(probe_result: dict) -> dict:
    return {r["route"]: r["status"] for r in probe_result.get("results", [])}


def run() -> dict:
    from playwright.sync_api import sync_playwright

    password = lab.demo_password()
    checks: list[dict] = []
    notes: list[str] = []

    def check(name: str, ok: bool, detail: str = "", screenshot: str | None = None) -> None:
        item = {"check": name, "ok": bool(ok), "detail": detail}
        if screenshot:
            item["screenshot"] = screenshot
        checks.append(item)

    api_base_used = API_FALLBACK
    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        console_errors: list[str] = []

        # The API base the RUNNING app actually uses (never assumed): taken from
        # the app's own /api/v3/* traffic, so the out-of-band probes replay the
        # same origin — and therefore the same CORS allow-list — as the product.
        api_origins: list[str] = []

        def note_api_origin(request) -> None:
            url = request.url
            if "/api/v3/" not in url:
                return
            origin = url.split("/api/v3/", 1)[0]
            if origin not in api_origins:
                api_origins.append(origin)

        def current_api() -> str:
            return api_origins[0] if api_origins else API_FALLBACK

        def wait_for_marker(target, label: str) -> None:
            """Wait for the D30 reporting card; absence is asserted by the caller."""
            try:
                target.wait_for_function(
                    "() => document.body && document.body.innerText"
                    ".includes('Reporting overview')",
                    timeout=45000,
                )
            except Exception as exc:  # noqa: BLE001 — timeout is evidence, not a crash
                notes.append(f"{label}: reporting marker wait ended early ({type(exc).__name__})")

        # ------------------------------------------------------------------
        # 1. authorised consultant — the F-NAV-1 business outcome
        # ------------------------------------------------------------------
        try:
            page = context.new_page()
            page.on(
                "console",
                lambda m: console_errors.append(m.text) if m.type == "error" else None,
            )
            page.on("request", note_api_origin)
            login(page, CONSULTANT_OWNER_EMAIL, password)
            seen = watch_reporting(page)
            page.goto(
                f"{FRONTEND}/consultant/clients/{CLIENT_A_ENGAGEMENT}/home",
                wait_until="domcontentloaded",
            )
            wait_for_marker(page, "authorised_consultant")
            page.wait_for_timeout(2500)
            body = page.locator("body").inner_text()
            check(
                "harness: API origin discovered from the app's own traffic",
                bool(api_origins),
                current_api(),
            )
            check(
                "authorised_consultant: workspace is the client's consultant-operated plane",
                "Consultant-operated client workspace" in body,
                body[:200],
            )
            check(
                "authorised_consultant: 'Reporting overview' RENDERS (customer-dashboard ok)",
                DASHBOARD_MARKER in body,
                "marker missing — reporting was refused"
                if DASHBOARD_MARKER not in body
                else "rendered",
                shot(page, "consultant_client_a_home"),
            )
            check(
                "authorised_consultant: NO denial message on the page",
                not any(marker in body for marker in DENIED_ERROR_MARKERS),
                [m for m in DENIED_ERROR_MARKERS if m in body],
            )
            check(
                "authorised_consultant: trend panel NOT stuck on 'Loading trend…'",
                TREND_LOADING_MARKER not in body,
                "still 'Loading trend…' (emissions-trend refused)"
                if TREND_LOADING_MARKER in body
                else "resolved",
            )
            observed = {item["route"]: item["status"] for item in seen}
            for route in REPORTING_ROUTES:
                check(
                    f"authorised_consultant: {route} -> 200 for the client organisation",
                    observed.get(route) == 200,
                    f"observed={observed.get(route)} (routes seen: {sorted(observed)})",
                )

            # --------------------------------------------------------------
            # 2. consultant SCOPE — ACTIVE grants yes, other tenants no
            # --------------------------------------------------------------
            own_status = statuses(probe(page, CLIENT_A_ORG, current_api()))
            check(
                "consultant_scope: token reaches the firm's ACTIVE grant (client_a)",
                all(own_status.get(r) == 200 for r in REPORTING_ROUTES),
                own_status,
            )
            other_grant_status = statuses(probe(page, CLIENT_B_ORG, current_api()))
            check(
                "consultant_scope: firm's second ACTIVE grant reachable (client_b)",
                all(other_grant_status.get(r) == 200 for r in REPORTING_ROUTES),
                other_grant_status,
            )
            unrelated_a = statuses(probe(page, ORG_A, current_api()))
            check(
                "consultant_scope: NON-managed organisation DENIED (org_a -> 403)",
                all(unrelated_a.get(r) == 403 for r in REPORTING_ROUTES),
                unrelated_a,
            )
            unrelated_b = statuses(probe(page, ORG_B, current_api()))
            check(
                "consultant_scope: second non-managed organisation DENIED (org_b -> 403)",
                all(unrelated_b.get(r) == 403 for r in REPORTING_ROUTES),
                unrelated_b,
            )
            page.close()
        except Exception as exc:  # noqa: BLE001 — harness failure is a FAIL, not a pass
            check("authorised consultant session completed", False, f"{type(exc).__name__}: {exc}")

        # ------------------------------------------------------------------
        # 3. restricted firm member (CAP-VIEW-CLIENT only) — F-1 admission
        # ------------------------------------------------------------------
        try:
            page2 = context.new_page()
            page2.on("request", note_api_origin)
            login(page2, CONSULTANT_MEMBER_EMAIL, password)
            page2.goto(
                f"{FRONTEND}/consultant/clients/{CLIENT_A_ENGAGEMENT}/home",
                wait_until="domcontentloaded",
            )
            wait_for_marker(page2, "restricted_member")
            page2.wait_for_timeout(2000)
            member_body = page2.locator("body").inner_text()
            check(
                "restricted_member: CAP-VIEW-CLIENT admits and reporting renders",
                DASHBOARD_MARKER in member_body,
                member_body[:200],
                shot(page2, "consultant_member_client_a_home"),
            )
            check(
                "restricted_member: trend panel NOT stuck on 'Loading trend…'",
                TREND_LOADING_MARKER not in member_body,
                "still 'Loading trend…'"
                if TREND_LOADING_MARKER in member_body
                else "resolved",
            )
            page2.close()
        except Exception as exc:  # noqa: BLE001
            check("restricted member session completed", False, f"{type(exc).__name__}: {exc}")

        # ------------------------------------------------------------------
        # 4. direct customer regression — the ORDINARY member path is unchanged
        # ------------------------------------------------------------------
        try:
            page3 = context.new_page()
            page3.on(
                "console",
                lambda m: console_errors.append(m.text) if m.type == "error" else None,
            )
            seen3 = watch_reporting(page3)
            login(page3, CLIENT_A_OWNER_EMAIL, password)
            page3.goto(f"{FRONTEND}/home", wait_until="domcontentloaded")
            wait_for_marker(page3, "direct_customer")
            page3.wait_for_timeout(2500)
            customer_body = page3.locator("body").inner_text()
            check(
                "direct_customer: 'Reporting overview' still RENDERS (no member regression)",
                DASHBOARD_MARKER in customer_body,
                customer_body[:200],
                shot(page3, "direct_customer_home"),
            )
            check(
                "direct_customer: trend panel resolves",
                TREND_LOADING_MARKER not in customer_body,
                "still 'Loading trend…'" if TREND_LOADING_MARKER in customer_body else "resolved",
            )
            customer_seen = {item["route"]: item["status"] for item in seen3}
            for route in REPORTING_ROUTES:
                check(
                    f"direct_customer: {route} -> 200 for own organisation",
                    customer_seen.get(route) == 200,
                    f"observed={customer_seen.get(route)}",
                )
            cross_status = statuses(probe(page3, ORG_A, current_api()))
            check(
                "direct_customer: cross-tenant organisation DENIED (org_a -> 403)",
                all(cross_status.get(r) == 403 for r in REPORTING_ROUTES),
                cross_status,
            )
            page3.close()
        except Exception as exc:  # noqa: BLE001
            check("direct customer session completed", False, f"{type(exc).__name__}: {exc}")

        api_base_used = current_api()
        browser.close()

    real_errors = [
        text for text in console_errors
        if "favicon" not in text.lower() and REALTIME_NOISE not in text
    ]
    if real_errors:
        notes.append(f"console errors observed ({len(real_errors)}): {real_errors[:5]}")

    failed = [c for c in checks if not c["ok"]]
    return {
        "task": "F-NAV-1 consultant reach to /api/v3/reporting/*",
        "frontend": FRONTEND,
        "api": api_base_used,
        "checks": checks,
        "notes": notes,
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "status": "PASS" if checks and not failed else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="F-NAV-1 reporting-scope browser check")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    result = run()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"F-NAV-1 reporting-scope browser verification — {result['status']}")
        print(f"  frontend: {result['frontend']}   api: {result['api']}")
        for item in result["checks"]:
            mark = "PASS" if item["ok"] else "FAIL"
            print(f"  [{mark}] {item['check']}")
            if item.get("detail"):
                print(f"          {item['detail']}")
        for note in result["notes"]:
            print(f"  note: {note}")
        print(f"  {result['passed']} passed, {result['failed']} failed")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())



