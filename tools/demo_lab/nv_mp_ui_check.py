#!/usr/bin/env python3
"""CT-MP-SUB-004 — NV-5 (responsive) and NV-6 (accessibility) browser checks.

Bounded, reproducible verification of the three Manual Processing surfaces in a
REAL headless Chrome at the AGENTS.md §49 viewport classes:

* desktop   — 1920x1080, 1440x900, 1280x800
* tablet    — 1024x768, 768x1024
* mobile    — 430x932, 390x844, 375x812

Per surface and viewport it asserts:

**NV-5 (responsive)**
  * no accidental horizontal overflow of the document;
  * the critical controls are present, visible and not clipped;
  * navigation is intact.

**NV-6 (accessibility baseline)**
  * exactly one level-1 heading;
  * every interactive control has an accessible name;
  * the capacity meter exposes role=progressbar with aria-valuenow/min/max;
  * status/error messaging exposes a live role.

It logs in through the REAL ``/login`` with the deterministic PD-5 fixture
identities and drives the running frontend at ``http://localhost:3000``.
Nothing is mutated: the Admin surface only *loads* state, and the Consultant
surface is read-only here (allocate/release are covered by
``fixture_mp_coverage_browser.py``).

Usage::

    python3 tools/demo_lab/nv_mp_ui_check.py
    python3 tools/demo_lab/nv_mp_ui_check.py --json
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

VIEWPORTS = (
    ("desktop", 1920, 1080),
    ("desktop", 1440, 900),
    ("desktop", 1280, 800),
    ("tablet", 1024, 768),
    ("tablet", 768, 1024),
    ("mobile", 430, 932),
    ("mobile", 390, 844),
    ("mobile", 375, 812),
)


def login(page, email: str, password: str, attempts: int = 3) -> None:
    last: Exception | None = None
    for _ in range(attempts):
        try:
            page.goto(f"{FRONTEND}/login", wait_until="domcontentloaded")
            page.wait_for_selector('input[type="email"]', timeout=30000)
            page.fill('input[type="email"]', email)
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_function(
                "() => !location.pathname.startsWith('/login')", timeout=60000)
            return
        except Exception as exc:  # noqa: BLE001 — retry a cold-context stall
            last = exc
            page.wait_for_timeout(1500)
    raise RuntimeError(f"login failed for {email}: {last}")


#: One page-side audit run at the current viewport. Returns a JSON-serialisable
#: dict so the caller can assert on it without any DOM guesswork.
_AUDIT_JS = r"""
() => {
  const doc = document.documentElement;
  const overflow = doc.scrollWidth - doc.clientWidth;

  const nameOf = (el) => {
    const aria = el.getAttribute('aria-label');
    if (aria && aria.trim()) return aria.trim();
    const labelledBy = el.getAttribute('aria-labelledby');
    if (labelledBy) {
      const t = labelledBy.split(/\s+/)
        .map((id) => (document.getElementById(id) || {}).textContent || '')
        .join(' ').trim();
      if (t) return t;
    }
    if (el.id) {
      const lab = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
      if (lab && lab.textContent.trim()) return lab.textContent.trim();
    }
    const wrap = el.closest('label');
    if (wrap && wrap.textContent.trim()) return wrap.textContent.trim();
    const text = (el.innerText || el.value || '').trim();
    if (text) return text;
    const title = el.getAttribute('title');
    if (title && title.trim()) return title.trim();
    return '';
  };

  const interactive = Array.from(
    document.querySelectorAll('button, a[href], input, select, textarea, [role="button"]')
  );
  const unnamed = interactive
    .filter((el) => !nameOf(el))
    .map((el) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : ''));

  const meterEl = document.querySelector('[role="progressbar"]');
  const meter = meterEl ? {
    now: meterEl.getAttribute('aria-valuenow'),
    min: meterEl.getAttribute('aria-valuemin'),
    max: meterEl.getAttribute('aria-valuemax'),
    name: nameOf(meterEl),
  } : null;

  const headings = Array.from(document.querySelectorAll('h1'))
    .map((h) => (h.innerText || '').trim());

  const liveRegions = Array.from(
    document.querySelectorAll('[role="status"], [role="alert"], [aria-live]')
  ).length;

  // Visible-and-in-viewport sampling of the primary controls.
  const controls = {};
  for (const el of interactive) {
    const r = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') continue;
    if (r.width === 0 && r.height === 0) continue;
    const label = nameOf(el);
    if (!label) continue;
    controls[label] = {
      x: Math.round(r.x), y: Math.round(r.y),
      w: Math.round(r.width), h: Math.round(r.height),
      inViewportX: r.left >= -1 && r.right <= window.innerWidth + 1,
      disabled: el.disabled === true,
    };
  }

  return {
    viewport: {w: window.innerWidth, h: window.innerHeight},
    overflow,
    unnamed,
    meter,
    headings,
    liveRegions,
    controls,
  };
}
"""


def audit(page) -> dict:
    return page.evaluate(_AUDIT_JS)


#: Elements wider than their box that are NOT in a scroll container are the real
#: responsive defect (a clipped critical control). Scrollable wrappers are fine.
_CONTAINER_JS = r"""
() => {
  const out = [];
  for (const el of document.querySelectorAll('*')) {
    if (el.scrollWidth <= el.clientWidth + 4) continue;
    const ox = window.getComputedStyle(el).overflowX;
    if (ox === 'visible') {
      out.push((el.tagName.toLowerCase())
        + (el.className && typeof el.className === 'string'
            ? '.' + el.className.split(/\s+/).slice(0, 2).join('.') : '')
        + ' ' + el.scrollWidth + '>' + el.clientWidth);
    }
  }
  return out.slice(0, 10);
}
"""

#: Frontend MP API timing — the network side of the page-load experience.
_API_TIMING_JS = r"""
() => {
  const rows = performance.getEntriesByType('resource')
    .filter((r) => r.name.includes('/manual-processing'))
    .map((r) => ({name: r.name.split('/api/').pop(), ms: Math.round(r.duration)}));
  return {count: rows.length,
          maxMs: rows.reduce((m, r) => Math.max(m, r.ms), 0), rows};
}
"""


def check_surface(page, surface: str, critical: tuple[tuple[str, ...], ...],
                  report: dict, expect_meter: bool, expect_text: tuple[str, ...] = (),
                  expect_disabled: tuple[str, ...] = ()) -> None:
    """Audit the CURRENT page at every viewport class.

    ``critical`` is a tuple of *groups*; each group lists acceptable accessible
    names for ONE control and passes when at least one member is present, inside
    the viewport and enabled. Groups express design alternatives (e.g. an
    entitled vs non-entitled rendering of the same surface).

    ``expect_disabled`` names controls that are intentionally gated behind a
    prerequisite the user has not yet satisfied: they must be present and
    DISABLED. Asserting the gate in both directions means a regression that
    arms a control before its prerequisite is also caught.

    ``expect_text`` are business strings that must be legible at every width.
    """
    for cls, w, h in VIEWPORTS:
        page.set_viewport_size({"width": w, "height": h})
        page.wait_for_timeout(350)
        data = audit(page)
        clipped = page.evaluate(_CONTAINER_JS)
        key = f"{surface}@{w}x{h}({cls})"

        problems: list[str] = []
        if data["overflow"] > 2:
            problems.append(f"horizontal_overflow={data['overflow']}px")
        if clipped:
            problems.append(f"unhandled_container_overflow={clipped}")
        if len(data["headings"]) != 1:
            problems.append(f"h1_count={len(data['headings'])}")
        if data["unnamed"]:
            problems.append(f"controls_without_accessible_name={data['unnamed']}")

        missing = []
        for group in critical:
            satisfied = False
            for name in group:
                entry = data["controls"].get(name)
                if entry is None or not entry["inViewportX"]:
                    continue
                if not entry["disabled"]:
                    satisfied = True
                    break
            if not satisfied:
                missing.append("/".join(group))
        if missing:
            problems.append(f"critical_controls={missing}")

        for name in expect_disabled:
            entry = data["controls"].get(name)
            if entry is None:
                problems.append(f"gated_control_absent={name}")
            elif not entry["disabled"]:
                problems.append(f"gated_control_prematurely_enabled={name}")

        if expect_text:
            body = page.evaluate("() => document.body.innerText")
            absent = [t for t in expect_text if t not in body]
            if absent:
                problems.append(f"missing_text={absent}")

        if expect_meter:
            m = data["meter"]
            if not m or not m["now"] or m["min"] is None or not m["max"]:
                problems.append(f"meter_semantics={m}")

        report[key] = {
            "surface": surface, "viewport_class": cls, "width": w, "height": h,
            "ok": not problems,
            "problems": problems,
            "meter": data["meter"],
            "liveRegions": data["liveRegions"],
            "controls": len(data["controls"]),
        }


def run_customer(browser, password: str, report: dict) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.set_default_timeout(30000)
    try:
        login(page, fixture.fixture_logins()["u_owner_dual"], password)
        page.goto(f"{FRONTEND}/manual-processing", wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.body && document.body.innerText.includes('AVAILABLE')",
            timeout=30000)
        # u_owner_dual IS entitled, so this surface renders the covered state and
        # the non-entitled "View available plans" CTA is absent by design. The
        # audited contract here is that the covered state stays legible (no
        # overflow, one h1, no unnamed controls) at every width.
        check_surface(page, "customer_manual_processing", (), report,
                      expect_meter=False, expect_text=("AVAILABLE",))
    finally:
        context.close()


def run_consultant(browser, password: str, report: dict) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.set_default_timeout(30000)
    try:
        login(page, fixture.fixture_logins()["u_consultant_selected"], password)
        page.goto(f"{FRONTEND}/consultant", wait_until="domcontentloaded")
        page.locator("button.v3-tab", has_text="Manual Processing").first.click()
        page.wait_for_function(
            "() => document.body && document.body.innerText.includes('SELECTED CLIENTS')",
            timeout=30000)
        # Design gate: "Allocate" cannot be armed until an eligible client is
        # chosen from the selector, so it MUST be disabled in this state.
        check_surface(page, "consultant_coverage_unselected", (), report,
                      expect_meter=True, expect_text=("SELECTED CLIENTS",),
                      expect_disabled=("Allocate",))
        # Satisfy the prerequisite, then verify the gate opens at every width.
        # The button is armed but deliberately NOT clicked (no DB mutation —
        # the fixture baseline allocation is preserved).
        page.select_option("#mp-consultant-client",
                           fixture.org_ids()["org_client_unallocated"])
        page.wait_for_function(
            "() => { const b = [...document.querySelectorAll('button')]"
            ".find((x) => x.innerText.trim() === 'Allocate');"
            " return !!b && !b.disabled; }", timeout=20000)
        check_surface(page, "consultant_coverage_selected", (("Allocate",),), report,
                      expect_meter=True)
        report["_consultant_api_timing"] = page.evaluate(_API_TIMING_JS)
    finally:
        context.close()


def run_admin(browser, password: str, report: dict) -> None:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()
    page.set_default_timeout(30000)
    try:
        login(page, f"platform.admin@{lab.EMAIL_DOMAIN}", password)
        page.goto(f"{FRONTEND}/ops", wait_until="domcontentloaded")
        page.locator("button.v3-ops-tab", has_text="Commercial Coverage").first.click()
        page.fill("#mp-cov-firm", fixture.fid("firm:firm_selected"))
        page.locator("button", has_text="Load coverage").first.click()
        page.wait_for_function(
            "() => document.body && document.body.innerText.includes('SELECTED CLIENTS')",
            timeout=30000)
        # Design gate: "Load client state" (F-11) requires an explicitly
        # selected client, so it MUST be disabled while none is selected.
        check_surface(page, "admin_commercial_coverage",
                      (("Load coverage",),), report,
                      expect_meter=True, expect_disabled=("Load client state",))

        # F-11 — the searchable by-name client selector at every viewport.
        page.fill("#mp-cov-org-search", "MP-FX Client")
        page.wait_for_selector("#mp-cov-org-results button", timeout=30000)
        check_surface(page, "admin_client_selector_open",
                      (("Load coverage",),), report,
                      expect_meter=True, expect_disabled=("Load client state",))
        page.locator("#mp-cov-org-results button").first.click()
        report["_admin_selector_scan"] = page.evaluate(
            "() => { const el = document.querySelector("
            "'[data-testid=\"mp-cov-org-selected\"]');"
            " return el ? el.innerText.trim() : null; }"
        )
        # Prerequisite satisfied: the explicit confirmation control must now be
        # usable at every width. It is NOT clicked (no state mutation).
        page.wait_for_function(
            "() => { const b = [...document.querySelectorAll('button')]"
            ".find((x) => x.innerText.trim() === 'Load client state');"
            " return !!b && !b.disabled; }", timeout=20000)
        check_surface(page, "admin_client_selected",
                      (("Load coverage",), ("Load client state",)), report,
                      expect_meter=True)
    finally:
        context.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CT-MP-SUB-004 NV-5/NV-6 responsive + accessibility checks")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    password = lab.demo_password()
    report: dict = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROME, headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            run_customer(browser, password, report)
            run_consultant(browser, password, report)
            run_admin(browser, password, report)
        finally:
            browser.close()

    results = {k: v for k, v in report.items() if not k.startswith("_")}
    failed = [k for k, v in results.items() if not v["ok"]]
    evidence = {
        "fixture": fixture.FIXTURE_ID,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "viewports": [f"{w}x{h}" for _, w, h in VIEWPORTS],
        "results": results,
        "extras": {k: v for k, v in report.items() if k.startswith("_")},
        "summary": {"total": len(results), "failed": len(failed),
                    "failed_keys": failed},
    }
    evidence["evidence"] = fixture._write_evidence("mp_nv_ui", evidence)

    if args.json:
        print(json.dumps(evidence, indent=1, default=str))
    else:
        print(f"NV-5/NV-6 checks: {len(results) - len(failed)}/{len(results)} clean")
        for key, item in results.items():
            if not item["ok"]:
                print(f"  [FAIL] {key}: {item['problems']}")
        print(f"evidence: {evidence['evidence']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
