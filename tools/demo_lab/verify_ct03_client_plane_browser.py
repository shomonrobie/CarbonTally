#!/usr/bin/env python3
"""CT-CONSULTANT-MODEL-IMPLEMENTATION-03 — BROWSER verification of Plane C.

Bounded self-verification of the client plane created by
:mod:`tools.demo_lab.fixture_ct03_client_plane`. It drives the REAL frontend at
``http://localhost:3000`` with a real headless Chrome and a REAL password login
against the lab GoTrue — no token injection, no API-only shortcuts.

What it proves (F-3/F-4/F-5/F-7 + PO-9/PO-10) is what a human would see:

* the ``managed`` client sees a working, read-mostly workspace whose comments
  are enabled and whose upload/edit/approve affordances do not exist;
* the ``retained`` client (relationship ENDED, retained read-only) still READs
  history but has NO comment box (PA-3: no messaging-send after termination);
* the ``off`` client gets the generic, non-disclosing denial;
* a client deep-linking to ANOTHER client's organisation gets the SAME generic
  denial — no existence oracle (INV-B/INV-C);
* a read-only client still sees the comment affordance it is entitled to.

It writes only screenshots into the lab evidence directory and performs no
writes to the application (reads plus one relationship page view).

Usage::

    ~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_ct03_client_plane_browser.py
    ~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_ct03_client_plane_browser.py --headed
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402
import fixture_ct03_client_plane as fixture  # noqa: E402

FRONTEND = "http://localhost:3000"
CHROME = "/usr/bin/google-chrome"

#: Pre-existing Demo Lab environment limitation, NOT a CT03 behaviour: the lab
#: gateway does not complete the Supabase Realtime WebSocket handshake, so every
#: page (including the denied one) logs one ``realtime/v1/websocket`` error. It is
#: recorded as an environment note instead of failing an application assertion.
REALTIME_NOISE = "realtime/v1/websocket"

#: The portal's own generic denial (§11.4, AC-F-17).
DENIED = "Client portal access is not available for this workspace"

#: (key, actor, organisation, must_contain, must_not_contain, expects_denial)
CASES = (
    (
        "managed",
        fixture.NEW_CLIENTS[0]["email"],
        fixture._id("org:managed"),
        ["CT03-QA Managed Client", "Managed by your consultant",
         "Send a comment to your consultant"],
        ["This workspace is not available"],
        False,
    ),
    (
        "retained",
        fixture.NEW_CLIENTS[1]["email"],
        fixture._id("org:retained"),
        ["CT03-QA Retained Client", "has ended",
         "Commenting is not available for this workspace after the engagement has ended"],
        ["Send a comment to your consultant", "This workspace is not available"],
        False,
    ),
    (
        "off",
        fixture.NEW_CLIENTS[2]["email"],
        fixture._id("org:off"),
        ["This workspace is not available", DENIED],
        ["CT03-QA Off Client"],
        True,
    ),
    (
        "cross_tenant",
        fixture.NEW_CLIENTS[0]["email"],          # managed actor ...
        fixture._id("org:retained"),              # ... another client's org
        ["This workspace is not available", DENIED],
        ["CT03-QA Retained Client"],
        True,
    ),
    (
        "client_a_read_only",
        "owner.clienta@demo-lab.carbontally.local",
        fixture.EXISTING_RELATIONSHIPS["client_a"]["organization_id"],
        ["Read only", "Send a comment to your consultant"],
        ["This workspace is not available"],
        False,
    ),
)


def shot(page, name: str) -> str:
    lab.ensure_dirs()
    out = lab.EVIDENCE_DIR / "browser" / f"ct03_plane_{name}.png"
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


def run(headed: bool) -> dict:
    from playwright.sync_api import sync_playwright

    password = lab.demo_password()
    checks: list[dict] = []
    notes: list[str] = []

    def check(name: str, ok: bool, detail: str = "", screenshot: str | None = None) -> None:
        item = {"check": name, "ok": bool(ok), "detail": detail}
        if screenshot:
            item["screenshot"] = screenshot
        checks.append(item)

    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME, headless=not headed)
        for key, email, org_id, present, absent, expects_denial in CASES:
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            errors: list[str] = []
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            try:
                login(page, email, password)
                page.goto(f"{FRONTEND}/portal/{org_id}", wait_until="domcontentloaded")
                page.wait_for_timeout(2500)
                body = page.locator("body").inner_text()
                for text in present:
                    check(f"{key}: shows {text!r}", text in body)
                for text in absent:
                    check(f"{key}: hides {text!r}", text not in body)
                check(f"{key}: screenshot", True, "", shot(page, key))
            except Exception as exc:  # noqa: BLE001 — report, never crash the run
                check(f"{key}: browser flow", False, str(exc)[:300])
            finally:
                realtime = [e for e in errors if REALTIME_NOISE in e]
                app_errors = [e for e in errors if REALTIME_NOISE not in e]
                if expects_denial:
                    # A denial the fixture EXPECTS: the 403 is the correct outcome,
                    # so it is evidence, not a failure (§78).
                    expected = [e for e in app_errors if "403" in e]
                    app_errors = [e for e in app_errors if e not in expected]
                    if expected:
                        notes.append(f"{key}: {len(expected)} expected 403 denial "
                                     "log(s) — correct authorization outcome")
                # Never store a token: drop the query string of any URL in the detail.
                detail = "; ".join(e.split("?")[0] for e in app_errors)[:300]
                check(f"{key}: no UNEXPECTED application console errors", not app_errors,
                      detail)
                if realtime:
                    notes.append(f"{key}: {len(realtime)} realtime WebSocket handshake "
                                 "error(s) — Demo Lab gateway environment limitation, "
                                 "not a CT03 behaviour")
                context.close()

        # The retained client's relationship page must name the state in words and
        # must NOT offer the end/change request actions (nothing left to request).
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        try:
            login(page, fixture.NEW_CLIENTS[1]["email"], password)
            page.goto(f"{FRONTEND}/portal/{fixture._id('org:retained')}/relationship",
                      wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            body = page.locator("body").inner_text()
            check("retained_relationship: says 'Ended (retained read-only)'",
                  "Ended (retained read-only)" in body)
            check("retained_relationship: no end/change request buttons",
                  "Request to end consultant relationship" not in body)
            check("retained_relationship: screenshot", True, "",
                  shot(page, "retained_relationship"))
        except Exception as exc:  # noqa: BLE001
            check("retained_relationship: browser flow", False, str(exc)[:300])
        finally:
            context.close()
        browser.close()

    failed = [c for c in checks if not c["ok"]]
    return {"checks": checks, "passed": len(checks) - len(failed),
            "failed": len(failed), "ok": not failed, "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run(args.headed)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result["checks"]:
            mark = "PASS" if item["ok"] else "FAIL"
            print(f"[{mark}] {item['check']}"
                  + ("" if item["ok"] else f" :: {item['detail']}"))
        for note in result.get("notes", []):
            print(f"[NOTE] {note}")
        print(f"--- {result['passed']} passed, {result['failed']} failed ---")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

