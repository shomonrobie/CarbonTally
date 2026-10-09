#!/usr/bin/env python3
"""CT-MP-SUB-004 / PD-5 — BROWSER verification of the Demo Lab QA fixture states.

Bounded self-verification of the fixture created by
:mod:`tools.demo_lab.fixture_mp_coverage`. It drives the REAL frontend at
``http://localhost:3000`` with a real headless Chrome and a REAL password login
against the lab GoAuth, then asserts the states the independent verification of
CT-MP-SUB-004 could not reach (finding **F-5**, NV-1…NV-4, NV-8).

It is deliberately small and read-mostly:

* every login is a real credential login through ``/login`` (no token injection);
* the only writes are the consultant **Allocate** then **Release** of one
  eligible client, which is exactly the NV-8 write path, and which is returned to
  the fixture baseline by re-running the fixture apply;
* it captures one meaningful screenshot per state (never blank/landing pages).

Usage::

    python3 tools/demo_lab/fixture_mp_coverage_browser.py
    python3 tools/demo_lab/fixture_mp_coverage_browser.py --headed --json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402
import fixture_mp_coverage as fixture  # noqa: E402

FRONTEND = "http://localhost:3000"
CHROME = "/usr/bin/google-chrome"


def _check(name: str, ok: bool, detail: str, screenshot: str | None = None) -> dict:
    item = {"check": name, "ok": bool(ok), "detail": detail}
    if screenshot:
        item["screenshot"] = screenshot
    return item


def wait_text(page, text: str, timeout: int = 30000) -> None:
    page.wait_for_function(
        "t => document.body && document.body.innerText.includes(t)",
        arg=text, timeout=timeout)


def meter(page) -> dict:
    """The first ARIA capacity meter on the page (never a visual guess)."""
    return page.evaluate(
        "() => { const el = document.querySelector('[role=\"progressbar\"]');"
        " return el ? {now: el.getAttribute('aria-valuenow'),"
        " max: el.getAttribute('aria-valuemax')} : null; }")


def shot(page, name: str) -> str:
    lab.ensure_dirs()
    out = lab.EVIDENCE_DIR / "browser" / f"mp_fixture_{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=True)
    return str(out)


def login(page, email: str, password: str, attempts: int = 3) -> str:
    """Real credential login through /login (retried — a cold context can be slow)."""
    last: Exception | None = None
    for _ in range(attempts):
        try:
            page.goto(f"{FRONTEND}/login", wait_until="domcontentloaded")
            page.wait_for_selector('input[type="email"]', timeout=30000)
            page.fill('input[type="email"]', email)
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_function("() => !location.pathname.startsWith('/login')",
                                   timeout=60000)
            return page.url
        except Exception as exc:  # noqa: BLE001 — retry a transient cold-context stall
            last = exc
            page.wait_for_timeout(1500)
    raise RuntimeError(f"login failed for {email}: {last}")


def _body(page) -> str:
    return page.locator("body").inner_text()


#: Customer states the fixture must make reachable (CT-UX-MP-SUB-003 §10).
CUSTOMER_CASES = (
    ("customer_direct", "u_owner_direct",
     ["AVAILABLE", "Included in your subscription",
      "Commercially entitled, not yet configured"], ["NOT INCLUDED"]),
    ("customer_dual", "u_owner_dual",
     ["AVAILABLE", "Your coverage includes:", "Direct subscription",
      "Consultant-sponsored coverage", "EFFECTIVE ENTITLEMENT",
      "GOVERNANCE STATUS", "Active", "Configured",
      "Both commercial paths support one operational Manual Processing service"],
     ["NOT INCLUDED"]),
    ("customer_sponsored", "u_owner_sponsored",
     ["AVAILABLE", "Provided through your consultant",
      "MP-FX Consultancy — All-Eligible Coverage"], ["NOT INCLUDED"]),
)


def run_customers(browser, password: str, checks: list) -> None:
    logins = fixture.fixture_logins()
    for name, actor_key, present, absent in CUSTOMER_CASES:
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(30000)
        try:
            login(page, logins[actor_key], password)
            page.goto(f"{FRONTEND}/manual-processing", wait_until="domcontentloaded")
            wait_text(page, "AVAILABLE")
            text = _body(page)
            ok = all(token in text for token in present) and \
                all(token not in text for token in absent)
            checks.append(_check(f"browser:{name}", ok,
                                 f"present={[t for t in present if t in text]} "
                                 f"absent_confirmed={[t for t in absent if t not in text]}",
                                 shot(page, name)))
        except Exception as exc:  # noqa: BLE001
            checks.append(_check(f"browser:{name}", False, str(exc)[:200]))
        finally:
            context.close()

    # Negative: a provisioned customer with no entitlement stays negative.
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(30000)
    try:
        login(page, f"owner.b@{lab.EMAIL_DOMAIN}", password)
        page.goto(f"{FRONTEND}/manual-processing", wait_until="domcontentloaded")
        wait_text(page, "NOT INCLUDED")
        text = _body(page)
        ok = "NOT INCLUDED" in text and "AVAILABLE" not in text
        checks.append(_check("browser:customer_negative_org_b", ok,
                             "NOT INCLUDED rendered; no AVAILABLE badge",
                             shot(page, "customer_negative_org_b")))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("browser:customer_negative_org_b", False, str(exc)[:200]))
    finally:
        context.close()


def _meter_is(page, value: str, timeout: int = 30000) -> None:
    page.wait_for_function(
        "v => { const el = document.querySelector('[role=\"progressbar\"]');"
        " return el && el.getAttribute('aria-valuenow') === v; }",
        arg=value, timeout=timeout)


def run_consultants(browser, password: str, checks: list) -> None:
    logins = fixture.fixture_logins()
    org = fixture.org_ids()

    # --- SELECTED_CLIENTS: capacity meter, covered clients, allocate/release ---
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(30000)
    try:
        login(page, logins["u_consultant_selected"], password)
        page.goto(f"{FRONTEND}/consultant", wait_until="domcontentloaded")
        page.locator("button.v3-tab", has_text="Manual Processing").first.click()
        wait_text(page, "SELECTED CLIENTS")
        wait_text(page, "MP-FX Client — Direct + Sponsored")
        scale = meter(page)
        text = _body(page)
        ok = (scale is not None and scale.get("max") == "3" and scale.get("now") == "1"
              and "Add Client" in text)
        checks.append(_check(
            "browser:consultant_selected", ok,
            f"meter={scale} add_client={'Add Client' in text}",
            shot(page, "consultant_selected")))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("browser:consultant_selected", False, str(exc)[:200]))

    # NV-8 — the Real-DB write path, exercised through the UI.
    try:
        page.select_option("#mp-consultant-client", org["org_client_unallocated"])
        page.locator("button.v3-btn-primary", has_text="Allocate").first.click()
        _meter_is(page, "2")
        allocated = meter(page)
        page.locator("button.danger", has_text="Release").first.click()
        _meter_is(page, "1")
        released = meter(page)
        ok2 = (allocated is not None and allocated.get("now") == "2"
               and released is not None and released.get("now") == "1")
        checks.append(_check(
            "browser:consultant_selected_allocate_release", ok2,
            f"after_allocate={allocated} after_release={released}",
            shot(page, "consultant_selected_allocate_release")))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("browser:consultant_selected_allocate_release", False,
                             str(exc)[:200]))
    finally:
        context.close()

    # --- ALL_ELIGIBLE_CLIENTS: populated eligible view, no allocation control --
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(30000)
    try:
        login(page, logins["u_consultant_allel"], password)
        page.goto(f"{FRONTEND}/consultant", wait_until="domcontentloaded")
        page.locator("button.v3-tab", has_text="Manual Processing").first.click()
        wait_text(page, "ALL ELIGIBLE CLIENTS")
        page.locator("button", has_text="View Eligible Clients").first.click()
        wait_text(page, "MP-FX Client — Sponsored")
        text = _body(page)
        ok = ("ALL ELIGIBLE CLIENTS" in text and "Add Client" not in text
              and "MP-FX Client — Sponsored" in text)
        checks.append(_check(
            "browser:consultant_all_eligible", ok,
            f"eligible_client_rendered={'MP-FX Client — Sponsored' in text} "
            f"no_allocate_control={'Add Client' not in text}",
            shot(page, "consultant_all_eligible")))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("browser:consultant_all_eligible", False, str(exc)[:200]))
    finally:
        context.close()


def run_admin(browser, password: str, checks: list) -> None:
    org = fixture.org_ids()
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(30000)
    try:
        login(page, f"platform.admin@{lab.EMAIL_DOMAIN}", password)
        page.goto(f"{FRONTEND}/ops", wait_until="domcontentloaded")
        page.locator("button.v3-ops-tab", has_text="Commercial Coverage").first.click()

        # selected-capacity firm (the covered-clients table renders organisation ids)
        page.fill("#mp-cov-firm", fixture.fid("firm:firm_selected"))
        page.locator("button", has_text="Load coverage").first.click()
        wait_text(page, "SELECTED CLIENTS")
        scale = meter(page)
        text = _body(page)
        ok = (scale is not None and scale.get("max") == "3" and scale.get("now") == "1"
              and "3 clients" in text and "1 / 3" in text
              and org["org_client_dual"] in text)
        checks.append(_check(
            "browser:admin_coverage_selected", ok,
            f"meter={scale} capacity_row={'3 clients' in text} "
            f"allocated_row={'1 / 3' in text} "
            f"covered_client_id={org['org_client_dual'] in text}",
            shot(page, "admin_coverage_selected")))

        # all-eligible firm (no allocation control; automatic coverage messaging)
        page.fill("#mp-cov-firm", fixture.fid("firm:firm_all"))
        page.locator("button", has_text="Load coverage").first.click()
        wait_text(page, "ALL ELIGIBLE CLIENTS")
        text = _body(page)
        ok = ("ALL ELIGIBLE CLIENTS" in text and "Automatically covered" in text
              and "Active consultant-client relationship" in text
              and "Eligible clients are covered automatically under ALL ELIGIBLE "
                  "CLIENTS coverage." in text)
        checks.append(_check(
            "browser:admin_coverage_all_eligible", ok,
            f"auto_coverage={'Automatically covered' in text} "
            f"eligibility_source={'Active consultant-client relationship' in text}",
            shot(page, "admin_coverage_all_eligible")))

        # effective entitlement for one organisation (commercial ≠ operational)
        # F-11 — the Admin client selector is now searchable by NAME; no raw id
        # is typed. Selecting a result performs no state change.
        page.fill("#mp-cov-org-search", "MP-FX Client — Direct + Sponsored")
        page.wait_for_selector("#mp-cov-org-results button", timeout=30000)
        page.locator("#mp-cov-org-results button").first.click()
        page.locator("button", has_text="Load client state").first.click()
        wait_text(page, "direct+sponsored")
        text = _body(page)
        ok = ("direct+sponsored" in text and "ENABLED" in text
              and "CONFIGURED" in text)
        checks.append(_check(
            "browser:admin_client_effective_state", ok,
            f"source_rendered={'direct+sponsored' in text} "
            f"governance={'ENABLED' in text} pe_configured={'CONFIGURED' in text}",
            shot(page, "admin_client_effective_state")))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("browser:admin_coverage", False, str(exc)[:200]))
    finally:
        context.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CT-MP-SUB-004 PD-5 browser verification of the QA fixture")
    parser.add_argument("--headed", action="store_true", help="show the browser")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    password = lab.demo_password()
    checks: list = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROME, headless=not args.headed,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            run_customers(browser, password, checks)
            run_consultants(browser, password, checks)
            run_admin(browser, password, checks)
        finally:
            browser.close()

    failed = [c for c in checks if not c["ok"]]
    evidence = {
        "fixture": fixture.FIXTURE_ID,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frontend": FRONTEND,
        "checks": checks,
        "summary": {"total": len(checks), "failed": len(failed)},
    }
    evidence["evidence"] = fixture._write_evidence("mp_fixture_browser", evidence)

    if args.json:
        print(json.dumps(evidence, indent=1, default=str))
    else:
        print(f"fixture browser verification: {len(checks) - len(failed)}/{len(checks)} as expected")
        for item in checks:
            print(f"  [{'PASS' if item['ok'] else 'FAIL'}] {item['check']}: {item['detail']}")
        print(f"evidence: {evidence['evidence']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
